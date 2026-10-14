"""Modelo mecánico de Keepon pro v3: cabeza plana y compacta con la Pi 5 adentro.

La Pi 5 va parada dentro de la cabeza, atornillada a la placa de roll, y la cámara en uno de los
ojos. Como la Pi y la cámara se mueven juntas, la cinta de 150 mm (15 → 22 pines) no se dobla ni se
tuerce con ningún movimiento del cuello: queda fija, con una sola curva en U.

Reutiliza de la v2 (../../keepon_v2_cad/fuente/keepon_cad.py) los servos, la caja base, la tapa,
los soportes de pitch y la horquilla: el cuello es el mismo.

    ~/cq_env/bin/python keepon_v3_cad.py           # escribe ../step, ../stl y ../vistas

Convenciones (mm): origen en el eje de yaw, a nivel del piso de la caja; +X adelante, +Y a la
izquierda del robot, +Z arriba. Ángulos del ensamble: pitch > 0 baja la nariz; roll > 0 gira la
cabeza hacia la derecha del robot (visto de frente, antihorario).
"""
from functools import lru_cache
from pathlib import Path
import math
import sys

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "keepon_v2_cad" / "fuente"))
import keepon_cad as v2   # noqa: E402
from keepon_cad import (V, caja, cil, cil_eje, unir, restar, rot, HOLGURA, M3, M3_ROSCA,  # noqa: E402
                        M25_ROSCA, M2_ROSCA, RDS3218, HS7955, MG996R, YAW, PITCH, ROLL,
                        servo_modelo, horn_modelo, horn_agujeros, Z_PLATO0, Z_PLATO1, Z_PITCH,
                        X_PITCH, X_PLACA0, X_PLACA1, Y_SOP_IZQ, Y_SOP_DER, ROD_R_AGUJ_SUP,
                        PASO_CABLES_R, PASO_CABLES_ANCHO, PASO_CABLES_ARCO)

# ============================================================================================
# PARÁMETROS
# ============================================================================================

# --- Plataforma de yaw: ya no lleva la Pi, así que es más chica que en la v2 (Ø180) ---------
PLATO_D = 146.0
PLATO_X_FRENTE = 52.0  # el plato se corta adelante (forma de D): ahí baja la cara con la nariz abajo
ESP_X0, ESP_Y0 = -55.0, -12.7  # esquina de la ESP32-C3 (48,3 × 25,4 mm), atrás y centrada
ESP_ALTURA = 12.0

# --- Raspberry Pi 5 (plano mecánico oficial: raspberry-pi-5-mechanical-drawing.pdf) --------
# Coordenadas de la placa: u a lo largo del lado largo, desde el extremo del USB-C (0 … 85);
# v desde el borde de los HDMI hacia el del GPIO (0 … 56); h altura sobre la cara de componentes.
PI_L, PI_A = 85.0, 56.0
PI_AGUJEROS_UV = [(u, v) for u in (3.5, 61.5) for v in (3.5, 52.5)]
# Conectores CAM/DISP: dos ranuras PERPENDICULARES al borde de los HDMI (u ≈ 48,5 y 54,3;
# v ≈ 1,2 … 16,6). La cinta sale a lo largo de u, con su ancho a lo largo de v.
PI_CSI_U = 48.5        # centro del conector usado (MEDIR: el más cercano a los HDMI)
PI_CSI_V = 8.9         # centro de la cinta a lo ancho
PI_CSI_SALIDA = "usbc" # hacia dónde sale la cinta del conector: "usbc" o "ethernet" (VERIFICAR en la Pi)
PI_SEP = 4.0           # separadores entre la placa de roll y la Pi (cara de abajo: pines del GPIO)
COOLER_H = 11.0        # Active Cooler: altura sobre la placa (MEDIR)

# --- Cámara: Camera Module 3 NoIR estándar (RSP-CAM-V3-NOIR), 25 × 24 mm ---------------------
CAM_LARGO = 11.5       # de la cara trasera de la placa a la punta de la lente
CAM_ABAJO, CAM_ARRIBA = 14.5, 9.5    # del centro de la lente a los bordes de abajo y de arriba
CAM_CONECTOR = 1.2     # la cinta entra al conector (en la cara trasera, abajo) a esta altura

# --- Cinta FFC (22 pines 0,5 mm → 15 pines 1 mm) ---------------------------------------------
FFC_LARGO = 150.0      # medido por el grupo (≈ 15 cm)
FFC_HOLGURA = 3.0      # largo que se deja de más, para no tirar de los conectores
FFC_INSERCION = 4.0    # largo que entra en cada conector
FFC_ANCHO = 16.0       # ancho del lado de la cámara (el lado de la Pi es más angosto)
FFC_R = 6.5            # radio de la curva en U (estática: la cinta no se mueve nunca)

# --- Cabeza ------------------------------------------------------------------------------------
Z_PI0 = -25.0          # extremo de abajo de la Pi respecto del eje de roll (más abajo choca al bajar la nariz)
PARED = 2.0            # paredes de la caja de la cabeza
CARA_T = 2.5           # espesor de la cara
PLACA_T = X_PLACA1 - X_PLACA0
CABEZA_R_ESQ = 10.0    # radio de las esquinas de la cara
OJO_D = 20.0           # los dos ojos: en el derecho del público (izquierdo del robot, +Y) va la cámara
LENTE_AGUJERO = 4.6    # radio del agujero para la lente
COSTILLA_D = 6.0       # costillas de las paredes donde se atornilla la caja a la placa (M2,5)

# --- Barrido que se verifica (config.yaml: pitch −20/+30, roll ±20) ---------------------------
# Se monta el pitch para que los 30° sean hacia ARRIBA (la persona está más alta que el robot).
PITCH_ABAJO, PITCH_ARRIBA = 22.0, 32.0
ROLL_MAX = 22.0

# ============================================================================================
# Cotas derivadas
# ============================================================================================
C = (X_PITCH, 0.0, Z_PITCH)            # cruce de los ejes de pitch y roll
X_PI0 = X_PLACA1 + PI_SEP              # cara trasera de la Pi
X_PI1 = X_PI0 + 1.6                    # cara de componentes


def pi_u_a_z(u):
    """Altura relativa al eje de roll. La Pi va parada con el extremo hacia el que sale la cinta
    abajo: así la cinta baja."""
    return Z_PI0 + (u if PI_CSI_SALIDA == "usbc" else PI_L - u)


def pi_v_a_y(v):
    """Borde de los HDMI a la izquierda del robot (+Y), GPIO a la derecha: la Pi queda centrada."""
    return PI_A / 2 - v


def caja_pi(u0, u1, v0, v1, h0, h1):
    za, zb = sorted((pi_u_a_z(u0), pi_u_a_z(u1)))
    ya, yb = sorted((pi_v_a_y(v0), pi_v_a_y(v1)))
    return caja(X_PI1 + h0, X_PI1 + h1, ya, yb, Z_PITCH + za, Z_PITCH + zb)


Y_CAM = pi_v_a_y(PI_CSI_V)             # la cámara queda alineada con la cinta: ningún doblez de costado
Z_PI_BAJO = pi_u_a_z(0 if PI_CSI_SALIDA == "usbc" else PI_L)
U_SALIDA = PI_CSI_U - 2.2 if PI_CSI_SALIDA == "usbc" else PI_CSI_U + 2.2
Z_SALIDA = pi_u_a_z(U_SALIDA)          # donde la cinta sale del conector, hacia abajo

# Recorrido de la cinta (plano XZ, en y = Y_CAM):
#   1) sale del conector a h = 1,5 y se separa a h = 4,5 (pasa por encima de los HDMI y el USB-C)
#   2) baja pegada a la Pi hasta debajo de su borde
#   3) curva en U hacia adelante (radio FFC_R)
#   4) sube por delante de la Pi y entra desde abajo al conector de la cámara
X_FFC1 = X_PI1 + 4.5
X_FFC3 = X_FFC1 + 2 * FFC_R
Z_FFC_U = Z_PI_BAJO - 1.5 - 0.5        # fin de los tramos rectos (el USB-C sobresale ~1 mm)
_largo_fijo = (math.hypot(3.0, 4.0) + (Z_SALIDA - 4.0 - Z_FFC_U) + math.pi * FFC_R
               - Z_FFC_U + 2 * FFC_INSERCION)
Z_CAM_BAJO = FFC_LARGO - FFC_HOLGURA - _largo_fijo     # el largo de la cinta ubica la cámara
X_CAM0 = X_FFC3 + CAM_CONECTOR         # cara trasera de la placa de la cámara
X_CARA1 = X_CAM0 + CAM_LARGO           # frente de la cara: la lente queda al ras
X_CARA0 = X_CARA1 - CARA_T
Z_LENTE = Z_CAM_BAJO + CAM_ABAJO

# Contorno de la cabeza (exterior), en el plano YZ
_z_arriba_int = max(Z_CAM_BAJO + CAM_ABAJO + CAM_ARRIBA, pi_u_a_z(PI_L + 3) if PI_CSI_SALIDA == "usbc"
                    else pi_u_a_z(-1)) + 1.5
_z_abajo_int = Z_FFC_U - FFC_R - 0.3 - 1.5
Z_CAB0, Z_CAB1 = _z_abajo_int - PARED, _z_arriba_int + PARED
Y_CAB = PI_A / 2 + 1.5 + COSTILLA_D + PARED      # semiancho: Pi + HDMI que sobresalen + costilla + pared
Y_COSTILLA = PI_A / 2 + 1.5 + COSTILLA_D / 2
Z_COSTILLAS = (Z_PI_BAJO + 10, Z_PI_BAJO + 62)
Z_OJOS = Z_LENTE

assert Z_LENTE + OJO_D / 2 < Z_CAB1 - 1, "el ojo no entra en la cara"


# ============================================================================================
# Piezas imprimibles nuevas
# ============================================================================================


def rect_redondeado_yz(y0, y1, z0, z1, x0, x1, r):
    w = (cq.Workplane("YZ").center((y0 + y1) / 2, (z0 + z1) / 2).rect(y1 - y0, z1 - z0)
         .extrude(x1 - x0).edges("|X").fillet(r))
    return w.val().translate(V(x0, 0, 0))


def plato_yaw():
    p = restar(cil(PLATO_D / 2, Z_PLATO0, Z_PLATO1),
               caja(PLATO_X_FRENTE, PLATO_D, -PLATO_D, PLATO_D, Z_PLATO0 - 1, Z_PLATO1 + 1))
    recortes = [YAW(h) for h in horn_agujeros(RDS3218, espesor=v2.PLATO_T + 1)]
    ranura = None
    for k in range(17):
        ang = math.radians(-PASO_CABLES_ARCO + 2 * PASO_CABLES_ARCO * k / 16)
        c = cil(PASO_CABLES_ANCHO / 2, Z_PLATO0 - 1, Z_PLATO1 + 1,
                PASO_CABLES_R * math.cos(ang), PASO_CABLES_R * math.sin(ang))
        ranura = c if ranura is None else ranura.fuse(c)
    recortes.append(ranura.clean())
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, ROD_R_AGUJ_SUP * math.cos(math.radians(30 + 60 * k)),
                     ROD_R_AGUJ_SUP * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    for y in (Y_SOP_IZQ - 7, Y_SOP_DER + 7):
        recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, X_PITCH + dx, y) for dx in (-7, 7)]
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, x, ESP_Y0 + 12.7) for x in (ESP_X0 - 7.5, ESP_X0 + 55.8)]
    recortes.append(cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, -5, -64))     # portabuzzer (el de la v2)
    return restar(p, *recortes)


def cuna_esp32():
    """La misma cuna de la v2, en la nueva posición (atrás del plato)."""
    L, A = 48.3, 25.4
    x0, y0 = ESP_X0, ESP_Y0
    zb = Z_PLATO1 + ESP_ALTURA
    base = caja(x0 - 11, x0 + L + 11, y0 + A / 2 - 6, y0 + A / 2 + 6, Z_PLATO1, Z_PLATO1 + 3)
    b1 = caja(x0 - 4, x0 + 3, y0 - 1, y0 + A + 1, Z_PLATO1, zb + 2)
    b2 = caja(x0 + L - 3, x0 + L + 4, y0 - 1, y0 + A + 1, Z_PLATO1, zb + 2)
    recortes = [caja(x0 - 0.3, x0 + 3.1, y0 - 0.3, y0 + A + 0.3, zb, zb + 3),
                caja(x0 + L - 3.1, x0 + L + 0.3, y0 - 0.3, y0 + A + 0.3, zb, zb + 3),
                caja(x0 - 5, x0 + 1, y0 + A / 2 - 6, y0 + A / 2 + 6, zb - 4, zb + 3)]
    recortes += [cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 4, x, y0 + A / 2) for x in (x0 - 7.5, x0 + L + 7.5)]
    return restar(unir(base, b1, b2), *recortes)


def pi_agujeros_yz():
    return [(pi_v_a_y(v), Z_PITCH + pi_u_a_z(u)) for u, v in PI_AGUJEROS_UV]


def costillas_yz():
    return [(sy * Y_COSTILLA, Z_PITCH + z) for sy in (-1, 1) for z in Z_COSTILLAS]


def placa_roll():
    """Placa atornillada al horn del MG996R: lleva la Pi (parada) y cierra la cabeza por atrás."""
    p = rect_redondeado_yz(-Y_CAB, Y_CAB, Z_PITCH + Z_CAB0, Z_PITCH + Z_CAB1, X_PLACA0, X_PLACA1, CABEZA_R_ESQ)
    # Separadores de la Pi
    p = unir(p, *[cil_eje(3.0, (X_PLACA1 - 0.5, y, z), (X_PI0, y, z)) for y, z in pi_agujeros_yz()])
    recortes = [ROLL(x) for x in horn_agujeros(MG996R, espesor=6)]
    recortes += [cil_eje(M25_ROSCA / 2, (X_PLACA0 + 1, y, z), (X_PI0 + 1, y, z)) for y, z in pi_agujeros_yz()]
    # Tornillos M2,5 de la caja (pasantes, cabeza del lado de atrás)
    recortes += [cil_eje(1.5, (X_PLACA0 - 1, y, z), (X_PLACA1 + 1, y, z)) for y, z in costillas_yz()]
    # Ventanas de ventilación detrás de la Pi, lejos del horn
    zc = Z_PITCH
    recortes += [caja(X_PLACA0 - 1, X_PLACA1 + 1, -16, 16, zc + 15, zc + Z_PI0 + 56),
                 caja(X_PLACA0 - 1, X_PLACA1 + 1, -16, 16, zc + Z_PI0 + 8, zc - 15)]
    return restar(p, *recortes)


def caja_cabeza():
    """Cara + paredes, abierta atrás. Se imprime apoyada sobre la cara, sin soportes."""
    z0, z1 = Z_PITCH + Z_CAB0, Z_PITCH + Z_CAB1
    ext = rect_redondeado_yz(-Y_CAB, Y_CAB, z0, z1, X_PLACA1, X_CARA1, CABEZA_R_ESQ)
    inte = rect_redondeado_yz(-Y_CAB + PARED, Y_CAB - PARED, z0 + PARED, z1 - PARED,
                              X_PLACA1 - 1, X_CARA0, CABEZA_R_ESQ - PARED)
    c = restar(ext, inte)
    # Costillas en las paredes laterales, de la placa a la cara (agujero para M2,5 autorroscante)
    cost = [restar(unir(cil_eje(COSTILLA_D / 2, (X_PLACA1, y, z), (X_CARA0 + 0.5, y, z)),
                        caja(X_PLACA1, X_CARA0 + 0.5, *sorted((y, math.copysign(Y_CAB - 0.5, y))),
                             z - COSTILLA_D / 2, z + COSTILLA_D / 2)),
                   cil_eje(M25_ROSCA / 2, (X_PLACA1 - 1, y, z), (X_PLACA1 + 12, y, z)))
            for y, z in costillas_yz()]
    # Separadores de la cámara (M2), desde la cara hacia atrás
    sep = [restar(cil_eje(2.5, (X_CAM0 + 1.0, y, z), (X_CARA0 + 0.5, y, z)),
                  cil_eje(M2_ROSCA / 2, (X_CAM0, y, z), (X_CARA0, y, z)))
           for y, z in camara_agujeros_yz()]
    c = unir(c, *cost, *sep)
    recortes = []
    for y in (Y_CAM, -Y_CAM):                                        # ojos
        recortes.append(cil_eje(OJO_D / 2, (X_CARA0 - 1, y, Z_PITCH + Z_OJOS), (X_CARA1 + 1, y, Z_PITCH + Z_OJOS)))
    # Arriba: los dos USB-A (para el cable de la ESP32; conviene uno acodado) y ranuras de ventilación
    ya, yb = sorted((pi_v_a_y(20), pi_v_a_y(56) - 0.5))
    recortes.append(caja(X_PI1 + 0.5, X_PI1 + 17, ya, yb, z1 - PARED - 1, z1 + 1))
    for y in (12, 20):
        recortes.append(caja(X_PI1 + 2, X_PI1 + 16, y - 2, y + 2, z1 - PARED - 1, z1 + 1))
    # Abajo: la U de la cinta queda a la vista para revisarla, y pasan los cables de la Pi
    recortes.append(caja(X_PI1 - 1, X_CARA0 - 2, -Y_CAB + PARED + 2, Y_CAB - PARED - 2, z0 - 1, z0 + PARED + 1))
    # Lateral del GPIO: acceso a los pines (alimentación por GPIO si hace falta)
    za, zb = sorted((Z_PITCH + pi_u_a_z(10), Z_PITCH + pi_u_a_z(58)))
    recortes.append(caja(X_PI1 + 2, X_PI1 + 12, -Y_CAB - 1, -Y_CAB + PARED + 1, za - 4, zb + 4))
    for r in recortes:
        c = c.cut(r)
    return c.clean()


def camara_agujeros_yz():
    """Agujeros de la Camera Module 3 (21 × 12,5 mm), a 2 mm del borde de arriba."""
    z_sup = Z_PITCH + Z_LENTE + CAM_ARRIBA - 2.0
    return [(Y_CAM + sy * 10.5, z) for sy in (-1, 1) for z in (z_sup, z_sup - 12.5)]


def ojo(lado):
    """Tapón negro para cada ojo, con un bisel de 1 mm por delante de la cara (se pega).
    El del lado de la cámara tiene el agujero de la lente, avellanado a 40° para no recortar la imagen."""
    y = Y_CAM * lado
    z = Z_PITCH + Z_OJOS
    tapon = cil_eje(OJO_D / 2 - 0.15, (X_CARA0, y, z), (X_CARA1, y, z))
    bisel = cil_eje(OJO_D / 2 + 2.5, (X_CARA1, y, z), (X_CARA1 + 1.0, y, z))
    o = unir(tapon, bisel)
    if lado > 0:
        o = o.cut(cil_eje(LENTE_AGUJERO, (X_CARA0 - 1, y, z), (X_CARA1 + 2, y, z)))
        o = o.cut(cq.Solid.makeCone(LENTE_AGUJERO, LENTE_AGUJERO + 1.6 * math.tan(math.radians(40)), 1.61,
                                    V(X_CARA1 - 0.6, y, z), V(1, 0, 0)))
    return o.clean()


# ============================================================================================
# Componentes comprados (solo para el ensamble)
# ============================================================================================


def pi5():
    pcb = restar(caja_pi(0, PI_L, 0, PI_A, -1.6, 0),
                 *[cil_eje(1.35, (X_PI0 - 1, y, z), (X_PI1 + 1, y, z)) for y, z in pi_agujeros_yz()])
    puertos = unir(caja_pi(64, 88, 2, 54, 0, 16),        # USB + Ethernet (sobresalen 3 mm)
                   caja_pi(6.8, 15.6, -1.0, 7.0, 0, 3.2),  # USB-C
                   caja_pi(22.1, 29.5, -1.2, 6.5, 0, 3.5),  # micro-HDMI 0
                   caja_pi(35.5, 42.9, -1.2, 6.5, 0, 3.5),  # micro-HDMI 1
                   caja_pi(7, 58, 49.5, 54.5, 0, 8.5))      # GPIO
    conectores = unir(caja_pi(PI_CSI_U - 2.2, PI_CSI_U + 2.2, 1.2, 16.6, 0, 1.8),
                      caja_pi(54.3 - 1.5, 54.3 + 1.5, 1.2, 16.6, 0, 1.8))
    cooler = caja_pi(14, 62, 18, 48, 0, COOLER_H)
    return pcb, puertos, conectores, cooler


def camara():
    x = X_CAM0
    y, z = Y_CAM, Z_PITCH + Z_LENTE
    pcb = caja(x, x + 1.0, y - 12.5, y + 12.5, z - CAM_ABAJO, z + CAM_ARRIBA)
    lente = unir(caja(x + 1, x + 5, y - 4.25, y + 4.25, z - 4.25, z + 4.25),
                 cil_eje(3.5, (x + 5, y, z), (x + CAM_LARGO, y, z)))
    conector = caja(x - 2.5, x, y - 10, y + 10, z - CAM_ABAJO, z - CAM_ABAJO + 5.5)
    return pcb, lente, conector


def ffc_puntos(paso=1.0):
    """Línea media de la cinta en el plano XZ (coordenadas absolutas). Devuelve (puntos, largo)."""
    z0 = Z_PITCH
    pts = []

    def recta(a, b):
        n = max(2, int(math.dist(a, b) / paso) + 1)
        for k in range(n):
            t = k / (n - 1)
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    a = (X_PI1 + 1.5, z0 + Z_SALIDA)
    b = (X_FFC1, z0 + Z_SALIDA - 4.0)
    c = (X_FFC1, z0 + Z_FFC_U)
    recta(a, b)
    recta(b, c)
    xc = X_FFC1 + FFC_R
    for k in range(1, 40):
        t = math.pi * k / 40
        pts.append((xc - FFC_R * math.cos(t), z0 + Z_FFC_U - FFC_R * math.sin(t)))
    recta((X_FFC3, z0 + Z_FFC_U), (X_FFC3, z0 + Z_CAM_BAJO))
    largo = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) + 2 * FFC_INSERCION
    return pts, largo


def ffc():
    pts, _ = ffc_puntos()
    e = 0.15
    ida, vuelta = [], []
    for i, p in enumerate(pts):
        q = pts[min(i + 1, len(pts) - 1)] if i < len(pts) - 1 else p
        o = pts[i - 1] if i > 0 else p
        dx, dz = (q[0] - o[0]), (q[1] - o[1])
        n = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / n, dx / n
        ida.append((p[0] + nx * e, p[1] + nz * e))
        vuelta.append((p[0] - nx * e, p[1] - nz * e))
    plano = cq.Plane(origin=(0, Y_CAM, 0), xDir=(1, 0, 0), normal=(0, -1, 0))
    return cq.Workplane(plano).polyline(ida + vuelta[::-1]).close().extrude(FFC_ANCHO / 2, both=True).val()


# ============================================================================================
# Ensamble, interferencias y exportación
# ============================================================================================
COLOR_IMPRESO = cq.Color(0.95, 0.75, 0.10)
COLOR_TAPA = cq.Color(0.85, 0.65, 0.10)
GRIS = cq.Color(0.7, 0.7, 0.72)


def ensamble(yaw=0.0, pitch=0.0, roll=0.0, con_base=True):
    piezas = []

    def add(nombre, forma, color, impresa=False, grupo="base"):
        piezas.append([nombre, forma, color, impresa, grupo])

    if con_base:
        add("caja_base", v2.caja_base(), COLOR_IMPRESO, True)
        add("tapa_base", v2.tapa_base(), COLOR_TAPA, True)
        bat, r6, r5, llave = v2.base_componentes()
        add("bateria_lipo_3s", bat, cq.Color(0.55, 0.57, 0.62))
        add("regulador_6v_20a", r6, cq.Color(0.15, 0.35, 0.75))
        add("regulador_5v_5a", r5, cq.Color(0.1, 0.1, 0.1))
        add("interruptor", llave, cq.Color(0.8, 0.1, 0.1))
        add("rodamiento_yaw", v2.rodamiento(), GRIS)
    add("servo_yaw_rds3218", YAW(servo_modelo(RDS3218)), cq.Color(0.12, 0.12, 0.12))

    add("horn_yaw", YAW(horn_modelo(RDS3218)), GRIS, grupo="yaw")
    add("plato_yaw", plato_yaw(), COLOR_IMPRESO, True, "yaw")
    x0, y0, zb = ESP_X0, ESP_Y0, Z_PLATO1 + ESP_ALTURA
    add("esp32c3", unir(caja(x0, x0 + 48.3, y0, y0 + 25.4, zb, zb + 1.6),
                        caja(x0 + 30, x0 + 46, y0 + 6, y0 + 19.4, zb + 1.6, zb + 4)),
        cq.Color(0.1, 0.1, 0.12), grupo="yaw")
    add("cuna_esp32", cuna_esp32(), COLOR_IMPRESO, True, "yaw")
    add("porta_buzzer", v2.porta_buzzer(), COLOR_IMPRESO, True, "yaw")
    add("buzzer", cil(6.0, Z_PLATO1 + 1, Z_PLATO1 + 10.5, -5, -46), cq.Color(0.1, 0.1, 0.1), grupo="yaw")
    add("soporte_pitch_izq", v2.soporte_pitch_izq(), COLOR_IMPRESO, True, "yaw")
    add("soporte_pitch_der", v2.soporte_pitch_der(), COLOR_IMPRESO, True, "yaw")
    add("servo_pitch_hs7955tg", PITCH(servo_modelo(HS7955)), cq.Color(0.08, 0.08, 0.08), grupo="yaw")

    add("horn_pitch", PITCH(horn_modelo(HS7955)), GRIS, grupo="pitch")
    add("horquilla_cabeza", v2.horquilla_cabeza(), COLOR_IMPRESO, True, "pitch")
    add("servo_roll_mg996r", ROLL(servo_modelo(MG996R)), cq.Color(0.15, 0.25, 0.6), grupo="pitch")

    add("horn_roll", ROLL(horn_modelo(MG996R)), GRIS, grupo="roll")
    add("placa_roll", placa_roll(), COLOR_IMPRESO, True, "roll")
    pcb, puertos, conectores, cooler = pi5()
    add("pi5_pcb", pcb, cq.Color(0.05, 0.45, 0.2), grupo="roll")
    add("pi5_puertos", puertos, cq.Color(0.75, 0.75, 0.78), grupo="roll")
    add("pi5_conectores_csi", conectores, cq.Color(0.9, 0.9, 0.9), grupo="roll")
    add("pi5_active_cooler", cooler, cq.Color(0.2, 0.2, 0.22), grupo="roll")
    cpcb, lente, cconector = camara()
    add("camara_pcb", cpcb, cq.Color(0.05, 0.05, 0.05), grupo="roll")
    add("camara_lente", lente, cq.Color(0.15, 0.15, 0.15), grupo="roll")
    add("camara_conector", cconector, cq.Color(0.9, 0.9, 0.9), grupo="roll")
    add("cinta_ffc", ffc(), cq.Color(0.85, 0.5, 0.15), grupo="roll")
    add("caja_cabeza", caja_cabeza(), COLOR_IMPRESO, True, "roll")
    add("ojo_camara", ojo(1), cq.Color(0.05, 0.05, 0.05), True, "roll")
    add("ojo_otro", ojo(-1), cq.Color(0.05, 0.05, 0.05), True, "roll")

    orden = {"base": 0, "yaw": 1, "pitch": 2, "roll": 3}
    for p in piezas:
        n = orden[p[4]]
        if n >= 3:
            p[1] = rot(p[1], (0, 0, Z_PITCH), (1, 0, 0), roll)
        if n >= 2:
            p[1] = rot(p[1], (X_PITCH, 0, Z_PITCH), (0, 1, 0), pitch)
        if n >= 1:
            p[1] = rot(p[1], (0, 0, 0), (0, 0, 1), yaw)
    return piezas


# Contactos a propósito: horn sobre el eje, cinta dentro de sus conectores, tapón de la lente
IGNORAR = {("servo_yaw_rds3218", "horn_yaw"), ("servo_pitch_hs7955tg", "horn_pitch"),
           ("servo_roll_mg996r", "horn_roll"), ("pi5_conectores_csi", "cinta_ffc"),
           ("cinta_ffc", "camara_conector"), ("camara_lente", "ojo_camara")}


def interferencias(piezas, solo_entre_grupos=False, tol=1.0):
    res = []
    for i in range(len(piezas)):
        for j in range(i + 1, len(piezas)):
            a, b = piezas[i], piezas[j]
            if (a[0], b[0]) in IGNORAR or (b[0], a[0]) in IGNORAR:
                continue
            if solo_entre_grupos and a[4] == b[4]:
                continue
            ba, bb = a[1].BoundingBox(), b[1].BoundingBox()
            if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
                    or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                continue
            if v > tol:
                res.append((a[0], b[0], round(v, 1)))
    return res


def verificar():
    """Interferencias en la pose 0 (todas) y en los extremos del barrido (solo entre grupos)."""
    problemas = {}
    p0 = ensamble(con_base=True)
    problemas[(0, 0)] = interferencias(p0)
    for pitch in (-PITCH_ARRIBA, -PITCH_ARRIBA / 2, PITCH_ABAJO / 2, PITCH_ABAJO):
        for roll in (-ROLL_MAX, 0.0, ROLL_MAX):
            problemas[(pitch, roll)] = interferencias(ensamble(pitch=pitch, roll=roll), solo_entre_grupos=True)
    for roll in (-ROLL_MAX, ROLL_MAX):
        problemas[(0.0, roll)] = interferencias(ensamble(roll=roll), solo_entre_grupos=True)
    return problemas


def holgura_minima(paso=2.0):
    """Distancia mínima entre lo que gira con la cabeza (pitch + roll) y lo fijo al plato."""
    fijos = [p for p in ensamble() if p[4] in ("base", "yaw")]
    res = []
    for pitch in (-PITCH_ARRIBA, PITCH_ABAJO):
        for roll in (-ROLL_MAX, ROLL_MAX):
            ps = ensamble(pitch=pitch, roll=roll)
            mov = [p for p in ps if p[4] in ("pitch", "roll")]
            d = min((a[1].distance(b[1]), a[0], b[0]) for a in mov for b in fijos
                    if (a[0], b[0]) not in IGNORAR and (b[0], a[0]) not in IGNORAR
                    and a[1].BoundingBox().zmin < b[1].BoundingBox().zmax + 30)
            res.append((pitch, roll, round(d[0], 1), d[1], d[2]))
    return res


def exportar(raiz: Path):
    (raiz / "step").mkdir(parents=True, exist_ok=True)
    (raiz / "stl").mkdir(parents=True, exist_ok=True)
    piezas = ensamble()
    asm = cq.Assembly(name="keepon_v3")
    for nombre, forma, color, impresa, _ in piezas:
        asm.add(forma, name=nombre, color=color)
        if impresa:
            cq.exporters.export(forma, str(raiz / "step" / f"{nombre}.step"))
            cq.exporters.export(forma, str(raiz / "stl" / f"{nombre}.stl"), tolerance=0.05, angularTolerance=0.2)
    asm.save(str(raiz / "step" / "keepon_v3_ensamble.step"))
    return piezas


def resumen():
    _, largo = ffc_puntos()
    return {
        "cabeza (ancho × alto × fondo) [mm]": (round(2 * Y_CAB, 1), round(Z_CAB1 - Z_CAB0, 1),
                                               round(X_CARA1 - X_PLACA0, 1)),
        "cabeza respecto del eje de roll [mm]": (round(Z_CAB0, 1), round(Z_CAB1, 1)),
        "altura total [mm]": round(Z_PITCH + Z_CAB1, 1),
        "lente (y, z rel. eje de roll) [mm]": (round(Y_CAM, 1), round(Z_LENTE, 1)),
        "cinta: largo del recorrido + inserciones [mm]": round(largo, 1),
        "cinta: radio mínimo [mm]": FFC_R,
        "frente de la cara delante del eje de pitch [mm]": round(X_CARA1 - X_PITCH, 1),
    }


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    for k, v in resumen().items():
        print(f"{k}: {v}")
    piezas = exportar(raiz)
    for nombre, forma, _, impresa, _ in piezas:
        if impresa:
            bb = forma.BoundingBox()
            print(f"  {nombre:20s} {bb.xlen:6.1f} × {bb.ylen:6.1f} × {bb.zlen:6.1f} mm, {forma.Volume() / 1000:6.1f} cm³")
    if "--verificar" in sys.argv:
        for pose, lista in verificar().items():
            print("pose (pitch, roll)", pose, "OK" if not lista else lista)
        for fila in holgura_minima():
            print("holgura mínima", fila)
