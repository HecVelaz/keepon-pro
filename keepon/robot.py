"""Lazo principal: mundo -> foco -> propuestas -> árbitro -> acciones -> ESP32."""

from __future__ import annotations

import csv
import time
from pathlib import Path

from . import ROOT
from .actuators import Actuators
from .arbiter import BUZZER, Arbiter
from .behaviors import Behavior, Context, default_behaviors
from .gaze import Focus
from .link import Link
from .world import World


class EventLog:
    """Log de transiciones con marca de tiempo (T7). CSV en logs/ + consola opcional."""

    def __init__(self, to_file: bool = True, echo: bool = True):
        self.echo, self.rows = echo, []
        self._f = None
        if to_file:
            d = ROOT / "logs"
            d.mkdir(exist_ok=True)
            self._f = open(d / time.strftime("run_%Y%m%d_%H%M%S.csv"), "w", newline="", encoding="utf-8")
            self._w = csv.writer(self._f)
            self._w.writerow(["t", "evento"])

    def __call__(self, t: float, msg: str) -> None:
        self.rows.append((t, msg))
        if self.echo:
            print(f"[{t:7.2f}] {msg}")
        if self._f:
            self._w.writerow([f"{t:.3f}", msg])
            self._f.flush()


class Robot:
    def __init__(self, cfg: dict, link: Link, behaviors: list[Behavior] | None = None, log=None):
        self.cfg, self.link = cfg, link
        self.log = log or EventLog()
        self.arb = Arbiter(self.log)
        self.act = Actuators(cfg, link, self.arb, self.log)
        self.focus = Focus(cfg)
        self.behaviors = {b.name: b for b in (behaviors or default_behaviors(cfg))}
        self._last = None
        self._target = None
        self._hello_t = -1e9
        self._perception_ok = True
        self.max_world_age = cfg["perception"]["max_age_s"]

    # ------------------------------------------------------------ operador
    def stop(self) -> None:
        now = self.link.now()
        self.link.send("STOP")
        for g in self.arb.emergency_stop(now):
            self.behaviors[g.behavior].on_cancel(g, self._ctx(now, 0.0, None))

    def resume(self) -> None:
        self.link.send("RESUME")
        self.arb.resume(self.link.now())

    # ------------------------------------------------------------ ciclo
    def _ctx(self, now, dt, world) -> Context:
        return Context(now, dt, world, self.act, self.arb, self.focus, self.cfg)

    def _resync(self, now: float) -> None:
        """El ESP32 se reinició: sus sonidos y referencias ya no existen."""
        for g in self.arb.cancel_all(now, "ESP32 reinició"):
            self.behaviors[g.behavior].on_cancel(g, self._ctx(now, 0.0, None))
        self.act.reset_after_reboot(self.cfg["neck"]["home"])
        if self.arb.stopped:
            self.link.send("STOP")  # el STOP del operador sobrevive al reinicio

    def tick(self, world: World, world_age: float = 0.0) -> None:
        """world_age: segundos desde que se capturó el cuadro que originó `world`."""
        now = self.link.now()
        dt = 0.0 if self._last is None else now - self._last
        self._last = now
        self.act.process(self.link.poll())
        if self.act.rebooted:
            self._resync(now)
        if not self.act.session:  # sin sesión no se comanda nada; reintentar HELLO cada 0,5 s
            if now - self._hello_t > 0.5:
                self.link.hello()
                self._hello_t = now
            return

        ok = world_age <= self.max_world_age
        if ok != self._perception_ok:
            self.log(now, "PERCEPCION ok" if ok else f"PERCEPCION sin datos frescos ({world_age:.2f} s)")
            self._perception_ok = ok
        if not ok:  # nadie es visible "ahora": el foco mantiene y luego libera por lost_hold
            world = World(world.t + world_age, world.img_w, world.img_h, world.hfov_deg, world.persons)

        target = self.focus.update(world)
        if target != self._target:
            self.log(now, f"FOCO {self._target} -> {target}")
            self._target = target

        ctx = self._ctx(now, dt, world)
        proposals = [p for b in self.behaviors.values() for p in b.propose(ctx)]
        d = self.arb.step(now, proposals)
        for g in d.cancelled:
            if BUZZER in g.resources:
                self.act.cancel_sound()
            self.behaviors[g.behavior].on_cancel(g, ctx)
        for g in d.started:
            self.behaviors[g.behavior].on_start(g, ctx)
        for g in self.arb.grants():
            self.behaviors[g.behavior].act(g, ctx)
