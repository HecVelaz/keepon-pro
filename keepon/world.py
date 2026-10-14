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
    # Intrínsecos de la cámara (fx, fy, cx, cy) [px]. Sin ellos se supone una cámara
    # ideal: focal a partir de hfov_deg y centro óptico en el centro de la imagen.
    K: tuple[float, float, float, float] | None = None

    @classmethod
    def from_cfg(cls, cfg: dict, t: float = 0.0) -> "World":
        """Mundo vacío con el tamaño de imagen y los intrínsecos de config.yaml."""
        c = cfg["camera"]
        K = (c["fx"], c["fy"], c["cx"], c["cy"]) if "fx" in c else None
        return cls(t, c["size"][0], c["size"][1], c["hfov_deg"], K=K)

    @property
    def fx(self) -> float:
        return self.K[0] if self.K else (self.img_w / 2) / math.tan(math.radians(self.hfov_deg) / 2)

    @property
    def fy(self) -> float:
        return self.K[1] if self.K else self.fx

    @property
    def cx(self) -> float:
        """Centro óptico: es el punto de la imagen que queda sobre el eje de la cámara."""
        return self.K[2] if self.K else self.img_w / 2

    @property
    def cy(self) -> float:
        return self.K[3] if self.K else self.img_h / 2

    def visible(self, pid: int | None) -> Person | None:
        p = self.persons.get(pid) if pid is not None else None
        return p if p is not None and p.last_seen >= self.t - 1e-9 else None
