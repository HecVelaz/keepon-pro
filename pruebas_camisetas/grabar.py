#!/usr/bin/env python3
"""Graba una toma de la cámara del robot (NoIR) para ajustar el detector de camisetas.

Lee los cuadros que publica camera_node (lo arranca 'grabar.sh camara') y los guarda en
~/keepon/capturas/camisetas/<nombre>.mp4. capturas/ está fuera de git: son imágenes de
personas, solo de integrantes que aceptaron, y se borran cuando el detector esté ajustado.

Uso (en la Pi, mejor a través de grabar.sh):
    python grabar.py olimpia_frente_1.5m --segundos 10 --espera 5
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # noqa: E402

from keepon import load_config  # noqa: E402
from keepon.camera import Camera  # noqa: E402
from keepon.link import SerialLink  # noqa: E402

DESTINO = Path(__file__).resolve().parent.parent / "capturas" / "camisetas"
FPS = 15  # alcanza para ajustar umbrales y deja archivos chicos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("nombre", help="p. ej. olimpia_frente_1.5m (letras, números, punto, guion y guion bajo)")
    ap.add_argument("--segundos", type=float, default=10.0)
    ap.add_argument("--espera", type=float, default=5.0, help="cuenta regresiva antes de grabar")
    ap.add_argument("--pitido", type=float, default=0.0,
                    help="cada cuántos segundos pita el buzzer (0 = sin pitidos); al final suena R2D2")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.nombre):
        print("Nombre inválido: usar solo letras, números, '.', '-' y '_'.", file=sys.stderr)
        return 2

    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / f"{a.nombre}.mp4"
    if ruta.exists():
        print(f"Ya existe {ruta.name}: elegí otro nombre o borralo.", file=sys.stderr)
        return 2

    cfg = load_config()
    link = None
    if a.pitido > 0:
        try:  # el buzzer es una ayuda: si la ESP32 no responde, se graba igual
            link = SerialLink(cfg["serial"]["port"])
            link.hello()
            link.send("RESUME")  # si quedó un STOP enclavado, la ESP32 rechaza los sonidos
        except Exception as e:  # noqa: BLE001
            print(f"(sin pitidos: {e})")
    cam = Camera(cfg)

    def pitar(sonido: str) -> None:
        if link is not None:
            link.send("S", sonido)

    try:
        cam.latest(timeout=10)  # esperar a que camera_node entregue
        for s in range(int(a.espera), 0, -1):
            print(f"  graba en {s}…", flush=True)
            time.sleep(1)
        img, _, n_prev = cam.latest()
        h, w = img.shape[:2]
        out = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
        print(f"GRABANDO {a.nombre} ({a.segundos:.0f} s)", flush=True)
        pitar("BEEP_NEUTRO")
        t0, cuadros, prox = time.monotonic(), 0, time.monotonic()
        prox_pitido = a.pitido
        while time.monotonic() - t0 < a.segundos:
            if link is not None:
                link.poll()  # mantiene vivo el watchdog de la ESP32
                if a.pitido > 0 and time.monotonic() - t0 >= prox_pitido:
                    pitar("BEEP_NEUTRO")
                    prox_pitido += a.pitido
            img, _, n = cam.latest()
            if n != n_prev:
                out.write(img)
                cuadros += 1
                n_prev = n
            prox += 1.0 / FPS
            time.sleep(max(0.0, prox - time.monotonic()))
        out.release()
        pitar("R2D2")
        if link is not None:  # dejar que suene antes de cerrar (sin comandos, el watchdog lo corta)
            fin = time.monotonic() + 1.8
            while time.monotonic() < fin:
                link.poll()
                time.sleep(0.05)
        print(f"Listo: {ruta} ({cuadros} cuadros)")
    finally:
        cam.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
