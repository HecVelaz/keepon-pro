"""Puerta de salida hacia el ESP32.

Todo comando de cuello o buzzer pasa por acá y se verifica contra el árbitro:
si el comportamiento no es dueño del recurso, el comando se descarta y se
registra la violación. Así "nunca dos dueños" se garantiza por construcción.
"""

from __future__ import annotations

from .arbiter import BUZZER, NECK, Arbiter, Grant
from .link import Link
from .trajectory import AXES, clamp


class Actuators:
    def __init__(self, cfg: dict, link: Link, arbiter: Arbiter, log):
        self.link, self.arb, self.log = link, arbiter, log
        self.limits = [cfg["neck"]["limits"][a] for a in AXES]
        self.ref = list(cfg["neck"]["home"])       # última referencia articular enviada
        self.sound_seq: dict[int, int] = {}        # grant.id -> seq del sonido
        self.done: set[int] = set()                # seqs con DONE recibido
        self.violations = 0
        self.esp_state = "RUN"

    def _check(self, g: Grant, res: str) -> bool:
        if self.arb.holds(g.id, res):
            return True
        self.violations += 1
        self.log(self.link.now(), f"VIOLACION {g.behavior}#{g.id} usó {res} sin ser dueño")
        return False

    def neck(self, g: Grant, yaw: float, pitch: float, roll: float) -> None:
        if not self._check(g, NECK):
            return
        self.ref = [clamp(v, lo, hi) for v, (lo, hi) in zip((yaw, pitch, roll), self.limits)]
        self.link.send("J", *(round(v, 1) for v in self.ref))

    def play(self, g: Grant, name: str) -> None:
        if self._check(g, BUZZER):
            self.sound_seq[g.id] = self.link.send("S", name)

    def sound_finished(self, g: Grant) -> bool:
        return self.sound_seq.get(g.id) in self.done

    def cancel_sound(self) -> None:
        self.link.send("CANCEL", "SOUND")

    def process(self, replies) -> None:
        for r in replies:
            if r.name == "DONE":
                self.done.add(r.seq)
            elif r.name == "ERR":
                self.log(self.link.now(), f"ESP32 ERR seq={r.seq} {' '.join(map(str, r.args))}")
            elif r.name == "STATE":
                self.esp_state = r.args[0]
            elif r.name == "HELLO":
                self.log(self.link.now(), f"ESP32 HELLO fw={r.args}")
