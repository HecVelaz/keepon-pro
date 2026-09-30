"""Modelo del mundo: lo que la percepción sabe en este instante.

La percepción (M2) llena este objeto a partir de la cámara; en M0 lo llena el
generador sintético (keepon/synthetic.py). Los comportamientos sólo leen de acá.

Eventos vs predicados:
  - predicado sostenido (looking, shirt): verdadero mientras dure, ya filtrado N-de-M.
  - evento (wave_count): contador que sube una vez por cada saludo detectado;
    un saludo nuevo = el contador cambió.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Person:
    id: int
    u: float                  # centro del rostro en la imagen [px]
    v: float
    size: float               # alto de la caja de la persona [px] (proxy de cercanía)
    looking: bool = False     # ME_MIRA
    shirt: str | None = None  # "OLIMPIA" | "CERRO" | None (OTRA / DESCONOCIDA)
    wave_count: int = 0       # SALUDO (evento)
    leaving: bool = False     # SALIENDO
    last_seen: float = 0.0


@dataclass
class World:
    t: float
    img_w: int
    img_h: int
    hfov_deg: float
    persons: dict[int, Person] = field(default_factory=dict)

    @property
    def fx(self) -> float:
        return (self.img_w / 2) / math.tan(math.radians(self.hfov_deg) / 2)

    def visible(self, pid: int | None) -> Person | None:
        p = self.persons.get(pid) if pid is not None else None
        return p if p is not None and p.last_seen >= self.t - 1e-9 else None
