"""Figura del overlay de monitoreo (T7) sin robot ni cámara, para el informe y el README.

Usa la función real keepon/overlay.py:dibujar() sobre una escena SINTÉTICA: un fondo ilustrado con dos siluetas
(no hay personas reales: el repo es público). Los datos son los que tendría el robot en un momento típico:
la persona 1 lleva la camiseta de Olimpia, mira al robot y es el objetivo (el seguimiento tiene el cuello y la
polca el buzzer); la persona 2 está saludando. Al lado, la explicación de cada elemento.

Uso:  python scripts/figura_overlay.py      → docs/img/overlay_monitoreo.png
"""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from keepon.overlay import Salud, dibujar  # noqa: E402

W, H = 640, 480                                   # resolución de la cámara del robot
LATO = "/usr/share/fonts/truetype/lato/Lato-{}.ttf"


def escena():
    """Fondo de laboratorio ilustrado (BGR) con dos siluetas planas, sin personas reales."""
    img = np.zeros((H, W, 3), np.uint8)
    for y in range(H):                                            # pared con un degradé suave
        img[y, :] = (205 - y // 12, 200 - y // 12, 190 - y // 14)
    cv2.rectangle(img, (0, 340), (W, H), (120, 125, 130), -1)     # piso
    cv2.rectangle(img, (470, 60), (600, 340), (95, 110, 140), -1)  # puerta
    cv2.rectangle(img, (40, 250), (230, 270), (70, 90, 110), -1)   # mesa
    cv2.rectangle(img, (55, 270), (65, 340), (60, 75, 95), -1)
    cv2.rectangle(img, (205, 270), (215, 340), (60, 75, 95), -1)
    cv2.rectangle(img, (60, 70), (200, 160), (225, 225, 220), -1)  # pizarra
    # persona 1: silueta con la camiseta de Olimpia (blanca con una franja negra horizontal)
    cv2.circle(img, (300, 150), 34, (150, 160, 175), -1)
    cv2.rectangle(img, (255, 195), (345, 330), (235, 235, 235), -1)
    cv2.rectangle(img, (255, 245), (345, 270), (30, 30, 30), -1)
    cv2.rectangle(img, (230, 200), (255, 300), (235, 235, 235), -1)
    cv2.rectangle(img, (345, 200), (370, 300), (235, 235, 235), -1)
    cv2.rectangle(img, (262, 330), (296, 440), (70, 60, 50), -1)
    cv2.rectangle(img, (304, 330), (338, 440), (70, 60, 50), -1)
    # persona 2: silueta saludando con la mano derecha levantada
    cv2.circle(img, (470 - 40, 175), 26, (150, 160, 175), -1)
    cv2.rectangle(img, (398, 208), (462, 320), (150, 110, 90), -1)
    cv2.line(img, (462, 215), (492, 150), (150, 110, 90), 16)
    cv2.line(img, (398, 215), (385, 290), (150, 110, 90), 16)
    cv2.rectangle(img, (403, 320), (427, 420), (70, 60, 50), -1)
    cv2.rectangle(img, (433, 320), (457, 420), (70, 60, 50), -1)
    return img


def datos():
    """Lo que el robot sabe en ese cuadro, con las mismas estructuras que usa robot.py."""
    mundo = NS(cx=W / 2, cy=H / 2, fy=948.0, persons={
        1: NS(looking=True, shirt="OLIMPIA", u=300, v=150),
        2: NS(looking=False, shirt=None, u=430, v=175)})
    det = NS(persons=[NS(id=1, box=(222, 105, 378, 445), face=NS(dev_deg=8.0, looking=True)),
                      NS(id=2, box=(372, 140, 505, 425), face=NS(dev_deg=34.0, looking=False))])
    kp1 = {"hombro_i": (262, 205, .9), "hombro_d": (338, 205, .9), "codo_i": (242, 250, .9),
           "codo_d": (358, 250, .9), "muneca_i": (242, 295, .9), "muneca_d": (358, 295, .9)}
    kp2 = {"hombro_i": (402, 215, .9), "hombro_d": (458, 215, .9), "codo_i": (392, 255, .9),
           "codo_d": (478, 182, .9), "muneca_i": (386, 290, .9), "muneca_d": (492, 150, .9)}
    pose = NS(poses=[kp1, kp2], camisetas=[("OLIMPIA", (262, 214, 338, 320)), ("OTRA", (404, 222, 456, 300))])
    dueños = {"CUELLO": NS(behavior="SEGUIMIENTO", id=8, person=1), "BUZZER": NS(behavior="CAMISETA", id=7, person=1)}
    return mundo, det, pose, dueños


def figura(overlay_bgr, salida):
    lam = Image.new("RGB", (1800, 980), (246, 245, 241))
    d = ImageDraw.Draw(lam)
    f = {n: ImageFont.truetype(LATO.format(e), s) for n, e, s in
         [("tit", "Black", 40), ("sub", "Medium", 20), ("h", "Black", 21), ("t", "Regular", 17), ("p", "Italic", 16)]}
    d.text((60, 40), "Overlay de monitoreo (T7): lo que el robot ve y decide", font=f["tit"], fill=(29, 29, 27))
    d.text((60, 96), "Dibujado por keepon/overlay.py (el mismo código del robot) sobre una escena sintética: "
                     "las siluetas no son personas reales.", font=f["sub"], fill=(107, 106, 100))
    img = Image.fromarray(cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)).resize((1056, 792), Image.LANCZOS)
    lam.paste(img, (60, 150))
    d.rectangle((59, 149, 1116, 942), outline=(29, 29, 27), width=2)
    items = [
        ("Persona objetivo (naranja)", ["Caja gruesa con \"ID 1 OBJETIVO\". La cruz marca el", "rostro y la línea, el error que corrige el control."]),
        ("Eventos de cada persona", ["ME_MIRA (verde), el ángulo cara→cámara,", "SALUDO! (magenta) y CAMISETA_OLIMPIA."]),
        ("Otras personas", ["Amarillo si no miran, verde si miran al robot.", "Cada una con su ID del tracker."]),
        ("Pose y torso", ["Brazos en cian; la muñeca en rojo cuando está", "sobre el hombro. El torso evaluado y su clase."]),
        ("Panel de estado", ["Modo, dueño del CUELLO y del BUZZER", "(comportamiento, n.º y persona), ángulos J y foco."]),
        ("Barra de salud", ["Hz del lazo, de personas y de pose, edad del", "cuadro (en rojo si pasa de 300 ms)."]),
        ("Cruz gris", ["Adonde el control lleva el rostro: el centro", "óptico, 8° más arriba para que entre la camiseta."]),
    ]
    y = 160
    for i, (tit, lineas) in enumerate(items, 1):
        d.ellipse((1150, y + 2, 1178, y + 30), fill=(242, 160, 32))
        d.text((1164, y + 16), str(i), font=f["h"], fill=(255, 255, 255), anchor="mm")
        d.text((1192, y + 2), tit, font=f["h"], fill=(29, 29, 27))
        for j, l in enumerate(lineas):
            d.text((1192, y + 34 + j * 23), l, font=f["t"], fill=(107, 106, 100))
        y += 108
    d.text((1150, y + 6), "Se ve en vivo en el navegador:", font=f["p"], fill=(107, 106, 100))
    d.text((1150, y + 28), "http://<ip-de-la-pi>:8080/stream_viewer?topic=/keepon/overlay", font=f["p"], fill=(107, 106, 100))
    lam.save(salida, optimize=True)


def main():
    img = escena()
    mundo, det, pose, dueños = datos()
    dibujar(img, mundo=mundo, det=det, pose=pose, objetivo=1, dueños=dueños, ref=(4.6, -2.1, 0.0), modo="NEUTRO",
            stop=False, saludo_reciente=lambda pid: pid == 2,
            salud=Salud(lazo_hz=38, personas_hz=15.2, pose_hz=8.6, edad_ms=112, desvio_espejo=0.4), abajo_deg=8.0)
    salida = RAIZ / "docs" / "img" / "overlay_monitoreo.png"
    figura(img, salida)
    print(salida)


if __name__ == "__main__":
    main()
