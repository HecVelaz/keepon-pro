#!/usr/bin/env python3
"""Keepon con la cámara y los servos de verdad (se corre en la Pi, con camera_node andando).

Cadena: Perception (procesos de personas —YOLO + tracker + rostros/ME_MIRA— y de pose) → World →
Eventos (ME_MIRA sostenido y SALUDO, keepon/eventos.py) → Robot (foco, comportamientos, árbitro, control
de mirada) → SerialLink → ESP32. Todavía sin camisetas ni SALIENDO.

    bash ~/keepon/scripts/robot_vivo.sh            # arranca camera_node y esto; Ctrl+C manda STOP
    ~/keepon_env/bin/python scripts/robot_vivo.py  # si camera_node ya está corriendo

Monitoreo (T7): el video con overlay (keepon/overlay.py) se publica en /keepon/overlay a ~10 Hz
(--sin-overlay lo apaga) y el log de transiciones va a logs/run_*.csv.
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


class Monitor:
    """Overlay T7: dibuja el estado del robot sobre el último cuadro y lo publica en /keepon/overlay
    (web_video_server lo sirve al navegador). Usa su propia suscripción a la cámara."""

    TOPICO = "/keepon/overlay"

    def __init__(self, cfg: dict, hz: float = 10.0):
        from sensor_msgs.msg import Image

        from keepon.camera import Camera

        self.Image = Image
        self.cam = Camera(cfg)
        self.pub = self.cam._node.create_publisher(Image, self.TOPICO, 2)
        self.periodo, self.t_ultimo = 1.0 / hz, 0.0

    def publicar(self, **estado) -> None:
        """Como mucho a `hz`; si todavía no hay cuadro (o la cámara se cortó), no hace nada."""
        from keepon import overlay

        if time.monotonic() - self.t_ultimo < self.periodo:
            return
        self.t_ultimo = time.monotonic()
        try:
            frame, _, _ = self.cam.latest(timeout=0)
        except Exception:  # noqa: BLE001 - sin cuadro: el robot sigue igual
            return
        img = overlay.dibujar(frame.copy(), **estado)
        msg = self.Image()
        msg.header.stamp = self.cam._node.get_clock().now().to_msg()
        msg.height, msg.width = img.shape[:2]
        msg.encoding, msg.step = "bgr8", img.shape[1] * 3
        msg.data = img.tobytes()
        self.pub.publish(msg)

    def close(self) -> None:
        self.cam.close()


def main() -> None:
    from keepon.arbiter import BUZZER, NECK
    from keepon.eventos import Eventos
    from keepon.link import SerialLink
    from keepon.overlay import Salud
    from keepon.perception import Perception
    from keepon.robot import Robot

    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default=load_config()["serial"]["port"])
    ap.add_argument("--duracion", type=float, default=0.0, help="segundos (0 = hasta Ctrl+C)")
    ap.add_argument("--sin-overlay", action="store_true", help="no publicar el video con overlay (T7)")
    a = ap.parse_args()

    cfg = load_config()
    link = SerialLink(a.puerto, espejo_cfg=cfg)
    robot = Robot(cfg, link)
    robot.resume()  # un Ctrl+C de una corrida anterior deja el STOP enclavado en la ESP32: liberarlo
    eventos = Eventos(cfg, log=robot.log)
    per = Perception(cfg, workers=("personas", "pose"))
    monitor = None if a.sin_overlay else Monitor(cfg)
    periodo = 1.0 / cfg["control"]["rate_hz"]
    print("Cargando modelos (~15 s). Ctrl+C manda STOP y sale.")
    if monitor:
        print(f"Overlay en el navegador: http://<IP de la Pi>:8080/stream_viewer?topic={Monitor.TOPICO}")
    t0 = link.now()
    det = pose = None
    salud = Salud()
    cuenta = {"lazo": 0, "personas": 0, "pose": 0}
    t_hz, t_log = time.monotonic(), time.monotonic()
    tick_max, hueco_max, inicio_ant = 0.0, 0.0, None  # trabas del lazo (ERR WATCHDOG de la ESP32)
    try:
        while not a.duracion or link.now() - t0 < a.duracion:
            inicio = link.now()
            if inicio_ant is not None:  # entre inicios de ticks: si pasa de 500 ms, salta el watchdog
                hueco_max = max(hueco_max, inicio - inicio_ant)
            inicio_ant = inicio
            for r in per.poll():
                cuenta[r.kind] += 1
                if r.kind == "personas":
                    det = r
                else:
                    pose = r
            # Edad: desde que se capturó el cuadro (stamp, reloj de pared). Sin resultados todavía: viejo.
            edad = time.time() - det.stamp if det is not None else 1e9
            cajas = {p.id: p.box for p in det.persons} if det is not None else {}
            mundo = eventos.aplicar(mundo_desde(det, cfg, inicio), pose, cajas)
            robot.tick(mundo, world_age=edad)
            cuenta["lazo"] += 1

            if time.monotonic() - t_hz >= 1.0:  # tasas del último segundo
                dt = time.monotonic() - t_hz
                salud.lazo_hz, salud.personas_hz, salud.pose_hz = (cuenta[k] / dt for k in ("lazo", "personas", "pose"))
                cuenta, t_hz = {k: 0 for k in cuenta}, time.monotonic()
            salud.edad_ms, salud.desvio_espejo = edad * 1000, link.max_desvio
            if monitor:
                monitor.publicar(mundo=mundo, det=det, pose=pose, objetivo=robot.focus.target,
                                 dueños={"CUELLO": robot.arb.owner[NECK], "BUZZER": robot.arb.owner[BUZZER]},
                                 ref=robot.act.ref, modo=getattr(robot, "modo", "NEUTRO"), stop=robot.arb.stopped,
                                 saludo_reciente=lambda pid: eventos.saludo_reciente(pid, inicio), salud=salud)
            tick_max = max(tick_max, link.now() - inicio)
            if time.monotonic() - t_log >= 10.0:  # cada 10 s al log: salud del lazo y de la percepción
                n = len(det.persons) if det else 0
                robot.log(link.now(), f"ESTADO lazo {salud.lazo_hz:.0f} Hz (tick máx {tick_max * 1000:.0f} ms, "
                                      f"hueco máx {hueco_max * 1000:.0f} ms), personas {salud.personas_hz:.1f} Hz, "
                                      f"pose {salud.pose_hz:.1f} Hz, edad {salud.edad_ms:.0f} ms, personas vistas {n}, "
                                      f"espejo {link.max_desvio:.2f}° ({link.resyncs} resinc.)")
                t_log, tick_max, hueco_max = time.monotonic(), 0.0, 0.0
            time.sleep(max(0.0, inicio + periodo - link.now()))
    except KeyboardInterrupt:
        robot.stop()
        robot.tick(World.from_cfg(cfg, t=link.now()), world_age=1e9)  # asegura que el STOP salga
        print("\nSTOP enviado (frenó donde estaba). Para seguir: RESUME y HOME.")
    else:
        link.send("HOME")
    finally:
        per.close()
        if monitor:
            monitor.close()


if __name__ == "__main__":
    main()
