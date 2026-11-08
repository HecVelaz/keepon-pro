"""Diagrama del sistema con la foto real de cada componente, sus datos y las conexiones.

Fotos: docs/hardware/diagrama_sistema/fotos/ y docs/hardware/fotos/ (sin personas). Datos: docs/HARDWARE.md y config.yaml.
Salida: docs/img/diagrama_componentes.png (y .svg), que usan el informe y el README.

Uso:  python scripts/diagrama_componentes.py        (necesita Pillow y cairosvg)
"""
import base64
import io
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
W, H = 1800, 1240

FONDO, TARJETA, BORDE, TINTA, GRIS = "#f6f5f1", "#ffffff", "#d9d6cc", "#1d1d1b", "#6b6a64"
# colores de los cables (los mismos que docs/hardware/diagrama_sistema/index.html)
V6, V5, GND, SENAL, USB, CSI = "#d62828", "#e07a00", "#2b2b2b", "#c99a00", "#5b6b82", "#7c3aed"
FUENTE = 'font-family="Lato"'


def foto(ruta, w, h, modo="contener"):
    """Foto ajustada a w × h (contener: entera sobre blanco; cubrir: recortada) como data URI JPEG."""
    im = Image.open(RAIZ / ruta).convert("RGB")
    if modo == "cubrir":
        k = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        x, y = (im.width - w) // 2, (im.height - h) // 2
        im = im.crop((x, y, x + w, y + h))
    else:
        im.thumbnail((w, h), Image.LANCZOS)
        lienzo = Image.new("RGB", (w, h), "white")
        lienzo.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
        im = lienzo
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def tarjeta(x, y, w, h, img, titulo, rol, datos, color_rol=TINTA, alto_foto=150, modo="contener", nota=None):
    """Tarjeta de un componente: foto arriba, modelo en negrita, función y datos."""
    g = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{TARJETA}" stroke="{BORDE}" stroke-width="1.5"/>']
    if img:
        g.append(f'<image x="{x + 12}" y="{y + 12}" width="{w - 24}" height="{alto_foto}" href="{foto(img, (w - 24) * 2, alto_foto * 2, modo)}"/>')
    yy = y + alto_foto + 46
    g.append(f'<text x="{x + 16}" y="{yy}" {FUENTE} font-weight="900" font-size="22" fill="{TINTA}">{titulo}</text>')
    g.append(f'<text x="{x + 16}" y="{yy + 27}" {FUENTE} font-weight="700" font-size="17" fill="{color_rol}">{rol}</text>')
    for i, d in enumerate(datos):
        g.append(f'<text x="{x + 16}" y="{yy + 54 + i * 23}" {FUENTE} font-size="16" fill="{GRIS}">{d}</text>')
    if nota:
        g.append(f'<text x="{x + w - 14}" y="{y + alto_foto + 6}" text-anchor="end" {FUENTE} font-style="italic" '
                 f'font-size="12" fill="{GRIS}">{nota}</text>')
    return "".join(g)


def cable(puntos, color, ancho=5, guiones=None, etiqueta=None, pos=None, ancla="middle"):
    """Polilínea de un cable con su etiqueta sobre un fondo claro."""
    d = " ".join(f"{x},{y}" for x, y in puntos)
    extra = f' stroke-dasharray="{guiones}"' if guiones else ""
    g = [f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{ancho}" stroke-linejoin="round" stroke-linecap="round"{extra}/>']
    if etiqueta:
        x, y = pos
        ancho_txt = 8.4 * len(etiqueta) + 16
        x0 = x - ancho_txt / 2 if ancla == "middle" else (x if ancla == "start" else x - ancho_txt)
        g.append(f'<rect x="{x0:.0f}" y="{y - 17}" width="{ancho_txt:.0f}" height="26" rx="6" fill="{FONDO}" stroke="{color}" stroke-width="1.5"/>')
        g.append(f'<text x="{x0 + ancho_txt / 2:.0f}" y="{y + 2}" text-anchor="middle" {FUENTE} font-weight="700" font-size="15" fill="{color}">{etiqueta}</text>')
    return "".join(g)


def fuente_laboratorio(x, y, w, h):
    """Dibujo simple de la fuente de laboratorio (no hay foto en el repo)."""
    cx = x + w / 2
    g = [f'<rect x="{x + 12}" y="{y + 12}" width="{w - 24}" height="150" rx="6" fill="#f1efe9"/>',
         f'<rect x="{cx - 95}" y="{y + 30}" width="190" height="114" rx="8" fill="#3a3d42" stroke="#24262a" stroke-width="2"/>',
         f'<rect x="{cx - 80}" y="{y + 44}" width="104" height="40" rx="4" fill="#0f2a1c"/>',
         f'<text x="{cx - 28}" y="{y + 74}" text-anchor="middle" font-family="DejaVu Sans Mono" font-weight="bold" font-size="26" fill="#5cff9d">6.00V</text>',
         f'<circle cx="{cx + 52}" cy="{y + 64}" r="16" fill="#9aa1a9" stroke="#24262a" stroke-width="2"/>',
         f'<circle cx="{cx - 50}" cy="{y + 118}" r="11" fill="{V6}" stroke="#24262a" stroke-width="2"/>',
         f'<circle cx="{cx - 14}" cy="{y + 118}" r="11" fill="{GND}" stroke="#555" stroke-width="2"/>',
         f'<circle cx="{cx + 52}" cy="{y + 118}" r="16" fill="#9aa1a9" stroke="#24262a" stroke-width="2"/>']
    return "".join(g)


def diagrama():
    g = [f'<rect width="{W}" height="{H}" fill="{FONDO}"/>',
         f'<text x="60" y="62" {FUENTE} font-weight="900" font-size="34" fill="{TINTA}">Wall-E · componentes reales y conexiones</text>',
         f'<text x="60" y="92" {FUENTE} font-size="18" fill="{GRIS}">Dos alimentaciones separadas, unidas solo por el GND. '
         f'Todo el procesamiento en la Pi; la ESP32 mueve los servos y toca el buzzer.</text>']

    # --- cables primero (quedan debajo de las tarjetas)
    # powerbank -> Pi (5 V USB)
    g.append(cable([(360, 290), (560, 290)], V5, etiqueta="USB 5 V / 3 A", pos=(460, 278)))
    # cámara -> Pi (CSI)
    g.append(cable([(1140, 290), (940, 290)], CSI, etiqueta="CSI · cinta 150 mm", pos=(1040, 278)))
    # Pi -> ESP32 (USB serie, datos y 5 V)
    g.append(cable([(750, 470), (750, 540)], USB, ancho=6, etiqueta="USB serie 115 200 baud (datos + 5 V)", pos=(750, 507)))
    # ESP32 -> servos y buzzer (señales PWM)
    xs = [240, 680, 1120, 1560]
    for x, etq in zip(xs, ("GPIO0", "GPIO1", "GPIO4", "GPIO5")):
        g.append(cable([(750, 800), (750, 850), (x, 850), (x, 920)], SENAL, ancho=4))
        g.append(cable([(x, 880), (x, 881)], SENAL, ancho=4, etiqueta=etq, pos=(x, 892)))
    # fuente de 6 V -> los tres servos (rojo) y GND común (negro, también a la ESP32)
    g.append(cable([(360, 650), (400, 650), (400, 905), (1180, 905), (1180, 920)], V6, ancho=6))
    for x in (300, 740):
        g.append(cable([(x, 905), (x, 920)], V6, ancho=6))
    g.append(cable([(300, 905), (400, 905)], V6, ancho=6))
    g.append(cable([(560, 760), (490, 760), (490, 808)], GND, ancho=4, guiones="10 6"))
    g.append(cable([(360, 700), (490, 700), (490, 760)], GND, ancho=4, guiones="10 6"))
    g.append(cable([(400, 790), (400, 791)], V6, etiqueta="6 V", pos=(400, 790)))
    g.append(cable([(490, 820), (490, 821)], GND, etiqueta="GND común", pos=(490, 822)))

    # --- tarjetas
    g.append(tarjeta(60, 120, 300, 350, "docs/hardware/diagrama_sistema/fotos/powerbank.jpg", "Xiaomi PB2020MI",
                     "Alimenta la Raspberry Pi", ["20 000 mAh · 74 Wh", "salida 5 V / 3 A", "≈ 9 h de uso"], V5))
    g.append(tarjeta(560, 120, 380, 350, "docs/hardware/diagrama_sistema/fotos/pi5.jpg", "Raspberry Pi 5 (4 GB)",
                     "Percepción y decisión", ["Ubuntu 24.04 + ROS 2 Jazzy · Python", "YOLO26n + MediaPipe · lazo 36–39 Hz",
                                               "va dentro de la cabeza"], USB))
    g.append(tarjeta(1140, 120, 300, 350, "docs/hardware/diagrama_sistema/fotos/camara.jpg", "Camera Module 3 NoIR",
                     "Visión: es la nariz del robot", ["sensor IMX708 · 640×480 a 30 fps", "montada invertida (180°)",
                                                       "sin filtro infrarrojo"], CSI, nota="foto de referencia"))
    g.append(tarjeta(60, 540, 300, 300, None, "Fuente de laboratorio", "Alimenta los 3 servos",
                     ["6,0 V · límite 4–5 A", "uso normal 2–3 A"], V6))
    g.append(fuente_laboratorio(60, 540, 300, 300))
    g.append(tarjeta(560, 540, 380, 260, "docs/hardware/fotos/esp32_c3_mini_1/51gB6Uad4BL._AC_SX425_.jpg", "ESP32-C3-DevKitM-1",
                     "Control de servos y buzzer", ["trayectorias con curva S a 100 Hz", "PWM 50 Hz · watchdog 500 ms"],
                     SENAL, alto_foto=110))
    servos = [
        ("docs/hardware/diagrama_sistema/fotos/rds3218.jpg", "DSSERVO RDS3218", "YAW · gira la horquilla",
         ["20 kg·cm · 270° · 6 V", "±70° · hasta 180 °/s", "sin pulso mantiene la posición"]),
        ("docs/hardware/fotos/MG_996r_nuevo/mg_996r.jpg", "TowerPro MG996R", "PITCH · mueve la cuna",
         ["~10 kgf·cm a 6 V", "−20° / +30° · hasta 120 °/s", "sin pulso queda flojo"]),
        ("docs/hardware/fotos/MG_996r_nuevo/mg_996r.jpg", "TowerPro MG996R", "ROLL · inclina la cabeza",
         ["~10 kgf·cm a 6 V · disco de 25T", "±20° · hasta 250 °/s", "sin pulso queda flojo"]),
        ("docs/hardware/diagrama_sistema/fotos/buzzer.jpg", "Buzzer pasivo MH-FMD", "SONIDOS · VCC 3V3",
         ["frecuencia variable (LEDC)", "polca, R2D2, abucheo, beeps", "activo en bajo"]),
    ]
    for (img, tit, rol, datos), x in zip(servos, (60, 500, 940, 1380)):
        g.append(tarjeta(x, 920, 360, 290, img, tit, rol, datos, TINTA, alto_foto=120, modo="cubrir" if "rds" in img or "MG_996r" in img else "contener"))

    # --- referencias
    lx, ly = 1500, 540
    g.append(f'<rect x="{lx}" y="{ly}" width="240" height="300" rx="14" fill="{TARJETA}" stroke="{BORDE}" stroke-width="1.5"/>')
    g.append(f'<text x="{lx + 18}" y="{ly + 36}" {FUENTE} font-weight="900" font-size="20" fill="{TINTA}">Referencias</text>')
    for i, (col, txt, gu) in enumerate([(V6, "6 V servos", None), (V5, "5 V Raspberry Pi", None), (GND, "GND común", "10 6"),
                                        (SENAL, "señal PWM / buzzer", None), (USB, "USB serie", None), (CSI, "CSI cámara", None)]):
        y = ly + 74 + i * 36
        extra = f' stroke-dasharray="{gu}"' if gu else ""
        g.append(f'<line x1="{lx + 18}" y1="{y}" x2="{lx + 66}" y2="{y}" stroke="{col}" stroke-width="5" stroke-linecap="round"{extra}/>')
        g.append(f'<text x="{lx + 78}" y="{y + 5}" {FUENTE} font-size="16" fill="{TINTA}">{txt}</text>')
    g.append(f'<text x="{lx + 18}" y="{ly + 288}" {FUENTE} font-size="13" fill="{GRIS}">Encender: powerbank → 6 V</text>')

    # nota de seguridad junto a la ESP32
    g.append(f'<text x="980" y="600" {FUENTE} font-weight="700" font-size="17" fill="{TINTA}">Por qué dos fuentes</text>')
    for i, t in enumerate(["Los picos y el ruido de los servos", "no reinician la Pi. Sin el GND",
                           "común, ningún servo se mueve.", "", "Apagar: al revés, sosteniendo la",
                           "cabeza (los MG996R quedan flojos)."]):
        g.append(f'<text x="980" y="{628 + i * 23}" {FUENTE} font-size="16" fill="{GRIS}">{t}</text>')

    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(g) + "</svg>"


def main():
    import cairosvg
    svg = diagrama()
    salida = RAIZ / "docs" / "img" / "diagrama_componentes.png"
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(salida), output_width=W, output_height=H)
    print(salida)


if __name__ == "__main__":
    main()
