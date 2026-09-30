"""Simulador del ESP32: especificación ejecutable del firmware.

Implementa exactamente el comportamiento que debe tener firmware/keepon_fw:
  - J conserva sólo la referencia más reciente (no encola movimientos).
  - STOP frena suave y queda ENCLAVADO hasta RESUME (no va a HOME).
  - Watchdog: sin comandos durante watchdog_ms corta el sonido y frena,
    manteniendo la postura. El próximo comando válido lo rearma.
  - S con un seq ya recibido no se reproduce dos veces.
  - Todo es no bloqueante: tick(dt) avanza el tiempo.
"""

from __future__ import annotations

from . import load_config
from .protocol import PROTOCOL_VERSION, Command, ProtocolError, Reply, parse_command
from .trajectory import Neck

FW_VERSION = 1
RUN, STOPPED, WATCHDOG = "RUN", "STOPPED", "WATCHDOG"


class SimESP32:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_config()
        self.neck = Neck.from_config(self.cfg)
        self.sound_len = dict(self.cfg["sounds"])
        self.watchdog_s = self.cfg["serial"]["watchdog_ms"] / 1000.0
        self.t = 0.0
        self.state = RUN
        self.last_rx = 0.0
        self.sound: str | None = None
        self.sound_seq = -1
        self.sound_end = 0.0
        self.last_sound_seq = -1
        self.out: list[Reply] = [Reply("HELLO", 0, (FW_VERSION, PROTOCOL_VERSION))]

    # ------------------------------------------------------------ entrada
    def feed(self, line: str) -> None:
        try:
            cmd = parse_command(line)
        except ProtocolError as e:
            self.out.append(Reply("ERR", e.seq, (e.reason,)))
            return
        self.last_rx = self.t
        if self.state == WATCHDOG:
            self.state = RUN
        self._handle(cmd)

    def _handle(self, c: Command) -> None:
        ok = Reply("ACK", c.seq)
        if c.name == "HELLO":
            self.out.append(Reply("HELLO", 0, (FW_VERSION, PROTOCOL_VERSION)))
        elif c.name == "PING":
            self.out += [ok, self._state_reply(c.seq)]
        elif c.name == "STOP":
            self.state = STOPPED
            self._stop_sound()
            self.neck.brake()
            self.out.append(ok)
        elif c.name == "RESUME":
            self.state = RUN
            self.out.append(ok)
        elif self.state == STOPPED:  # J, S, HOME, CANCEL rechazados mientras STOP está enclavado
            self.out.append(Reply("ERR", c.seq, ("STOP_ACTIVE",)))
        elif c.name == "J":
            clipped = self.neck.set_target(*c.args)
            self.out.append(Reply("ACK", c.seq, ("CLIPPED",) if clipped else ()))
        elif c.name == "HOME":
            self.neck.set_target(*self.cfg["neck"]["home"])
            self.out.append(ok)
        elif c.name == "S":
            name = c.args[0]
            if name not in self.sound_len:
                self.out.append(Reply("ERR", c.seq, ("UNKNOWN_SOUND",)))
                return
            self.out.append(ok)
            if c.seq == self.last_sound_seq:  # reenvío: ya se está reproduciendo / ya sonó
                return
            self.last_sound_seq = c.seq
            self.sound, self.sound_seq = name, c.seq
            self.sound_end = self.t + self.sound_len[name]
        elif c.name == "CANCEL":
            self._stop_sound()
            self.out.append(ok)

    def _stop_sound(self) -> None:
        self.sound, self.sound_seq = None, -1

    def _state_reply(self, seq: int) -> Reply:
        y, p, r = self.neck.pos
        return Reply("STATE", seq, (self.state, round(y, 1), round(p, 1), round(r, 1), self.sound or "NONE"))

    # ------------------------------------------------------------ tiempo
    def tick(self, dt: float) -> None:
        self.t += dt
        if self.state == RUN and self.t - self.last_rx > self.watchdog_s:
            self.state = WATCHDOG
            self._stop_sound()
            self.neck.brake()
            self.out.append(Reply("ERR", 0, ("WATCHDOG",)))
        if self.sound and self.t >= self.sound_end:
            self.out.append(Reply("DONE", self.sound_seq))
            self._stop_sound()
        self.neck.step(dt)

    def read(self) -> list[Reply]:
        out, self.out = self.out, []
        return out
