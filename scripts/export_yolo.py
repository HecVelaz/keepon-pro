#!/usr/bin/env python3
"""Exporta YOLO a NCNN con una entrada fija (la red NCNN no cambia de tamaño en ejecución).

    python scripts/export_yolo.py /ruta/yolo26n.pt 320 256
    -> models/yolo26n_320_ncnn_model, models/yolo26n_256_ncnn_model

El .pt se COPIA a models/ antes de exportar: nunca se escribe junto al original
(en la Pi el original pertenece a ~/vision_estereo).
"""

import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

MODELS = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    src = Path(sys.argv[1]).expanduser()
    sizes = [int(x) for x in sys.argv[2:]] or [320]
    MODELS.mkdir(exist_ok=True)
    pt = MODELS / src.name
    if not pt.exists():
        shutil.copy2(src, pt)
    for s in sizes:
        out = MODELS / f"{pt.stem}_{s}_ncnn_model"
        if out.exists():
            print(f"ya existe: {out}")
            continue
        exported = Path(YOLO(str(pt)).export(format="ncnn", imgsz=s))
        exported.rename(out)
        print(f"exportado: {out}")


if __name__ == "__main__":
    main()
