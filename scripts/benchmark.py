#!/usr/bin/env python3
"""Benchmark de percepción. Correr EN LA RASPBERRY PI 5 (ver scripts/pi_bench.sh).

Mide sobre cuadros reales de la cámara, con los modelos en serie (peor caso):
  - Hz de cámara recibidos y Hz de cuadros PROCESADOS (observaciones nuevas)
  - ms por cuadro de YOLO (personas), Face Landmarker y Pose Landmarker lite
  - edad del cuadro al terminar de procesarlo (ros2: desde header.stamp)
  - CPU real del proceso (100 % = 1 núcleo), RAM máxima, temperatura y frecuencia
Cada corrida agrega una fila a logs/benchmark.csv.

    python scripts/benchmark.py --model models/yolo26n_320_ncnn_model --imgsz 320 --threads 2
    python scripts/benchmark.py --model ... --no-face --no-pose      # sólo YOLO
"""

from __future__ import annotations

import argparse
import csv
import os
import resource
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from keepon import load_config  # noqa: E402
from keepon.camera import Camera  # noqa: E402

MODELS = ROOT / "models"


def read_int(path: str) -> int | None:
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


def set_ncnn_threads(yolo, n: int) -> bool:
    """Ultralytics no expone los hilos de NCNN: se busca el ncnn.Net cargado y se ajusta
    opt.num_threads (cada Extractor copia opt al crearse, así que aplica desde la próxima inferencia)."""
    seen, stack = set(), [yolo.predictor.model]
    while stack:
        o = stack.pop()
        if id(o) in seen:
            continue
        seen.add(id(o))
        net = getattr(o, "net", None)
        if net is not None and hasattr(net, "opt") and hasattr(net.opt, "num_threads"):
            net.opt.num_threads = n
            return True
        if hasattr(o, "__dict__"):
            stack += [v for v in vars(o).values() if hasattr(v, "__dict__")]
    return False


def load_mediapipe(face: bool, pose: bool, num: int):
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    f = p = None
    if face:
        f = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODELS / "face_landmarker.task")),
            running_mode=vision.RunningMode.VIDEO, num_faces=num,
            output_facial_transformation_matrixes=True))
    if pose:
        p = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODELS / "pose_landmarker_lite.task")),
            running_mode=vision.RunningMode.VIDEO, num_poses=num))
    return mp, f, p


def stats(xs):
    if not xs:
        return float("nan"), float("nan")
    xs = sorted(xs)
    return statistics.mean(xs), xs[int(0.95 * (len(xs) - 1))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=None, help="ros2|picamera2|gstreamer|opencv (default: config)")
    ap.add_argument("--model", default=str(MODELS / "yolo26n_320_ncnn_model"))
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--threads", type=int, default=0, help="hilos NCNN (0 = por defecto)")
    ap.add_argument("--no-yolo", action="store_true")
    ap.add_argument("--no-face", action="store_true")
    ap.add_argument("--no-pose", action="store_true")
    ap.add_argument("--num", type=int, default=2, help="máx. rostros/poses de MediaPipe")
    ap.add_argument("--secs", type=float, default=15.0)
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    cfg = load_config()
    if a.backend:
        cfg["camera"]["backend"] = a.backend

    import cv2

    yolo = None
    if not a.no_yolo:
        from ultralytics import YOLO
        yolo = YOLO(a.model, task="detect")
    mp, face, pose = load_mediapipe(not a.no_face, not a.no_pose, a.num)
    cam = Camera(cfg)
    frame, _, _ = cam.latest(timeout=10)
    if yolo:
        yolo.predict(frame, imgsz=a.imgsz, classes=[0], verbose=False)  # carga el backend
        if a.threads and not set_ncnn_threads(yolo, a.threads):
            print("aviso: no se encontró ncnn.Net para fijar hilos")
        for _ in range(3):
            yolo.predict(frame, imgsz=a.imgsz, classes=[0], verbose=False)

    t_y, t_f, t_p, t_tot, ages, n_per, n_face, n_pose = [], [], [], [], [], [], [], []
    temp0 = read_int("/sys/class/thermal/thermal_zone0/temp")
    cpu0, wall0 = os.times(), time.monotonic()
    _, _, n_start = cam.latest()
    last_n, ts_ms = -1, 0
    while time.monotonic() - wall0 < a.secs:
        frame, t_rx, n = cam.latest()
        if n == last_n:
            time.sleep(0.001)
            continue
        last_n = n
        stamp = cam.stamp
        t0 = time.perf_counter()
        if yolo:
            r = yolo.predict(frame, imgsz=a.imgsz, classes=[0], conf=0.4, verbose=False)[0]
            n_per.append(len(r.boxes))
        t1 = time.perf_counter()
        if face or pose:
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ts_ms = max(ts_ms + 1, int(time.monotonic() * 1000))
        if face:
            n_face.append(len(face.detect_for_video(img, ts_ms).face_landmarks))
        t2 = time.perf_counter()
        if pose:
            n_pose.append(len(pose.detect_for_video(img, ts_ms).pose_landmarks))
        t3 = time.perf_counter()
        t_y.append((t1 - t0) * 1e3)
        t_f.append((t2 - t1) * 1e3)
        t_p.append((t3 - t2) * 1e3)
        t_tot.append((t3 - t0) * 1e3)
        ages.append((time.time() - stamp) * 1e3 if stamp else (time.monotonic() - t_rx) * 1e3)
    wall = time.monotonic() - wall0
    cpu1 = os.times()
    _, _, n_end = cam.latest()
    cam.close()
    for m in (face, pose):
        if m:
            m.close()

    cpu_pct = 100 * ((cpu1.user - cpu0.user) + (cpu1.system - cpu0.system)) / wall
    hz = len(t_tot) / wall
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    temp1 = read_int("/sys/class/thermal/thermal_zone0/temp")
    freq = read_int("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    mean = lambda xs: statistics.mean(xs) if xs else float("nan")  # noqa: E731
    age_label = "edad cuadro (stamp)" if cam.backend == "ros2" else "recepción->resultado"

    print(f"\n=== {a.label or Path(a.model).name} | imgsz {a.imgsz} | hilos {a.threads or 'def'} | "
          f"yolo={'no' if a.no_yolo else 'sí'} face={'no' if a.no_face else 'sí'} pose={'no' if a.no_pose else 'sí'} ===")
    print(f"  cámara recibida       {(n_end - n_start) / wall:7.1f} Hz")
    print(f"  cuadros PROCESADOS    {hz:7.1f} Hz   {'OK' if hz >= 10 else 'NO LLEGA a 10 Hz'}")
    for name, xs in (("YOLO", t_y), ("Face Landmarker", t_f), ("Pose lite", t_p), ("TOTAL", t_tot), (age_label, ages)):
        m, p95 = stats(xs)
        print(f"  {name:<22}{m:7.1f} ms  p95 {p95:6.1f} ms")
    print(f"  CPU proceso           {cpu_pct:7.0f} %   (400 % = 4 núcleos)")
    print(f"  RAM máx               {rss:7.0f} MB")
    print(f"  personas/rostros/poses promedio: {mean(n_per):.2f} / {mean(n_face):.2f} / {mean(n_pose):.2f}")
    if temp1:
        print(f"  temperatura {temp0 / 1000:.1f} -> {temp1 / 1000:.1f} °C | frecuencia CPU {freq / 1e6 if freq else 0:.2f} GHz")

    out = ROOT / "logs" / "benchmark.csv"
    out.parent.mkdir(exist_ok=True)
    new = not out.exists()
    with open(out, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["fecha", "label", "modelo", "imgsz", "hilos", "yolo", "face", "pose", "cam_hz", "proc_hz",
                        "yolo_ms", "yolo_p95", "face_ms", "pose_ms", "total_ms", "total_p95", "edad_ms", "edad_p95",
                        "cpu_pct", "ram_mb", "personas", "rostros", "poses", "temp_c"])
        (ym, yp), (fm, _), (pm, _), (tm, tp), (am, ap95) = map(stats, (t_y, t_f, t_p, t_tot, ages))
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), a.label, Path(a.model).name, a.imgsz, a.threads,
                    int(not a.no_yolo), int(not a.no_face), int(not a.no_pose), round((n_end - n_start) / wall, 1),
                    round(hz, 1), *(round(x, 1) for x in (ym, yp, fm, pm, tm, tp, am, ap95)), round(cpu_pct),
                    round(rss), round(mean(n_per), 2), round(mean(n_face), 2), round(mean(n_pose), 2),
                    (temp1 or 0) / 1000])


if __name__ == "__main__":
    main()
