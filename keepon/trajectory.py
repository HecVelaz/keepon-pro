"""Generador de trayectorias suaves por eje (misma lógica que el firmware).

Dos etapas por eje, a paso fijo dt (10 ms):

1) PLAN trapezoidal (velocidad y aceleración limitadas). Planificación discreta exacta, aceleración
   máxima a (Δv = a·dt por paso):

  Con velocidad v la posición avanza v·dt en este paso y, frenando a tope en los
  siguientes (v-a·dt, v-2a·dt, ...), recorre además dist(v). En cada paso se elige
  la MAYOR velocidad v tal que  v·dt + dist(v) <= |e|  (e = distancia al objetivo),
  limitada a vmax y a ±a·dt de la velocidad anterior. Así:
    - nunca se pasa del objetivo ni excede vmax/amax en las posiciones del plan,
    - el último paso cae exacto en el objetivo (v = e/dt, siempre dentro de la ventana),
    - si el objetivo cambia a mitad de camino se re-planifica sin saltos.
  Fórmula cerrada (sin iteraciones, apta para el ESP32), con A = a·dt:
    n = floor((sqrt(1 + 8|e|/(dt·A)) - 1) / 2)
    v = (|e|/dt + A·n(n+1)/2) / (n+1)

2) CURVA S: la posición que va al servo es el PROMEDIO de las últimas N posiciones del plan
   (ventana de N·dt segundos, neck.suavizado_s de config.yaml). En el trapecio la aceleración salta de
   0 a amax de golpe (sacudón, "jerk" infinito); promediar una ventana convierte cada salto en una
   rampa que dura N·dt, y la velocidad queda con forma de S. Propiedades (sobre las posiciones emitidas):
    - velocidad = promedio de velocidades del plan → nunca pasa de vmax,
    - aceleración = promedio de aceleraciones del plan → nunca pasa de amax,
    - jerk ≤ 2·amax / (N·dt): la aceleración del plan va de +amax a −amax como mucho, y el promedio
      reparte ese cambio en N pasos (yaw con N = 10: 12000 °/s³; el trapecio solo, 60000 a 100000),
    - el promedio queda entre posiciones del plan → sin sobrepaso y dentro de los límites,
    - llega exacto al objetivo N pasos después que el plan (cada movimiento dura N·dt más),
    - vale para TODO movimiento (seguimiento, gestos, STOP, observador): está en el firmware.
   Con N = 1 es el trapecio de antes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

AXES = ("yaw", "pitch", "roll")
DT_FIRMWARE = 0.01  # paso del lazo del firmware [s]: la ventana de la curva S se cuenta en estos pasos
MAX_VENTANA = 50    # como el firmware (nucleo.h): hasta 0,5 s de promedio


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def pasos_ventana(suavizado_s: float, dt: float = DT_FIRMWARE) -> int:
    """Largo de la ventana del promedio en pasos (mínimo 1 = sin curva S). Igual que generar_firmware.py."""
    n = max(1, math.floor(suavizado_s / dt + 0.5))
    if n > MAX_VENTANA:
        raise ValueError(f"neck.suavizado_s = {suavizado_s} s: el firmware admite hasta {MAX_VENTANA * dt} s")
    return n


@dataclass
class Axis:
    lo: float
    hi: float
    vmax: float
    amax: float
    pos: float = 0.0        # posición que va al servo (salida de la curva S)
    target: float = 0.0
    ventana: int = 1        # N: pasos que se promedian (curva S)
    plan: float = field(init=False)      # posición del trapecio
    vel: float = field(init=False)       # velocidad del trapecio [°/s]
    buf: list[float] = field(init=False, repr=False)  # últimas N posiciones del plan (anillo)
    i_buf: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.fijar(self.pos, self.target)

    def fijar(self, pos: float, target: float | None = None) -> None:
        """Quieto en `pos` (arranque o resincronización): plan, ventana y salida en el mismo lugar."""
        self.pos = self.plan = pos
        self.target = pos if target is None else target
        self.vel = 0.0
        self.buf = [pos] * self.ventana
        self.i_buf = 0

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
        # 1) Trapecio
        e = self.target - self.plan
        A = self.amax * dt
        v_des = math.copysign(min(self.vmax, self._v_max_to_stop(abs(e), dt)), e) if e else 0.0
        self.vel += clamp(v_des - self.vel, -A, A)
        self.plan = clamp(self.plan + self.vel * dt, self.lo, self.hi)
        if abs(self.target - self.plan) < 1e-9 and abs(self.vel) <= A:
            self.plan = self.target  # sólo absorbe error de redondeo de coma flotante
        # 2) Curva S: promedio de la ventana. Se suma siempre en el orden del arreglo (0..N-1), igual que
        # el firmware, para que los dos den exactamente los mismos números.
        self.buf[self.i_buf] = self.plan
        self.i_buf = (self.i_buf + 1) % self.ventana
        suma, iguales = 0.0, True
        for x in self.buf:
            suma += x
            iguales = iguales and x == self.plan
        # Ventana llena de la misma posición: es esa (el promedio en coma flotante podría diferir en 1e-15).
        self.pos = self.plan if iguales else suma / self.ventana

    def stopping_distance(self, dt: float = DT_FIRMWARE) -> float:
        """Recorrido del plan si frena a tope desde ahora: dt·Σ max(0, |v| - k·a·dt)."""
        A, v = self.amax * dt, abs(self.vel)
        n = math.floor(v / A)
        return dt * (n * v - A * n * (n + 1) / 2.0)

    def brake_target(self, dt: float = DT_FIRMWARE) -> float:
        """Punto donde el plan se detiene frenando con amax (STOP/watchdog suaves, sin golpe). La salida
        llega ahí N pasos después, también con curva S."""
        return clamp(self.plan + math.copysign(self.stopping_distance(dt), self.vel), self.lo, self.hi)


@dataclass
class Neck:
    axes: dict[str, Axis] = field(default_factory=dict)

    @classmethod
    def from_config(cls, cfg: dict) -> "Neck":
        n = cfg["neck"]
        suav = n.get("suavizado_s", 0.0)
        suav = suav if isinstance(suav, list) else [suav] * 3
        axes = {}
        for i, name in enumerate(AXES):
            lo, hi = n["limits"][name]
            home = n["home"][i]
            axes[name] = Axis(lo, hi, n["vmax"][i], n["amax"][i], pos=home, target=home,
                              ventana=pasos_ventana(suav[i]))
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
