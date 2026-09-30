"""Generador de trayectorias suaves por eje (misma lógica que el firmware).

Planificación discreta exacta, paso dt, aceleración máxima a (Δv = a·dt por paso):

  Con velocidad v la posición avanza v·dt en este paso y, frenando a tope en los
  siguientes (v-a·dt, v-2a·dt, ...), recorre además dist(v). En cada paso se elige
  la MAYOR velocidad v tal que  v·dt + dist(v) <= |e|  (e = distancia al objetivo),
  limitada a vmax y a ±a·dt de la velocidad anterior. Así:
    - nunca se pasa del objetivo ni excede vmax/amax en las POSICIONES emitidas,
    - el último paso cae exacto en el objetivo (v = e/dt, siempre dentro de la ventana),
    - si el objetivo cambia a mitad de camino se re-planifica sin saltos.
  Fórmula cerrada (sin iteraciones, apta para el ESP32), con A = a·dt:
    n = floor((sqrt(1 + 8|e|/(dt·A)) - 1) / 2)
    v = (|e|/dt + A·n(n+1)/2) / (n+1)
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

    def _v_max_to_stop(self, dist: float, dt: float) -> float:
        """Mayor velocidad (>=0) con la que se puede avanzar este paso y aún frenar en `dist`."""
        A = self.amax * dt
        n = math.floor((math.sqrt(1.0 + 8.0 * dist / (dt * A)) - 1.0) / 2.0)
        return (dist / dt + A * n * (n + 1) / 2.0) / (n + 1)

    def step(self, dt: float) -> None:
        e = self.target - self.pos
        A = self.amax * dt
        v_des = math.copysign(min(self.vmax, self._v_max_to_stop(abs(e), dt)), e) if e else 0.0
        self.vel += clamp(v_des - self.vel, -A, A)
        self.pos = clamp(self.pos + self.vel * dt, self.lo, self.hi)
        if abs(self.target - self.pos) < 1e-9 and abs(self.vel) <= A:
            self.pos = self.target  # sólo absorbe error de redondeo de coma flotante

    def stopping_distance(self, dt: float = 0.01) -> float:
        """Recorrido si frena a tope desde ahora: dt·Σ max(0, |v| - k·a·dt)."""
        A, v = self.amax * dt, abs(self.vel)
        n = math.floor(v / A)
        return dt * (n * v - A * n * (n + 1) / 2.0)

    def brake_target(self, dt: float = 0.01) -> float:
        """Punto donde se detiene frenando con amax (STOP/watchdog suaves, sin golpe)."""
        return clamp(self.pos + math.copysign(self.stopping_distance(dt), self.vel), self.lo, self.hi)


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
