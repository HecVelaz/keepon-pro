"""Prueba del firmware en la ESP32 real, por el puerto serie (se corre en la Pi).

No necesita los servos ni la fuente de 6 V: verifica el protocolo, los tiempos y la trayectoria
que reporta STATE (las referencias del generador, los servos no tienen realimentación).

    cd ~/keepon && ~/keepon_env/bin/python scripts/prueba_firmware_real.py [--puerto /dev/...]

Abrir el puerto NO reinicia la ESP32 (pyserial deja DTR y RTS en alto y el circuito de reset del
CH340 no actúa): la prueba la reinicia con un pulso de RTS y espera su "HELLO 0".
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import serial  # noqa: E402

from keepon import load_config  # noqa: E402
from keepon.protocol import ProtocolError, parse_reply  # noqa: E402
from keepon.sim_esp32 import SimESP32  # noqa: E402

resultados: list[tuple[bool, str]] = []


def chequear(ok: bool, texto: str) -> None:
    resultados.append((ok, texto))
    print(("  OK   " if ok else "  FALLA") + "  " + texto, flush=True)


class Puerto:
    def __init__(self, nombre: str):
        self.s = serial.Serial(nombre, 115200, timeout=0)
        self.buf = b""

    def enviar(self, linea: str) -> None:
        self.s.write((linea + "\n").encode("ascii"))

    def lineas(self, segundos: float) -> list[tuple[float, str]]:
        """Todo lo que llega durante `segundos`, con la hora de llegada."""
        fin, out = time.monotonic() + segundos, []
        while True:
            self.buf += self.s.read(self.s.in_waiting or 1)
            while b"\n" in self.buf:
                l, self.buf = self.buf.split(b"\n", 1)
                out.append((time.monotonic(), l.decode("ascii", "replace").strip()))
            if time.monotonic() >= fin:
                return out

    def esperar(self, condicion, segundos: float = 1.0) -> tuple[float, str] | None:
        """Primera línea que cumple `condicion` (las otras se descartan)."""
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            for t, l in self.lineas(0.005):
                if condicion(l):
                    return t, l
        return None

    def pedir(self, linea: str, segundos: float = 0.5) -> list[str]:
        self.enviar(linea)
        return [l for _, l in self.lineas(segundos)]


def reiniciar(p: Puerto) -> None:
    """Pulso de reset por el CH340: RTS baja EN mientras DTR está bajo."""
    p.s.dtr = False
    p.s.rts = True
    time.sleep(0.1)
    p.s.rts = False


def estado(p: Puerto, seq: int):
    """Manda PING y devuelve el STATE parseado (o None)."""
    p.enviar(f"PING {seq}")
    r = p.esperar(lambda l: l.startswith(f"STATE {seq} "), 0.5)
    return parse_reply(r[1]) if r else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default=load_config()["serial"]["port"])
    args = ap.parse_args()
    cfg = load_config()
    p = Puerto(args.puerto)

    print("Arranque y sesión")
    reiniciar(p)
    r = p.esperar(lambda l: l.startswith("HELLO 0"), 4.0)
    chequear(r is not None and r[1] == "HELLO 0 1 1", f"la ESP32 anuncia el arranque: {r[1] if r else 'nada'}")
    chequear(p.pedir("HELLO 1", 0.2) == ["HELLO 1 1 1"], "HELLO 1 abre la sesión")
    chequear(p.pedir("HELLO 7", 0.2) == ["ERR 0 BAD_VERSION"], "rechaza otra versión del protocolo")

    print("Latencia (PING → ACK, ida y vuelta por el puerto serie)")
    lat = []
    for k in range(50):
        t0 = time.monotonic()
        p.enviar(f"PING {100 + k}")
        r = p.esperar(lambda l, k=k: l == f"ACK {100 + k}", 0.5)
        if r:
            lat.append((r[0] - t0) * 1000)
        p.lineas(0.01)
    chequear(len(lat) == 50 and max(lat) < 30,
             f"50 PING: media {statistics.mean(lat):.1f} ms, máximo {max(lat):.1f} ms (tiene que ser < 30 ms)")

    print("Movimiento y trayectoria (comparada con SimESP32)")
    sim = SimESP32(cfg)
    sim.feed("J 1 70 30 -20")
    pasos = 0
    while sim.neck.moving():
        sim.tick(0.01)
        pasos += 1
    t_sim = pasos * 0.01
    t0 = time.monotonic()
    chequear(p.pedir("J 1 70 30 -20", 0.05) == ["ACK 1"], "J 1 70 30 -20 → ACK 1")
    llegada, seq = None, 200
    while time.monotonic() - t0 < 3.0:
        e = estado(p, seq)
        seq += 1
        if e and e.args[1:4] == (70.0, 30.0, -20.0):
            llegada = time.monotonic() - t0
            break
    chequear(llegada is not None and abs(llegada - t_sim) < 0.08,
             f"llega a 70/30/-20 en {llegada if llegada else float('nan'):.2f} s; el simulador dice {t_sim:.2f} s")
    chequear(p.pedir("J 2 200 -90 0", 0.1) == ["ACK 2 CLIPPED"], "un objetivo fuera de límites se recorta (CLIPPED)")

    print("Líneas mal formadas (no rearman el watchdog: entre una y otra va un PING)")
    for k, (linea, esperado) in enumerate( [("X 1", "ERR -1 UNKNOWN_CMD"), ("J 3 1 2", "ERR 3 BAD_ARGS"), ("J 4 1 x 0", "ERR 4 BAD_NUMBER"),
                            ("J a 0 0 0", "ERR -1 BAD_SEQ"), ("", "ERR -1 EMPTY"), ("CANCEL 5 NECK", "ERR 5 BAD_ARGS"),
                            ("J 6 " + "1" * 80 + " 0 0", "ERR -1 TOO_LONG"), ("PING " + "9" * 300, "ERR -1 TOO_LONG")]):
        chequear(p.pedir(linea, 0.1) == [esperado], f"{linea[:30]!r} → {esperado}")
        p.pedir(f"PING {300 + k}", 0.05)

    print("Sonidos (sin buzzer conectado: se verifican los tiempos)")
    p.lineas(0.05)
    t0 = time.monotonic()
    p.enviar("S 10 BEEP_NEUTRO")
    ack = p.esperar(lambda l: l == "ACK 10", 0.2)
    done = p.esperar(lambda l: l == "DONE 10", 1.0)
    d = (done[0] - t0) * 1000 if done else float("nan")
    chequear(ack is not None and done is not None and abs(d - 250) < 30, f"BEEP_NEUTRO: DONE a los {d:.0f} ms (250 ms)")
    otra = p.pedir("S 10 BEEP_NEUTRO", 0.5)
    chequear(otra == ["ACK 10"], f"un S reenviado con el mismo seq no se repite: {otra}")
    chequear(p.pedir("S 11 HIMNO", 0.1) == ["ERR 11 UNKNOWN_SOUND"], "sonido desconocido → ERR UNKNOWN_SOUND")
    p.pedir("S 12 POLCA", 0.1)
    e = estado(p, 13)
    chequear(e is not None and e.args[4] == "POLCA", "STATE informa el sonido que está sonando")
    p.pedir("CANCEL 14 SOUND", 0.1)
    e = estado(p, 15)
    chequear(e is not None and e.args[4] == "NONE", "CANCEL lo corta")

    print("STOP enclavado")
    p.pedir("J 20 -60 0 0", 0.25)
    chequear(p.pedir("STOP 21", 0.05) == ["ACK 21"], "STOP → ACK")
    chequear(p.pedir("J 22 0 0 0", 0.05) == ["ERR 22 STOP_ACTIVE"], "con STOP, J se rechaza")
    chequear(p.pedir("S 23 R2D2", 0.05) == ["ERR 23 STOP_ACTIVE"], "con STOP, S se rechaza")
    p.lineas(0.8)
    e = estado(p, 24)
    chequear(e is not None and e.args[0] == "STOPPED" and -60 < e.args[1] < 70,
             f"frena donde estaba, sin ir a HOME: {e.args if e else None}")
    chequear(p.pedir("RESUME 25", 0.05) == ["ACK 25"], "RESUME lo libera")
    chequear(p.pedir("HOME 26", 0.05) == ["ACK 26"], "HOME → ACK")

    print("Watchdog (500 ms sin comandos)")
    p.pedir("S 30 POLCA", 0.02)
    t0 = time.monotonic()
    w = p.esperar(lambda l: l == "ERR 0 WATCHDOG", 1.5)
    dw = (w[0] - t0) * 1000 if w else float("nan")
    chequear(w is not None and 480 < dw < 560, f"ERR 0 WATCHDOG a los {dw:.0f} ms")
    e = estado(p, 31)
    chequear(e is not None and e.args[0] == "RUN" and e.args[4] == "NONE",
             f"cortó el sonido y el próximo comando lo rearma: {e.args if e else None}")

    print("Reinicio")
    reiniciar(p)
    r = p.esperar(lambda l: l.startswith("HELLO 0"), 4.0)
    chequear(r is not None, "tras un reinicio vuelve a anunciar HELLO 0")
    e = estado(p, 40)
    chequear(e is not None and e.args[1:4] == (0.0, 0.0, 0.0), f"arranca en HOME: {e.args if e else None}")

    fallas = sum(not ok for ok, _ in resultados)
    print(f"\n{len(resultados) - fallas} de {len(resultados)} OK")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    try:
        main()
    except ProtocolError as e:
        print("respuesta mal formada:", e)
        sys.exit(1)
