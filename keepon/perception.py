"""Percepción en procesos paralelos (T2).

Las librerías de IA (NCNN, MediaPipe) no liberan el GIL de Python: en hilos no
corren a la vez (medido en la Pi: 2,11 s en serie vs 2,04 s en hilos). Por eso
cada modelo pesado va en su propio PROCESO, y cada proceso lee el último cuadro
directamente del tópico ROS 2 de la cámara:

  proceso "personas":  YOLO26n (personas) + tracker IoU propio (IDs)  ->  por cada persona,
                       recorte de la cabeza -> Face Landmarker -> orientación de la
                       cara con solvePnP e intrínsecos reales -> ME_MIRA (crudo)
                       (rostro y persona salen del MISMO cuadro: asociación directa)
  proceso "pose":      Pose Landmarker multi-persona (hombros, codos, muñecas)

Los resultados vuelven al proceso principal por colas (mensajes chicos, sin
imágenes), una por proceso y de capacidad mínima: si el principal se atrasa, el
resultado viejo se descarta y queda el nuevo (`_put_latest`). Así nunca se
acumula un retraso ni se bloquea un proceso de IA. Cada resultado lleva el
número de cuadro y su marca de tiempo.
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import queue
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import ROOT

# Puntos de Face Landmarker (MediaPipe) y modelo 3D genérico de cara [mm] para solvePnP.
# El modelo mira hacia +z (la nariz sobresale); y hacia arriba.
FACE_IDX = [1, 152, 33, 263, 61, 291]  # punta de nariz, mentón, ojo (izq. imagen), ojo (der.), boca izq., boca der.
FACE_3D = np.array([
    (0.0, 0.0, 0.0), (0.0, -63.6, -12.5), (-43.3, 32.7, -26.0),
    (43.3, 32.7, -26.0), (-28.9, -28.9, -24.1), (28.9, -28.9, -24.1)], dtype=np.float64)
# Face Detector (BlazeFace): 6 puntos. Orden de MediaPipe: ojo derecho del sujeto (a la
# IZQUIERDA en la imagen), ojo izquierdo, punta de nariz, centro de boca, trago derecho,
# trago izquierdo. Modelo 3D con medidas antropométricas promedio [mm], misma convención.
FACE6_3D = np.array([
    (-31.0, 33.0, -28.0), (31.0, 33.0, -28.0), (0.0, 0.0, 0.0),
    (0.0, -30.0, -22.0), (-72.0, 10.0, -95.0), (72.0, 10.0, -95.0)], dtype=np.float64)
POSE_KP = {"nariz": 0, "hombro_i": 11, "hombro_d": 12, "codo_i": 13, "codo_d": 14,
           "muneca_i": 15, "muneca_d": 16, "cadera_i": 23, "cadera_d": 24}


@dataclass
class FaceObs:
    dev_deg: float        # ángulo entre el eje de la cara y la línea cara->cámara
    yaw_deg: float        # componente horizontal (+ = gira hacia la derecha de la imagen)
    pitch_deg: float      # componente vertical
    nose: tuple           # punta de la nariz en la imagen [px]
    looking: bool         # dev_deg < looking_deg (crudo, sin filtro temporal)


@dataclass
class PersonObs:
    id: int
    box: tuple            # x1, y1, x2, y2 [px]
    conf: float
    face: FaceObs | None = None


@dataclass
class DetResult:
    kind: str             # "personas" | "pose"
    frame: int
    stamp: float          # header.stamp del cuadro (reloj de pared)
    t_done: float         # time.time() al terminar
    proc_ms: float
    persons: list[PersonObs] = field(default_factory=list)
    poses: list[dict] = field(default_factory=list)   # {nombre: (x, y, visibilidad)}
    parts: dict = field(default_factory=dict)         # desglose de tiempos [ms]


# ------------------------------------------------------------------ utilidades
def intrinsics(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    c = cfg["camera"]
    K = np.array([[c["fx"], 0, c["cx"]], [0, c["fy"], c["cy"]], [0, 0, 1]], dtype=np.float64)
    return K, np.array(c.get("dist", [0, 0, 0, 0, 0]), dtype=np.float64)


def head_crop(box, img_w: int, img_h: int) -> tuple[int, int, int]:
    """Cuadrado sobre la cabeza a partir de la caja de la persona: (x0, y0, lado)."""
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    side = max(64.0, min(0.75 * bw, 0.6 * bh if bh > bw else 0.75 * bw))
    cx = (x1 + x2) / 2
    x0 = int(round(cx - side / 2))
    y0 = int(round(y1 - 0.1 * side))
    side = int(round(side))
    x0 = max(0, min(x0, img_w - side))
    y0 = max(0, min(y0, img_h - side))
    return x0, y0, min(side, img_w, img_h)


def face_orientation(pts2d: np.ndarray, K: np.ndarray, dist: np.ndarray, looking_deg: float,
                     model3d: np.ndarray = FACE_3D) -> FaceObs | None:
    """Orientación de la cara respecto de la cámara con solvePnP (intrínsecos reales).
    pts2d[i] corresponde a model3d[i]; pts2d[2] (FACE6) o pts2d[0] (FACE) es la nariz."""
    import cv2

    ok, rvec, tvec = cv2.solvePnP(model3d, pts2d.astype(np.float64), K, dist, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok or tvec[2, 0] <= 0:
        return None
    R, _ = cv2.Rodrigues(rvec)
    fwd = R @ np.array([0.0, 0.0, 1.0])            # hacia dónde apunta la cara (coords. cámara)
    to_cam = -tvec[:, 0] / np.linalg.norm(tvec)     # de la cara hacia la cámara
    dev = math.degrees(math.acos(max(-1.0, min(1.0, float(fwd @ to_cam)))))
    yaw = math.degrees(math.atan2(fwd[0], -fwd[2]) - math.atan2(to_cam[0], -to_cam[2]))
    pitch = math.degrees(math.atan2(-fwd[1], -fwd[2]) - math.atan2(-to_cam[1], -to_cam[2]))
    nose = pts2d[int(np.argmin(np.linalg.norm(model3d, axis=1)))]  # el punto en el origen del modelo
    return FaceObs(dev, -yaw, pitch, (float(nose[0]), float(nose[1])), dev < looking_deg)


def _pin(cores: list[int] | None) -> None:
    """Fija el proceso a ciertos núcleos y limita los hilos de las librerías.
    Sin esto, NCNN, torch y MediaPipe quieren usar los 4 núcleos cada uno y se estorban
    (medido: YOLO pasó de 18 a 188 ms por cuadro). Debe llamarse ANTES de importar
    torch/ultralytics/mediapipe: los hilos que ya existen no heredan la afinidad."""
    if not cores:
        return
    os.sched_setaffinity(0, set(cores))
    n = str(len(cores))
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = n


def _repin_threads(cores: list[int] | None) -> None:
    """NCNN reubica sus hilos OpenMP en TODOS los núcleos al crearlos (verificado en la Pi:
    3 hilos con afinidad 0-3 en un proceso fijado a 0-1). Se vuelven a fijar todos los
    hilos del proceso; se repite cada tanto por si NCNN crea hilos nuevos."""
    if not cores:
        return
    for tid in os.listdir("/proc/self/task"):
        try:
            os.sched_setaffinity(int(tid), set(cores))
        except OSError:
            pass  # el hilo terminó


def _limit_ncnn_threads(n: int) -> None:
    """Ultralytics crea el ncnn.Net sin fijar hilos (usa todos). Los hilos deben fijarse
    ANTES de cargar el modelo (las convoluciones guardan el valor de carga): se reemplaza
    la clase Net por una que nace con opt.num_threads = n."""
    import ncnn

    base = ncnn.Net

    class _Net(base):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.opt.num_threads = n
            # Sin espera activa: si otro hilo (cámara, pose) comparte el núcleo, los hilos de
            # OpenMP giran esperando y YOLO pasa de 20 a ~70 ms (medido en la Pi).
            self.opt.openmp_blocktime = 0

    ncnn.Net = _Net


def _cpu_seconds() -> float:
    t = os.times()
    return t.user + t.system


# ------------------------------------------------------------------ procesos
def _put_latest(out: mp.Queue, r: DetResult) -> None:
    """Entrega sin bloquear, quedándose con lo más nuevo.

    Antes era una cola de 64 con put() bloqueante: si el principal no leía, se
    juntaban hasta ~2,4 s de resultados viejos y después los procesos se trababan
    (revisión de Codex). Ahora, si la cola está llena se saca el resultado viejo
    y se pone el nuevo. Sólo este proceso escribe en su cola."""
    try:
        out.put_nowait(r)
        return
    except queue.Full:
        pass
    try:
        out.get(timeout=0.05)  # timeout: el viejo puede estar todavía en tránsito por el pipe
    except queue.Empty:
        pass
    try:
        out.put_nowait(r)
    except queue.Full:
        pass  # el principal acaba de leer y otro quedó adelante: se pierde este, viene otro en ~60 ms


def _worker_personas(cfg: dict, out: mp.Queue, stop) -> None:
    p = cfg["perception"]
    _pin(p.get("cores_personas"))
    import cv2
    import mediapipe as mpipe
    from mediapipe.tasks.python import BaseOptions, vision
    from ultralytics import YOLO

    from .camera import Camera

    import torch

    torch.set_num_threads(1)  # sólo pre/posproceso de ultralytics; la red corre en NCNN
    cv2.setNumThreads(1)
    _limit_ncnn_threads(p.get("ncnn_threads", 2))
    K, dist = intrinsics(cfg)
    yolo = YOLO(str(ROOT / p["yolo_model"]), task="detect")
    use_det = p.get("face_model", "detector") == "detector"
    if use_det:  # BlazeFace, 6 puntos: pocos ms por recorte
        face = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=str(ROOT / "models" / "blaze_face_short_range.tflite")),
            running_mode=vision.RunningMode.IMAGE, min_detection_confidence=0.5))
    else:        # Face Landmarker, 478 puntos: ~49 ms por recorte en la Pi
        face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(ROOT / "models" / "face_landmarker.task")),
            running_mode=vision.RunningMode.IMAGE, num_faces=1))
    from .tracker import IoUTracker

    tracker = IoUTracker()  # el de ultralytics costaba ~68 ms/cuadro en la Pi
    cam = Camera(cfg)
    last, crop_px, cores = -1, p["face_crop_px"], p.get("cores_personas")
    while not stop.is_set():
        try:
            frame, _, n = cam.latest(timeout=5)
        except Exception:  # noqa: BLE001 - cámara caída: reintentar, el principal lo detecta por edad
            time.sleep(0.05)
            continue
        if n == last:
            time.sleep(0.002)
            continue
        last, stamp, t0 = n, cam.stamp, time.perf_counter()
        r = yolo.predict(frame, imgsz=p["yolo_imgsz"], conf=p["yolo_conf"], classes=[0], verbose=False)[0]
        t_yolo = time.perf_counter()
        h, w = frame.shape[:2]
        persons = []
        boxes = r.boxes
        ids = tracker.update([tuple(b) for b in boxes.xyxy.tolist()])
        order = sorted(range(len(boxes)), key=lambda i: -float(boxes.xyxy[i][3] - boxes.xyxy[i][1]))
        for rank, i in enumerate(order):
            box = tuple(float(v) for v in boxes.xyxy[i].tolist())
            po = PersonObs(ids[i], box, float(boxes.conf[i]))
            if rank < p["max_persons"]:
                x0, y0, side = head_crop(box, w, h)
                crop = cv2.resize(frame[y0:y0 + side, x0:x0 + side], (crop_px, crop_px))
                img = mpipe.Image(image_format=mpipe.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                res = face.detect(img)
                if use_det and res.detections:
                    kp = max(res.detections, key=lambda d: d.categories[0].score).keypoints
                    pts = np.array([(x0 + k.x * side, y0 + k.y * side) for k in kp[:6]])
                    po.face = face_orientation(pts, K, dist, p["looking_deg"], FACE6_3D)
                elif not use_det and res.face_landmarks:
                    lm = res.face_landmarks[0]
                    pts = np.array([(x0 + lm[j].x * side, y0 + lm[j].y * side) for j in FACE_IDX])
                    po.face = face_orientation(pts, K, dist, p["looking_deg"])
            persons.append(po)
        t1 = time.perf_counter()
        if n % 50 == 1 or n < 5:
            _repin_threads(cores)
        _put_latest(out, DetResult("personas", n, stamp, time.time(), (t1 - t0) * 1e3, persons=persons,
                          parts={"yolo": (t_yolo - t0) * 1e3, "rostros": (t1 - t_yolo) * 1e3}))
    cam.close()
    face.close()


def _worker_pose(cfg: dict, out: mp.Queue, stop) -> None:
    _pin(cfg["perception"].get("cores_pose"))
    import cv2
    import mediapipe as mpipe
    from mediapipe.tasks.python import BaseOptions, vision

    from .camera import Camera

    cv2.setNumThreads(1)
    pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(ROOT / "models" / "pose_landmarker_lite.task")),
        running_mode=vision.RunningMode.VIDEO, num_poses=cfg["perception"]["pose_num"]))
    cam = Camera(cfg)
    last, ts, cores = -1, 0, cfg["perception"].get("cores_pose")
    min_dt = 1.0 / cfg["perception"].get("pose_max_hz", 30)
    t_last = 0.0
    while not stop.is_set():
        try:
            frame, _, n = cam.latest(timeout=5)
        except Exception:  # noqa: BLE001
            time.sleep(0.05)
            continue
        if n == last or time.monotonic() - t_last < min_dt:
            time.sleep(0.002)
            continue
        t_last = time.monotonic()
        last, stamp, t0 = n, cam.stamp, time.perf_counter()
        h, w = frame.shape[:2]
        ts = max(ts + 1, int(time.monotonic() * 1000))
        res = pose.detect_for_video(
            mpipe.Image(image_format=mpipe.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), ts)
        poses = [{k: (lm[i].x * w, lm[i].y * h, lm[i].visibility) for k, i in POSE_KP.items()}
                 for lm in res.pose_landmarks]
        if n % 50 == 1 or n < 5:
            _repin_threads(cores)  # MediaPipe también crea hilos con afinidad propia
        _put_latest(out, DetResult("pose", n, stamp, time.time(), (time.perf_counter() - t0) * 1e3, poses=poses))
    cam.close()
    pose.close()


class Perception:
    """Arranca los procesos y entrega siempre el resultado más reciente de cada uno."""

    WORKERS = {"personas": _worker_personas, "pose": _worker_pose}
    QUEUE_SIZE = 2  # por proceso: como mucho un resultado de atraso (~60-100 ms)

    def __init__(self, cfg: dict, workers=("personas", "pose")):
        ctx = mp.get_context("spawn")  # proceso limpio: rclpy y MediaPipe no se llevan con fork
        self.stop = ctx.Event()
        self.queues: dict[str, mp.Queue] = {k: ctx.Queue(maxsize=self.QUEUE_SIZE) for k in workers}
        self.procs = {k: ctx.Process(target=self.WORKERS[k], args=(cfg, self.queues[k], self.stop), daemon=True,
                                     name=f"keepon_{k}")
                      for k in workers}
        for pr in self.procs.values():
            pr.start()
        self.latest: dict[str, DetResult] = {}

    def poll(self) -> list[DetResult]:
        """Vacía las colas sin bloquear; devuelve los resultados nuevos, en orden por proceso."""
        got = []
        for q in self.queues.values():
            while True:
                try:
                    r = q.get_nowait()
                except queue.Empty:
                    break
                self.latest[r.kind] = r
                got.append(r)
        return got

    def pids(self) -> dict[str, int]:
        return {k: p.pid for k, p in self.procs.items()}

    def close(self) -> None:
        self.stop.set()
        for p in self.procs.values():
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()


def proc_cpu_seconds(pid: int) -> float:
    """CPU acumulada (user+sys) de otro proceso, leyendo /proc (Linux)."""
    f = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return (int(f[11]) + int(f[12])) / os.sysconf("SC_CLK_TCK")
