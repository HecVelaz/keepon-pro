#!/usr/bin/env python3
"""Visor de la percepción (prueba visual + base del monitoreo T7).

Corre keepon/perception.py, dibuja sus resultados sobre la imagen de la cámara y la
publica en el tópico ROS 2 /keepon/percepcion, que web_video_server sirve al navegador.
Lanzarlo con scripts/ver_percepcion.sh (arranca cámara + servidor web).

Qué se dibuja:
  - caja e ID de cada persona (el ID debe mantenerse al moverse y cruzarse)
  - rostro: punto en la nariz y línea hacia donde apunta la cara;
    VERDE + "MIRA" si el desvío cara->cámara es menor al umbral, gris si no
  - pose: hombros, codos y muñecas
  - Hz y edad de cada proceso, y si algún proceso dejó de entregar
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from keepon import load_config  # noqa: E402
from keepon.camera import Camera  # noqa: E402
from keepon.perception import Perception  # noqa: E402

VERDE, GRIS, AMARILLO, CIAN, BLANCO, ROJO = (60, 200, 60), (160, 160, 160), (0, 210, 255), (230, 200, 0), (255, 255, 255), (60, 60, 230)
HUESOS = [("hombro_i", "hombro_d"), ("hombro_i", "codo_i"), ("codo_i", "muneca_i"),
          ("hombro_d", "codo_d"), ("codo_d", "muneca_d")]


def texto(img, s, org, color=BLANCO, escala=0.5):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, escala, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, escala, color, 1, cv2.LINE_AA)


def dibujar(img, per: Perception, rates: dict, cfg: dict) -> None:
    ahora = time.time()
    rp = per.latest.get("personas")
    if rp and ahora - rp.t_done < 0.5:
        for p in rp.persons:
            x1, y1, x2, y2 = (int(v) for v in p.box)
            f = p.face
            col = VERDE if f and f.looking else AMARILLO
            cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
            texto(img, f"ID {p.id}", (x1 + 4, y1 + 18), col, 0.6)
            if f:
                nx, ny = int(f.nose[0]), int(f.nose[1])
                # Línea hacia donde apunta la cara (yaw/pitch relativos a mirar la cámara).
                L = 60
                ex = int(nx + L * np.sin(np.radians(f.yaw_deg)))
                ey = int(ny - L * np.sin(np.radians(f.pitch_deg)))
                cv2.circle(img, (nx, ny), 5, VERDE if f.looking else GRIS, -1)
                cv2.line(img, (nx, ny), (ex, ey), VERDE if f.looking else GRIS, 2)
                etiqueta = f"MIRA {f.dev_deg:.0f}" if f.looking else f"no mira {f.dev_deg:.0f}"
                texto(img, etiqueta + "°".encode("ascii", "ignore").decode(), (x1 + 4, y1 + 40), VERDE if f.looking else GRIS)
            else:
                texto(img, "sin rostro", (x1 + 4, y1 + 40), GRIS)
    pp = per.latest.get("pose")
    if pp and ahora - pp.t_done < 0.5:
        for pose in pp.poses:
            for a, b in HUESOS:
                pa, pb = pose[a], pose[b]
                if pa[2] > 0.5 and pb[2] > 0.5:
                    cv2.line(img, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), CIAN, 2)
            for k in ("muneca_i", "muneca_d"):
                x, y, v = pose[k]
                if v > 0.5:
                    arriba = y < min(pose["hombro_i"][1], pose["hombro_d"][1])
                    cv2.circle(img, (int(x), int(y)), 7, ROJO if arriba else CIAN, -1)
    # Barra de estado
    cv2.rectangle(img, (0, img.shape[0] - 26), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
    estado = []
    for k in ("personas", "pose"):
        r = per.latest.get(k)
        edad = (ahora - r.stamp) * 1000 if r else float("nan")
        caido = not r or ahora - r.t_done > 1.0
        estado.append(f"{k}: {'CAIDO' if caido else f'{rates.get(k, 0):.1f} Hz, {edad:.0f} ms'}")
    texto(img, " | ".join(estado) + f" | umbral MIRA {cfg['perception']['looking_deg']:.0f}", (6, img.shape[0] - 8), BLANCO, 0.45)


def main() -> None:
    import rclpy
    from sensor_msgs.msg import Image

    cfg = load_config()
    per = Perception(cfg)
    cam = Camera(cfg)  # su propia suscripción, sólo para dibujar encima
    node = cam._node   # se reutiliza el nodo de la cámara para publicar
    pub = node.create_publisher(Image, "/keepon/percepcion", 2)
    counts, rates, t_rate = {"personas": 0, "pose": 0}, {}, time.monotonic()
    print("Visor publicando en /keepon/percepcion (Ctrl+C para salir)")
    try:
        while rclpy.ok():
            for r in per.poll():
                counts[r.kind] += 1
            if time.monotonic() - t_rate >= 1.0:
                dt = time.monotonic() - t_rate
                rates = {k: v / dt for k, v in counts.items()}
                counts, t_rate = {k: 0 for k in counts}, time.monotonic()
            try:
                frame, _, _ = cam.latest(timeout=2)
            except Exception:  # noqa: BLE001
                time.sleep(0.1)
                continue
            img = frame.copy()
            dibujar(img, per, rates, cfg)
            msg = Image()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.height, msg.width = img.shape[:2]
            msg.encoding, msg.step = "bgr8", img.shape[1] * 3
            msg.data = img.tobytes()
            pub.publish(msg)
            time.sleep(0.08)  # ~12 Hz de visor: suficiente y barato
    except KeyboardInterrupt:
        pass
    finally:
        per.close()
        cam.close()


if __name__ == "__main__":
    main()
