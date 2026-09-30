"""Árbitro de comportamientos (T6). Desarrollo propio del grupo.

Reglas:
  1. Recursos exclusivos: NECK y BUZZER tienen a lo sumo un dueño.
  2. Prioridades: número menor = más importante. Una propuesta sólo quita un
     recurso a un dueño menos importante y además interrumpible por ella.
  3. Adquisición atómica: se conceden TODOS los recursos pedidos o ninguno.
     Si se le quita un recurso a una acción, se cancela la acción completa.
  4. Propuestas vencidas (expires) o en cooldown se descartan.
  5. El cooldown se registra cuando la acción EMPIEZA, no cuando se propone.
  6. Acciones continuas (seguir, observar) retienen el recurso mientras se
     vuelvan a proponer en cada ciclo; las episódicas (saludo, polca) hasta
     que el comportamiento avisa finish().
  7. STOP del operador cancela todo, incluso lo no interrumpible, y queda
     enclavado hasta resume().
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

NECK, BUZZER = "NECK", "BUZZER"
RESOURCES = (NECK, BUZZER)


@dataclass(frozen=True)
class Proposal:
    behavior: str
    priority: int
    resources: frozenset
    continuous: bool = False           # True: seguir/observar (se renueva cada ciclo)
    interruptible_by: int | None = None  # máxima prioridad que puede interrumpirla (None = cualquiera más importante)
    person: int | None = None
    expires: float = math.inf          # tiempo absoluto; vencida -> se descarta
    cooldown: tuple | None = None      # (clave, segundos) registrado al empezar
    params: dict = field(default_factory=dict, compare=False, hash=False)

    def can_interrupt(self, g: "Grant") -> bool:
        limit = g.priority - 1 if g.interruptible_by is None else g.interruptible_by
        return self.priority < g.priority and self.priority <= limit


@dataclass
class Grant:
    """Acción en ejecución: dueño de uno o más recursos."""
    id: int
    behavior: str
    priority: int
    resources: frozenset
    continuous: bool
    interruptible_by: int | None
    person: int | None
    started: float
    params: dict
    seen: bool = True  # para continuas: ¿se volvió a proponer en este ciclo?


@dataclass
class Decision:
    started: list[Grant] = field(default_factory=list)
    cancelled: list[Grant] = field(default_factory=list)
    finished: list[Grant] = field(default_factory=list)


class Arbiter:
    def __init__(self, log=None):
        self.owner: dict[str, Grant | None] = {r: None for r in RESOURCES}
        self.cooldown_until: dict[tuple, float] = {}
        self.stopped = False
        self._ids = itertools.count(1)
        self._finished: list[Grant] = []
        self.log = log or (lambda now, msg: None)

    # ------------------------------------------------------------ consultas
    def grants(self) -> list[Grant]:
        seen, out = set(), []
        for g in self.owner.values():
            if g and g.id not in seen:
                seen.add(g.id)
                out.append(g)
        return out

    def holds(self, grant_id: int, resource: str) -> bool:
        g = self.owner[resource]
        return g is not None and g.id == grant_id

    def in_cooldown(self, key: tuple, now: float) -> bool:
        return self.cooldown_until.get(key, -math.inf) > now

    # ------------------------------------------------------------ operador
    def cancel_all(self, now: float, why: str) -> list[Grant]:
        cancelled = self.grants()
        for g in cancelled:
            self._release(g, now, why)
        return cancelled

    def emergency_stop(self, now: float) -> list[Grant]:
        self.stopped = True
        return self.cancel_all(now, "STOP")

    def resume(self, now: float) -> None:
        self.stopped = False
        self.log(now, "ARB resume")

    def finish(self, grant_id: int, now: float) -> None:
        """Llamado por un comportamiento episódico al terminar su acción."""
        for g in self.grants():
            if g.id == grant_id:
                self._release(g, now, "fin")
                self._finished.append(g)

    # ------------------------------------------------------------ ciclo
    def step(self, now: float, proposals: list[Proposal]) -> Decision:
        d = Decision(finished=self._finished)
        self._finished = []
        if self.stopped:
            return d

        for g in self.grants():
            g.seen = False

        live = [p for p in proposals if p.expires > now]
        live.sort(key=lambda p: p.priority)  # estable: a igual prioridad, gana el orden de llegada

        for p in live:
            # ¿Ya es dueño de todo lo que pide? -> renovar.
            mine = [self.owner[r] for r in p.resources]
            if all(g is not None and g.behavior == p.behavior and (g.person == p.person or p.continuous) for g in mine):
                for g in mine:
                    if g.person != p.person:  # continua que cambia de persona: sin soltar el recurso
                        self.log(now, f"ARB retarget {g.behavior}#{g.id} persona {g.person} -> {p.person}")
                        g.person = p.person
                    g.seen = True
                    if g.continuous:  # las episódicas conservan los parámetros con que empezaron
                        g.params = p.params
                continue
            if p.cooldown and self.in_cooldown(p.cooldown[0], now):
                continue
            holders = {g.id: g for g in mine if g is not None}
            if not all(p.can_interrupt(g) for g in holders.values()):
                continue  # algún recurso está tomado por alguien que no puede interrumpir
            for g in holders.values():
                self._release(g, now, f"interrumpido por {p.behavior}")
                d.cancelled.append(g)
            g = Grant(next(self._ids), p.behavior, p.priority, frozenset(p.resources), p.continuous,
                      p.interruptible_by, p.person, now, p.params)
            for r in p.resources:
                self.owner[r] = g
            if p.cooldown:
                key, secs = p.cooldown
                self.cooldown_until[key] = now + secs
            self.log(now, f"ARB start {g.behavior}#{g.id} persona={g.person} recursos={'+'.join(sorted(g.resources))}")
            d.started.append(g)

        # Continuas que no se volvieron a proponer liberan el recurso.
        for g in self.grants():
            if g.continuous and not g.seen:
                self._release(g, now, "sin propuesta")
                d.finished.append(g)
        return d

    def _release(self, g: Grant, now: float, why: str) -> None:
        for r in g.resources:
            if self.owner[r] is g:
                self.owner[r] = None
        self.log(now, f"ARB stop  {g.behavior}#{g.id} ({why})")
