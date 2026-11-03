"""Enlace PC -> ESP32. Misma interfaz para el ESP32 real (serie) y el simulado.

El resto del software sólo usa `Link`: cambiar de simulador a robot real es
cambiar una línea (`--sim` en los scripts).
"""

from __future__ import annotations

import time

from .protocol import PROTOCOL_VERSION, Command, ProtocolError, Reply, parse_reply
from .sim_esp32 import SimESP32


class Link:
    """Numera los comandos, manda keepalive y junta las respuestas."""

    def __init__(self, keepalive_s: float = 0.2):
        self.seq = 0
        self.keepalive_s = keepalive_s
        self.last_tx = -1e9
        self.replies: list[Reply] = []

    def hello(self) -> None:
        """Abre sesión: el ESP32 verifica la versión y reinicia su numeración de sonidos."""
        self._write(f"HELLO {PROTOCOL_VERSION}\n")
        self.last_tx = self.now()

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
        out = []
        for r in self.esp.read():  # ida y vuelta por texto: valida igual que el enlace serie
            try:
                out.append(parse_reply(r.encode()))
            except ProtocolError:
                pass
        return out

    @property
    def neck_pos(self) -> tuple[float, float, float]:
        return self.esp.neck.pos


class SerialLink(Link):
    """ESP32 real por USB-serie. No bloqueante: lee sólo lo que ya llegó.

    Con `espejo_cfg`, lleva además un SimESP32 que recibe los mismos comandos y avanza en tiempo real.
    El firmware da las mismas posiciones que el simulador (tests/test_firmware_nucleo.py), así que el
    espejo dice dónde está el cuello a 100 Hz sin esperar los STATE (que llegan con cada PING, ~5 Hz).
    Cada STATE real se compara con el espejo: `max_desvio` guarda la mayor diferencia [°]."""

    DESVIO_RESYNC = 1.0  # [°] si el STATE real se separa más que esto, el espejo adopta la posición real

    def __init__(self, port: str, baud: int = 115200, keepalive_s: float = 0.2, espejo_cfg: dict | None = None):
        import serial  # pyserial

        super().__init__(keepalive_s)
        self.ser = serial.Serial(port, baud, timeout=0, write_timeout=0.05)
        self._buf = b""
        self._t0 = time.monotonic()
        self.esp = SimESP32(espejo_cfg) if espejo_cfg is not None else None
        self._t_espejo = 0.0
        self.max_desvio = 0.0
        self.resyncs = 0

    def now(self) -> float:
        return time.monotonic() - self._t0

    def _avanzar_espejo(self) -> None:
        """Lleva el espejo hasta ahora, en pasos de ~10 ms como el lazo del firmware."""
        t = self.now()
        if self.esp is not None and t > self._t_espejo:
            n = max(1, round((t - self._t_espejo) / 0.01))
            for _ in range(n):
                self.esp.tick((t - self._t_espejo) / n)
            self._t_espejo = t

    def _write(self, line: str) -> None:
        self.ser.write(line.encode("ascii"))
        if self.esp is not None:
            self._avanzar_espejo()
            self.esp.feed(line)
            self.esp.read()  # las respuestas del espejo no se usan: valen las del ESP32 real

    def _read(self) -> list[Reply]:
        self._buf += self.ser.read(self.ser.in_waiting or 0)
        *lines, self._buf = self._buf.split(b"\n")
        out = []
        for raw in lines:
            try:
                out.append(parse_reply(raw.decode("ascii", "replace")))
            except ProtocolError:
                pass  # ruido de arranque del ESP32, se ignora
        if self.esp is not None:
            self._avanzar_espejo()
            for r in out:
                self._comparar_espejo(r)
        return out

    def _comparar_espejo(self, r: Reply) -> None:
        if r.name == "HELLO" and r.seq == 0:  # el ESP32 real se reinició: el espejo también
            self.esp.reboot()
            self.esp.read()
        elif r.name == "STATE":
            real = [float(x) for x in r.args[1:4]]
            desvio = max(abs(a - b) for a, b in zip(real, self.esp.neck.pos))
            self.max_desvio = max(self.max_desvio, desvio)
            if desvio > self.DESVIO_RESYNC:  # p. ej. al arrancar con el cuello fuera de HOME
                # Posición y objetivo: queda quieto ahí hasta el próximo J, igual que el ESP32 real.
                for eje, v in zip(self.esp.neck.axes.values(), real):
                    eje.pos, eje.target, eje.vel = v, v, 0.0
                self.resyncs += 1

    @property
    def neck_pos(self) -> tuple[float, float, float]:
        if self.esp is None:
            raise AttributeError("SerialLink sin espejo: crearlo con espejo_cfg")
        self._avanzar_espejo()
        return self.esp.neck.pos
