"""Lazo principal: mundo -> foco -> propuestas -> árbitro -> acciones -> ESP32."""

from __future__ import annotations

import bisect
import csv
import time
from collections import deque
from dataclasses import replace
from pathlib import Path

from . import ROOT
from .actuators import Actuators
from .arbiter import BUZZER, Arbiter
from .behaviors import Behavior, Context, default_behaviors
from .gaze import Focus
from .link import Link
from .protocol import VOL_MAX
from .sim_esp32 import volumen_inicial
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
        self._stop_unsent = False  # STOP del operador que todavía no se pudo transmitir
        self.en_home = False       # HOME del operador: quieto en HOME hasta RESUME (o STOP)
        self.max_world_age = cfg["perception"]["max_age_s"]
        self.modo = cfg["modos"]["inicial"]
        # Volumen del buzzer [%] (comando del operador). La ESP32 lo pierde al reiniciarse y lo conserva
        # entre sesiones: se le manda cada vez que se abre una, así los dos dicen lo mismo.
        self.volumen = volumen_inicial(cfg)
        self._volumen_enviado = False
        # Historia de la posición del cuello [(t, (yaw, pitch, roll))], unos 2 s a 40 Hz: para saber dónde
        # miraba la cámara cuando se capturó cada cuadro (la percepción llega ~100 ms tarde).
        self._historia: deque[tuple[float, tuple[float, float, float]]] = deque(maxlen=80)

    # ------------------------------------------------------------ modo de personalidad (T5)
    def set_modo(self, modo: str) -> bool:
        """Comando del operador: cambia el modo en tiempo de ejecución y lo confirma con BEEP_<MODO>.
        False si el modo no existe."""
        from .behaviors import MODOS

        modo = modo.strip().upper().replace("Í", "I")
        if modo not in MODOS:
            return False
        now = self.link.now()
        self.log(now, f"OPERADOR modo {self.modo} -> {modo}")
        self.modo = modo
        if "OPERADOR" in self.behaviors:
            self.behaviors["OPERADOR"].pedir(modo, now)
        return True

    def set_volumen(self, pct) -> int:
        """Comando del operador: volumen del buzzer en % (0..100, se recorta). Se oye también en el sonido
        que está sonando. Devuelve el volumen que quedó."""
        self.volumen = min(max(int(pct), 0), VOL_MAX)
        self.log(self.link.now(), f"OPERADOR volumen {self.volumen} %")
        self._volumen_enviado = False  # sale en el próximo tick, si hay sesión
        return self.volumen

    def sonar(self, sonido: str) -> bool:
        """Comando del operador: reproduce un sonido de config.yaml (p. ej. para probar el buzzer)."""
        sonido = sonido.strip().upper()
        if sonido not in self.cfg["sounds"] or "OPERADOR" not in self.behaviors:
            return False
        now = self.link.now()
        self.log(now, f"OPERADOR sonido {sonido}")
        self.behaviors["OPERADOR"].pedir_sonido(sonido, now)
        return True

    # ------------------------------------------------------------ operador
    def stop(self) -> None:
        """Primero se enclava el STOP localmente y después se transmite: si la escritura
        falla (cable suelto, puerto caído), el robot igual queda detenido de este lado
        y el STOP se reintenta en cada tick hasta que salga (revisión de Codex)."""
        now = self.link.now()
        self.en_home = False       # el STOP manda: frena donde esté, aunque estuviera yendo a HOME
        for g in self.arb.emergency_stop(now):
            self.behaviors[g.behavior].on_cancel(g, self._ctx(now, 0.0, None))
        self._send_stop(now)

    def home(self) -> None:
        """HOME del operador (prioridad 0, como STOP): lleva la cabeza a HOME y la deja ahí hasta RESUME.
        El árbitro queda detenido para que ningún comportamiento mande un J encima del HOME (antes el botón
        mandaba solo "HOME" y, en el ciclo siguiente, el Observador o el seguimiento lo pisaban). A la ESP32:
        RESUME (si había un STOP enclavado, rechaza el HOME con STOP_ACTIVE) y después HOME."""
        now = self.link.now()
        for g in self.arb.emergency_stop(now):
            self.behaviors[g.behavior].on_cancel(g, self._ctx(now, 0.0, None))
        self._stop_unsent = False  # no reintentar un STOP viejo encima del HOME
        self.link.send("RESUME")
        self.link.send("HOME")
        self.act.ref = list(self.cfg["neck"]["home"])  # lo que se comandó (overlay, panel, Observador al volver)
        self.en_home = True
        self.log(now, "OPERADOR HOME (quieto hasta RESUME)")

    def _send_stop(self, now: float) -> None:
        try:
            self.link.send("STOP")
        except Exception as e:  # noqa: BLE001 - cualquier error del enlace: se reintenta
            if not self._stop_unsent:
                self.log(now, f"STOP no transmitido ({type(e).__name__}: {e}); se reintenta")
            self._stop_unsent = True
        else:
            if self._stop_unsent:
                self.log(now, "STOP transmitido")
            self._stop_unsent = False

    def ejes(self) -> bool:
        """Comando del operador: demostración de los tres ejes (DemoEjes). Desde HOME la reanuda sola; con
        el STOP enclavado no (es la parada de seguridad: se levanta a propósito con RESUME)."""
        if self.en_home:
            self.resume()
        elif self.arb.stopped:
            return False
        now = self.link.now()
        self.log(now, "OPERADOR ejes")
        self.behaviors["EJES"].pedir(now)
        return True

    def resume(self) -> None:
        # Al revés que stop(): si RESUME no sale, el árbitro sigue detenido (lo seguro).
        self.link.send("RESUME")
        self.arb.resume(self.link.now())
        self.en_home = False

    # ------------------------------------------------------------ ciclo
    def _ctx(self, now, dt, world, cuello_captura=None) -> Context:
        return Context(now, dt, world, self.act, self.arb, self.focus, self.cfg, self.modo, cuello_captura)

    def _posicion_cuello(self) -> tuple[float, float, float]:
        """Dónde está el cuello ahora. Con el espejo del firmware (SimLink, o SerialLink con espejo_cfg) es la
        posición de la trayectoria; sin él, la última referencia enviada (una aproximación)."""
        try:
            return tuple(self.link.neck_pos)
        except AttributeError:
            return tuple(self.act.ref)

    def _cuello_en(self, t: float) -> tuple[float, float, float] | None:
        """Posición del cuello en el instante t, interpolando la historia. None si t es más viejo que la historia."""
        h = self._historia
        if not h or t < h[0][0]:
            return None
        if t >= h[-1][0]:
            return h[-1][1]
        i = bisect.bisect_right([ti for ti, _ in h], t)   # h[i-1].t <= t < h[i].t
        (t0, p0), (t1, p1) = h[i - 1], h[i]
        k = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
        return tuple(a + k * (b - a) for a, b in zip(p0, p1))

    def _resync(self, now: float) -> None:
        """El ESP32 se reinició: sus sonidos y referencias ya no existen."""
        for g in self.arb.cancel_all(now, "ESP32 reinició"):
            self.behaviors[g.behavior].on_cancel(g, self._ctx(now, 0.0, None))
        self.act.reset_after_reboot(self.cfg["neck"]["home"])
        self._volumen_enviado = False  # la ESP32 volvió al volumen de config.yaml
        if self.arb.stopped:
            self._send_stop(now)  # el STOP del operador sobrevive al reinicio

    def tick(self, world: World, world_age: float = 0.0) -> None:
        """world_age: segundos desde que se capturó el cuadro que originó `world`."""
        now = self.link.now()
        dt = 0.0 if self._last is None else now - self._last
        self._last = now
        self.act.process(self.link.poll())
        if self.act.rebooted:
            self._resync(now)
        if self._stop_unsent and self.arb.stopped:
            self._send_stop(now)
        if not self.act.session:  # sin sesión no se comanda nada; reintentar HELLO cada 0,5 s
            self._volumen_enviado = False
            if now - self._hello_t > 0.5:
                self.link.hello()
                self._hello_t = now
            return
        if not self._volumen_enviado:  # sesión nueva (o ESP32 reiniciada) o el operador lo cambió
            self.link.send("VOL", self.volumen)
            self._volumen_enviado = True

        ok = world_age <= self.max_world_age
        if ok != self._perception_ok:
            self.log(now, "PERCEPCION ok" if ok else f"PERCEPCION sin datos frescos ({world_age:.2f} s)")
            self._perception_ok = ok
        if not ok:  # nadie es visible "ahora": el foco mantiene y luego libera por lost_hold
            world = replace(world, t=world.t + world_age)
        self._historia.append((now, self._posicion_cuello()))
        cuello_captura = self._cuello_en(now - world_age) if ok else None

        target = self.focus.update(world)
        if target != self._target:
            self.log(now, f"FOCO {self._target} -> {target}")
            self._target = target

        ctx = self._ctx(now, dt, world, cuello_captura)
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
