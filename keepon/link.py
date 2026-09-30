"""Enlace PC -> ESP32. Misma interfaz para el ESP32 real (serie) y el simulado.

El resto del software sólo usa `Link`: cambiar de simulador a robot real es
cambiar una línea (`--sim` en los scripts).
"""

from __future__ import annotations

import time

from .protocol import Command, ProtocolError, Reply, parse_reply
from .sim_esp32 import SimESP32


class Link:
    """Numera los comandos, manda keepalive y junta las respuestas."""

    def __init__(self, keepalive_s: float = 0.2):
        self.seq = 0
        self.keepalive_s = keepalive_s
        self.last_tx = -1e9
        self.replies: list[Reply] = []

    def send(self, name: str, *args) -> int:
        self.seq += 1
        self._write(Command(name, self.seq, args).encode())
        self.last_tx = self.now()
        return self.seq

    def poll(self) -> list[Reply]:
        """Llamar en cada ciclo: lee respuestas pendientes y mantiene vivo el watchdog."""
        if self.now() - self.last_tx > self.keepalive_s:
            self.send("PING")
        out = self._read()
        self.replies += out
        return out

    # a implementar
    def now(self) -> float: ...
    def _write(self, line: str) -> None: ...
    def _read(self) -> list[Reply]: ...


class SimLink(Link):
    """ESP32 simulado. Con realtime=False el tiempo avanza sólo con advance(dt):
    sirve para escenarios reproducibles y tests."""

    def __init__(self, cfg: dict | None = None, realtime: bool = True, keepalive_s: float = 0.2):
        super().__init__(keepalive_s)
        self.esp = SimESP32(cfg)
        self.realtime = realtime
        self._t0 = time.monotonic()
        self._last = 0.0

    def now(self) -> float:
        return time.monotonic() - self._t0 if self.realtime else self.esp.t

    def advance(self, dt: float, substep: float = 0.01) -> None:
        """Avanza el tiempo simulado (el firmware corre su lazo a 100 Hz)."""
        n = max(1, round(dt / substep))
        for _ in range(n):
            self.esp.tick(dt / n)

    def _sync(self) -> None:
        if self.realtime:
            t = self.now()
            if t > self._last:
                self.advance(t - self._last)
                self._last = t

    def _write(self, line: str) -> None:
        self._sync()
        self.esp.feed(line)

    def _read(self) -> list[Reply]:
        self._sync()
        return self.esp.read()

    @property
    def neck_pos(self) -> tuple[float, float, float]:
        return self.esp.neck.pos


class SerialLink(Link):
    """ESP32 real por USB-serie. No bloqueante: lee sólo lo que ya llegó."""

    def __init__(self, port: str, baud: int = 115200, keepalive_s: float = 0.2):
        import serial  # pyserial

        super().__init__(keepalive_s)
        self.ser = serial.Serial(port, baud, timeout=0, write_timeout=0.05)
        self._buf = b""
        self._t0 = time.monotonic()

    def now(self) -> float:
        return time.monotonic() - self._t0

    def _write(self, line: str) -> None:
        self.ser.write(line.encode("ascii"))

    def _read(self) -> list[Reply]:
        self._buf += self.ser.read(self.ser.in_waiting or 0)
        *lines, self._buf = self._buf.split(b"\n")
        out = []
        for raw in lines:
            try:
                out.append(parse_reply(raw.decode("ascii", "replace")))
            except ProtocolError:
                pass  # ruido de arranque del ESP32, se ignora
        return out
