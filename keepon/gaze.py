"""Control de mirada (T3) y selección del foco de atención (T4).

Control visual proporcional en velocidad (sin integral):

    e_yaw   =  atan((u - cx) / fx)        [grados]
    e_pitch = -atan((v - cy) / fy)        (v crece hacia abajo)
    ref    += sat(kp * e) * dt

Convención de signos: yaw positivo gira hacia la DERECHA de la imagen, pitch
positivo mira hacia ARRIBA. Verificarlo físicamente al montar la cabeza.
"""

from __future__ import annotations

import math

from .world import Person, World


def _sat(x: float, lim: float) -> float:
    return max(-lim, min(lim, x))


class GazeController:
    """Zona muerta SUAVE: la velocidad es proporcional a (|e| - dz), así es continua.
    Una zona muerta dura (0 adentro, kp*e afuera) hace que el seguimiento de una
    persona que camina avance a saltos: el error de régimen v/kp cae en el borde."""

    def __init__(self, cfg: dict):
        g = cfg["gaze"]
        self.kp = g["kp"]
        self.vmax = g["vmax"]
        self.dz = g["deadzone"]
        self.alpha = g["ema"]
        self.reset()

    def reset(self) -> None:
        self.ex = self.ey = 0.0

    @staticmethod
    def _soft_dz(e: float, dz: float) -> float:
        return math.copysign(max(0.0, abs(e) - dz), e)

    def update(self, ref: list[float], p: Person, w: World, dt: float) -> list[float]:
        # Se centra al rostro en el CENTRO ÓPTICO (cx, cy), no en el centro de la imagen:
        # con la calibración actual están 108 px corridos en u (≈ 6,5° de error en yaw).
        ex = math.degrees(math.atan((p.u - w.cx) / w.fx))
        ey = -math.degrees(math.atan((p.v - w.cy) / w.fy))
        self.ex += self.alpha * (ex - self.ex)
        self.ey += self.alpha * (ey - self.ey)
        dzx = math.degrees(math.atan(self.dz * w.img_w / w.fx))
        dzy = math.degrees(math.atan(self.dz * w.img_h / w.fy))
        vy = _sat(self.kp * self._soft_dz(self.ex, dzx), self.vmax[0])
        vp = _sat(self.kp * self._soft_dz(self.ey, dzy), self.vmax[1])
        return [ref[0] + vy * dt, ref[1] + vp * dt, ref[2]]


class Focus:
    """Elige a quién mirar. Prefiere a quien ME_MIRA; si nadie, al más cercano/centrado.
    Cambia de objetivo sólo si el candidato es mejor durante switch_after_s (histéresis)."""

    def __init__(self, cfg: dict):
        f = cfg["focus"]
        self.switch_after = f["switch_after_s"]
        self.w = (f["w_looking"], f["w_size"], f["w_center"])
        self.lost_hold = cfg["gaze"]["lost_hold_s"]
        self.target: int | None = None
        self._cand: int | None = None
        self._cand_since = 0.0

    def score(self, p: Person, w: World) -> tuple[bool, float]:
        """(mira, puntaje). ME_MIRA tiene prioridad estricta (T4); tamaño y centrado
        sólo ordenan dentro de cada grupo."""
        _, ws, wc = self.w
        centered = 1.0 - min(1.0, abs(p.u - w.cx) / (w.img_w / 2))  # "centrada" = cerca del eje óptico
        return p.looking, ws * min(1.0, p.size / w.img_h) + wc * centered

    def _better(self, a: Person, b: Person, w: World) -> bool:
        """¿a es claramente mejor que b? La histéresis temporal se aplica afuera."""
        (la, sa), (lb, sb) = self.score(a, w), self.score(b, w)
        return la > lb or (la == lb and sa > sb + 0.1)

    def update(self, w: World) -> int | None:
        visible = [p for p in w.persons.values() if p.last_seen >= w.t - 1e-9]
        cur = w.persons.get(self.target) if self.target is not None else None
        if cur is not None and w.t - cur.last_seen > self.lost_hold:
            cur = None  # perdido más de lost_hold -> se libera el objetivo
        if cur is None:
            self._cand = None
            self.target = max(visible, key=lambda p: self.score(p, w)).id if visible else None
            return self.target
        if not w.visible(cur.id):
            return self.target  # pérdida momentánea (< lost_hold): mantener
        best = max(visible, key=lambda p: self.score(p, w))
        if best.id != self.target and self._better(best, cur, w):
            if self._cand != best.id:
                self._cand, self._cand_since = best.id, w.t
            elif w.t - self._cand_since >= self.switch_after:
                self.target, self._cand = best.id, None
        else:
            self._cand = None
        return self.target
