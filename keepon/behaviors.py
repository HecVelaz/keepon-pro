"""Comportamientos (T5). Cada uno:
  - propose(ctx): mira el mundo y devuelve propuestas al árbitro (no actúa).
  - on_start / on_cancel: el árbitro le concedió o quitó los recursos.
  - act(g, ctx): se llama en cada ciclo MIENTRAS es dueño; ordena a los actuadores.
Ningún comportamiento escribe al puerto serie directamente.

Observador, Seguimiento (con inclinación de curiosidad), Saludo, Camiseta, Modo (Tímido / Atrevido /
Maleducado) y Operador (sonido de confirmación del cambio de modo).
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
    modo: str = "NEUTRO"   # modo de personalidad actual (T5): NEUTRO | TIMIDO | ATREVIDO | MALEDUCADO


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
    """Eye contact con el objetivo del foco (T3 + T4), con inclinación de curiosidad (T3 d).

    Inclinación: si el objetivo se queda quieto durante quieto_s, el roll va a ±amp_deg (alternando el
    lado), lo sostiene sostener_s y vuelve a 0. Si la persona se mueve antes, vuelve enseguida. Después
    espera espera_s. Yaw y pitch siguen igual. "Quieto": la dirección de la persona (ángulo comandado del
    cuello + error en la imagen) no se aparta más de movimiento_max_deg de donde estaba al empezar a contar;
    así una pequeña oscilación de la cabeza alrededor de la persona no reinicia la cuenta."""
    name = "SEGUIMIENTO"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.gaze = GazeController(cfg)
        self.cur = cfg["curiosidad"]
        self.lado = 1                    # próximo lado de la inclinación (+1 = horario visto desde atrás)
        self.espera_hasta = -1e9
        self.quieto_desde = self.incl_desde = None
        self.ancla = (0.0, 0.0)          # dirección de la persona [°] cuando empezó a estar quieta
        self.incl_lado = 0

    def propose(self, ctx):
        if ctx.focus.target is not None:
            return [Proposal(self.name, self.priority, frozenset({NECK}), continuous=True, person=ctx.focus.target)]
        return []

    def on_start(self, g, ctx):
        self.gaze.reset()
        self.quieto_desde = self.incl_desde = None

    def on_cancel(self, g, ctx):
        if self.incl_desde is not None:  # otro comportamiento (o el STOP) tomó el cuello estando inclinada
            ctx.act.log(ctx.now, f"CURIOSIDAD persona={g.person} interrumpida por otro comportamiento")
            self.espera_hasta = ctx.now + self.cur["espera_s"]
        self.quieto_desde = self.incl_desde = None

    def act(self, g, ctx):
        p = ctx.world.visible(g.person)
        if p is None:
            return  # pérdida momentánea: mantener la mirada (el foco la libera a los lost_hold_s)
        y, pi, _ = self.gaze.update(ctx.act.ref, p, ctx.world, ctx.dt)
        # El roll va a la inclinación o a 0; la trayectoria del firmware lo hace suave (vmax/amax de roll).
        ctx.act.neck(g, y, pi, self._roll(g, ctx))

    def _roll(self, g, ctx) -> float:
        c, now = self.cur, ctx.now
        direccion = (ctx.act.ref[0] + self.gaze.ex, ctx.act.ref[1] + self.gaze.ey)  # adónde está la persona
        if self.quieto_desde is None:
            self.ancla = direccion
        centrado = all(abs(d - a) <= c["movimiento_max_deg"] for d, a in zip(direccion, self.ancla))
        if self.incl_desde is not None:  # inclinada
            if centrado and now - self.incl_desde < c["sostener_s"]:
                return self.incl_lado * c["amp_deg"]
            motivo = "fin" if centrado else "la persona se movió"
            ctx.act.log(now, f"CURIOSIDAD persona={g.person} vuelve a 0 ({motivo})")
            self.incl_desde = self.quieto_desde = None
            self.espera_hasta = now + c["espera_s"]
            return 0.0
        if not centrado:  # se movió: la cuenta empieza de nuevo desde la dirección actual
            self.quieto_desde, self.ancla = now, direccion
            return 0.0
        if self.quieto_desde is None:
            self.quieto_desde = now
        if c["activa"] and now - self.quieto_desde >= c["quieto_s"] and now >= self.espera_hasta:
            self.incl_desde, self.incl_lado, self.lado = now, self.lado, -self.lado
            ctx.act.log(now, f"CURIOSIDAD persona={g.person} inclina roll {self.incl_lado * c['amp_deg']:+.0f}°")
            return self.incl_lado * c["amp_deg"]
        return 0.0


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
            if ctx.act.sound_finished(g):
                ctx.arb.finish(g.id, ctx.now)
            elif t > dur + self.cfg["sounds"]["R2D2"] + 0.5:  # sin DONE: cortar antes de soltar el buzzer
                ctx.act.cancel_sound()
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
        if ctx.act.sound_finished(g):
            ctx.arb.finish(g.id, ctx.now)
        elif ctx.now - self.t0 > self.cfg["sounds"][g.params["sound"]] + 0.5:  # sin DONE: cortar y soltar
            ctx.act.cancel_sound()
            ctx.arb.finish(g.id, ctx.now)


MODOS = ("NEUTRO", "TIMIDO", "ATREVIDO", "MALEDUCADO")


class ConfirmaModo(Behavior):
    """Comando del operador: confirma el cambio de modo con un sonido breve distintivo (BEEP_<MODO>), o
    reproduce un sonido a pedido (prueba del buzzer). Prioridad 0, sólo el buzzer: no le quita el cuello
    a nadie."""
    name = "OPERADOR"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.pedido: tuple[str, float] | None = None  # (sonido, instante del pedido)

    def pedir(self, modo: str, now: float) -> None:
        self.pedir_sonido(f"BEEP_{modo}", now)

    def pedir_sonido(self, sonido: str, now: float) -> None:
        self.pedido = (sonido, now)

    def propose(self, ctx):
        if self.pedido is None:
            return []
        sonido, t = self.pedido
        if ctx.now > t + 1.0:  # no se pudo (p. ej. con STOP): se descarta
            self.pedido = None
            return []
        return [Proposal(self.name, self.priority, frozenset({BUZZER}), interruptible_by=0,
                         expires=t + 1.0, params={"sound": sonido})]

    def on_start(self, g, ctx):
        self.pedido, self.t0 = None, ctx.now
        ctx.act.play(g, g.params["sound"])

    def act(self, g, ctx):
        if ctx.act.sound_finished(g):
            ctx.arb.finish(g.id, ctx.now)
        elif ctx.now - self.t0 > self.cfg["sounds"][g.params["sound"]] + 0.5:
            ctx.act.cancel_sound()
            ctx.arb.finish(g.id, ctx.now)


class Mode(Behavior):
    """Reacción del modo de personalidad sobre la persona que se sigue (T5, prioridad 3):

    - TIMIDO: si lo mira (ME_MIRA), desvía la mirada hacia un costado y abajo, la sostiene y vuelve a
      espiar gradualmente (cuello).
    - ATREVIDO: si lo mira, levanta el mentón varias veces (pitch hacia arriba) sin dejar de seguirla
      en yaw (cuello).
    - MALEDUCADO: si la persona seguida está SALIENDO, le silba un piropo, una vez por salida y como
      mucho uno cada PIROPO_global segundos entre todos (buzzer: convive con el seguimiento).
    NEUTRO no propone nada: sólo sostiene el contacto visual (el seguimiento)."""
    name = "MODO"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.m = cfg["modos"]
        self.gaze = GazeController(cfg)
        self.saliendo_antes: dict[int, bool] = {}  # para detectar el flanco de SALIENDO (una vez por salida)
        self.lado = 1

    def propose(self, ctx):
        pid = ctx.focus.target
        p = ctx.world.visible(pid)
        if p is None:
            return []
        if ctx.modo == "TIMIDO" and p.looking:
            c = self.m["timido"]
            return [Proposal(self.name, self.priority, frozenset({NECK}), person=pid, expires=ctx.now + 0.3,
                             cooldown=(("TIMIDO", pid), c["sostener_s"] + c["regreso_s"] + c["espera_s"]),
                             params={"reaccion": "TIMIDO"})]
        if ctx.modo == "ATREVIDO" and p.looking:
            c = self.m["atrevido"]
            return [Proposal(self.name, self.priority, frozenset({NECK}), person=pid, expires=ctx.now + 0.3,
                             cooldown=(("ATREVIDO", pid), c["veces"] * c["periodo_s"] + c["espera_s"]),
                             params={"reaccion": "ATREVIDO"})]
        antes, ahora = self.saliendo_antes.get(pid, False), p.leaving
        self.saliendo_antes[pid] = ahora
        if ctx.modo == "MALEDUCADO" and ahora and not antes:  # flanco: empieza una salida
            return [Proposal(self.name, self.priority, frozenset({BUZZER}), person=pid, expires=ctx.now + 0.5,
                             interruptible_by=1, cooldown=(("PIROPO",), self.cfg["cooldowns"]["PIROPO_global"]),
                             params={"reaccion": "MALEDUCADO", "sound": "PIROPO"})]
        return []

    def on_start(self, g, ctx):
        self.t0, self.base = ctx.now, list(ctx.act.ref)
        r = g.params["reaccion"]
        if r == "TIMIDO":
            # Hacia el costado que deja más lugar dentro de los límites de yaw; alterna si están parejos.
            self.lado = -1 if self.base[0] > 5 else 1 if self.base[0] < -5 else -self.lado
        elif r == "ATREVIDO":
            self.gaze.reset()
        elif r == "MALEDUCADO":
            ctx.act.play(g, g.params["sound"])
        ctx.act.log(ctx.now, f"MODO reacción {r} persona={g.person}")

    def act(self, g, ctx):
        t = ctx.now - self.t0
        r = g.params["reaccion"]
        if r == "TIMIDO":
            c = self.m["timido"]
            # 1) desvía y sostiene; 2) vuelve de a poco (espía), con una curva suave (coseno) de 1 a 0.
            k = 1.0 if t < c["sostener_s"] else 0.5 * (1 + math.cos(math.pi * min(1.0, (t - c["sostener_s"]) / c["regreso_s"])))
            ctx.act.neck(g, self.base[0] + self.lado * k * c["desvio_yaw_deg"],
                         self.base[1] - k * c["desvio_pitch_deg"], self.base[2] + self.lado * k * c["desvio_roll_deg"])
            if t >= c["sostener_s"] + c["regreso_s"]:
                ctx.arb.finish(g.id, ctx.now)
        elif r == "ATREVIDO":
            c = self.m["atrevido"]
            dur = c["veces"] * c["periodo_s"]
            y = self.base[0]
            p = ctx.world.visible(g.person)
            if p is not None:  # sigue en yaw (el pitch lo maneja el gesto)
                y = self.gaze.update(ctx.act.ref, p, ctx.world, ctx.dt)[0]
            menton = c["menton_deg"] * math.sin(math.pi * min(t, dur) / c["periodo_s"]) ** 2  # sólo hacia arriba
            ctx.act.neck(g, y, self.base[1] + menton, self.base[2])
            if t >= dur:
                ctx.arb.finish(g.id, ctx.now)
        elif r == "MALEDUCADO":
            if ctx.act.sound_finished(g):
                ctx.arb.finish(g.id, ctx.now)
            elif t > self.cfg["sounds"][g.params["sound"]] + 0.5:
                ctx.act.cancel_sound()
                ctx.arb.finish(g.id, ctx.now)


def default_behaviors(cfg: dict) -> list[Behavior]:
    return [Observer(cfg), Tracking(cfg), Greeting(cfg), Shirt(cfg), Mode(cfg), ConfirmaModo(cfg)]
