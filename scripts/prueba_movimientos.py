"""Prueba de movimientos en grados con el firmware del robot y los servos montados (se corre en la Pi).

Abre sesión (HELLO), manda una secuencia corta de posturas con pausas y mantiene vivo el enlace con PING
(el watchdog de la ESP32 es de 500 ms). Sirve para comprobar la calibración de neck.servos: con cada
postura, el robot tiene que hacer lo que dice el texto (convención de docs/PROTOCOLO.md).

    cd ~/keepon && ~/keepon_env/bin/python scripts/prueba_movimientos.py [--pausa 2.5]
    ... prueba_movimientos.py --posturas "0 0 15; 0 0 0; 0 0 -25"   # solo esas posturas (yaw pitch roll)

Ctrl+C manda STOP (frena donde está) y sale. Antes de correrlo: el puerto libre (sin consola ni robot).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import serial  # noqa: E402

from keepon import load_config  # noqa: E402

# (yaw, pitch, roll) en grados y lo que se tiene que ver
POSTURAS = [
    ((0, 0, 0), "HOME: mirada al frente, cara vertical, cabeza derecha"),
    ((30, 0, 0), "yaw +30: gira a SU DERECHA"),
    ((-30, 0, 0), "yaw -30: gira a SU IZQUIERDA"),
    ((0, 0, 0), "HOME"),
    ((0, 20, 0), "pitch +20: la cara SUBE"),
    ((0, -15, 0), "pitch -15: la cara BAJA"),
    ((0, 0, 0), "HOME"),
    ((0, 0, 15), "roll +15: se inclina en sentido HORARIO visto desde atrás (hacia su derecha)"),
    ((0, 0, -25), "roll -25: se inclina en sentido ANTIHORARIO visto desde atrás (hacia su izquierda)"),
    ((0, 0, 0), "HOME"),
    ((60, 25, 0), "yaw +60, pitch +25: arriba a su derecha (cerca de los extremos)"),
    ((-60, -15, 0), "yaw -60, pitch -15: abajo a su izquierda (cerca de los extremos)"),
    ((0, 0, 0), "HOME"),
]


class Enlace:
    def __init__(self, puerto: str):
        self.s = serial.Serial(puerto, 115200, timeout=0)
        self.seq = 0
        self.buf = b""

    def mandar(self, texto: str) -> None:
        self.s.write((texto + "\n").encode())

    def comando(self, nombre: str, *args) -> None:
        self.seq += 1
        self.mandar(" ".join([nombre, str(self.seq), *map(str, args)]))

    def leer(self) -> list[str]:
        self.buf += self.s.read(4096)
        *lineas, self.buf = self.buf.split(b"\n")
        return [l.decode(errors="replace").strip() for l in lineas if l.strip()]

    def esperar(self, segundos: float) -> None:
        """Espera mandando PING cada 0,2 s (watchdog de 500 ms) y muestra los errores que lleguen."""
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            self.comando("PING")
            for l in self.leer():
                # Mientras se espera el Enter no hay PING: salta el watchdog (frena y mantiene la postura) y
                # el próximo comando lo rearma. Es esperado, no se muestra.
                if l == "ERR 0 WATCHDOG":
                    continue
                if l.startswith("ERR") or l.startswith("HELLO 0"):
                    print("   ESP32:", l)
            time.sleep(0.2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default=load_config()["serial"]["port"])
    ap.add_argument("--pausa", type=float, default=2.5, help="segundos en cada postura")
    ap.add_argument("--posturas", help='lista propia, ej. "0 0 15; 0 0 -25" (yaw pitch roll en grados)')
    a = ap.parse_args()
    posturas = POSTURAS
    if a.posturas:
        posturas = [(tuple(float(x) for x in p.split()), "postura pedida") for p in a.posturas.split(";")]

    e = Enlace(a.puerto)
    for _ in range(10):  # sesión: reintentar HELLO cada 0,5 s
        e.mandar("HELLO 1")
        time.sleep(0.5)
        if any(l.startswith("HELLO 1") for l in e.leer()):
            break
    else:
        sys.exit("la ESP32 no respondió al HELLO: ¿está cargado el firmware del robot y el puerto libre?")
    # Un Ctrl+C anterior deja el STOP enclavado (sigue así aunque se cierre la sesión): liberarlo.
    e.comando("RESUME")

    try:
        for (y, p, r), texto in posturas:
            input(f"\nEnter → {texto}  [J {y} {p} {r}]")
            e.comando("J", y, p, r)
            e.esperar(a.pausa)
    except KeyboardInterrupt:
        e.comando("STOP")
        print("\nSTOP enviado: frenó donde estaba (mandar RESUME y HOME para seguir).")
    finally:
        time.sleep(0.1)
        e.s.close()


if __name__ == "__main__":
    main()
