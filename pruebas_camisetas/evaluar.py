#!/usr/bin/env python3
"""Evalúa keepon/camiseta.py con los videos grabados y con las imágenes de referencia.

Videos (en la Pi): ~/keepon/capturas/camisetas/<nombre>.mp4, grabados con grabar.sh. La clase esperada sale del
nombre: olimpia* → OLIMPIA, cerro* → CERRO, cualquier otro → nada (prueba de falsos positivos). Por cada video:
cuadros por clase (crudo, cuadro a cuadro) y qué fracción del tiempo queda activa la clase después del filtro de
6 cuadros. Sin mostrar ni guardar imágenes.

Imágenes de referencia (fotos de la camiseta sola, sin personas): no hay hombros, así que se evalúa el centro de
la foto como si fuera el torso.

Uso:
    python pruebas_camisetas/evaluar.py videos [--cada 1] [--detalle]
    python pruebas_camisetas/evaluar.py referencias
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import cv2  # noqa: E402

from keepon import load_config  # noqa: E402
from keepon.camiseta import CERRO, OLIMPIA, FiltroCamiseta, clasificar_hsv, detectar  # noqa: E402
from keepon.perception import POSE_KP  # noqa: E402

VIDEOS = RAIZ / "capturas" / "camisetas"
REFERENCIAS = RAIZ / "pruebas_camisetas" / "imagenes_referencia"


def esperada(nombre: str) -> str | None:
    n = nombre.lower()
    return OLIMPIA if n.startswith("olimpia") else CERRO if n.startswith("cerro") else None


def videos(cfg: dict, cada: int, detalle: bool) -> None:
    import mediapipe as mpipe
    from mediapipe.tasks.python import BaseOptions, vision

    print(f"{'video':22} {'esperada':9} {'cuadros':>7} {'sin torso':>9} {'OTRA':>6} {'OLIMPIA':>8} {'CERRO':>6}"
          f" {'filtrada OK':>11} {'filtrada MAL':>12}")
    for ruta in sorted(VIDEOS.glob("*.mp4")):
        pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(RAIZ / "models" / "pose_landmarker_lite.task")),
            running_mode=vision.RunningMode.VIDEO, num_poses=1))
        cap = cv2.VideoCapture(str(ruta))
        fps = cap.get(cv2.CAP_PROP_FPS) or 15
        esp = esperada(ruta.stem)
        crudo, filtro, bien, mal, n, i = Counter(), FiltroCamiseta(cfg["camiseta"]["confirmar"],
                                                                    cfg["camiseta"]["soltar"]), 0, 0, 0, 0
        malos = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            i += 1
            if (i - 1) % cada:
                continue
            h, w = f.shape[:2]
            r = pose.detect_for_video(mpipe.Image(image_format=mpipe.ImageFormat.SRGB,
                                                  data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
            n += 1
            if r.pose_landmarks:
                lm = r.pose_landmarks[0]
                kp = {k: (lm[j].x * w, lm[j].y * h, lm[j].visibility) for k, j in POSE_KP.items()}
                res = detectar(f, kp, cfg)
            else:
                res = None
            clase = res.clase if res else None
            crudo[clase] += 1
            activa = filtro.actualizar(clase)
            bien += activa == esp
            mal += activa is not None and activa != esp
            if detalle and clase is not None and clase != (esp or "OTRA") and len(malos) < 8:
                malos.append(f"    t={i / fps:5.1f}s {clase}: {res.detalle}")
        pose.close()
        print(f"{ruta.stem:22} {esp or '-':9} {n:7d} {crudo[None]:9d} {crudo['OTRA']:6d} {crudo[OLIMPIA]:8d}"
              f" {crudo[CERRO]:6d} {bien / n:11.0%} {mal / n:12.0%}")
        for m in malos:
            print(m)


def referencias(cfg: dict) -> None:
    for carpeta in sorted(p for p in REFERENCIAS.iterdir() if p.is_dir()):
        for ruta in sorted(carpeta.glob("*.*")):
            img = cv2.imread(str(ruta))
            if img is None:
                continue
            h, w = img.shape[:2]
            torso = img[int(h * .3):int(h * .8), int(w * .3):int(w * .7)]  # centro de la camiseta
            clase, d = clasificar_hsv(cv2.cvtColor(torso, cv2.COLOR_BGR2HSV), cfg["camiseta"])
            print(f"{carpeta.name:10} {ruta.name:45} {clase:8} {d}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("que", choices=("videos", "referencias"))
    ap.add_argument("--cada", type=int, default=1, help="evaluar 1 de cada N cuadros")
    ap.add_argument("--detalle", action="store_true", help="mostrar los números de algunos cuadros mal clasificados")
    a = ap.parse_args()
    cfg = load_config()
    videos(cfg, a.cada, a.detalle) if a.que == "videos" else referencias(cfg)


if __name__ == "__main__":
    main()
