"""Personas y cámara sintéticas para probar sin percepción ni mecánica (M0).

Cada persona tiene una posición angular absoluta (azimut, elevación) que puede
moverse en el tiempo. La cámara virtual está montada en el cuello simulado:
proyecta a cada persona según la postura REAL del cuello (con latencia), así el
lazo de control visual se cierra de verdad.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from .world import Person, World


def const(x):
    return lambda t: x


def ramp(t0: float, t1: float, a: float, b: float):
    """a hasta t0, interpola hasta b en t1, luego b."""
    return lambda t: a if t <= t0 else b if t >= t1 else a + (b - a) * (t - t0) / (t1 - t0)


@dataclass
class SynthPerson:
    id: int
    appear: float
    leave: float = math.inf
    az: Callable[[float], float] = const(0.0)      # [°] + = derecha del robot
    el: Callable[[float], float] = const(5.0)      # [°] altura del rostro
    size: float = 300.0                            # alto de la caja [px]
    looking: list[tuple[float, float]] = field(default_factory=list)   # intervalos (t0, t1)
    shirt: list[tuple[float, float, str]] = field(default_factory=list)
    waves: list[float] = field(default_factory=list)                    # instantes de saludo
    hidden: list[tuple[float, float]] = field(default_factory=list)     # oclusiones breves

    def present(self, t: float) -> bool:
        return self.appear <= t < self.leave and not any(a <= t < b for a, b in self.hidden)


class SynthCamera:
    def __init__(self, cfg: dict, persons: list[SynthPerson], latency_s: float = 0.06, noise_px: float = 1.5, seed: int = 0):
        c = cfg["camera"]
        self.w, self.h = c["size"]
        self.hfov = c["hfov_deg"]
        self.persons = persons
        self.latency = latency_s
        self.noise = noise_px
        self.rng = random.Random(seed)
        self.hist: deque = deque()
        self.last_seen: dict[int, float] = {}
        self.world = World.from_cfg(cfg)  # proyecta con los mismos intrínsecos que usa el control

    def observe(self, t: float, neck_pos: tuple[float, float, float]) -> World:
        # La imagen que llega ahora fue tomada hace `latency` segundos.
        self.hist.append((t, neck_pos))
        while len(self.hist) > 1 and self.hist[1][0] <= t - self.latency:
            self.hist.popleft()
        yaw, pitch, _ = self.hist[0][1]
        w = self.world
        w.t = t
        for sp in self.persons:
            if not sp.present(t):
                continue
            rel_az, rel_el = sp.az(t) - yaw, sp.el(t) - pitch
            if abs(rel_az) >= 80 or abs(rel_el) >= 80:
                continue
            u = w.cx + w.fx * math.tan(math.radians(rel_az)) + self.rng.gauss(0, self.noise)
            v = w.cy - w.fy * math.tan(math.radians(rel_el)) + self.rng.gauss(0, self.noise)
            if not (0 <= u < w.img_w and 0 <= v < w.img_h):
                continue
            p = w.persons.get(sp.id) or Person(sp.id, u, v, sp.size)
            p.u, p.v, p.size, p.last_seen = u, v, sp.size, t
            p.looking = any(a <= t < b for a, b in sp.looking)
            p.shirt = next((s for a, b, s in sp.shirt if a <= t < b), None)
            p.wave_count = sum(1 for tw in sp.waves if tw <= t)
            margin = 0.08 * w.img_w
            p.leaving = u < margin or u > w.img_w - margin
            w.persons[sp.id] = p
        # Tracks no vistos por más de 2 s se borran (como haría el tracker).
        for pid in [pid for pid, p in w.persons.items() if t - p.last_seen > 2.0]:
            del w.persons[pid]
        return w
