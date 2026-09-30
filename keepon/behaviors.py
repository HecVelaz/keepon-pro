"""Comportamientos (T5). Cada uno:
  - propose(ctx): mira el mundo y devuelve propuestas al árbitro (no actúa).
  - on_start / on_cancel: el árbitro le concedió o quitó los recursos.
  - act(g, ctx): se llama en cada ciclo MIENTRAS es dueño; ordena a los actuadores.
Ningún comportamiento escribe al puerto serie directamente.

M0: Observador, Seguimiento, Saludo, Camiseta. Los modos de personalidad van en M3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .arbiter import BUZZER, NECK, Arbiter, Grant, Proposal
from .actuators import Actuators
from .gaze import Focus, GazeController
from .world import World


@dataclass
class Context:
    now: float
    dt: float
    world: World
    act: Actuators
    arb: Arbiter
    focus: Focus
    cfg: dict


class Behavior:
    name = "?"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.priority = cfg["priorities"][self.name]

    def propose(self, ctx: Context) -> list[Proposal]:
        return []

    def on_start(self, g: Grant, ctx: Context) -> None: ...
    def on_cancel(self, g: Grant, ctx: Context) -> None: ...
    def act(self, g: Grant, ctx: Context) -> None: ...


class Observer(Behavior):
    """Sin personas: barrido lento de la escena, arranca desde donde está la cabeza."""
    name = "OBSERVADOR"

    def propose(self, ctx):
        if ctx.focus.target is None:
            return [Proposal(self.name, self.priority, frozenset({NECK}), continuous=True)]
        return []

    def on_start(self, g, ctx):
        o = self.cfg["observer"]
        # Fase inicial tal que el barrido empiece en el yaw actual (sin salto).
        s = max(-1.0, min(1.0, ctx.act.ref[0] / o["yaw_amp"]))
        self.phase0 = math.asin(s)
        self.t0 = ctx.now
        self.start_pitch = ctx.act.ref[1]

    def act(self, g, ctx):
        o = self.cfg["observer"]
        ph = self.phase0 + 2 * math.pi * (ctx.now - self.t0) / o["period_s"]
        blend = min(1.0, (ctx.now - self.t0) / 2.0)  # pitch vuelve suave en 2 s
        pitch = (1 - blend) * self.start_pitch + blend * o["pitch_amp"] * math.sin(2 * ph)
        ctx.act.neck(g, o["yaw_amp"] * math.sin(ph), pitch, 0.0)


class Tracking(Behavior):
    """Eye contact con el objetivo del foco (T3 + T4)."""
    name = "SEGUIMIENTO"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.gaze = GazeController(cfg)

    def propose(self, ctx):
        if ctx.focus.target is not None:
            return [Proposal(self.name, self.priority, frozenset({NECK}), continuous=True, person=ctx.focus.target)]
        return []

    def on_start(self, g, ctx):
        self.gaze.reset()

    def act(self, g, ctx):
        p = ctx.world.visible(g.person)
        if p is None:
            return  # pérdida momentánea: mantener la mirada (el foco la libera a los lost_hold_s)
        y, pi, r = self.gaze.update(ctx.act.ref, p, ctx.world, ctx.dt)
        ctx.act.neck(g, y, pi, r * 0.9)  # roll vuelve suave a 0 mientras sigue


class Greeting(Behavior):
    """SALUDO -> asiente 2-3 veces + R2D2. No interrumpible (acción corta)."""
    name = "SALUDO"

    WINDOW_S = 0.5  # un gesto se responde dentro de esta ventana o se descarta

    def __init__(self, cfg):
        super().__init__(cfg)
        self.seen: dict[int, int] = {}                 # persona -> último wave_count ya consumido
        self.pending: dict[int, tuple[int, float]] = {}  # persona -> (wave_count, t_detectado)

    def propose(self, ctx):
        out = []
        for p in ctx.world.persons.values():
            if not ctx.world.visible(p.id):
                continue
            last = self.seen.setdefault(p.id, p.wave_count)
            if p.wave_count > last and self.pending.get(p.id, (None,))[0] != p.wave_count:
                self.pending[p.id] = (p.wave_count, ctx.now)
            if p.id not in self.pending:
                continue
            count, t_det = self.pending[p.id]
            if ctx.now > t_det + self.WINDOW_S:  # no se pudo responder a tiempo (cooldown/ocupado)
                self.seen[p.id] = count
                del self.pending[p.id]
                continue
            out.append(Proposal(self.name, self.priority, frozenset({NECK, BUZZER}),
                                interruptible_by=0, person=p.id, expires=t_det + self.WINDOW_S,
                                cooldown=(("SALUDO", p.id), self.cfg["cooldowns"]["SALUDO_por_persona"]),
                                params={"wave": count}))
        return out

    def on_start(self, g, ctx):
        self.seen[g.person] = g.params["wave"]
        self.pending.pop(g.person, None)
        self.t0, self.base = ctx.now, list(ctx.act.ref)
        ctx.act.play(g, "R2D2")

    def act(self, g, ctx):
        c = self.cfg["greeting"]
        t = ctx.now - self.t0
        dur = c["nods"] * c["nod_period_s"]
        if t < dur:
            nod = c["nod_amp"] * math.sin(math.pi * t / c["nod_period_s"]) ** 2  # sólo hacia abajo
            ctx.act.neck(g, self.base[0], self.base[1] - nod, self.base[2])
        else:
            ctx.act.neck(g, *self.base)
            timeout = t > dur + self.cfg["sounds"]["R2D2"] + 0.5
            if ctx.act.sound_finished(g) or timeout:
                ctx.arb.finish(g.id, ctx.now)


class Shirt(Behavior):
    """CAMISETA_OLIMPIA -> polca; CAMISETA_CERRO -> abucheo. Sólo usa el buzzer,
    así que convive con el seguimiento. Interrumpible sólo por prioridad 0-1."""
    name = "CAMISETA"
    SOUND = {"OLIMPIA": "POLCA", "CERRO": "ABUCHEO"}

    def propose(self, ctx):
        out = []
        for p in ctx.world.persons.values():
            if ctx.world.visible(p.id) and p.shirt in self.SOUND:
                out.append(Proposal(self.name, self.priority, frozenset({BUZZER}),
                                    interruptible_by=1, person=p.id, expires=ctx.now + 0.3,
                                    cooldown=(("CAMISETA", p.id), self.cfg["cooldowns"]["CAMISETA_por_persona"]),
                                    params={"sound": self.SOUND[p.shirt]}))
        return out

    def on_start(self, g, ctx):
        self.t0 = ctx.now
        ctx.act.play(g, g.params["sound"])

    def act(self, g, ctx):
        if ctx.act.sound_finished(g) or ctx.now - self.t0 > self.cfg["sounds"][g.params["sound"]] + 0.5:
            ctx.arb.finish(g.id, ctx.now)


def default_behaviors(cfg: dict) -> list[Behavior]:
    return [Observer(cfg), Tracking(cfg), Greeting(cfg), Shirt(cfg)]
