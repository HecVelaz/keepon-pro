"""Lista de componentes de Keepon pro v3 (mecánica y electrónica) en PDF.

Las dimensiones de las piezas impresas salen del modelo (keepon_v3_cad.py): si cambia el CAD,
se vuelve a correr este script. Las de los componentes comprados son las nominales que usa el
modelo (hojas de datos y medidas típicas): las marcadas "MEDIR" hay que verificarlas con calibre.

    ~/cq_env/bin/python lista_componentes.py      # escribe ../lista_componentes_v3.pdf
"""
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import keepon_v3_cad as k
from keepon_cad import RDS3218, HS7955, MG996R

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "lista_componentes_v3.pdf"

# DejaVu tiene todos los símbolos que se usan (µ, Ω, ≈, ×, ≥, →, Ø)
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

AMARILLO = colors.HexColor("#F2BF1A")
OSCURO = colors.HexColor("#2B2B2B")
GRIS = colors.HexColor("#F3F3F3")
ESTADOS = {"TENEMOS": "#2E7D32", "FALTA": "#C62828", "IMPRIMIR": "#B8860B", "RECOM.": "#1565C0",
           "OPCIONAL": "#6D6D6D", "MEDIR": "#C62828"}

st_titulo = ParagraphStyle("t", fontName="DVB", fontSize=20, leading=24, spaceAfter=4)
st_sub = ParagraphStyle("s", fontName="DV", fontSize=10, leading=13, textColor=colors.HexColor("#555555"))
st_h1 = ParagraphStyle("h1", fontName="DVB", fontSize=14, leading=18, spaceBefore=10, spaceAfter=4)
st_h2 = ParagraphStyle("h2", fontName="DVB", fontSize=11, leading=14, spaceBefore=8, spaceAfter=3)
st_txt = ParagraphStyle("p", fontName="DV", fontSize=8.5, leading=11)
st_cel = ParagraphStyle("c", fontName="DV", fontSize=7.6, leading=9.6)
st_celb = ParagraphStyle("cb", parent=st_cel, fontName="DVB")
st_cab = ParagraphStyle("h", parent=st_cel, fontName="DVB", textColor=colors.white)
st_est = ParagraphStyle("e", parent=st_cel, fontName="DVB", alignment=TA_CENTER, textColor=colors.white)


def estado(e):
    return Paragraph(e, st_est), ESTADOS.get(e, "#6D6D6D")


def tabla(filas, anchos, cabecera=("Componente", "Cant.", "Dimensiones [mm]", "Detalle", "Estado")):
    """filas: (nombre, cantidad, dimensiones, detalle, estado). La columna de estado va coloreada."""
    datos = [[Paragraph(c, st_cab) for c in cabecera]]
    estilo = [("BACKGROUND", (0, 0), (-1, 0), OSCURO), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
              ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
              ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    for i, (nombre, cant, dim, det, est) in enumerate(filas, start=1):
        p_est, color = estado(est)
        datos.append([Paragraph(nombre, st_celb), Paragraph(str(cant), st_cel), Paragraph(dim, st_cel),
                      Paragraph(det, st_cel), p_est])
        estilo.append(("BACKGROUND", (-1, i), (-1, i), colors.HexColor(color)))
        estilo.append(("VALIGN", (-1, i), (-1, i), "MIDDLE"))
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-2, i), GRIS))
    t = Table(datos, colWidths=[a * mm for a in anchos], repeatRows=1)
    t.setStyle(TableStyle(estilo))
    return t


ANCHOS = (36, 11, 38, 82, 19)


def f(x):
    return f"{x:.1f}".replace(".", ",")


def dim3(x, y, z):
    return f"{f(x)} × {f(y)} × {f(z)}"


# ============================================================================================
# Datos
# ============================================================================================

def piezas_impresas():
    """Dimensiones (caja envolvente en el robot: X adelante × Y lado × Z alto) y volumen del modelo."""
    info = {
        "caja_base": ("Caja base", "Aloja la batería, los reguladores y el interruptor. Pared y piso de 3 mm. "
                      "Imprimir boca arriba (o MDF de 3 mm)."),
        "tapa_base": ("Tapa de la base", "Lleva el servo de yaw (brida por debajo) y el paso de cables. "
                      "Sin aro de rodamiento. Plana (o MDF de 4 mm)."),
        "plato_yaw": ("Plato de yaw", "Plataforma giratoria Ø146 cortada adelante (forma de D). Se atornilla "
                      "al horn del RDS3218: es lo único que la sostiene. Plano."),
        "cuna_esp32": ("Cuna de la ESP32", "Sostiene la ESP32-C3 por los extremos; los pines cuelgan libres."),
        "porta_buzzer": ("Portabuzzer", "Soporte del buzzer de Ø12 mm sobre el plato."),
        "soporte_pitch_izq": ("Soporte de pitch izquierdo", "Lleva el HS-7955TG atravesado (brida adentro)."),
        "soporte_pitch_der": ("Soporte de pitch derecho", "Pivote M4 alineado con el eje del HS-7955TG."),
        "horquilla_cabeza": ("Horquilla de la cabeza", "Gira con el pitch (horn del HS ↔ pivote M4) y lleva el "
                             "MG996R de roll."),
        "placa_roll": ("Placa de roll", "Se atornilla al horn del MG996R; lleva la Pi 5 parada y cierra la cabeza "
                       "por atrás. Plana, separadores hacia arriba."),
        "caja_cabeza": ("Caja de la cabeza (cara)", "Cara + paredes, abierta atrás. Imprimir apoyada sobre la cara, "
                        "sin soportes."),
        "nariz_camara": ("Nariz (cámara)", "Tapón negro Ø14 en el centro de la cara, con el agujero de la lente "
                         "(avellanado a 40°). Se pega."),
        "ojo_izq": ("Ojo izquierdo", "Tapón negro Ø20, decorativo. Se pega."),
        "ojo_der": ("Ojo derecho", "Tapón negro Ø20, decorativo. Se pega."),
    }
    filas, total = [], 0.0
    for nombre, forma, _, impresa, _ in k.ensamble():
        if not impresa:
            continue
        bb = forma.BoundingBox()
        vol = forma.Volume() / 1000
        total += vol
        titulo, det = info[nombre]
        det += f" Volumen {f(vol)} cm³ (≈ {round(vol * 1.24 * 0.5)} g de PLA con ~50 % de relleno)."
        filas.append((f"{titulo}<br/><font size=6.5 color='#666666'>{nombre}.stl</font>", 1,
                      dim3(bb.xlen, bb.ylen, bb.zlen), det, "IMPRIMIR"))
    return filas, total


def servo_dim(s):
    return (f"Cuerpo {f(s.L)} × {f(s.W)} × {f(s.H)}<br/>Brida {f(s.Lf)} (agujeros {f(s.hs)} × {f(s.hw)})<br/>"
            f"Eje a {f(s.S)} sobre la brida")


SERVOS = [
    ("Servo de yaw<br/>DSSERVO RDS3218 (n.º 2)", 1, servo_dim(RDS3218),
     "GPIO0. 270°, ±70° ≈ 960/2010 µs (límites 950/2020). Sin tope mecánico. Picos de ~1 A. ≈ 60 g. "
     "<b>Sin rodamiento: su eje sostiene todo el plato</b> (≈ 330 g, ≈ 1,3 kgf·cm de vuelco).", "TENEMOS"),
    ("Servo de pitch<br/>Hitec HS-7955TG", 1, servo_dim(HS7955),
     "GPIO1. ~18 kgf·cm, engranajes de titanio. Límites 760/2240 µs. Montado +30° arriba / −20° abajo. "
     "Sin pulso se mantiene firme.", "TENEMOS"),
    ("Servo de roll<br/>TowerPro MG996R", 1, servo_dim(MG996R),
     "GPIO4. Límites 1000/2000 µs (roll ±20°). Banda muerta ~10°. Sin pulso queda flojo. 55 g.", "TENEMOS"),
    ("Brazo doble de plástico (uno por servo)", 3,
     f"{f(k.BRAZO_L)} de punta a punta · cubo Ø{f(k.BRAZO_CUBO_D)}<br/>ancho {f(k.BRAZO_ANCHO[0])} → "
     f"{f(k.BRAZO_ANCHO[1])} · espesor {f(k.BRAZO_T)}<br/>agujeros cada ≈ 2,5–3 (MEDIR)",
     "El mismo en los tres servos (foto docs/Fotos/brazo_servo.jpeg). Plato, horquilla y placa de roll tienen una "
     "ranura a cada lado del eje: el tornillo entra en el agujero del brazo que quede debajo. "
     "Ojo: el HS-7955TG tiene estriado Hitec (24 dientes) y el RDS3218 y el MG996R de 25: cada brazo tiene que "
     "ser el de su servo.", "TENEMOS"),
    ("Servo de repuesto<br/>TowerPro MG90S", 1, "22,8 × 12,2 × 28,5",
     "Repuesto de roll (0,09 °/µs, banda muerta 20–30 µs). No se usa en el diseño.", "TENEMOS"),
]

TORNILLOS = [
    ("Tornillo M3 × 10–12 + tuerca", 12, "M3",
     "Bridas de los servos: 4 por servo (RDS a la tapa, HS al soporte izquierdo, MG996R a la horquilla).", "FALTA"),
    ("Tornillo M3 × 16 autorroscante / inserto", 4, "M3", "Tapa a las columnas de la caja base.", "FALTA"),
    ("Tornillo M3 × 10 + tuerca", 7, "M3",
     "Soportes de pitch al plato (4), cuna de la ESP32 (2) y portabuzzer (1).", "FALTA"),
    ("Tornillo M2 × 8 autorroscante (brazo)", 6, "M2",
     "Piezas a los brazos: 2 por brazo, uno en cada ranura (plato, horquilla, placa de roll). El central viene "
     "con el servo.", "FALTA"),
    ("Tornillo M4 × 20 + 2 arandelas + tuerca autofrenante", 1, "M4",
     "Pivote del pitch (soporte derecho ↔ horquilla).", "FALTA"),
    ("Tornillo M2,5 × 6 autorroscante", 4, "M2,5", "Pi 5 a los separadores de la placa de roll.", "FALTA"),
    ("Tornillo M2,5 × 12 autorroscante", 4, "M2,5", "Caja de la cabeza a la placa de roll (desde atrás).",
     "FALTA"),
    ("Tornillo M2 × 5", 4, "M2", "Cámara a los separadores de la cara.", "FALTA"),
    ("Cinta de velcro", 1, "≈ 20 de ancho", "Sujeta la batería (ranuras en el piso de la caja).", "FALTA"),
]

PROCESAMIENTO = [
    ("Raspberry Pi 5 · 4 GB", 1, "85 × 56 × 17 (con USB/Ethernet)<br/>agujeros 58 × 49, M2,5",
     "Ubuntu 24.04 + ROS 2 Jazzy. Percepción (YOLO26n + MediaPipe), árbitro y comportamientos. Va parada dentro de "
     "la cabeza; se alimenta por el GPIO (pines 2/4 = 5 V, 6 = GND). ~7 W típico, 12 W pico.", "TENEMOS"),
    ("Active Cooler de la Pi 5", 1, "≈ 48 × 30 × 11 sobre la placa (MEDIR la altura)",
     "Sin ventilador la Pi baja la frecuencia con ~240 % de CPU sostenido.", "RECOM."),
    ("Tarjeta microSD", 1, "15 × 11 × 1", "Sistema de la Pi (ya instalada).", "TENEMOS"),
    ("Camera Module 3 NoIR estándar<br/>(RSP-CAM-V3-NOIR, IMX708)", 1,
     "25 × 24 × 11,5<br/>agujeros 21 × 12,5, M2<br/>lente a 14,5 del borde inferior",
     "Es la nariz, en el centro de la cara. 66° H nominal, sin filtro IR. Conector de 22 pines.", "TENEMOS"),
    ("Cinta FFC CSI 22 → 15 pines", 1, "≈ 150 de largo × 16 de ancho (MEDIR)",
     "Recorrido con la U y el doblez en Z (dos pliegues a 45°, una sola vez): 147 de 150 mm. No torcerla.", "TENEMOS"),
    ("ESP32-C3-DevKitM-1 (clon CH340)", 1, "48,3 × 25,4 × ≈ 12 (con pines)",
     "Controla los 3 servos y el buzzer (LEDC 50 Hz / 14 bits, watchdog 500 ms). /dev/serial/by-id/usb-1a86_…",
     "TENEMOS"),
    ("Cable USB-A acodado → micro-USB", 1, "≈ 50 cm", "Pi (USB-A arriba en la cabeza) → ESP32. Flexible, con bucle "
     "de servicio en roll y pitch.", "RECOM."),
]

POTENCIA = [
    ("Batería LiPo 3S 8000 mAh", 1, "166 × 50 × 37 (MEDIR)",
     "11,1 V nominal, 12,6 V cargada, ≈ 89 Wh. Corte a 10,5 V. ≈ 550 g. Va en la caja base.", "TENEMOS"),
    ("Regulador 12 → 6,0 V, ≥ 10 A (módulo 20 A / 300 W)", 1, "≈ 65 × 50 × 25",
     "Alimenta los tres servos. Ajustar a 6,0 V antes de conectarlos. Verificar que IN− y OUT− estén unidos.",
     "FALTA"),
    ("Regulador 12 → 5,1 V, 5 A, salida a bornera", 1, "≈ 55 × 32 × 15",
     "Alimenta la Pi por el GPIO. Sin pasar de 5,25 V en los pines. Cable ≥ 20 AWG.", "FALTA"),
    ("Fusible 10 A (ATO) + portafusible", 1, "19 × 5 × 19 (fusible)", "Lo más cerca del + de la batería.", "FALTA"),
    ("Interruptor de balancín ≥ 15 A", 1, "corte 19,2 × 12,8 en la pared",
     "Sobre el positivo. Es también la parada de emergencia física.", "FALTA"),
    ("Conector XT60 hembra", 1, "16 × 8 × 15", "El que combine con la batería.", "FALTA"),
    ("Cable 14–16 AWG (rojo + negro)", "1 m", "—", "Tramos de 12 V y 6 V.", "FALTA"),
    ("Cable 20 AWG (5 V de la Pi)", "1 m", "—", "De la caja a la cabeza: cruza yaw, pitch y roll.", "FALTA"),
    ("Alargues de servo (macho-hembra)", 3, "≈ 30 cm", "Los servos de pitch y roll suben por el cuello.", "FALTA"),
    ("Alarma de tensión LiPo", 1, "≈ 40 × 25 × 10", "En el balanceador; pita si una celda baja de ~3,5 V.", "FALTA"),
    ("Capacitor electrolítico 2200 µF / 16 V", 1, "Ø13 × 25", "Bus de 6 V, cerca de los servos.", "FALTA"),
    ("Capacitor cerámico 100 nF", 1, "5 × 3", "En paralelo con el de 2200 µF.", "FALTA"),
    ("Bornera / barra de GND en estrella", 1, "≈ 30 × 10 × 10",
     "Une los negativos de los reguladores y el GND de la ESP32. Sin GND común no se mueve ningún servo.", "FALTA"),
    ("Cargador balanceador LiPo + bolsa ignífuga", 1, "—", "Cargar con balanceo a 1C (8 A) o menos.", "FALTA"),
]

BUZZER = [
    ("Buzzer pasivo", 1, "Ø12 × 9,5", "Sonidos del robot (GPIO10). En el portabuzzer, sobre el plato.", "FALTA"),
    ("Transistor 2N2222", 1, "TO-92 (4,5 × 3,5 × 4,5)", "Conmuta el buzzer desde el 5 V de la ESP32.", "FALTA"),
    ("Resistencia 1 kΩ, 1/4 W", 1, "6 × 2,3", "GPIO10 → base del 2N2222.", "FALTA"),
    ("Resistencia 10 kΩ, 1/4 W", 1, "6 × 2,3", "Base → emisor (lo mantiene apagado al arrancar).", "FALTA"),
    ("Diodo 1N4148", 1, "4 × 2", "Solo si el buzzer es electromagnético: en paralelo, en inversa.", "FALTA"),
    ("Resistencias 100 kΩ + 22 kΩ", 1, "6 × 2,3 c/u",
     "Divisor para medir la batería con un ADC (12,6 V → 2,27 V), p. ej. GPIO3.", "OPCIONAL"),
]


# ============================================================================================
# Documento
# ============================================================================================

def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(15 * mm, 9 * mm, f"Keepon pro v3 · lista de componentes · {date.today():%d/%m/%Y}")
    canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"página {doc.page}")
    canvas.setFillColor(AMARILLO)
    canvas.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    canvas.restoreState()


def main():
    impresas, vol_total = piezas_impresas()
    doc = SimpleDocTemplate(str(SALIDA), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=15 * mm, title="Keepon pro v3: lista de componentes",
                            author="Grupo Keepon pro (FIUNA, Robótica II)")
    h = []
    h.append(Paragraph("Keepon pro v3 · Lista de componentes", st_titulo))
    h.append(Paragraph("Cabeza robótica social de 3 GDL (yaw / pitch / roll) con visión artificial · µTP de "
                       "Robótica II, FIUNA", st_sub))
    h.append(Spacer(1, 5 * mm))

    vista = RAIZ / "vistas" / "01_frente_iso.png"
    if vista.exists():
        img = Image(str(vista), width=95 * mm, height=95 * mm * 900 / 1100)
        resumen = [
            ["Altura total", "≈ 227 mm"],
            ["Cabeza (ancho × alto × fondo)", "75 × 104 × 40 mm"],
            ["Caja base", "200 × 190 × 74 mm (con tapa)"],
            ["Plato de yaw", "Ø146 mm, en D, sin rodamiento"],
            ["Rangos", "yaw ±70°, pitch −20/+30°, roll ±20°"],
            ["Piezas a imprimir", f"{len(impresas)} ({f(vol_total)} cm³)"],
            ["Tornillería", f"{sum(t[1] for t in TORNILLOS if t[0].startswith("Tornillo"))} tornillos"],
        ]
        tr = Table([[Paragraph(a, st_celb), Paragraph(b, st_cel)] for a, b in resumen], colWidths=[40 * mm, 43 * mm])
        tr.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
                                ("BACKGROUND", (0, 0), (0, -1), GRIS), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        t = Table([[img, tr]], colWidths=[98 * mm, 84 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        h.append(t)
    h.append(Spacer(1, 4 * mm))
    h.append(Paragraph(
        "<b>Cómo leer las dimensiones.</b> Las piezas impresas se dan como la caja envolvente en la posición del "
        "robot: <b>X</b> (de atrás hacia la cara) × <b>Y</b> (de lado a lado) × <b>Z</b> (alto), en mm, tomadas "
        "del modelo CAD (<font name='DV'>docs/keepon_v3_cad/</font>). Los componentes comprados llevan las medidas "
        "nominales que usa el modelo (hojas de datos y medidas típicas); los marcados <b>MEDIR</b> hay que "
        "verificarlos con calibre antes de imprimir. <b>Estado:</b> TENEMOS = ya está en el grupo; FALTA = hay que "
        "conseguirlo; IMPRIMIR = pieza propia; RECOM. = recomendado; OPCIONAL.", st_txt))

    h.append(Paragraph("1. Diseño mecánico", st_h1))
    h.append(Paragraph("1.1 Piezas impresas (PLA)", st_h2))
    h.append(tabla(impresas, ANCHOS, ("Pieza", "Cant.", "X × Y × Z [mm]", "Función / impresión", "Estado")))
    h.append(Paragraph(f"Total a imprimir: {f(vol_total)} cm³ (≈ {round(vol_total * 1.24 * 0.5)} g de PLA con ~50 % "
                       "de relleno). La caja base y la tapa son el 70 %: se pueden hacer en MDF.", st_txt))
    h.append(Paragraph("1.2 Actuadores", st_h2))
    h.append(tabla(SERVOS, ANCHOS))
    h.append(Paragraph("Medidas de los servos: cuerpo largo × ancho × alto (sin brida ni eje); la brida es el largo "
                       "total de las orejas. Lo más delicado de medir es la altura del eje sobre la brida: de ahí "
                       "sale dónde apoya cada pieza sobre su horn.", st_txt))
    h.append(Paragraph("1.3 Tornillería", st_h2))
    h.append(tabla(TORNILLOS, ANCHOS, ("Elemento", "Cant.", "Medida", "Dónde va", "Estado")))
    h.append(Paragraph("No hay rodamiento de yaw: el plato se atornilla al horn del RDS3218 (ver "
                       "docs/keepon_v3_cad/README.md, «Yaw sin rodamiento»).", st_txt))
    h.append(PageBreak())

    h.append(Paragraph("2. Diseño electrónico", st_h1))
    h.append(Paragraph("2.1 Procesamiento, visión y control", st_h2))
    h.append(tabla(PROCESAMIENTO, ANCHOS))
    h.append(Paragraph("2.2 Alimentación", st_h2))
    h.append(KeepTogether([tabla(POTENCIA, ANCHOS)]))
    h.append(Paragraph("Batería + → fusible → interruptor → entradas de los dos reguladores. 6 V a los tres servos "
                       "y 5,1 V a la Pi por el GPIO. Todos los negativos se juntan en la barra de GND.", st_txt))
    h.append(KeepTogether([Paragraph("2.3 Buzzer y señales", st_h2), tabla(BUZZER, ANCHOS)]))
    doc.build(h, onFirstPage=pie, onLaterPages=pie)
    print("PDF en", SALIDA)


if __name__ == "__main__":
    main()
