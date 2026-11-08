"""Overlay de monitoreo (T7) sobre el video de la cámara.

Muestra lo que pide la guía: personas con ID, persona objetivo, eventos activos (ME_MIRA, SALUDO,
camiseta), modo, comportamiento dueño de cada recurso (cuello y buzzer) y ángulos comandados; además,
la salud del sistema (Hz del lazo, Hz y edad de la percepción). Solo dibuja: no decide nada.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

VERDE, GRIS, AMARILLO, CIAN = (60, 200, 60), (160, 160, 160), (0, 210, 255), (230, 200, 0)
BLANCO, ROJO, NARANJA, MAGENTA = (255, 255, 255), (60, 60, 230), (0, 140, 255), (220, 80, 220)
HUESOS = [("hombro_i", "hombro_d"), ("hombro_i", "codo_i"), ("codo_i", "muneca_i"),
          ("hombro_d", "codo_d"), ("codo_d", "muneca_d")]


@dataclass
class Salud:
    lazo_hz: float = 0.0
    personas_hz: float = 0.0
    pose_hz: float = 0.0
    edad_ms: float = float("nan")  # desde la captura del cuadro hasta ahora
    desvio_espejo: float = 0.0


def texto(img, s: str, org, color=BLANCO, escala=0.5, grosor=1) -> None:
    """Texto con borde negro, legible sobre cualquier fondo (OpenCV no dibuja tildes: se quitan)."""
    s = s.encode("ascii", "ignore").decode()
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, escala, (0, 0, 0), grosor + 2, cv2.LINE_AA)
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, escala, color, grosor, cv2.LINE_AA)


def _dueño(g) -> str:
    return f"{g.behavior}#{g.id}" + (f" p{g.person}" if g.person is not None else "") if g else "-"


def dibujar(img: np.ndarray, *, mundo, det, pose, objetivo: int | None, dueños: dict, ref, modo: str,
            stop: bool, saludo_reciente, salud: Salud) -> np.ndarray:
    """Dibuja sobre img (BGR, se modifica y se devuelve).

    mundo: World filtrado (looking y wave_count ya pasaron por Eventos). det/pose: últimos DetResult (o None).
    dueños: {"CUELLO": Grant|None, "BUZZER": Grant|None}. ref: ángulos comandados (yaw, pitch, roll).
    saludo_reciente(pid) -> bool: si esa persona saludó hace poco."""
    h, w = img.shape[:2]
    # Centro óptico: adonde el control lleva el rostro del objetivo.
    cx, cy = int(mundo.cx), int(mundo.cy)
    cv2.drawMarker(img, (cx, cy), GRIS, cv2.MARKER_CROSS, 18, 1)

    if pose is not None:
        for kp in pose.poses:
            for a, b in HUESOS:
                pa, pb = kp[a], kp[b]
                if pa[2] > 0.5 and pb[2] > 0.5:
                    cv2.line(img, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), CIAN, 2)
            for k in ("muneca_i", "muneca_d"):
                x, y, v = kp[k]
                if v > 0.5:
                    arriba = y < min(kp["hombro_i"][1], kp["hombro_d"][1])
                    cv2.circle(img, (int(x), int(y)), 7, ROJO if arriba else CIAN, -1)

    if det is not None:
        for po in det.persons:
            p = mundo.persons.get(po.id)
            x1, y1, x2, y2 = (int(v) for v in po.box)
            es_obj = po.id == objetivo
            col = NARANJA if es_obj else (VERDE if p is not None and p.looking else AMARILLO)
            cv2.rectangle(img, (x1, y1), (x2, y2), col, 4 if es_obj else 2)
            texto(img, f"ID {po.id}" + ("  OBJETIVO" if es_obj else ""), (x1 + 4, max(16, y1 + 18)), col, 0.6,
                  2 if es_obj else 1)
            etiquetas = []
            if p is not None and p.looking:
                etiquetas.append(("ME_MIRA", VERDE))
            if saludo_reciente(po.id):
                etiquetas.append(("SALUDO!", MAGENTA))
            if p is not None and p.shirt:
                etiquetas.append((p.shirt, NARANJA))
            for i, (s, c) in enumerate(etiquetas):
                texto(img, s, (x1 + 4, y1 + 42 + 22 * i), c, 0.6, 2)
            if es_obj and p is not None:  # error del control: del centro óptico al rostro
                u, v = int(p.u), int(p.v)
                cv2.drawMarker(img, (u, v), NARANJA, cv2.MARKER_TILTED_CROSS, 22, 2)
                cv2.line(img, (cx, cy), (u, v), NARANJA, 1, cv2.LINE_AA)

    # Panel de estado: abajo a la izquierda y semitransparente (las cabezas suelen quedar arriba)
    y0 = h - 24 - 104
    fondo = img[y0:h - 24, 0:300]
    fondo[:] = (fondo * 0.35).astype(fondo.dtype)
    texto(img, f"MODO {modo}" + ("   STOP" if stop else ""), (8, y0 + 20), ROJO if stop else BLANCO, 0.55,
          2 if stop else 1)
    texto(img, f"CUELLO: {_dueño(dueños.get('CUELLO'))}", (8, y0 + 42), AMARILLO)
    texto(img, f"BUZZER: {_dueño(dueños.get('BUZZER'))}", (8, y0 + 62), AMARILLO)
    y, p_, r = ref
    texto(img, f"J yaw {y:+6.1f}  pitch {p_:+5.1f}  roll {r:+5.1f}", (8, y0 + 84), CIAN)
    texto(img, f"foco: {objetivo if objetivo is not None else '-'}", (8, y0 + 100), BLANCO, 0.45)

    # Barra de salud (abajo)
    cv2.rectangle(img, (0, h - 24), (w, h), (0, 0, 0), -1)
    edad_ok = salud.edad_ms <= 300
    texto(img, f"lazo {salud.lazo_hz:.0f} Hz | personas {salud.personas_hz:.1f} Hz, pose {salud.pose_hz:.1f} Hz | "
               f"edad {salud.edad_ms:.0f} ms | espejo {salud.desvio_espejo:.1f}", (6, h - 7),
          BLANCO if edad_ok else ROJO, 0.45)
    return img
