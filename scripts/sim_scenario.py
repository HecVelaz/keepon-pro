#!/usr/bin/env python3
"""Escenario sintético de M0: prueba árbitro + comportamientos + control de mirada
sin mecánica ni percepción. Tiempo simulado (reproducible y más rápido que real).

    python scripts/sim_scenario.py            # imprime el log
    python scripts/sim_scenario.py --plot     # además grafica ángulos y dueños
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keepon import load_config  # noqa: E402
from keepon.arbiter import BUZZER, NECK  # noqa: E402
from keepon.link import SimLink  # noqa: E402
from keepon.robot import EventLog, Robot  # noqa: E402
from keepon.synthetic import SynthCamera, SynthPerson, const, ramp  # noqa: E402


def scenario() -> list[SynthPerson]:
    """Línea de tiempo (s):
     0- 3  nadie                          -> OBSERVADOR
     3     aparece A a la derecha, camina -> SEGUIMIENTO
     8     A saluda                       -> SALUDO (cuello + buzzer, 3 cabeceos de 1 s)
    11.5   A con camiseta de Olimpia      -> POLCA (buzzer) mientras sigue
    13.5   A saluda durante la polca      -> SALUDO interrumpe la POLCA
    14     A saluda otra vez (cooldown)   -> ignorado
    16     A deja de mirar; aparece B (Cerro) mirando -> ABUCHEO; foco pasa a B tras 1,5 s
    17-17.5 A ocluido 0,5 s               -> se mantiene la mirada
    22     STOP del operador; 23 RESUME
    26     todos se van                   -> OBSERVADOR
    """
    A = SynthPerson(1, appear=3.0, leave=26.0, az=ramp(3.5, 9.5, 30.0, -15.0), el=const(8.0), size=320,
                    looking=[(6.0, 16.0)], shirt=[(11.5, 26.0, "OLIMPIA")], waves=[8.0, 13.5, 14.0],
                    hidden=[(17.0, 17.5)])
    B = SynthPerson(2, appear=16.0, leave=26.0, az=const(-5.0), el=const(4.0), size=420,
                    looking=[(16.0, 26.0)], shirt=[(16.0, 26.0, "CERRO")])
    return [A, B]


def run(duration: float = 30.0, rate: float = 40.0, echo: bool = True):
    cfg = load_config()
    link = SimLink(cfg, realtime=False)
    log = EventLog(to_file=echo, echo=echo)
    robot = Robot(cfg, link, log=log)
    cam = SynthCamera(cfg, scenario())
    dt = 1.0 / rate
    trace = []
    events = {22.0: robot.stop, 23.0: robot.resume}
    t = 0.0
    while t < duration:
        for te, fn in list(events.items()):
            if t >= te:
                log(t, f"OPERADOR {fn.__name__.upper()}")
                fn()
                del events[te]
        world = cam.observe(t, link.neck_pos)
        robot.tick(world)
        own = {r: (g.behavior if (g := robot.arb.owner[r]) else "-") for r in (NECK, BUZZER)}
        tgt = world.visible(robot.focus.target)
        err = (tgt.u - world.cx) if tgt else None  # contra el centro óptico, como el control
        trace.append((t, *link.neck_pos, own[NECK], own[BUZZER], err, link.esp.sound))
        link.advance(dt)
        t += dt
    return robot, trace


def plot(trace, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = [r[0] for r in trace]
    fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2, 1.4]})
    for i, name in enumerate(("yaw", "pitch", "roll")):
        ax[0].plot(t, [r[1 + i] for r in trace], label=name)
    ax[0].set_ylabel("ángulo real [°]")
    ax[0].legend(loc="upper right")
    ax[1].plot(t, [r[6] if r[6] is not None else float("nan") for r in trace], color="C3")
    ax[1].axhline(0, color="gray", lw=0.6)
    ax[1].set_ylabel("error objetivo [px]")
    names = ["OBSERVADOR", "SEGUIMIENTO", "SALUDO", "CAMISETA", "-"]
    ax[2].plot(t, [names.index(r[4]) for r in trace], ".", ms=2, label="dueño CUELLO")
    ax[2].plot(t, [names.index(r[5]) + 0.15 for r in trace], ".", ms=2, label="dueño BUZZER")
    ax[2].set_yticks(range(len(names)), names, fontsize=8)
    ax[2].legend(loc="upper right", fontsize=8)
    ax[2].set_xlabel("t [s]")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"gráfico: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    a = ap.parse_args()
    robot, trace = run()
    print(f"\nviolaciones de recursos: {robot.act.violations}")
    if a.plot:
        plot(trace, Path(__file__).resolve().parent.parent / "logs" / "sim_scenario.png")
