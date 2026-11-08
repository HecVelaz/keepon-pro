"""Portadas del video (apertura y cierre) con un dibujo de Wall-E en vista frontal.

El dibujo usa las medidas del modelo de SolidWorks v6 R4 (docs/diseno_v6/config.yaml y las láminas de
docs/diseno_v6/documentacion/planos_svg_revision/): cara de 124 × 104 mm, ojos con el contorno octogonal de
`ojos.contorno_local_uv_mm` centrados a ±30 mm y 22 mm sobre el centro, lente de 27,8 mm, horquilla de
204,5 mm, cuna de 185,6 mm, base de 210 mm y ejes de pitch y roll que se cruzan a 163 mm (la cámara-nariz).
Las alturas de la base y del yaw están simplificadas (es una ilustración, no un plano).

Uso:  python scripts/portadas_video.py [carpeta_salida]      (por defecto video/portadas/, fuera de git)
Necesita cairosvg para el PNG (pip install cairosvg); sin él deja solo los SVG.
"""
import math
import sys
from pathlib import Path

W, H = 1920, 1080

# Colores: PLA negro del robot, filamento amarillo de los bordes, ojos blancos, papel y tinta de plano
PAPEL, GRILLA, GRILLA2 = "#f3eee4", "#e7e0d3", "#dcd3c3"
TINTA, AZUL, AMARILLO = "#1f2328", "#2f5d8a", "#f2b705"
NEGRO, NEGRO2, BORDE = "#17191c", "#23272c", "#3a4047"
BLANCO, GRIS = "#f7f5ef", "#8a9098"

# Contorno de un ojo [mm] (u horizontal, v vertical), de docs/diseno_v6/config.yaml
OJO = [(-18, 22), (12, 13), (23, 4), (24, -11), (15, -21), (-1, -21), (-18, -12), (-23, 0)]
Z_EJES = 163.0          # cruce de los ejes de pitch y roll = centro óptico de la cámara


class Lienzo:
    """Pasa de milímetros del robot (y a la derecha, z hacia arriba) a píxeles."""

    def __init__(self, x0, y0, escala):
        self.x0, self.y0, self.s = x0, y0, escala

    def p(self, y, z):
        return self.x0 + y * self.s, self.y0 - z * self.s

    def pts(self, lista):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(a, b) for a, b in lista))

    def rect(self, y1, z1, y2, z2, fill, r=0.0, stroke=BORDE, sw=1.5, extra=""):
        x, ya = self.p(min(y1, y2), max(z1, z2))
        w, h = abs(y2 - y1) * self.s, abs(z2 - z1) * self.s
        return (f'<rect x="{x:.1f}" y="{ya:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r * self.s:.1f}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circ(self, y, z, d, fill, stroke="none", sw=0.0):
        x, yy = self.p(y, z)
        return f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{d / 2 * self.s:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def ojo(L, yc, zc, espejo):
    """Marco amarillo con el contorno del CAD, ojo blanco, lente, pupila y brillos."""
    k = -1 if espejo else 1
    contorno = [(yc + k * u, zc + v) for u, v in OJO]
    s = L.s
    out = [f'<polygon points="{L.pts(contorno)}" fill="{BLANCO}" stroke="{AMARILLO}" '
           f'stroke-width="{2.6 * s:.1f}" stroke-linejoin="round"/>']
    out.append(L.circ(yc, zc - 1, 27.8, "#ece8de", "#c9c4b8", 0.9 * s))      # lente de 27,8 mm
    out.append(L.circ(yc + k * -1.0, zc - 2, 18.5, NEGRO))                   # pupila
    out.append(L.circ(yc + k * -4.5, zc + 2.5, 5.2, BLANCO))                 # brillos
    out.append(L.circ(yc + k * 3.0, zc - 6.0, 2.4, BLANCO))
    return out


def cabeza(L, roll_deg=0.0):
    """Cara de 124 × 104 mm con su muesca superior, chaflanes, tornillos, ojos, cámara-nariz y buzzer."""
    zc = Z_EJES
    cara = [(-62, zc + 52), (-11, zc + 52), (0, zc + 46.5), (11, zc + 52), (62, zc + 52),
            (62, zc - 46), (56, zc - 52), (-56, zc - 52), (-62, zc - 46)]
    g = []
    g.append(f'<polygon points="{L.pts([(y + 2.2, z - 2.2) for y, z in cara])}" fill="#000" opacity="0.10"/>')
    g.append(f'<polygon points="{L.pts(cara)}" fill="{NEGRO}" stroke="{AMARILLO}" '
             f'stroke-width="{1.8 * L.s:.1f}" stroke-linejoin="round"/>')
    # textura de las capas de impresión: líneas horizontales muy tenues
    for z in range(int(zc - 50), int(zc + 50), 3):
        x1, y1 = L.p(-60, z)
        x2, _ = L.p(60, z)
        g.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y1:.1f}" stroke="#fff" stroke-opacity="0.025" stroke-width="1"/>')
    for y, z in [(-55, 34), (55, 34), (-55, -34), (55, -34)]:                 # tornillos de la cara
        g.append(L.circ(y, zc + z, 4.6, "#6f757d", "#2a2e33", 0.4 * L.s))
        g.append(L.circ(y, zc + z, 1.6, "#3b4046"))
    g += ojo(L, -30, zc + 22, espejo=True)
    g += ojo(L, 30, zc + 22, espejo=False)
    # cámara Module 3: placa cuadrada, aro y lente, en el centro óptico (cruce de los ejes)
    g.append(L.rect(-6, zc - 6, 6, zc + 6, "#2a2d31", r=1, stroke="#4a5058", sw=1.2))
    g.append(L.circ(0, zc, 8.0, "#9aa1a9", "#5b6168", 0.4 * L.s))
    g.append(L.circ(0, zc, 5.6, "#0b0c0e"))
    g.append(L.circ(-1.0, zc + 1.0, 1.4, "#7fa7c9"))
    # agujero del buzzer, debajo de la nariz
    g.append(L.circ(0, zc - 27, 10.5, "#0a0b0d", "#30353b", 0.8 * L.s))
    g.append(L.circ(0, zc - 27, 4.0, "#22262b"))
    x, y = L.p(0, zc)
    return f'<g transform="rotate({-roll_deg:.2f} {x:.1f} {y:.1f})">' + "".join(g) + "</g>"


def cuerpo(L):
    """Base, yaw, horquilla de pitch con sus ventanas, servo de pitch con su disco y el perno del otro lado."""
    g = []
    # sombra en el piso
    for i, a in enumerate((0.05, 0.05, 0.05)):
        x, y = L.p(0, -1)
        g.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{(118 - i * 8) * L.s:.1f}" ry="{(7 - i * 2) * L.s:.1f}" fill="#000" opacity="{a}"/>')
    g.append(L.rect(-105, 0, 105, 6, NEGRO2, r=1.5))                     # base de 210 mm
    g.append(L.rect(-33, 6, -21, 54, NEGRO))                             # pilares del yaw
    g.append(L.rect(21, 6, 33, 54, NEGRO))
    g.append(L.rect(-19, 6, 19, 44, "#8e2a2f", r=1.5, stroke="#5e1a1e"))  # servo de yaw RDS3218
    g.append(L.rect(-19, 34, 19, 39, "#6f2126", stroke="none"))
    g.append(L.rect(-42, 54, 42, 62, NEGRO2, r=1))                       # adaptador del yaw
    g.append(L.rect(-14, 62, 14, 72, NEGRO, r=1))                        # cubo del horn
    # horquilla de pitch: placa inferior y dos brazos de 129 mm con su ventana
    g.append(L.rect(-102.25, 72, 102.25, 80, NEGRO2, r=1))
    for y1, y2 in ((-102.25, -92.25), (92.25, 102.25)):
        g.append(L.rect(y1, 72, y2, 201, NEGRO, r=1))
        g.append(L.rect(y1 + 2.5, 92, y2 - 2.5, 140, "#2d3238", stroke="none"))
    g.append(L.rect(-92.8, 84, 92.8, 90, "#2a2e33", r=1))                # cuna de 185,6 mm
    g.append(L.rect(-17, 90, 17, 112, NEGRO, r=1))                       # soporte del servo de roll
    g.append(L.circ(0, 101, 9, "#30353b", "#4a5058", 1.2))               # horn del roll
    # servo de pitch (MG996R) por fuera del brazo izquierdo, con el disco entre el brazo y la cabeza
    g.append(L.rect(-146, Z_EJES - 10, -104, Z_EJES + 10, "#1b1d20", r=1.5))
    g.append(L.rect(-150, Z_EJES - 2.5, -100, Z_EJES + 2.5, "#1b1d20", stroke=BORDE, sw=1))
    g.append(L.rect(-91, Z_EJES - 17, -78, Z_EJES + 17, NEGRO2, r=4))   # disco del horn
    # perno del pivote, del lado derecho
    g.append(L.rect(102.25, Z_EJES - 3, 122, Z_EJES + 3, "#9aa1a9", r=1, stroke="#5b6168", sw=1))
    g.append(L.rect(102.25, Z_EJES - 5, 107, Z_EJES + 5, "#7f868e", stroke="#5b6168", sw=1))
    g.append(L.rect(-78, Z_EJES - 3, -62, Z_EJES + 3, "#30353b", stroke="none"))  # eje hacia la cabeza
    g.append(L.rect(62, Z_EJES - 3, 92.25, Z_EJES + 3, "#30353b", stroke="none"))
    return "".join(g)


def flecha_arco(cx, cy, rx, ry, a1, a2, color, sw=2.4):
    """Arco elíptico con punta de flecha al final (ángulos en grados, sentido antihorario en pantalla)."""
    p1 = (cx + rx * math.cos(math.radians(a1)), cy - ry * math.sin(math.radians(a1)))
    p2 = (cx + rx * math.cos(math.radians(a2)), cy - ry * math.sin(math.radians(a2)))
    grande = 1 if abs(a2 - a1) > 180 else 0
    barrido = 0 if a2 > a1 else 1
    d = f"M{p1[0]:.1f},{p1[1]:.1f} A{rx:.1f},{ry:.1f} 0 {grande} {barrido} {p2[0]:.1f},{p2[1]:.1f}"
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'marker-end="url(#punta)" stroke-linecap="round"/>')


def cotas(L):
    """Ejes y cotas del modelo de SolidWorks, en azul de plano."""
    g = []
    mono = 'font-family="DejaVu Sans Mono" font-size="17" fill="' + AZUL + '"'
    linea = f'stroke="{AZUL}" stroke-width="1.4"'
    # eje de yaw (vertical) y de pitch (horizontal), con trazo y punto
    x, y1 = L.p(0, -8)
    _, y2 = L.p(0, 240)
    g.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" {linea} stroke-dasharray="14 5 3 5"/>')
    xa, yp = L.p(-162, Z_EJES)
    xb, _ = L.p(140, Z_EJES)
    g.append(f'<line x1="{xa:.1f}" y1="{yp:.1f}" x2="{xb:.1f}" y2="{yp:.1f}" {linea} stroke-dasharray="14 5 3 5"/>')
    # yaw: flecha alrededor del eje vertical, a la altura de los pilares
    cx, cy = L.p(0, 38)
    g.append(flecha_arco(cx, cy, 58 * L.s, 7 * L.s, 200, 340, AZUL))
    tx, ty = L.p(-150, 30)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" {mono}>YAW ±70°</text>')
    # pitch: flecha alrededor del eje horizontal, al final del perno
    cx, cy = L.p(132, Z_EJES)
    g.append(flecha_arco(cx, cy, 5 * L.s, 16 * L.s, 110, 430 - 70, AZUL))
    tx, ty = L.p(142, Z_EJES + 14)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" {mono}>PITCH</text>')
    tx, ty = L.p(142, Z_EJES + 6)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" {mono}>−20° / +30°</text>')
    # roll: arco alrededor de la cámara (el eje sale hacia el que mira)
    cx, cy = L.p(0, Z_EJES)
    g.append(flecha_arco(cx, cy, 87 * L.s, 87 * L.s, 122, 166, AZUL))
    tx, ty = L.p(-62, 236)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="end" {mono}>ROLL ±20°</text>')
    # cota del ancho de la cara (124 mm), arriba
    xa, yy = L.p(-62, 229)
    xb, _ = L.p(62, 229)
    g.append(f'<line x1="{xa:.1f}" y1="{yy:.1f}" x2="{xb:.1f}" y2="{yy:.1f}" {linea} marker-start="url(#punta_ini)" marker-end="url(#punta)"/>')
    for yv in (-62, 62):
        x, ya = L.p(yv, 218)
        _, yb = L.p(yv, 233)
        g.append(f'<line x1="{x:.1f}" y1="{ya:.1f}" x2="{x:.1f}" y2="{yb:.1f}" stroke="{AZUL}" stroke-width="1"/>')
    tx, ty = L.p(0, 233)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" {mono}>124</text>')
    # cota de la horquilla (204,5 mm), abajo
    xa, yy = L.p(-102.25, -16)
    xb, _ = L.p(102.25, -16)
    g.append(f'<line x1="{xa:.1f}" y1="{yy:.1f}" x2="{xb:.1f}" y2="{yy:.1f}" {linea} marker-start="url(#punta_ini)" marker-end="url(#punta)"/>')
    for yv in (-102.25, 102.25):
        x, ya = L.p(yv, -20)
        _, yb = L.p(yv, 86)
        g.append(f'<line x1="{x:.1f}" y1="{ya:.1f}" x2="{x:.1f}" y2="{yb:.1f}" stroke="{AZUL}" stroke-width="1" stroke-dasharray="3 4"/>')
    tx, ty = L.p(0, -23)
    g.append(f'<text x="{tx:.1f}" y="{ty + 8:.1f}" text-anchor="middle" {mono}>204,5</text>')
    # cota de la altura de los ejes (163 mm), a la derecha
    x, ya = L.p(160, 0)
    _, yb = L.p(160, Z_EJES)
    g.append(f'<line x1="{x:.1f}" y1="{ya:.1f}" x2="{x:.1f}" y2="{yb:.1f}" {linea} marker-start="url(#punta_ini)" marker-end="url(#punta)"/>')
    xa, yy = L.p(110, 0)
    xb, _ = L.p(166, 0)
    g.append(f'<line x1="{xa:.1f}" y1="{yy:.1f}" x2="{xb:.1f}" y2="{yy:.1f}" stroke="{AZUL}" stroke-width="1"/>')
    tx, ty = L.p(166, Z_EJES / 2)
    g.append(f'<text x="{tx:.1f}" y="{ty:.1f}" {mono} transform="rotate(-90 {tx:.1f} {ty:.1f})" text-anchor="middle" dy="-6">163</text>')
    return "".join(g)


def lamina(contenido):
    """Hoja con grilla de plano, marco con marcas y las definiciones comunes."""
    defs = f"""<defs>
  <marker id="punta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,1 L9,5 L0,9 z" fill="{AZUL}"/></marker>
  <marker id="punta_ini" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M10,1 L1,5 L10,9 z" fill="{AZUL}"/></marker>
</defs>"""
    g = [f'<rect width="{W}" height="{H}" fill="{PAPEL}"/>']
    for x in range(0, W + 1, 33):
        g.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{GRILLA2 if x % 165 == 0 else GRILLA}" stroke-width="1"/>')
    for y in range(0, H + 1, 33):
        g.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{GRILLA2 if y % 165 == 0 else GRILLA}" stroke-width="1"/>')
    m = 30
    g.append(f'<rect x="{m}" y="{m}" width="{W - 2 * m}" height="{H - 2 * m}" fill="none" stroke="{TINTA}" stroke-width="2"/>')
    for i in range(1, 12):                                    # marcas del marco, como en una lámina
        x = m + i * (W - 2 * m) / 12
        g.append(f'<line x1="{x:.0f}" y1="{m}" x2="{x:.0f}" y2="{m + 10}" stroke="{TINTA}" stroke-width="1.5"/>')
        g.append(f'<line x1="{x:.0f}" y1="{H - m}" x2="{x:.0f}" y2="{H - m - 10}" stroke="{TINTA}" stroke-width="1.5"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            + defs + "".join(g) + contenido + "</svg>")


def rotulo(x, y, lineas):
    """Rótulo de plano (abajo a la derecha): título, vista, modelo y unidades."""
    w, h = 470, 34 * len(lineas) + 8
    g = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="1.6"/>']
    for i, (etq, val) in enumerate(lineas):
        yy = y + 30 + i * 34
        if i:
            g.append(f'<line x1="{x}" y1="{yy - 26}" x2="{x + w}" y2="{yy - 26}" stroke="{TINTA}" stroke-width="0.8"/>')
        g.append(f'<text x="{x + 14}" y="{yy}" font-family="DejaVu Sans Mono" font-size="13" fill="{GRIS}">{etq}</text>')
        g.append(f'<text x="{x + 120}" y="{yy}" font-family="DejaVu Sans Mono" font-size="17" fill="{TINTA}">{val}</text>')
    return "".join(g)


INTEGRANTES = ["Mathias Aguilar", "Héctor Velázquez", "Pablo Otazú", "Pedro Vera"]
LATO = 'font-family="Lato"'


def apertura():
    L = Lienzo(510, 880, 2.75)
    dibujo = cuerpo(L) + cabeza(L) + cotas(L)
    x = 1090
    t = [f'<text x="{x}" y="200" font-family="DejaVu Sans Mono" font-size="20" letter-spacing="3" fill="{AZUL}">'
         f'µTP ROBÓTICA SOCIAL · ROBÓTICA II · FIUNA</text>',
         f'<text x="{x - 8}" y="390" {LATO} font-weight="900" font-size="210" fill="{TINTA}">Wall-E</text>',
         f'<rect x="{x}" y="425" width="150" height="12" fill="{AMARILLO}"/>',
         f'<text x="{x}" y="505" {LATO} font-weight="500" font-size="42" fill="{TINTA}">Cabeza robótica social de 3 grados</text>',
         f'<text x="{x}" y="558" {LATO} font-weight="500" font-size="42" fill="{TINTA}">de libertad con visión artificial</text>',
         f'<text x="{x}" y="625" font-family="DejaVu Sans Mono" font-size="21" fill="{GRIS}">'
         f'Raspberry Pi 5 · ESP32-C3 · YOLO26n · MediaPipe</text>',
         f'<text x="{x}" y="712" font-family="DejaVu Sans Mono" font-size="17" letter-spacing="3" fill="{AZUL}">INTEGRANTES</text>']
    for i, n in enumerate(INTEGRANTES):
        t.append(f'<text x="{x + (i % 2) * 330}" y="{760 + (i // 2) * 46}" {LATO} font-weight="700" font-size="32" fill="{TINTA}">{n}</text>')
    t.append(rotulo(1400, 890, [("ROBOT", "Wall-E · proyecto Keepon pro"), ("VISTA", "frontal · cotas en mm"),
                                ("MODELO", "SolidWorks v6 R4 · 2026")]))
    return lamina(dibujo + "".join(t))


def cierre():
    L = Lienzo(1440, 880, 2.75)
    dibujo = cuerpo(L) + cabeza(L, roll_deg=-12)        # cabeza inclinada, como en la curiosidad
    cx, cy = L.p(0, Z_EJES)
    dibujo += flecha_arco(cx, cy, 92 * L.s, 92 * L.s, 102, 62, AZUL)
    tx, ty = L.p(-20, Z_EJES + 98)
    dibujo += (f'<text x="{tx:.1f}" y="{ty:.1f}" font-family="DejaVu Sans Mono" font-size="17" '
               f'fill="{AZUL}" text-anchor="end">ROLL 12° · curiosidad</text>')
    x = 110
    t = [f'<text x="{x}" y="200" font-family="DejaVu Sans Mono" font-size="20" letter-spacing="3" fill="{AZUL}">'
         f'FIN DE LA DEMOSTRACIÓN</text>',
         f'<text x="{x - 8}" y="380" {LATO} font-weight="900" font-size="190" fill="{TINTA}">¡Gracias!</text>',
         f'<rect x="{x}" y="418" width="150" height="12" fill="{AMARILLO}"/>',
         f'<text x="{x}" y="500" {LATO} font-weight="700" font-size="44" fill="{TINTA}">Wall-E · cabeza robótica social de 3 GDL</text>',
         f'<text x="{x}" y="560" font-family="DejaVu Sans Mono" font-size="17" letter-spacing="3" fill="{AZUL}">CÓDIGO, INFORME Y GUÍA</text>',
         f'<text x="{x}" y="602" {LATO} font-weight="500" font-size="34" fill="{TINTA}">github.com/HecVelaz/keepon-pro</text>',
         f'<text x="{x}" y="680" font-family="DejaVu Sans Mono" font-size="17" letter-spacing="3" fill="{AZUL}">INTEGRANTES</text>']
    for i, n in enumerate(INTEGRANTES):
        t.append(f'<text x="{x + (i % 2) * 330}" y="{726 + (i // 2) * 44}" {LATO} font-weight="700" font-size="30" fill="{TINTA}">{n}</text>')
    t += [f'<text x="{x}" y="878" font-family="DejaVu Sans Mono" font-size="17" fill="{GRIS}">'
          f'Modelos preentrenados: YOLO26n (Ultralytics) · MediaPipe (Google)</text>',
          f'<text x="{x}" y="906" font-family="DejaVu Sans Mono" font-size="17" fill="{GRIS}">'
          f'Árbitro, comportamientos, control y firmware: desarrollo propio</text>',
          f'<text x="{x}" y="1000" font-family="DejaVu Sans Mono" font-size="19" letter-spacing="2" fill="{TINTA}">'
          f'Robótica II · Facultad de Ingeniería · Universidad Nacional de Asunción · 2026</text>']
    return lamina(dibujo + "".join(t))


def main():
    salida = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "video" / "portadas")
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, svg in (("portada_inicio", apertura()), ("portada_final", cierre())):
        (salida / f"{nombre}.svg").write_text(svg, encoding="utf-8")
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=svg.encode(), write_to=str(salida / f"{nombre}.png"),
                             output_width=W, output_height=H)
            print(salida / f"{nombre}.png")
        except ImportError:
            print(salida / f"{nombre}.svg", "(sin cairosvg: solo SVG)")


if __name__ == "__main__":
    main()
