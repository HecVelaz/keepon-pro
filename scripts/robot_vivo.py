#!/usr/bin/env python3
"""Keepon con la cámara y los servos de verdad (se corre en la Pi, con camera_node andando).

Cadena: Perception (procesos de personas —YOLO + tracker + rostros/ME_MIRA— y de pose) → World →
Eventos (ME_MIRA sostenido y SALUDO, keepon/eventos.py) → Robot (foco, comportamientos, árbitro, control
de mirada) → SerialLink → ESP32. Todavía sin camisetas ni SALIENDO.

    bash ~/keepon/scripts/robot_vivo.sh            # arranca camera_node y esto; Ctrl+C manda STOP
    ~/keepon_env/bin/python scripts/robot_vivo.py  # si camera_node ya está corriendo

El log de transiciones (T7) va a logs/run_*.csv.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keepon import load_config  # noqa: E402
from keepon.world import Person, World  # noqa: E402


def mundo_desde(det, cfg: dict, t: float) -> World:
    """Un resultado del proceso de personas → World en el instante t (reloj del enlace).

    Person.u/v es el centro del rostro: la nariz si se encontró la cara; si no, un punto a la altura
    de la cabeza dentro de la caja (el 12 % superior), para seguir igual a quien está de espaldas."""
    w = World.from_cfg(cfg, t=t)
    if det is None:
        return w
    for p in det.persons:
        x1, y1, x2, y2 = p.box
        if p.face is not None:
            u, v = p.face.nose[0], p.face.nose[1]
        else:
            u, v = (x1 + x2) / 2, y1 + 0.12 * (y2 - y1)
        w.persons[p.id] = Person(p.id, float(u), float(v), float(y2 - y1),
                                 looking=bool(p.face.looking) if p.face else False, last_seen=t)
    return w


def main() -> None:
    from keepon.eventos import Eventos
    from keepon.link import SerialLink
    from keepon.perception import Perception
    from keepon.robot import Robot

    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default=load_config()["serial"]["port"])
    ap.add_argument("--duracion", type=float, default=0.0, help="segundos (0 = hasta Ctrl+C)")
    a = ap.parse_args()

    cfg = load_config()
    link = SerialLink(a.puerto, espejo_cfg=cfg)
    robot = Robot(cfg, link)
    robot.resume()  # un Ctrl+C de una corrida anterior deja el STOP enclavado en la ESP32: liberarlo
    eventos = Eventos(cfg, log=robot.log)
    per = Perception(cfg, workers=("personas", "pose"))
    periodo = 1.0 / cfg["control"]["rate_hz"]
    print("Cargando modelos (~15 s). Ctrl+C manda STOP y sale.")
    t0 = link.now()
    det = pose = None
    ciclos, t_hz = 0, time.monotonic()
    try:
        while not a.duracion or link.now() - t0 < a.duracion:
            inicio = link.now()
            for r in per.poll():
                if r.kind == "personas":
                    det = r
                else:
                    pose = r
            # Edad: desde que se capturó el cuadro (stamp, reloj de pared). Sin resultados todavía: viejo.
            edad = time.time() - det.stamp if det is not None else 1e9
            cajas = {p.id: p.box for p in det.persons} if det is not None else {}
            mundo = eventos.aplicar(mundo_desde(det, cfg, inicio), pose, cajas)
            robot.tick(mundo, world_age=edad)
            ciclos += 1
            if time.monotonic() - t_hz >= 10.0:  # cada 10 s: salud del lazo y de la percepción
                hz = ciclos / (time.monotonic() - t_hz)
                n = len(det.persons) if det else 0
                robot.log(link.now(), f"ESTADO lazo {hz:.0f} Hz, edad percepción {edad * 1000:.0f} ms, "
                                      f"personas {n}, desvío espejo {link.max_desvio:.2f}°")
                ciclos, t_hz = 0, time.monotonic()
            time.sleep(max(0.0, inicio + periodo - link.now()))
    except KeyboardInterrupt:
        robot.stop()
        robot.tick(World.from_cfg(cfg, t=link.now()), world_age=1e9)  # asegura que el STOP salga
        print("\nSTOP enviado (frenó donde estaba). Para seguir: RESUME y HOME.")
    else:
        link.send("HOME")
    finally:
        per.close()


if __name__ == "__main__":
    main()
