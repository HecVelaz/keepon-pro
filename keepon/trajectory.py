"""Generador de trayectorias suaves por eje (misma lógica que el firmware).

Perfil trapezoidal "online": en cada paso la velocidad deseada es la máxima que
todavía permite frenar justo en el objetivo con aceleración amax. En tiempo
continuo sería sqrt(2·amax·|e|); como el lazo es discreto (paso dt) se usa la
versión exacta para frenado en pasos de amax·dt, si no, llega con velocidad y
el frenado final es un golpe:

    v_des = sign(e) * min(vmax, a·dt·(sqrt(1/4 + 2|e|/(a·dt²)) - 1/2))

y la velocidad real se acerca a v_des con aceleración limitada a amax. Si el
objetivo cambia a mitad de camino (seguimiento), la trayectoria se re-planifica
sola sin saltos de velocidad: por eso no hay golpes ni vibraciones.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

AXES = ("yaw", "pitch", "roll")


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


@dataclass
class Axis:
    lo: float
    hi: float
    vmax: float
    amax: float
    pos: float = 0.0
    vel: float = 0.0
    target: float = 0.0

    def set_target(self, t: float) -> bool:
        """Fija el objetivo dentro de los límites. Devuelve True si hubo que recortarlo."""
        self.target = clamp(t, self.lo, self.hi)
        return self.target != t

    def step(self, dt: float) -> None:
        e = self.target - self.pos
        adt = self.amax * dt
        v_stop = adt * (math.sqrt(0.25 + 2.0 * abs(e) / (adt * dt)) - 0.5)
        v_des = math.copysign(min(self.vmax, v_stop), e)
        self.vel += clamp(v_des - self.vel, -adt, adt)
        if abs(e) <= abs(self.vel) * dt and abs(self.vel) <= adt + 1e-9:
            self.pos = self.target  # último tramo: llega exacto; la velocidad (ya limitada) se anula en el próximo paso
        else:
            self.pos = clamp(self.pos + self.vel * dt, self.lo, self.hi)

    def brake_target(self) -> float:
        """Punto donde se detiene si frena ya con amax (para STOP/watchdog suaves)."""
        d = self.vel * self.vel / (2.0 * self.amax)
        return clamp(self.pos + math.copysign(d, self.vel), self.lo, self.hi)


@dataclass
class Neck:
    axes: dict[str, Axis] = field(default_factory=dict)

    @classmethod
    def from_config(cls, cfg: dict) -> "Neck":
        n = cfg["neck"]
        axes = {}
        for i, name in enumerate(AXES):
            lo, hi = n["limits"][name]
            home = n["home"][i]
            axes[name] = Axis(lo, hi, n["vmax"][i], n["amax"][i], pos=home, target=home)
        return cls(axes)

    def set_target(self, yaw: float, pitch: float, roll: float) -> bool:
        clipped = False
        for name, v in zip(AXES, (yaw, pitch, roll)):
            clipped |= self.axes[name].set_target(v)
        return clipped

    def step(self, dt: float) -> None:
        for a in self.axes.values():
            a.step(dt)

    def brake(self) -> None:
        for a in self.axes.values():
            a.target = a.brake_target()

    @property
    def pos(self) -> tuple[float, float, float]:
        return tuple(self.axes[n].pos for n in AXES)

    @property
    def target(self) -> tuple[float, float, float]:
        return tuple(self.axes[n].target for n in AXES)

    def moving(self) -> bool:
        return any(abs(a.vel) > 1e-6 or abs(a.target - a.pos) > 1e-3 for a in self.axes.values())
