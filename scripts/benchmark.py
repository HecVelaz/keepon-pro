#!/usr/bin/env python3
"""Benchmark de percepción (M0). Correr EN LA RASPBERRY PI 5, con el cooler puesto.

Mide, sobre cuadros reales de la cámara:
  - FPS de captura
  - ms por cuadro de: YOLOv8n (personas), Face Landmarker, Pose Landmarker lite
  - Hz del pipeline completo (los tres en serie, como en el peor caso)
  - temperatura de la CPU (throttling)
  - "recepción -> resultado": desde que el backend entrega el cuadro. NO incluye
    exposición ni buffers internos de la cámara: no es la latencia completa (T6e).

    python scripts/benchmark.py                      # cámara según config.yaml
    python scripts/benchmark.py --backend opencv     # webcam USB (notebook)
    python scripts/benchmark.py --yolo ncnn --imgsz 320 --secs 30

Criterio de M0: pipeline completo >= 10 Hz. Si no llega, ver las opciones que imprime al final.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from keepon import load_config  # noqa: E402
from keepon.camera import Camera  # noqa: E402

MODELS = ROOT / "models"


def cpu_temp() -> float | None:
    try:
        return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000
    except OSError:
        return None


def load_yolo(kind: str, imgsz: int):
    from ultralytics import YOLO

    pt = MODELS / "yolov8n.pt"
    if not pt.exists():
        YOLO(str(pt))  # ultralytics lo descarga en esa ruta si no existe
    if kind == "ncnn":
        out = MODELS / f"yolov8n_{imgsz}_ncnn_model"  # el sufijo _ncnn_model es obligatorio
        if not out.exists():
            exported = YOLO(str(pt)).export(format="ncnn", imgsz=imgsz)
            Path(exported).rename(out)
        return YOLO(str(out), task="detect")
    return YOLO(str(pt))


def load_mediapipe():
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "face_landmarker.task")),
        running_mode=vision.RunningMode.VIDEO, num_faces=3,
        output_facial_transformation_matrixes=True))
    pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELS / "pose_landmarker_lite.task")),
        running_mode=vision.RunningMode.VIDEO, num_poses=3))
    return mp, face, pose


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=None, help="auto|picamera2|gstreamer|opencv")
    ap.add_argument("--yolo", default="ncnn", choices=["ncnn", "torch"])
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--secs", type=float, default=20.0)
    a = ap.parse_args()

    cfg = load_config()
    if a.backend:
        cfg["camera"]["backend"] = a.backend

    print("Cargando modelos...")
    yolo = load_yolo(a.yolo, a.imgsz)
    mp, face, pose = load_mediapipe()
    cam = Camera(cfg)
    print(f"Cámara: {cam.backend} {cam.w}x{cam.h}")

    import cv2

    frame, _, n0 = cam.latest()
    for _ in range(3):  # calentamiento
        yolo.predict(frame, imgsz=a.imgsz, classes=[0], verbose=False)

    t_yolo, t_face, t_pose, t_total, lat = [], [], [], [], []
    persons = faces = 0
    t_start = time.monotonic()
    _, _, n_start = cam.latest()
    last_n = -1
    while time.monotonic() - t_start < a.secs:
        frame, t_cap, n = cam.latest()
        if n == last_n:
            time.sleep(0.001)
            continue
        last_n = n
        t0 = time.perf_counter()
        r = yolo.predict(frame, imgsz=a.imgsz, classes=[0], verbose=False)[0]
        t1 = time.perf_counter()
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ts = int(time.monotonic() * 1000)
        fr = face.detect_for_video(img, ts)
        t2 = time.perf_counter()
        pose.detect_for_video(img, ts)
        t3 = time.perf_counter()
        t_yolo.append((t1 - t0) * 1e3)
        t_face.append((t2 - t1) * 1e3)
        t_pose.append((t3 - t2) * 1e3)
        t_total.append((t3 - t0) * 1e3)
        lat.append((time.monotonic() - t_cap) * 1e3)
        persons = max(persons, len(r.boxes))
        faces = max(faces, len(fr.face_landmarks))
    elapsed = time.monotonic() - t_start
    _, _, n_end = cam.latest()
    cam.close()
    face.close()
    pose.close()

    def row(name, xs):
        xs = sorted(xs)
        p95 = xs[int(0.95 * (len(xs) - 1))]
        print(f"  {name:<22}{statistics.mean(xs):8.1f} ms   p95 {p95:6.1f} ms")

    hz = len(t_total) / elapsed
    print(f"\n=== Resultados ({elapsed:.0f} s, {len(t_total)} cuadros procesados) ===")
    print(f"  captura cámara        {(n_end - n_start) / elapsed:8.1f} FPS")
    row(f"YOLOv8n {a.yolo} {a.imgsz}", t_yolo)
    row("Face Landmarker", t_face)
    row("Pose Landmarker lite", t_pose)
    row("TOTAL por cuadro", t_total)
    row("recepción -> resultado", lat)
    print(f"  pipeline completo     {hz:8.1f} Hz   {'OK (>=10 Hz)' if hz >= 10 else 'NO LLEGA a 10 Hz'}")
    print(f"  máx. personas / rostros vistos: {persons} / {faces}")
    t = cpu_temp()
    if t:
        print(f"  temperatura CPU       {t:8.1f} °C {'(riesgo de throttling > 80 °C)' if t > 80 else ''}")
    if hz < 10:
        print("\nOpciones si no llega a 10 Hz:\n"
              "  1. --imgsz 256 para YOLO\n"
              "  2. Pose cada 2 cuadros (el saludo dura >1 s, alcanza con 5-8 Hz)\n"
              "  3. Face Landmarker sólo sobre el recorte del objetivo y candidatos\n"
              "  4. Reemplazar YOLO por el detector de Pose (num_poses=3) como detector de personas\n"
              "  5. Correr YOLO y MediaPipe en hilos separados (la Pi 5 tiene 4 núcleos)")


if __name__ == "__main__":
    main()
