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
                        servo_modelo, Z_PLATO0, Z_PLATO1, Z_PITCH,
                        X_PITCH, X_PLACA0, X_PLACA1, Y_SOP_IZQ, Y_SOP_DER, M4,
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
OJO_D = 20.0           # los dos ojos (decorativos)
OJO_Y = 22.0           # separación de cada ojo al centro de la cara
OJO_SOBRE_NARIZ = 15.0 # los ojos van esta altura por encima de la lente
NARIZ_D = 14.0         # la nariz es la cámara: tapón con el agujero de la lente, en el centro de la cara
LENTE_AGUJERO = 4.6    # radio del agujero para la lente
COSTILLA_D = 6.0       # costillas de las paredes donde se atornilla la caja a la placa (M2,5)

# --- Brazo de los servos -----------------------------------------------------------------------
# Brazo doble de plástico (docs/Fotos/brazo_servo.jpeg): el mismo en los tres servos, en lugar del horn
# circular de la v2. Medido: largo de punta a punta y paso de los agujeros (≈ 2,5; en la foto da ≈ 3).
# El resto se estimó de la foto con la escala de los 38 mm: MEDIR.
BRAZO_L = 38.0         # de punta a punta (medido)
BRAZO_CUBO_D = 9.0     # anillo del cubo central (MEDIR)
BRAZO_ANCHO = (6.5, 4.0)   # ancho junto al cubo y en la punta (MEDIR)
BRAZO_T = 2.5          # espesor de los brazos (MEDIR)
BRAZO_AGUJEROS = (7.0, 10.0, 13.0, 16.0)   # radios de los agujeros de cada brazo (MEDIR)
# Las piezas que van sobre el brazo no tienen agujeros fijos sino una ranura a cada lado del eje:
# el tornillo M2 autorroscante pasa por la ranura y entra en el agujero del brazo que quede debajo,
# sea cual sea el paso real. Cubre los agujeros entre estos radios:
RANURA_R = (5.5, 14.5)
RANURA_ANCHO = 2.4     # pasante para M2
CUBO_ALIVIO = (10.5, 1.0)  # rebaje en la pieza por si el cubo sobresale del brazo (diámetro, profundidad)

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


Y_FFC = pi_v_a_y(PI_CSI_V)             # la cinta sale del conector de la Pi corrida 19 mm al costado
Y_CAM = 0.0                            # la cámara (la nariz) va en el centro de la cara
Z_PI_BAJO = pi_u_a_z(0 if PI_CSI_SALIDA == "usbc" else PI_L)
U_SALIDA = PI_CSI_U - 2.2 if PI_CSI_SALIDA == "usbc" else PI_CSI_U + 2.2
Z_SALIDA = pi_u_a_z(U_SALIDA)          # donde la cinta sale del conector, hacia abajo

# Recorrido de la cinta (plano XZ, en y = Y_FFC hasta el doblez):
#   1) sale del conector a h = 1,5 y se separa a h = 4,5 (pasa por encima de los HDMI y el USB-C)
#   2) baja pegada a la Pi hasta debajo de su borde
#   3) curva en U hacia adelante (radio FFC_R)
#   4) sube por delante de la Pi hasta el doblez en Z: dos pliegues a 45° la corren al centro (y = 0)
#   5) sigue subiendo y entra desde abajo al conector de la cámara
# Los pliegues se hacen una vez al armar y la cinta queda quieta. El tramo horizontal del doblez
# gasta |Y_FFC| de cinta: por eso la cámara queda más abajo que si subiera derecha.
X_FFC1 = X_PI1 + 4.5
X_FFC3 = X_FFC1 + 2 * FFC_R
Z_FFC_U = Z_PI_BAJO - 1.5 - 0.5        # fin de los tramos rectos (el USB-C sobresale ~1 mm)
_largo_fijo = (math.hypot(3.0, 4.0) + (Z_SALIDA - 4.0 - Z_FFC_U) + math.pi * FFC_R
               - Z_FFC_U + 2 * FFC_INSERCION)
DOBLEZ_Y = abs(Y_FFC - Y_CAM)          # corrimiento del doblez en Z (línea media)
Z_CAM_BAJO = FFC_LARGO - FFC_HOLGURA - _largo_fijo - DOBLEZ_Y   # el largo de la cinta ubica la cámara
Z_DOBLEZ = (Z_FFC_U + Z_CAM_BAJO) / 2  # altura de la línea media del tramo horizontal del doblez
assert Z_DOBLEZ - FFC_ANCHO / 2 > Z_FFC_U + 2 and Z_DOBLEZ + FFC_ANCHO / 2 < Z_CAM_BAJO - 2, \
    "no hay lugar para el doblez en Z"
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
Z_OJOS = Z_LENTE + OJO_SOBRE_NARIZ

assert Z_OJOS + OJO_D / 2 + 2.5 < Z_CAB1 - 1, "el ojo no entra en la cara"
# Los agujeros de los ojos no pueden cortar los separadores de la cámara (r = 2,5)
assert math.hypot(OJO_Y - 10.5, Z_OJOS - (Z_LENTE + CAM_ARRIBA - 2.0)) > OJO_D / 2 + 3.0, \
    "los ojos chocan con los separadores de la cámara"


# ============================================================================================
# Piezas imprimibles nuevas
# ============================================================================================


def brazo_modelo(s):
    """Brazo doble en el sistema local del servo: a lo largo de x local, con la cara de arriba en S + 1
    (donde apoya la pieza, igual que el horn circular de la v2)."""
    z1 = s.S + 1.0
    z0 = z1 - BRAZO_T
    w0, w1 = BRAZO_ANCHO
    xp = BRAZO_L / 2 - w1 / 2          # centro de la punta redondeada
    perfil = (cq.Workplane("XY").polyline([(-xp, -w1 / 2), (0, -w0 / 2), (xp, -w1 / 2), (xp, w1 / 2), (0, w0 / 2),
                                           (-xp, w1 / 2)]).close().extrude(BRAZO_T).val().translate(V(0, 0, z0)))
    puntas = [cil(w1 / 2, z0, z1, sx * xp, 0) for sx in (-1, 1)]
    cubo = cil(BRAZO_CUBO_D / 2, s.H - s.Fb + 0.5, z1)
    b = unir(perfil, *puntas, cubo)
    agujeros = [cil(0.75, z0 - 1, z1 + 1, sx * r, 0) for sx in (-1, 1) for r in BRAZO_AGUJEROS]
    return restar(b, cil(1.3, z1 - 3, z1 + 1), *agujeros)


def brazo_agujeros(s, espesor=10.0):
    """Recortes de la pieza que se atornilla al brazo: una ranura a cada lado (a lo largo de x local),
    el acceso al tornillo central y un rebaje para el cubo."""
    z0 = s.S + 1.0 - 0.5
    r0, r1 = RANURA_R
    a = RANURA_ANCHO / 2
    rec = []
    for sx in (-1, 1):
        rec.append(caja(min(sx * r0, sx * r1), max(sx * r0, sx * r1), -a, a, z0, z0 + espesor))
        rec += [cil(a, z0, z0 + espesor, sx * r, 0) for r in (r0, r1)]
    rec.append(cil(3.5, z0, z0 + espesor))
    rec.append(cil(CUBO_ALIVIO[0] / 2, z0, s.S + 1.0 + CUBO_ALIVIO[1]))
    return rec


def horquilla_cabeza():
    """La horquilla de la v2 con las ranuras para el brazo del HS-7955TG en lugar de los agujeros del horn."""
    t = v2.HORQ_T
    xa, xb = X_PITCH - 12, v2.X_FRENTE_HORQ + t
    za, zb = Z_PITCH - 42, Z_PITCH + 18
    yl = v2.Y_HORQ
    izq = caja(xa, xb, yl, yl + t, za, Z_PITCH + 16)
    der = caja(xa, xb, -yl - t, -yl, za, Z_PITCH + 16)
    frente = caja(v2.X_FRENTE_HORQ, xb, yl, -yl, za, zb)
    piso = caja(xa, xb, yl, -yl, za, za + t)
    h = unir(izq, der, frente, piso)
    recortes = [ROLL(v2.servo_ventana(MG996R))] + [ROLL(x) for x in v2.servo_agujeros(MG996R, -1, t + 1)]
    recortes += [PITCH(x) for x in brazo_agujeros(HS7955, espesor=t + 1)]
    recortes.append(cil_eje(M4 / 2, (X_PITCH, -yl - t - 1, Z_PITCH), (X_PITCH, -yl + 1, Z_PITCH)))
    recortes.append(caja(xa + 6, v2.X_FRENTE_HORQ - 4, -12, 12, za - 1, za + t + 1))   # paso de cables
    return restar(h, *recortes)


def rect_redondeado_yz(y0, y1, z0, z1, x0, x1, r):
    w = (cq.Workplane("YZ").center((y0 + y1) / 2, (z0 + z1) / 2).rect(y1 - y0, z1 - z0)
         .extrude(x1 - x0).edges("|X").fillet(r))
    return w.val().translate(V(x0, 0, 0))


def plato_yaw():
    p = restar(cil(PLATO_D / 2, Z_PLATO0, Z_PLATO1),
               caja(PLATO_X_FRENTE, PLATO_D, -PLATO_D, PLATO_D, Z_PLATO0 - 1, Z_PLATO1 + 1))
    recortes = [YAW(h) for h in brazo_agujeros(RDS3218, espesor=v2.PLATO_T + 1)]
    ranura = None
    for k in range(17):
        ang = math.radians(-PASO_CABLES_ARCO + 2 * PASO_CABLES_ARCO * k / 16)
        c = cil(PASO_CABLES_ANCHO / 2, Z_PLATO0 - 1, Z_PLATO1 + 1,
                PASO_CABLES_R * math.cos(ang), PASO_CABLES_R * math.sin(ang))
        ranura = c if ranura is None else ranura.fuse(c)
    recortes.append(ranura.clean())
    for y in (Y_SOP_IZQ - 7, Y_SOP_DER + 7):
        recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, X_PITCH + dx, y) for dx in (-7, 7)]
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, x, ESP_Y0 + 12.7) for x in (ESP_X0 - 7.5, ESP_X0 + 55.8)]
    recortes.append(cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, -5, -64))     # portabuzzer (el de la v2)
    return restar(p, *recortes)


def tapa_base():
    """La tapa de la v2 sin el rodamiento (no lo tenemos): sin el aro elevador ni sus 6 agujeros.
    El plato queda apoyado solo en el horn del yaw, 14 mm por encima de la tapa."""
    t = caja(-v2.CAJA_X / 2, v2.CAJA_X / 2, -v2.CAJA_Y / 2, v2.CAJA_Y / 2, v2.Z_TAPA0, v2.Z_TAPA1)
    recortes = [YAW(v2.servo_ventana(RDS3218))] + [YAW(h) for h in v2.servo_agujeros(RDS3218, -1, v2.TAPA_T + 1)]
    # Paso de cables fijo (los cables suben desde la caja y entran a la ranura del plato)
    recortes.append(cil(PASO_CABLES_ANCHO / 2, v2.Z_TAPA0 - 1, v2.Z_TAPA1 + 1, PASO_CABLES_R, 0))
    ex, ey = v2.CAJA_X / 2 - 8, v2.CAJA_Y / 2 - 8
    recortes += [cil(M3 / 2, v2.Z_TAPA0 - 1, v2.Z_TAPA1 + 1, sx * ex, sy * ey) for sx in (-1, 1) for sy in (-1, 1)]
    return restar(t, *recortes)


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
    recortes = [ROLL(x) for x in brazo_agujeros(MG996R, espesor=6)]
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
    for y in (OJO_Y, -OJO_Y):                                        # ojos
        recortes.append(cil_eje(OJO_D / 2, (X_CARA0 - 1, y, Z_PITCH + Z_OJOS), (X_CARA1 + 1, y, Z_PITCH + Z_OJOS)))
    zl = Z_PITCH + Z_LENTE                                           # nariz = cámara
    recortes.append(cil_eje(NARIZ_D / 2, (X_CARA0 - 1, Y_CAM, zl), (X_CARA1 + 1, Y_CAM, zl)))
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


def tapon(y, z, d, lente=False):
    """Tapón negro para un agujero de la cara, con un bisel de 1 mm por delante (se pega).
    El de la nariz tiene el agujero de la lente, avellanado a 40° para no recortar la imagen."""
    t = cil_eje(d / 2 - 0.15, (X_CARA0, y, z), (X_CARA1, y, z))
    bisel = cil_eje(d / 2 + 2.5, (X_CARA1, y, z), (X_CARA1 + 1.0, y, z))
    o = unir(t, bisel)
    if lente:
        o = o.cut(cil_eje(LENTE_AGUJERO, (X_CARA0 - 1, y, z), (X_CARA1 + 2, y, z)))
        o = o.cut(cq.Solid.makeCone(LENTE_AGUJERO, LENTE_AGUJERO + 1.6 * math.tan(math.radians(40)), 1.61,
                                    V(X_CARA1 - 0.6, y, z), V(1, 0, 0)))
    return o.clean()


def ojo(lado):
    """lado = +1: ojo izquierdo del robot (+Y); −1: derecho."""
    return tapon(OJO_Y * lado, Z_PITCH + Z_OJOS, OJO_D)


def nariz():
    return tapon(Y_CAM, Z_PITCH + Z_LENTE, NARIZ_D, lente=True)


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
    """Línea media de la cinta hasta el doblez en Z, en el plano XZ (coordenadas absolutas).
    Devuelve (puntos, largo total de la cinta, contando el doblez, el tramo final y las inserciones)."""
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
    recta((X_FFC3, z0 + Z_FFC_U), (X_FFC3, z0 + Z_DOBLEZ))
    largo = (sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) + DOBLEZ_Y
             + (Z_CAM_BAJO - Z_DOBLEZ) + 2 * FFC_INSERCION)
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
    plano = cq.Plane(origin=(0, Y_FFC, 0), xDir=(1, 0, 0), normal=(0, -1, 0))
    tramo1 = cq.Workplane(plano).polyline(ida + vuelta[::-1]).close().extrude(FFC_ANCHO / 2, both=True).val()
    # Doblez en Z (simplificado): el tramo 1 llega hasta arriba del pliegue, el tramo horizontal queda
    # por delante (la cinta da vuelta en cada pliegue) y el tramo 2 sube desde el centro hasta la cámara.
    w, zd = FFC_ANCHO / 2, Z_PITCH + Z_DOBLEZ
    y0, y1 = sorted((Y_CAM, Y_FFC))
    tramo1 = unir(tramo1, caja(X_FFC3 - e, X_FFC3 + e, Y_FFC - w, Y_FFC + w, zd, zd + w))
    horizontal = caja(X_FFC3 + e, X_FFC3 + 3 * e, y0 - w, y1 + w, zd - w, zd + w)
    tramo2 = caja(X_FFC3 - e, X_FFC3 + e, Y_CAM - w, Y_CAM + w, zd - w, Z_PITCH + Z_CAM_BAJO + FFC_INSERCION)
    return unir(tramo1, horizontal, tramo2)


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
        add("tapa_base", tapa_base(), COLOR_TAPA, True)
        bat, r6, r5, llave = v2.base_componentes()
        add("bateria_lipo_3s", bat, cq.Color(0.55, 0.57, 0.62))
        add("regulador_6v_20a", r6, cq.Color(0.15, 0.35, 0.75))
        add("regulador_5v_5a", r5, cq.Color(0.1, 0.1, 0.1))
        add("interruptor", llave, cq.Color(0.8, 0.1, 0.1))
    add("servo_yaw_rds3218", YAW(servo_modelo(RDS3218)), cq.Color(0.12, 0.12, 0.12))

    add("horn_yaw", YAW(brazo_modelo(RDS3218)), GRIS, grupo="yaw")
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

    add("horn_pitch", PITCH(brazo_modelo(HS7955)), GRIS, grupo="pitch")
    add("horquilla_cabeza", horquilla_cabeza(), COLOR_IMPRESO, True, "pitch")
    add("servo_roll_mg996r", ROLL(servo_modelo(MG996R)), cq.Color(0.15, 0.25, 0.6), grupo="pitch")

    add("horn_roll", ROLL(brazo_modelo(MG996R)), GRIS, grupo="roll")
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
    add("nariz_camara", nariz(), cq.Color(0.05, 0.05, 0.05), True, "roll")
    add("ojo_izq", ojo(1), cq.Color(0.05, 0.05, 0.05), True, "roll")
    add("ojo_der", ojo(-1), cq.Color(0.05, 0.05, 0.05), True, "roll")

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
           ("cinta_ffc", "camara_conector"), ("camara_lente", "nariz_camara")}


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


# ============================================================================================
# Relaciones de posición para SolidWorks
# ============================================================================================
# El STEP no guarda relaciones de posición: solo la posición de cada pieza. Por eso se genera una
# macro (solidworks/keepon_v3_relaciones.bas) que las agrega al ensamble importado:
#   - Cada grupo rígido tiene una pieza de referencia. Las demás piezas del grupo se le pegan con
#     tres planos coincidentes (Alzado, Planta y Vista lateral): todas las piezas se exportan con el
#     mismo origen (el del robot), así que sus planos coinciden.
#   - Entre grupos, una bisagra por eje: una relación concéntrica entre dos caras cilíndricas que
#     están sobre el eje, más un plano coincidente perpendicular al eje (traba el desplazamiento).
# La caja base queda fija. Resultado: el ensamble se mueve solo en yaw, pitch y roll.
REFERENCIA = {"base": "caja_base", "yaw": "plato_yaw", "pitch": "horquilla_cabeza", "roll": "placa_roll"}

# (eje, pieza móvil y radio de su cilindro, pieza fija y radio, punto del eje, dirección,
#  plano perpendicular: pieza móvil, pieza fija). Radios y puntos en mm.
BISAGRAS = [
    ("yaw", ("plato_yaw", 3.5), ("servo_yaw_rds3218", 3.0), (0.0, 0.0, 0.0), (0, 0, 1),
     ("plato_yaw", "caja_base")),                       # agujero central del plato ↔ eje del RDS3218
    ("pitch", ("horquilla_cabeza", M4 / 2), ("soporte_pitch_der", M4 / 2), (X_PITCH, 0.0, Z_PITCH), (0, 1, 0),
     ("horquilla_cabeza", "plato_yaw")),                # pivote M4 de la horquilla ↔ el del soporte
    ("roll", ("horn_roll", BRAZO_CUBO_D / 2), ("servo_roll_mg996r", 3.0), (0.0, 0.0, Z_PITCH), (1, 0, 0),
     ("placa_roll", "horquilla_cabeza")),               # cubo del brazo del MG996R ↔ su eje
]


def tiene_cilindro(forma, r, p, e, tol_r=0.02, tol_eje=0.1):
    """¿La pieza tiene una cara cilíndrica de radio r cuyo eje pasa por p con dirección e?
    Es la misma búsqueda que hace la macro: así se sabe antes de abrir SolidWorks que la encuentra."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    for f in forma.Faces():
        if f.geomType() != "CYLINDER":
            continue
        cy = BRepAdaptor_Surface(f.wrapped).Cylinder()
        if abs(cy.Radius() - r) > tol_r:
            continue
        d, o = cy.Axis().Direction(), cy.Axis().Location()
        if abs(d.X() * e[0] + d.Y() * e[1] + d.Z() * e[2]) < 0.9999:
            continue
        v = (p[0] - o.X(), p[1] - o.Y(), p[2] - o.Z())
        t = v[0] * d.X() + v[1] * d.Y() + v[2] * d.Z()
        if v[0] ** 2 + v[1] ** 2 + v[2] ** 2 - t * t < tol_eje ** 2:
            return True
    return False


def verificar_relaciones(piezas):
    """Devuelve la lista de problemas (vacía si la macro va a encontrar todo)."""
    formas = {p[0]: p[1] for p in piezas}
    grupos = {p[0]: p[4] for p in piezas}
    problemas = [n for n in REFERENCIA.values() if n not in formas]
    for eje, (pm, rm), (pf, rf), punto, d, (qm, qf) in BISAGRAS:
        for n, r in ((pm, rm), (pf, rf)):
            if n not in formas or not tiene_cilindro(formas[n], r, punto, d):
                problemas.append(f"bisagra {eje}: no hay un cilindro de r = {r} mm sobre el eje en {n}")
        if grupos.get(qm) == grupos.get(qf):
            problemas.append(f"bisagra {eje}: {qm} y {qf} están en el mismo grupo")
    return problemas


def macro_solidworks(piezas):
    """Texto de la macro VBA (módulo .bas) que crea las relaciones de posición."""
    fijas = [p[0] for p in piezas if p[0] != REFERENCIA["base"]]
    rigidas = [(p[0], REFERENCIA[p[4]]) for p in piezas if p[0] != REFERENCIA[p[4]]]
    L = [
        'Attribute VB_Name = "KeeponRelaciones"',
        "' Relaciones de posición del ensamble Keepon pro v3.",
        "' GENERADO por fuente/keepon_v3_cad.py: no editar a mano (se sobreescribe).",
        "'",
        "' Uso (ver README.md): abrir step/keepon_v3_ensamble.step en SolidWorks, guardarlo como",
        "' ensamble (.SLDASM) sin mover nada, y ejecutar main.",
        "'   - Cada grupo rígido (base, yaw, pitch, roll) se arma con planos coincidentes contra su",
        "'     pieza de referencia: todas las piezas tienen el mismo origen, el del robot.",
        "'   - Entre grupos, una bisagra por eje: concéntrica entre dos cilindros que están sobre el",
        "'     eje + plano coincidente perpendicular al eje.",
        "' Los planos y las caras se buscan por tipo y por geometría, no por nombre: anda igual con",
        "' SolidWorks en español o en inglés.",
        "Option Explicit",
        "",
        "Const TOL_RADIO As Double = 0.00002   ' 0,02 mm (SolidWorks trabaja en metros)",
        "Const TOL_EJE As Double = 0.0001      ' 0,1 mm",
        "",
        "Dim swApp As SldWorks.SldWorks",
        "Dim swModel As SldWorks.ModelDoc2",
        "Dim swAssy As SldWorks.AssemblyDoc",
        "Dim errores As String",
        "Dim nRel As Long",
        "Dim listadas As Boolean",
        "",
        "Sub main()",
        "    Set swApp = Application.SldWorks",
        "    Set swModel = swApp.ActiveDoc",
        "    If swModel Is Nothing Then",
        '        MsgBox "Abrir primero el ensamble (keepon_v3_ensamble.step)."',
        "        Exit Sub",
        "    End If",
        "    If swModel.GetType <> swDocASSEMBLY Then",
        '        MsgBox "El documento activo no es un ensamble."',
        "        Exit Sub",
        "    End If",
        "    Set swAssy = swModel",
        '    errores = ""',
        "    nRel = 0",
        "    listadas = False",
        "",
        "    ' 1) La caja base queda fija; lo demás se libera para que lo ubiquen las relaciones",
        f'    Fijar "{REFERENCIA["base"]}", True',
    ]
    L += [f'    Fijar "{n}", False' for n in fijas]
    L += ["", "    ' 2) Grupos rígidos: tres planos coincidentes con la pieza de referencia del grupo"]
    L += [f'    Rigida "{n}", "{ref}"' for n, ref in rigidas]
    L += ["", "    ' 3) Bisagras: yaw (eje Z), pitch (eje Y) y roll (eje X)"]
    for eje, (pm, rm), (pf, rf), (px, py, pz), (ex, ey, ez), (qm, qf) in BISAGRAS:
        L.append(f'    Bisagra "{eje}", "{pm}", {rm:.4f}, "{pf}", {rf:.4f}, {px:.4f}, {py:.4f}, {pz:.4f}, '
                 f'{ex}, {ey}, {ez}, "{qm}", "{qf}"')
    L += [
        "",
        "    swModel.ClearSelection2 True",
        "    swModel.EditRebuild3",
        '    If errores = "" Then',
        '        MsgBox nRel & " relaciones de posición creadas. El robot se mueve en yaw, pitch y roll."',
        "    Else",
        '        MsgBox nRel & " relaciones creadas. Problemas:" & vbCrLf & errores',
        "    End If",
        "End Sub",
        "",
        "' Busca un componente por nombre: acepta 'plato_yaw-1' o 'algo/plato_yaw-1'.",
        "Function Pieza(nombre As String) As SldWorks.Component2",
        "    Dim v As Variant, i As Long, c As SldWorks.Component2, n As String, p As Long",
        "    v = swAssy.GetComponents(False)",
        "    If IsEmpty(v) Then Exit Function",
        "    For i = 0 To UBound(v)",
        "        Set c = v(i)",
        "        n = c.Name2",
        '        p = InStrRev(n, "/")',
        "        If p > 0 Then n = Mid(n, p + 1)",
        '        p = InStrRev(n, "-")',
        "        If p > 0 And IsNumeric(Mid(n, p + 1)) Then n = Left(n, p - 1)",
        "        If n = nombre Then",
        "            Set Pieza = c",
        "            Exit Function",
        "        End If",
        "    Next i",
        "    ' Segunda pasada: SolidWorks a veces les agrega un prefijo al importar ('ensamble - caja_base-1').",
        "    ' Se acepta el nombre dentro del de la pieza si no está pegado a otra palabra (buzzer no es porta_buzzer).",
        "    For i = 0 To UBound(v)",
        "        Set c = v(i)",
        "        n = c.Name2",
        "        p = InStr(n, nombre)",
        "        Do While p > 0",
        "            If Borde(n, p - 1) And Borde(n, p + Len(nombre)) Then",
        "                Set Pieza = c",
        "                Exit Function",
        "            End If",
        "            p = InStr(p + 1, n, nombre)",
        "        Loop",
        "    Next i",
        '    errores = errores & "No se encontró la pieza " & nombre & vbCrLf',
        "    If Not listadas Then",
        "        listadas = True",
        '        errores = errores & "  (nombres que tiene el ensamble: "',
        "        For i = 0 To UBound(v)",
        "            If i < 8 Then",
        '                Set c = v(i): errores = errores & c.Name2 & ", "',
        "            End If",
        "        Next i",
        '        errores = errores & "...)" & vbCrLf',
        "    End If",
        "End Function",
        "",
        "' ¿El carácter k de n es un borde de palabra (o está fuera del texto)?",
        "Function Borde(n As String, k As Long) As Boolean",
        "    Dim ch As String",
        "    If k < 1 Or k > Len(n) Then",
        "        Borde = True",
        "    Else",
        "        ch = Mid(n, k, 1)",
        '        Borde = Not (ch Like "[A-Za-z0-9_]")',
        "    End If",
        "End Function",
        "",
        "Sub Fijar(nombre As String, fija As Boolean)",
        "    Dim c As SldWorks.Component2",
        "    Set c = Pieza(nombre)",
        "    If c Is Nothing Then Exit Sub",
        "    swModel.ClearSelection2 True",
        "    c.Select4 False, Nothing, False",
        "    If fija Then",
        "        swAssy.FixComponent",
        "    Else",
        "        swAssy.UnfixComponent",
        "    End If",
        "End Sub",
        "",
        "' k-ésimo plano de referencia del componente: 1 = Alzado (XY), 2 = Planta (XZ), 3 = Vista lateral (YZ).",
        "Function Plano(c As SldWorks.Component2, k As Long) As SldWorks.Feature",
        "    Dim f As SldWorks.Feature, i As Long",
        "    Set f = c.FirstFeature",
        "    Do While Not f Is Nothing",
        '        If f.GetTypeName2 = "RefPlane" Then',
        "            i = i + 1",
        "            If i = k Then",
        "                Set Plano = f",
        "                Exit Function",
        "            End If",
        "        End If",
        "        Set f = f.GetNextFeature",
        "    Loop",
        "End Function",
        "",
        "' Índice del plano de referencia perpendicular a la dirección (ex, ey, ez).",
        "Function PlanoNormal(c As SldWorks.Component2, ex As Double, ey As Double, ez As Double) As Long",
        "    Dim k As Long, f As SldWorks.Feature, rp As SldWorks.RefPlane, d As Variant",
        "    For k = 1 To 3",
        "        Set f = Plano(c, k)",
        "        If Not f Is Nothing Then",
        "            Set rp = f.GetSpecificFeature2",
        "            d = rp.Transform.ArrayData   ' (6-8): normal del plano",
        "            If Abs(d(6) * ex + d(7) * ey + d(8) * ez) > 0.99 Then",
        "                PlanoNormal = k",
        "                Exit Function",
        "            End If",
        "        End If",
        "    Next k",
        "    ' Si no se pudo leer: el orden estándar de los planos",
        "    If ez <> 0 Then",
        "        PlanoNormal = 1",
        "    ElseIf ey <> 0 Then",
        "        PlanoNormal = 2",
        "    Else",
        "        PlanoNormal = 3",
        "    End If",
        "End Function",
        "",
        "' Cara cilíndrica de radio r (mm) cuyo eje pasa por (px, py, pz) (mm) con dirección (ex, ey, ez).",
        "Function Cilindro(c As SldWorks.Component2, r As Double, px As Double, py As Double, pz As Double, _",
        "                  ex As Double, ey As Double, ez As Double) As SldWorks.Face2",
        "    Dim cuerpos As Variant, info As Variant, i As Long, b As SldWorks.Body2",
        "    Dim f As SldWorks.Face2, s As SldWorks.Surface, p As Variant",
        "    Dim n As Double, ax As Double, ay As Double, az As Double",
        "    Dim dx As Double, dy As Double, dz As Double, t As Double",
        "    cuerpos = c.GetBodies3(swSolidBody, info)",
        "    If IsEmpty(cuerpos) Then Exit Function",
        "    For i = 0 To UBound(cuerpos)",
        "        Set b = cuerpos(i)",
        "        Set f = b.GetFirstFace",
        "        Do While Not f Is Nothing",
        "            Set s = f.GetSurface",
        "            If s.IsCylinder Then",
        "                p = s.CylinderParams   ' origen (0-2), eje (3-5), radio (6), en metros",
        "                If Abs(p(6) - r / 1000#) < TOL_RADIO Then",
        "                    n = Sqr(p(3) ^ 2 + p(4) ^ 2 + p(5) ^ 2)",
        "                    ax = p(3) / n: ay = p(4) / n: az = p(5) / n",
        "                    If Abs(ax * ex + ay * ey + az * ez) > 0.9999 Then",
        "                        dx = px / 1000# - p(0): dy = py / 1000# - p(1): dz = pz / 1000# - p(2)",
        "                        t = dx * ax + dy * ay + dz * az",
        "                        If dx ^ 2 + dy ^ 2 + dz ^ 2 - t ^ 2 < TOL_EJE ^ 2 Then",
        "                            Set Cilindro = f",
        "                            Exit Function",
        "                        End If",
        "                    End If",
        "                End If",
        "            End If",
        "            Set f = f.GetNextFace",
        "        Loop",
        "    Next i",
        "End Function",
        "",
        "Function SelPlano(c As SldWorks.Component2, k As Long) As Boolean",
        "    Dim f As SldWorks.Feature",
        "    Set f = Plano(c, k)",
        "    If f Is Nothing Then Exit Function",
        "    SelPlano = f.Select2(True, 1)",
        "End Function",
        "",
        "Function SelCara(f As SldWorks.Face2) As Boolean",
        "    Dim e As SldWorks.Entity, sd As SldWorks.SelectData",
        "    Set sd = swModel.SelectionManager.CreateSelectData",
        "    sd.Mark = 1",
        "    Set e = f",
        "    SelCara = e.Select4(True, sd)",
        "End Function",
        "",
        "' Crea la relación con lo que está seleccionado y le pone nombre.",
        "Sub Relacion(tipo As Long, nombre As String)",
        "    Dim est As Long, m As SldWorks.Mate2, f As SldWorks.Feature",
        "    Set m = swAssy.AddMate5(tipo, swMateAlignCLOSEST, False, 0, 0, 0, 1, 1, 0, 0, 0, False, False, 0, est)",
        "    If m Is Nothing Then",
        '        errores = errores & nombre & " (error " & est & ")" & vbCrLf',
        "    Else",
        "        Set f = m",
        "        f.Name = nombre",
        "        nRel = nRel + 1",
        "    End If",
        "    swModel.ClearSelection2 True",
        "End Sub",
        "",
        "Sub Rigida(nombre As String, ref As String)",
        "    Dim a As SldWorks.Component2, b As SldWorks.Component2, k As Long, ok As Boolean",
        "    Dim planos As Variant",
        '    planos = Array("", "XY", "XZ", "YZ")',
        "    Set a = Pieza(nombre)",
        "    Set b = Pieza(ref)",
        "    If a Is Nothing Or b Is Nothing Then Exit Sub",
        "    For k = 1 To 3",
        "        swModel.ClearSelection2 True",
        "        ok = SelPlano(a, k)",
        "        ok = SelPlano(b, k) And ok",
        "        If ok Then",
        '            Relacion swMateCOINCIDENT, nombre & " = " & ref & " (" & planos(k) & ")"',
        "        Else",
        '            errores = errores & "No se pudieron seleccionar los planos de " & nombre & vbCrLf',
        "        End If",
        "    Next k",
        "End Sub",
        "",
        "Sub Bisagra(eje As String, movil As String, rMovil As Double, fija As String, rFija As Double, _",
        "            px As Double, py As Double, pz As Double, ex As Double, ey As Double, ez As Double, _",
        "            planoMovil As String, planoFija As String)",
        "    Dim cm As SldWorks.Component2, cf As SldWorks.Component2, fm As SldWorks.Face2, ff As SldWorks.Face2",
        "    Dim qm As SldWorks.Component2, qf As SldWorks.Component2, k As Long, ok As Boolean",
        "    Set cm = Pieza(movil)",
        "    Set cf = Pieza(fija)",
        "    Set qm = Pieza(planoMovil)",
        "    Set qf = Pieza(planoFija)",
        "    If cm Is Nothing Or cf Is Nothing Or qm Is Nothing Or qf Is Nothing Then Exit Sub",
        "    ' Eje: concéntrica entre los dos cilindros",
        "    Set fm = Cilindro(cm, rMovil, px, py, pz, ex, ey, ez)",
        "    Set ff = Cilindro(cf, rFija, px, py, pz, ex, ey, ez)",
        "    If fm Is Nothing Or ff Is Nothing Then",
        '        errores = errores & "Bisagra " & eje & ": no se encontraron las caras del eje" & vbCrLf',
        "    Else",
        "        swModel.ClearSelection2 True",
        "        ok = SelCara(fm)",
        "        ok = SelCara(ff) And ok",
        '        If ok Then Relacion swMateCONCENTRIC, "Bisagra " & eje & ": eje (" & movil & " - " & fija & ")"',
        "    End If",
        "    ' Plano perpendicular al eje: traba el deslizamiento a lo largo del eje",
        "    k = PlanoNormal(qm, ex, ey, ez)",
        "    swModel.ClearSelection2 True",
        "    ok = SelPlano(qm, k)",
        "    ok = SelPlano(qf, k) And ok",
        '    If ok Then Relacion swMateCOINCIDENT, "Bisagra " & eje & ": plano (" & planoMovil & " - " & planoFija & ")"',
        "End Sub",
    ]
    return "\r\n".join(L) + "\r\n"


def carga_yaw():
    """Peso y momento de vuelco sobre el eje del RDS3218, que ahora carga todo (no hay rodamiento).
    Impreso: PLA a 1,24 g/cm³ con ~50 % de relleno efectivo. Comprados: masas aproximadas."""
    masas = {"servo_pitch_hs7955tg": 65, "servo_roll_mg996r": 55, "esp32c3": 6, "buzzer": 3, "camara_pcb": 4,
             "pi5_pcb": 46, "pi5_active_cooler": 24, "horn_yaw": 3, "horn_pitch": 3, "horn_roll": 3}
    peor = None
    for pitch in (-PITCH_ARRIBA, 0.0, PITCH_ABAJO):
        for roll in (-ROLL_MAX, 0.0, ROLL_MAX):
            m_tot, mx, my = 0.0, 0.0, 0.0
            for n, forma, _, impresa, grupo in ensamble(pitch=pitch, roll=roll, con_base=False):
                if grupo == "base":
                    continue
                m = forma.Volume() / 1000 * 1.24 * 0.5 if impresa else masas.get(n, 0.0)
                c = forma.Center()
                m_tot += m
                mx, my = mx + m * c.x, my + m * c.y
            r = math.hypot(mx, my) / m_tot          # distancia horizontal del centro de masa al eje [mm]
            fila = (pitch, roll, round(m_tot), round(r, 1), round(m_tot * r / 10000, 2))
            if peor is None or fila[4] > peor[4]:
                peor = fila
    return peor   # (pitch, roll, masa [g], brazo [mm], momento [kgf·cm])


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
    problemas = verificar_relaciones(piezas)
    if problemas:
        raise SystemExit("relaciones de posición: " + "; ".join(problemas))
    (raiz / "solidworks").mkdir(exist_ok=True)
    # cp1252: el editor de VBA de SolidWorks no lee UTF-8 (los acentos saldrían mal)
    macro = macro_solidworks(piezas)
    (raiz / "solidworks" / "keepon_v3_relaciones.bas").write_bytes(macro.encode("cp1252"))
    # La misma macro sin la línea "Attribute": para pegarla en el editor de VBA (pegada, esa línea da error)
    (raiz / "solidworks" / "keepon_v3_relaciones_PEGAR.txt").write_bytes(
        macro.split("\r\n", 1)[1].encode("cp1252"))
    print("macro de relaciones de posición: solidworks/keepon_v3_relaciones.bas")
    if "--verificar" in sys.argv:
        pitch, roll, m, r, mom = carga_yaw()
        print(f"carga sobre el eje del yaw (peor pose: pitch {pitch}, roll {roll}): {m} g, "
              f"centro de masa a {r} mm del eje → {mom} kgf·cm de vuelco")
        for pose, lista in verificar().items():
            print("pose (pitch, roll)", pose, "OK" if not lista else lista)
        for fila in holgura_minima():
            print("holgura mínima", fila)
