"""Modelo mecánico de Keepon pro v2: la Pi 5 y la ESP32-C3 van sobre la plataforma de yaw.

Genera las piezas imprimibles y el ensamble en STEP (para SolidWorks) y STL (para el slicer).

    python keepon_cad.py            # escribe ../step, ../stl y ../vistas

Convenciones (unidades en mm):
  - Origen en el eje de yaw, a nivel del piso de la caja base.
  - +X hacia adelante (hacia la persona), +Y a la izquierda del robot, +Z hacia arriba.
  - Cada servo tiene un sistema local: el eje de salida es +z local, el origen está sobre el eje,
    a la altura de la cara superior de la brida (la cara que se atornilla). +x local corre a lo
    largo del cuerpo, desde el eje hacia el otro extremo.

Las medidas de los servos y de las placas son nominales (hojas de datos y medidas típicas):
**verificarlas con calibre** antes de imprimir. Todo lo que hay que medir está en PARÁMETROS.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import math

import cadquery as cq
from OCP.gp import gp_Trsf

# ============================================================================================
# PARÁMETROS
# ============================================================================================


@dataclass
class Servo:
    nombre: str
    L: float        # largo del cuerpo (sin la brida)
    W: float        # ancho del cuerpo
    H: float        # alto del cuerpo, de la base a la tapa (sin el eje estriado)
    Fb: float       # altura de la cara superior de la brida medida desde la base
    a: float        # distancia del eje de salida al extremo más cercano del cuerpo
    Lf: float       # largo total de la brida
    tf: float       # espesor de la brida
    hs: float       # separación de los agujeros de la brida a lo largo del cuerpo
    hw: float       # separación de los agujeros a lo ancho
    S: float        # altura de la punta del eje estriado sobre la cara superior de la brida
    horn_d: float = 24.0   # diámetro del horn circular
    horn_r: float = 8.0    # radio del círculo de agujeros del horn que se usa para atornillar
    color: str = "gray15"


# Medidas nominales. Verificar con calibre (sobre todo Fb, S y a, que cambian entre fabricantes).
RDS3218 = Servo("RDS3218", L=40.0, W=20.0, H=40.5, Fb=28.5, a=10.0, Lf=54.5, tf=2.5, hs=49.5, hw=10.0, S=17.0)
HS7955 = Servo("HS-7955TG", L=40.0, W=20.0, H=37.0, Fb=27.0, a=10.0, Lf=54.0, tf=2.5, hs=48.0, hw=10.0, S=15.0,
               horn_d=23.0, color="gray10")
MG996R = Servo("MG996R", L=40.7, W=19.7, H=42.9, Fb=30.0, a=10.0, Lf=54.0, tf=2.5, hs=49.5, hw=10.0, S=16.0,
               color="royalblue4")

HOLGURA = 0.4          # juego entre pieza impresa y componente, por lado
M3 = 3.4               # agujero pasante M3
M3_ROSCA = 2.6         # agujero para tornillo autorroscante M3 / inserto
M25_ROSCA = 2.2        # agujero para tornillo M2,5 autorroscante (soportes de la Pi)
M2_ROSCA = 1.8         # agujero para tornillo M2 (cámara)
M4 = 4.3               # pivote del pitch

# --- Caja base -------------------------------------------------------------------------------
CAJA_X, CAJA_Y, CAJA_Z = 200.0, 190.0, 70.0   # exterior, sin la tapa
PARED, PISO = 3.0, 3.0
TAPA_T = 4.0

# Batería LiPo 3S 8000 mAh: MEDIR la de ustedes (las de 8000 mAh rondan 165 × 50 × 37 mm, ~550 g).
BATERIA = (50.0, 166.0, 37.0)                  # (x, y, z)
BATERIA_X0 = 36.0                              # adelante, a lo largo del eje Y
REG6 = (50.0, 65.0, 25.0)                      # regulador 12→6 V, 20 A (módulo con disipador)
REG5 = (32.0, 55.0, 15.0)                      # regulador 12→5,1 V, 5 A, USB-C

# --- Rodamiento de yaw ("lazy susan" redondo / rodamiento de sección delgada) -----------------
ROD_DI, ROD_DE, ROD_H = 80.0, 100.0, 8.0       # diámetro interior, exterior, alto total
ROD_R_AGUJ_INF, ROD_R_AGUJ_SUP = 46.0, 42.0    # radios de los agujeros (adaptar al rodamiento real)

# --- Plataforma giratoria --------------------------------------------------------------------
PLATO_D, PLATO_T = 180.0, 4.0
PASO_CABLES_R, PASO_CABLES_ANCHO, PASO_CABLES_ARCO = 26.0, 12.0, 75.0   # ranura en arco, ±75°

# --- Cabeza ------------------------------------------------------------------------------------
X_PITCH = 20.0         # posición del eje de pitch (adelante del eje de yaw)
H_PITCH = 65.0         # altura del eje de pitch sobre la plataforma (más alto = abertura del cuello más chica)
SOPORTE_T = 5.0        # espesor de los laterales del soporte de pitch
HORQ_T = 4.0           # espesor de las paredes de la horquilla de la cabeza
PLACA_CABEZA = 64.0    # lado de la placa de la cabeza (cuadrada, esquinas redondeadas)
CAM_LARGO = 11.5       # Camera Module 3: de la cara trasera de la placa a la punta de la lente

# --- Carcasa estilo Keepon ----------------------------------------------------------------------
# La cabeza es una esfera centrada en el cruce de los ejes de pitch y roll: al moverse ocupa siempre
# el mismo lugar, y solo hay que abrirle abajo el paso de las piezas fijas al plato (se calcula
# muestreando todas las poses: ver contorno_abertura).
CABEZA_R = 82.5        # radio exterior de la cabeza (Ø165)
CARCASA_T = 2.5        # espesor de pared de la cabeza y del cuerpo
CUERPO_A = 100.0       # semieje horizontal del cuerpo (elipsoide, Ø200)
CUERPO_C = 80.0        # semieje vertical del cuerpo
CUERPO_ZC = 110.0      # altura del centro del cuerpo
OJO_D = 12.0           # diámetro de los ojos
OJO_AZ, OJO_EL = 20.0, 14.0    # posición de los ojos: ángulo a cada lado y hacia arriba [°]
PITCH_BARRIDO = 32     # rango que se le despeja a la cabeza [°] (config.yaml pide −20/+30)
ROLL_BARRIDO = 22      # (config.yaml pide ±20)
MARGEN_BARRIDO = 2.0   # holgura alrededor de las piezas fijas

# --- Electrónica sobre la plataforma ---------------------------------------------------------
PI_X1 = -16.0          # borde delantero de la Pi (el de USB-C, HDMI y conectores de cámara)
PI_ALTURA = 6.0        # separadores impresos debajo de la Pi
ESP_X0, ESP_Y0 = -26.0, 56.0   # esquina de la ESP32-C3 (48,3 × 25,4 mm)
ESP_ALTURA = 12.0      # los pines de la ESP32 cuelgan ~8,5 mm

# ============================================================================================
# Utilidades
# ============================================================================================
V = cq.Vector


def caja(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cil(r, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def cil_eje(r, p0, p1):
    """Cilindro entre dos puntos."""
    p0, p1 = V(*p0), V(*p1)
    return cq.Solid.makeCylinder(r, (p1 - p0).Length, p0, (p1 - p0).normalized())


def unir(*s):
    s = [x for x in s if x is not None]
    r = s[0]
    for x in s[1:]:
        r = r.fuse(x)
    return r.clean()


def restar(base, *s):
    return base.cut(*s).clean()


@dataclass
class Montaje:
    """Ubica el sistema local de un servo en el mundo."""
    P: tuple   # punto del eje a la altura de la cara superior de la brida
    d: tuple   # dirección del eje de salida (z local)
    u: tuple   # dirección del cuerpo (x local)

    def trsf(self):
        d, u = V(*self.d).normalized(), V(*self.u).normalized()
        w = d.cross(u)  # y local = z × x
        P = self.P
        t = gp_Trsf()
        t.SetValues(u.x, w.x, d.x, P[0], u.y, w.y, d.y, P[1], u.z, w.z, d.z, P[2])
        return t

    def __call__(self, forma):
        return forma.moved(cq.Location(self.trsf()))


# ============================================================================================
# Servos: modelo visual y recortes para las piezas
# ============================================================================================


def servo_modelo(s: Servo):
    xc = s.L / 2 - s.a
    cuerpo = caja(-s.a, s.L - s.a, -s.W / 2, s.W / 2, -s.Fb, s.H - s.Fb)
    brida = caja(xc - s.Lf / 2, xc + s.Lf / 2, -s.W / 2, s.W / 2, -s.tf, 0)
    agujeros = [cil(2.2, -s.tf - 1, 1, xc + sx * s.hs / 2, sy * s.hw / 2) for sx in (-1, 1) for sy in (-1, 1)]
    brida = restar(brida, *agujeros)
    eje = cil(3.0, s.H - s.Fb, s.S)
    return unir(cuerpo, brida, eje)


def horn_modelo(s: Servo):
    disco = cil(s.horn_d / 2, s.S - 1.5, s.S + 1.0)
    cubo = cil(4.5, s.H - s.Fb + 0.5, s.S - 1.5)
    return unir(disco, cubo)


def servo_ventana(s: Servo, z0=-1.0, z1=None):
    """Hueco para que el cuerpo atraviese una placa. Por defecto la placa está sobre la brida (z > 0)."""
    h = HOLGURA
    return caja(-s.a - h, s.L - s.a + h, -s.W / 2 - h, s.W / 2 + h, z0, s.H - s.Fb + 1 if z1 is None else z1)


def servo_agujeros(s: Servo, z0=-1.0, z1=12.0, d=M3):
    xc = s.L / 2 - s.a
    return [cil(d / 2, z0, z1, xc + sx * s.hs / 2, sy * s.hw / 2) for sx in (-1, 1) for sy in (-1, 1)]


def horn_agujeros(s: Servo, espesor=10.0):
    """Agujeros para atornillar una pieza apoyada sobre el horn (4 a 90° + uno central)."""
    z0 = s.S + 1.0 - 0.5
    r = [cil(M2_ROSCA / 2 + 0.3, z0, z0 + espesor,
             s.horn_r * math.cos(math.radians(45 + 90 * k)), s.horn_r * math.sin(math.radians(45 + 90 * k)))
         for k in range(4)]
    r.append(cil(3.5, z0, z0 + espesor))   # acceso al tornillo central del horn
    return r


# ============================================================================================
# Cotas derivadas (no tocar: salen de los parámetros)
# ============================================================================================
Z_TAPA0 = CAJA_Z                     # cara inferior de la tapa: ahí se atornilla la brida del yaw
Z_TAPA1 = CAJA_Z + TAPA_T
YAW = Montaje(P=(0, 0, Z_TAPA0), d=(0, 0, 1), u=(-1, 0, 0))
Z_PLATO0 = Z_TAPA0 + RDS3218.S + 1.0           # el plato se apoya sobre el horn de yaw
Z_PLATO1 = Z_PLATO0 + PLATO_T
Z_ROD0 = Z_PLATO0 - ROD_H                      # el rodamiento llena el resto
ALZA_ROD = Z_ROD0 - Z_TAPA1                    # aro elevador del rodamiento sobre la tapa
assert ALZA_ROD >= 0, "el rodamiento es más alto que el espacio entre la tapa y el horn"

Z_PITCH = Z_PLATO1 + H_PITCH
Y_SOP_IZQ = -48.0                              # cara exterior del lateral izquierdo
Y_BRIDA_HS = Y_SOP_IZQ + SOPORTE_T + HS7955.tf # cara superior de la brida del HS, que apoya su cara de abajo
                                               # en la cara interior del soporte: el cuerpo sale hacia afuera
                                               # (sobresale 5 mm menos que del otro lado)
PITCH = Montaje(P=(X_PITCH, Y_BRIDA_HS, Z_PITCH), d=(0, 1, 0), u=(0, 0, -1))
Y_HORQ = Y_BRIDA_HS + HS7955.S + 1.0           # cara exterior izquierda de la horquilla (sobre el horn)
HORQ_ANCHO = -2 * Y_HORQ                       # la horquilla queda centrada en el eje de yaw
Y_SOP_DER = -Y_HORQ + 2.0                      # cara interior del lateral derecho (2 mm para arandelas)

X_FRENTE_HORQ = X_PITCH + 20.0                 # cara trasera de la pared frontal de la horquilla
ROLL = Montaje(P=(X_FRENTE_HORQ, 0, Z_PITCH), d=(1, 0, 0), u=(0, 0, -1))
X_PLACA0 = X_FRENTE_HORQ + MG996R.S + 1.0      # la placa de la cabeza se apoya en el horn de roll
X_PLACA1 = X_PLACA0 + 4.0
# Separadores M2 entre la placa de la cabeza y la cámara: la lente queda al ras de la carcasa
CAM_SEPARADOR = X_PITCH + CABEZA_R - CAM_LARGO - X_PLACA1

# Pi 5: 85 × 56 mm. Lado largo a lo largo de Y, puertos USB/Ethernet hacia +Y (hacia la ESP32).
PI_X0 = PI_X1 - 56.0
PI_Y0 = -42.5
Z_PI = Z_PLATO1 + PI_ALTURA
PI_AGUJEROS = [(PI_X1 - yb, PI_Y0 + xb) for xb in (3.5, 61.5) for yb in (3.5, 52.5)]

# ============================================================================================
# Piezas imprimibles
# ============================================================================================


def caja_base():
    ext = caja(-CAJA_X / 2, CAJA_X / 2, -CAJA_Y / 2, CAJA_Y / 2, 0, CAJA_Z)
    inte = caja(-CAJA_X / 2 + PARED, CAJA_X / 2 - PARED, -CAJA_Y / 2 + PARED, CAJA_Y / 2 - PARED, PISO, CAJA_Z + 1)
    c = restar(ext, inte)
    # Columnas en las esquinas para los tornillos de la tapa
    ex, ey = CAJA_X / 2 - 8, CAJA_Y / 2 - 8
    for sx in (-1, 1):
        for sy in (-1, 1):
            # cilindro unido a la esquina por un cuadrado hacia las paredes
            col = unir(cil(5.0, PISO, CAJA_Z, sx * ex, sy * ey),
                       caja(min(sx * ex, sx * (ex + 6)), max(sx * ex, sx * (ex + 6)),
                            min(sy * ey, sy * (ey + 6)), max(sy * ey, sy * (ey + 6)), PISO, CAJA_Z))
            col = restar(col, cil(M3_ROSCA / 2, CAJA_Z - 16, CAJA_Z + 1, sx * ex, sy * ey))
            c = unir(c, col)
    # Pared trasera: interruptor de balancín (corte estándar 19,2 × 12,8 mm)
    c = restar(c, caja(-CAJA_X / 2 - 1, -CAJA_X / 2 + PARED + 1, -9.6, 9.6, 34, 46.8))
    # Lateral +Y: ranura para sacar el XT60 y el balanceador al cargar
    c = restar(c, caja(BATERIA_X0 + 5, BATERIA_X0 + 35, CAJA_Y / 2 - PARED - 1, CAJA_Y / 2 + 1, 46, 58))
    # Ventilación de los reguladores (laterales, a la altura de los módulos)
    for k in range(6):
        x = -88 + k * 7
        c = restar(c, caja(x, x + 3, -CAJA_Y / 2 - 1, -CAJA_Y / 2 + PARED + 1, 15, 45))
        c = restar(c, caja(x, x + 3, CAJA_Y / 2 - PARED - 1, CAJA_Y / 2 + 1, 15, 45))
    # Ranuras para la cinta de velcro de la batería
    for y in (-45, 45):
        c = restar(c, caja(BATERIA_X0 - 6, BATERIA_X0 - 3, y - 10, y + 10, -1, PISO + 1))
        c = restar(c, caja(BATERIA_X0 + BATERIA[0] + 1, BATERIA_X0 + BATERIA[0] + 4, y - 10, y + 10, -1, PISO + 1))
    return c


def tapa_base():
    t = caja(-CAJA_X / 2, CAJA_X / 2, -CAJA_Y / 2, CAJA_Y / 2, Z_TAPA0, Z_TAPA1)
    if ALZA_ROD > 0:
        t = unir(t, restar(cil(ROD_DE / 2, Z_TAPA1, Z_ROD0), cil(ROD_DI / 2, Z_TAPA1 - 1, Z_ROD0 + 1)))
    recortes = [YAW(servo_ventana(RDS3218))] + [YAW(h) for h in servo_agujeros(RDS3218, -1, TAPA_T + 1)]
    # Paso de cables fijo (los cables suben desde la caja y entran a la ranura del plato)
    recortes.append(cil(PASO_CABLES_ANCHO / 2, Z_TAPA0 - 1, Z_ROD0 + 1, PASO_CABLES_R, 0))
    ex, ey = CAJA_X / 2 - 8, CAJA_Y / 2 - 8
    recortes += [cil(M3 / 2, Z_TAPA0 - 1, Z_TAPA1 + 1, sx * ex, sy * ey) for sx in (-1, 1) for sy in (-1, 1)]
    recortes += [cil(M3 / 2, Z_TAPA0 - 1, Z_ROD0 + 1, ROD_R_AGUJ_INF * math.cos(math.radians(60 * k)),
                     ROD_R_AGUJ_INF * math.sin(math.radians(60 * k))) for k in range(6)]
    return restar(t, *recortes)


def plato_yaw():
    p = cil(PLATO_D / 2, Z_PLATO0, Z_PLATO1)
    # Separadores de la Pi
    for x, y in PI_AGUJEROS:
        p = unir(p, cil(3.0, Z_PLATO1 - 0.5, Z_PI, x, y))
    recortes = [YAW(h) for h in horn_agujeros(RDS3218, espesor=PLATO_T + 1)]
    recortes += [cil(M25_ROSCA / 2, Z_PLATO1 - 3, Z_PI + 1, x, y) for x, y in PI_AGUJEROS]
    # Ranura en arco para los cables: sigue cubriendo el paso fijo de la tapa en todo el rango de yaw
    ranura = None
    pasos = 16
    for k in range(pasos + 1):
        ang = math.radians(-PASO_CABLES_ARCO + 2 * PASO_CABLES_ARCO * k / pasos)
        c = cil(PASO_CABLES_ANCHO / 2, Z_PLATO0 - 1, Z_PLATO1 + 1,
                PASO_CABLES_R * math.cos(ang), PASO_CABLES_R * math.sin(ang))
        ranura = c if ranura is None else ranura.fuse(c)
    recortes.append(ranura.clean())
    # Agujeros al aro superior del rodamiento
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, ROD_R_AGUJ_SUP * math.cos(math.radians(30 + 60 * k)),
                     ROD_R_AGUJ_SUP * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    # Soportes de pitch (2 por lado) y cuna de la ESP32 (2)
    for y in (Y_SOP_IZQ - 7, Y_SOP_DER + 7):
        recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, X_PITCH + dx, y) for dx in (-7, 7)]
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, x, ESP_Y0 + 12.7) for x in (ESP_X0 - 7.5, ESP_X0 + 55.8)]
    # Portabuzzer
    recortes.append(cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, -5, -64))
    # Orejas de la carcasa del cuerpo
    recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, x, y) for x, y in OREJAS_CUERPO]
    return restar(p, *recortes)


def soporte_pitch_izq():
    """Lateral izquierdo: lleva el HS-7955TG atravesado, con la brida del lado de adentro."""
    x0, x1 = X_PITCH - 14, X_PITCH + 14
    y_in = Y_SOP_IZQ + SOPORTE_T
    pared = caja(x0, x1, Y_SOP_IZQ, y_in, Z_PLATO1, Z_PITCH + 20)
    pie = caja(x0, x1, Y_SOP_IZQ - 14, y_in, Z_PLATO1, Z_PLATO1 + 4)
    # Refuerzos triangulares hacia afuera (adentro pasa la horquilla)
    refuerzo = (cq.Workplane("YZ").polyline([(Y_SOP_IZQ, Z_PLATO1), (Y_SOP_IZQ - 12, Z_PLATO1),
                                            (Y_SOP_IZQ, Z_PLATO1 + 20)]).close().extrude(4).val())
    refuerzos = [refuerzo.translate(V(x0, 0, 0)), refuerzo.translate(V(x1 - 4, 0, 0))]
    s = unir(pared, pie, *refuerzos)
    z0 = -HS7955.tf - SOPORTE_T - 1   # la pared está del lado de abajo de la brida
    recortes = [PITCH(servo_ventana(HS7955, z0, -HS7955.tf + 0.5))]
    recortes += [PITCH(h) for h in servo_agujeros(HS7955, z0, -HS7955.tf + 0.5)]
    recortes += [cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 5, X_PITCH + dx, Y_SOP_IZQ - 7) for dx in (-7, 7)]
    return restar(s, *recortes)


def soporte_pitch_der():
    """Lateral derecho: pivote M4 alineado con el eje del HS."""
    x0, x1 = X_PITCH - 14, X_PITCH + 14
    y_out = Y_SOP_DER + SOPORTE_T
    pared = caja(x0, x1, Y_SOP_DER, y_out, Z_PLATO1, Z_PITCH + 12)
    pie = caja(x0, x1, Y_SOP_DER, y_out + 14, Z_PLATO1, Z_PLATO1 + 4)
    refuerzo = (cq.Workplane("YZ").polyline([(y_out, Z_PLATO1), (y_out + 12, Z_PLATO1),
                                            (y_out, Z_PLATO1 + 20)]).close().extrude(4).val())
    s = unir(pared, pie, refuerzo.translate(V(x0, 0, 0)), refuerzo.translate(V(x1 - 4, 0, 0)))
    recortes = [cil_eje(M4 / 2, (X_PITCH, Y_SOP_DER - 1, Z_PITCH), (X_PITCH, y_out + 1, Z_PITCH))]
    recortes += [cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 5, X_PITCH + dx, Y_SOP_DER + 7) for dx in (-7, 7)]
    return restar(s, *recortes)


def horquilla_cabeza():
    """Horquilla que gira en pitch: va del horn del HS al pivote y lleva el MG996R de roll."""
    t = HORQ_T
    xa, xb = X_PITCH - 12, X_FRENTE_HORQ + t
    za, zb = Z_PITCH - 42, Z_PITCH + 18
    yl = Y_HORQ
    izq = caja(xa, xb, yl, yl + t, za, Z_PITCH + 16)
    der = caja(xa, xb, -yl - t, -yl, za, Z_PITCH + 16)
    frente = caja(X_FRENTE_HORQ, xb, yl, -yl, za, zb)
    piso = caja(xa, xb, yl, -yl, za, za + t)
    h = unir(izq, der, frente, piso)
    recortes = [ROLL(servo_ventana(MG996R))] + [ROLL(x) for x in servo_agujeros(MG996R, -1, t + 1)]
    recortes += [PITCH(x) for x in horn_agujeros(HS7955, espesor=t + 1)]
    recortes.append(cil_eje(M4 / 2, (X_PITCH, -yl - t - 1, Z_PITCH), (X_PITCH, -yl + 1, Z_PITCH)))
    # Ventana en el piso para pasar los cables del roll y de la cámara
    recortes.append(caja(xa + 6, X_FRENTE_HORQ - 4, -12, 12, za - 1, za + t + 1))
    return restar(h, *recortes)


def camara_agujeros_yz():
    """Agujeros de la Camera Module 3 (21 × 12,5 mm), con la lente sobre el eje de roll."""
    z_sup = Z_PITCH + 9.5 - 2.0
    return [(sy * 10.5, z) for sy in (-1, 1) for z in (z_sup, z_sup - 12.5)]


def placa_cabeza():
    p = (cq.Workplane("YZ").rect(PLACA_CABEZA, PLACA_CABEZA).extrude(X_PLACA1 - X_PLACA0)
         .edges("|X").fillet(10).val().translate(V(X_PLACA0, 0, Z_PITCH)))
    recortes = [ROLL(x) for x in horn_agujeros(MG996R, espesor=6)]
    recortes += [cil_eje(M2_ROSCA / 2, (X_PLACA0 - 1, y, z), (X_PLACA1 + 1, y, z)) for y, z in camara_agujeros_yz()]
    return restar(p, *recortes)


def cuna_esp32():
    """Cuna para la ESP32-C3-DevKitM-1: la placa se apoya por los extremos y los pines cuelgan libres."""
    L, A = 48.3, 25.4
    x0, y0 = ESP_X0, ESP_Y0
    zb = Z_PLATO1 + ESP_ALTURA
    base = caja(x0 - 11, x0 + L + 11, y0 + A / 2 - 6, y0 + A / 2 + 6, Z_PLATO1, Z_PLATO1 + 3)
    bloque1 = caja(x0 - 4, x0 + 3, y0 - 1, y0 + A + 1, Z_PLATO1, zb + 2)
    bloque2 = caja(x0 + L - 3, x0 + L + 4, y0 - 1, y0 + A + 1, Z_PLATO1, zb + 2)
    c = unir(base, bloque1, bloque2)
    recortes = [caja(x0 - 0.3, x0 + 3.1, y0 - 0.3, y0 + A + 0.3, zb, zb + 3),
                caja(x0 + L - 3.1, x0 + L + 0.3, y0 - 0.3, y0 + A + 0.3, zb, zb + 3),
                # muesca para el micro-USB, que asoma por el extremo -X
                caja(x0 - 5, x0 + 1, y0 + A / 2 - 6, y0 + A / 2 + 6, zb - 4, zb + 3)]
    recortes += [cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 4, x, y0 + A / 2) for x in (x0 - 7.5, x0 + L + 7.5)]
    return restar(c, *recortes)


def porta_buzzer():
    return restar(unir(cil(8.0, Z_PLATO1, Z_PLATO1 + 6, -5, -64 + 18), caja(-9, -1, -68, -46, Z_PLATO1, Z_PLATO1 + 3)),
                  cil(6.1, Z_PLATO1 + 1, Z_PLATO1 + 7, -5, -46), cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 4, -5, -64))


# ============================================================================================
# Carcasa estilo Keepon
# ============================================================================================
C_CABEZA = (X_PITCH, 0.0, Z_PITCH)
OREJAS_CUERPO = [(87 * math.cos(math.radians(45 + 90 * k)), 87 * math.sin(math.radians(45 + 90 * k)))
                 for k in range(4)]


def esfera(r, centro=C_CABEZA):
    return cq.Solid.makeSphere(r, V(*centro), angleDegrees1=-90, angleDegrees2=90)


def elipsoide(a, c, zc):
    return esfera(1.0, (0, 0, 0)).transformGeometry(cq.Matrix([[a, 0, 0, 0], [0, a, 0, 0], [0, 0, c, zc]]))


def caja_de(forma, m=MARGEN_BARRIDO):
    b = forma.BoundingBox()
    return (b.xmin - m, b.xmax + m, b.ymin - m, b.ymax + m, b.zmin - m, b.zmax + m)


def obstaculos_fijos():
    """Piezas fijas al plato que la cabeza no puede tocar, simplificadas a cajas con margen."""
    pcb, puertos, disip = pi5()
    epcb, emod = esp32()
    return [caja_de(soporte_pitch_izq()), caja_de(soporte_pitch_der()),
            caja_de(PITCH(servo_modelo(HS7955))),
            caja_de(unir(pcb, puertos, disip)), caja_de(unir(epcb, emod, cuna_esp32())),
            caja_de(porta_buzzer())]


@lru_cache(maxsize=None)
def contorno_abertura(paso_th=1.0, paso_ph=3.0, paso_pose=2.0):
    """Borde de la abertura inferior de la cabeza: para cada azimut, el ángulo máximo desde −Z.

    Se muestrean puntos de la cáscara (en la pose 0) y se marcan los que, en alguna pose de pitch
    y roll, caen dentro de una pieza fija (plato, soportes, HS, Pi, ESP32, buzzer).
    """
    import numpy as np
    R, Ri = CABEZA_R, CABEZA_R - CARCASA_T
    th = np.radians(np.arange(0, 180 + 1e-9, paso_th))
    ph = np.radians(np.arange(0, 360, paso_ph))
    T, P = np.meshgrid(th, ph, indexing="ij")
    d = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), -np.cos(T)], -1)
    pts = np.concatenate([d * r for r in (Ri - 0.5, (Ri + R) / 2, R + 0.5)], 0)   # relativo al centro
    cajas = np.array(obstaculos_fijos())
    c = np.array(C_CABEZA)
    m = MARGEN_BARRIDO
    marcado = np.zeros(pts.shape[:2], bool)
    for pg in np.arange(-PITCH_BARRIDO, PITCH_BARRIDO + 1e-9, paso_pose):
        a = math.radians(pg)
        Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        for rg in np.arange(-ROLL_BARRIDO, ROLL_BARRIDO + 1e-9, paso_pose):
            b = math.radians(rg)
            Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
            w = pts @ (Ry @ Rx).T + c
            x, y, z = w[..., 0], w[..., 1], w[..., 2]
            dentro = (np.hypot(x, y) < PLATO_D / 2 + m) & (z > Z_PLATO0 - m) & (z < Z_PLATO1 + m)
            for x0, x1, y0, y1, z0, z1 in cajas:
                dentro |= (x > x0) & (x < x1) & (y > y0) & (y < y1) & (z > z0) & (z < z1)
            marcado |= dentro
    n = len(th)
    marcado = marcado[:n] | marcado[n:2 * n] | marcado[2 * n:]
    th_max = np.array([np.degrees(th[np.nonzero(marcado[:, j])[0]].max()) if marcado[:, j].any() else 0.0
                       for j in range(len(ph))])
    th_max = np.maximum.reduce([np.roll(th_max, k) for k in (-1, 0, 1)])   # vecinos, por las dudas
    return tuple(np.degrees(ph)), tuple(th_max)


def abertura_cabeza(extra=2.0):
    """Sólido de corte (bipirámide): vértice en el centro de la cabeza, borde en el contorno de la
    abertura y segundo vértice bien abajo. El borde va lejos (r = 500) para que las caras de abajo no
    corten la cáscara: así el sólido coincide con el cono del contorno en toda la cabeza."""
    ph, th = contorno_abertura()
    c = V(*C_CABEZA)
    r = 500.0
    borde = []
    for f, t in zip(ph, th):
        t, f = math.radians(min(t + extra, 178)), math.radians(f)
        borde.append(c + V(math.sin(t) * math.cos(f), math.sin(t) * math.sin(f), -math.cos(t)) * r)
    abajo = c + V(0, 0, -3000)
    caras = []
    for i in range(len(borde)):
        a, b = borde[i], borde[(i + 1) % len(borde)]
        caras.append(cq.Face.makeFromWires(cq.Wire.makePolygon([c, a, b], close=True)))
        caras.append(cq.Face.makeFromWires(cq.Wire.makePolygon([abajo, b, a], close=True)))
    return cq.Solid.makeSolid(cq.Shell.makeShell(caras)).fix()


def direccion_ojo(lado):
    az, el = math.radians(OJO_AZ * lado), math.radians(OJO_EL)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))


@lru_cache(maxsize=None)
def cabeza_completa():
    R, Ri = CABEZA_R, CABEZA_R - CARCASA_T
    cx, _, cz = C_CABEZA
    c = esfera(R).cut(esfera(Ri))
    # Mordazas: abrazan los bordes laterales de la placa de la cabeza (entran de costado, por Y).
    # Van por encima del centro, lejos de la abertura de abajo, donde el borde de la placa es recto.
    y_borde = PLACA_CABEZA / 2
    z0, z1 = cz + 3, cz + PLACA_CABEZA / 2 - 11
    refuerzos = []
    for sy in (-1, 1):
        brazo = caja(X_PLACA0 - 5, X_PLACA1 + 5, -R if sy < 0 else y_borde - 6,
                     -(y_borde - 6) if sy < 0 else R, z0 + 4, z1)
        mandibula = caja(X_PLACA0 - 5, X_PLACA1 + 5, -(y_borde + 8) if sy < 0 else y_borde - 6,
                         -(y_borde - 6) if sy < 0 else y_borde + 8, z0, z1)
        canal = caja(X_PLACA0 - HOLGURA / 2, X_PLACA1 + HOLGURA / 2,
                     -(y_borde + HOLGURA) if sy < 0 else -1, 1 if sy < 0 else y_borde + HOLGURA,
                     z0 - 1, z1 + 1)
        refuerzos.append(restar(unir(brazo, mandibula), canal))
    # Unión de las dos mitades: dos bloques sobre el plano y = 0 con un tornillo M3 a lo largo de Y
    uniones = []
    for dx, dz in ((-0.6, 0.8), (0.5, 0.866)):
        px, pz = cx + dx * (Ri - 5), cz + dz * (Ri - 5)
        uniones.append(restar(caja(px - 6, px + 6, -6, 6, pz - 6, pz + 6),
                              cil_eje(M3 / 2, (px, -7, pz), (px, 7, pz))))
    extra = unir(*refuerzos, *uniones).intersect(esfera(R - 0.5))
    c = unir(c, extra)
    # Aberturas
    recortes = [abertura_cabeza()]
    for lado in (-1, 1):
        d = direccion_ojo(lado)
        recortes.append(cil_eje(OJO_D / 2, tuple(C_CABEZA[i] + d[i] * (Ri - 3) for i in range(3)),
                                tuple(C_CABEZA[i] + d[i] * (R + 3) for i in range(3))))
    # Lente de la cámara: agujero y avellanado para no recortar el campo visual
    recortes.append(cil_eje(4.6, (cx + Ri - 5, 0, cz), (cx + R + 2, 0, cz)))
    recortes.append(cq.Solid.makeCone(4.6, 4.6 + 6 * math.tan(math.radians(40)), 6,
                                      V(cx + R - CARCASA_T, 0, cz), V(1, 0, 0)))
    for r in recortes:            # de a uno: con herramientas superpuestas el corte puede fallar
        c = c.cut(r)
    return max(c.clean().Solids(), key=lambda x: x.Volume())   # descarta astillas sueltas


def cabeza_mitad(lado):
    """lado = -1: mitad derecha del robot (y < 0); +1: izquierda (y > 0)."""
    medio = caja(-200, 200, 0 if lado > 0 else -200, 200 if lado > 0 else 0, -10, 400)
    return cabeza_completa().intersect(medio).clean()


def ojo(lado):
    d = direccion_ojo(lado)
    R, Ri = CABEZA_R, CABEZA_R - CARCASA_T
    p = lambda r: tuple(C_CABEZA[i] + d[i] * r for i in range(3))
    tapon = cil_eje(OJO_D / 2 - 0.15, p(Ri), p(R + 0.8))
    tope = cil_eje(OJO_D / 2 + 2, p(Ri - 1.2), p(Ri - 0.05))
    return unir(tapon, tope)


@lru_cache(maxsize=None)
def cuerpo_carcasa():
    T = CARCASA_T
    c = elipsoide(CUERPO_A, CUERPO_C, CUERPO_ZC).cut(elipsoide(CUERPO_A - T, CUERPO_C - T, CUERPO_ZC))
    c = c.intersect(caja(-200, 200, -200, 200, Z_PLATO0, 400))
    # Orejas para atornillarlo al plato
    orejas = []
    for k, (x, y) in enumerate(OREJAS_CUERPO):
        o = restar(caja(80, 99, -7, 7, Z_PLATO1, Z_PLATO1 + 3), cil(M3 / 2, Z_PLATO1 - 1, Z_PLATO1 + 4, 87, 0))
        orejas.append(o.rotate(V(0, 0, 0), V(0, 0, 1), 45 + 90 * k))
    c = unir(c, unir(*orejas).intersect(elipsoide(CUERPO_A - 0.5, CUERPO_C - 0.5, CUERPO_ZC)))
    # Ventilación de la Pi (atrás)
    rejillas = [caja(-120, -80, -2, 2, 100, 128).rotate(V(0, 0, 0), V(0, 0, 1), a) for a in range(-24, 25, 8)]
    # Lejos de la cabeza: el cuerpo nunca entra en la esfera de la cabeza
    return restar(c, esfera(CABEZA_R + 2), *rejillas)


def cuerpo_mitad(lado):
    """Como la cabeza, el cuerpo se parte en y = 0 y cada mitad entra de costado (después de la cabeza)."""
    medio = caja(-200, 200, 0 if lado > 0 else -200, 200 if lado > 0 else 0, -10, 400)
    return cuerpo_carcasa().intersect(medio).clean()


# ============================================================================================
# Componentes comprados (solo para el ensamble)
# ============================================================================================


def pi5():
    x0, x1, y0 = PI_X0, PI_X1, PI_Y0
    pcb = restar(caja(x0, x1, y0, y0 + 85, Z_PI, Z_PI + 1.6),
                 *[cil(1.35, Z_PI - 1, Z_PI + 3, x, y) for x, y in PI_AGUJEROS])
    puertos = caja(x0 + 2, x1 - 2, y0 + 64, y0 + 87, Z_PI + 1.6, Z_PI + 17.6)          # USB + Ethernet
    disipador = caja(x0 + 8, x1 - 10, y0 + 18, y0 + 58, Z_PI + 1.6, Z_PI + 11.6)       # disipador activo
    gpio = caja(x0 + 1, x0 + 6, y0 + 7, y0 + 58, Z_PI + 1.6, Z_PI + 10)
    return pcb, unir(puertos, gpio), disipador


def esp32():
    x0, y0, zb = ESP_X0, ESP_Y0, Z_PLATO1 + ESP_ALTURA
    pcb = caja(x0, x0 + 48.3, y0, y0 + 25.4, zb, zb + 1.6)
    modulo = caja(x0 + 30, x0 + 46, y0 + 6, y0 + 19.4, zb + 1.6, zb + 4)
    usb = caja(x0 - 1.5, x0 + 4, y0 + 9, y0 + 16.4, zb + 1.6, zb + 4.6)
    pines = unir(caja(x0 + 5, x0 + 43, y0 + 0.5, y0 + 3, zb - 8.5, zb),
                 caja(x0 + 5, x0 + 43, y0 + 22.4, y0 + 24.9, zb - 8.5, zb))
    return pcb, unir(modulo, usb, pines)


def camara():
    x = X_PLACA1 + CAM_SEPARADOR
    pcb = caja(x, x + 1.0, -12.5, 12.5, Z_PITCH - 14.5, Z_PITCH + 9.5)
    lente = unir(caja(x + 1, x + 5, -4.25, 4.25, Z_PITCH - 4.25, Z_PITCH + 4.25),
                 cil_eje(3.5, (x + 5, 0, Z_PITCH), (x + CAM_LARGO, 0, Z_PITCH)))
    separadores = unir(*[cil_eje(2.0, (X_PLACA1, y, z), (x, y, z)) for y, z in camara_agujeros_yz()])
    return pcb, lente, separadores


def rodamiento():
    inf = restar(cil(ROD_DE / 2, Z_ROD0, Z_ROD0 + ROD_H / 2), cil(ROD_DI / 2 + 4, Z_ROD0 - 1, Z_PLATO0))
    sup = restar(cil(ROD_DE / 2 - 4, Z_ROD0 + ROD_H / 2, Z_PLATO0), cil(ROD_DI / 2, Z_ROD0, Z_PLATO0 + 1))
    return unir(inf, sup)


def base_componentes():
    bat = caja(BATERIA_X0, BATERIA_X0 + BATERIA[0], -BATERIA[1] / 2, BATERIA[1] / 2, PISO, PISO + BATERIA[2])
    r6 = caja(-CAJA_X / 2 + PARED + 3, -CAJA_X / 2 + PARED + 3 + REG6[0], -80, -80 + REG6[1], PISO, PISO + REG6[2])
    r5 = caja(-CAJA_X / 2 + PARED + 3, -CAJA_X / 2 + PARED + 3 + REG5[0], 20, 20 + REG5[1], PISO, PISO + REG5[2])
    llave = caja(-CAJA_X / 2 - 3, -CAJA_X / 2 + 22, -9.4, 9.4, 34.2, 46.6)
    return bat, r6, r5, llave


# ============================================================================================
# Ensamble y poses
# ============================================================================================

COLOR_IMPRESO = cq.Color(0.95, 0.75, 0.10)   # amarillo Keepon
COLOR_TAPA = cq.Color(0.85, 0.65, 0.10)


def rot(forma, eje_p, eje_d, grados):
    if grados == 0:
        return forma
    return forma.rotate(V(*eje_p), V(*eje_p) + V(*eje_d), grados)


def ensamble(yaw=0.0, pitch=0.0, roll=0.0):
    """Devuelve una lista (nombre, forma, color, imprimible) en la pose pedida (grados)."""
    piezas = []

    def add(nombre, forma, color, impresa=False, grupo="base"):
        piezas.append([nombre, forma, color, impresa, grupo])

    # Base fija
    add("caja_base", caja_base(), COLOR_IMPRESO, True)
    add("tapa_base", tapa_base(), COLOR_TAPA, True)
    bat, r6, r5, llave = base_componentes()
    add("bateria_lipo_3s", bat, cq.Color(0.55, 0.57, 0.62))
    add("regulador_6v_20a", r6, cq.Color(0.15, 0.35, 0.75))
    add("regulador_5v_5a", r5, cq.Color(0.1, 0.1, 0.1))
    add("interruptor", llave, cq.Color(0.8, 0.1, 0.1))
    add("servo_yaw_rds3218", YAW(servo_modelo(RDS3218)), cq.Color(0.12, 0.12, 0.12))
    add("rodamiento_yaw", rodamiento(), cq.Color(0.75, 0.75, 0.78))

    # Plataforma (gira con yaw)
    add("horn_yaw", YAW(horn_modelo(RDS3218)), cq.Color(0.7, 0.7, 0.72), grupo="yaw")
    add("plato_yaw", plato_yaw(), COLOR_IMPRESO, True, "yaw")
    pcb, puertos, disip = pi5()
    add("pi5_pcb", pcb, cq.Color(0.05, 0.45, 0.2), grupo="yaw")
    add("pi5_puertos", puertos, cq.Color(0.75, 0.75, 0.78), grupo="yaw")
    add("pi5_disipador", disip, cq.Color(0.2, 0.2, 0.22), grupo="yaw")
    epcb, emod = esp32()
    add("esp32c3_pcb", epcb, cq.Color(0.1, 0.1, 0.12), grupo="yaw")
    add("esp32c3_modulo", emod, cq.Color(0.7, 0.7, 0.72), grupo="yaw")
    add("cuna_esp32", cuna_esp32(), COLOR_IMPRESO, True, "yaw")
    add("porta_buzzer", porta_buzzer(), COLOR_IMPRESO, True, "yaw")
    add("buzzer", cil(6.0, Z_PLATO1 + 1, Z_PLATO1 + 10.5, -5, -46), cq.Color(0.1, 0.1, 0.1), grupo="yaw")
    add("soporte_pitch_izq", soporte_pitch_izq(), COLOR_IMPRESO, True, "yaw")
    add("soporte_pitch_der", soporte_pitch_der(), COLOR_IMPRESO, True, "yaw")
    add("cuerpo_der", cuerpo_mitad(-1), COLOR_IMPRESO, True, "yaw")
    add("cuerpo_izq", cuerpo_mitad(1), COLOR_IMPRESO, True, "yaw")
    add("servo_pitch_hs7955tg", PITCH(servo_modelo(HS7955)), cq.Color(0.08, 0.08, 0.08), grupo="yaw")

    # Cabeza (gira con pitch)
    add("horn_pitch", PITCH(horn_modelo(HS7955)), cq.Color(0.7, 0.7, 0.72), grupo="pitch")
    add("horquilla_cabeza", horquilla_cabeza(), COLOR_IMPRESO, True, "pitch")
    add("servo_roll_mg996r", ROLL(servo_modelo(MG996R)), cq.Color(0.15, 0.25, 0.6), grupo="pitch")

    # Placa de la cabeza y cámara (giran con roll)
    add("horn_roll", ROLL(horn_modelo(MG996R)), cq.Color(0.7, 0.7, 0.72), grupo="roll")
    add("placa_cabeza", placa_cabeza(), COLOR_IMPRESO, True, "roll")
    cpcb, lente, sep = camara()
    add("camara_pcb", cpcb, cq.Color(0.05, 0.45, 0.2), grupo="roll")
    add("camara_lente", lente, cq.Color(0.1, 0.1, 0.1), grupo="roll")
    add("separadores_camara", sep, cq.Color(0.8, 0.7, 0.3), grupo="roll")
    add("cabeza_der", cabeza_mitad(-1), COLOR_IMPRESO, True, "roll")
    add("cabeza_izq", cabeza_mitad(1), COLOR_IMPRESO, True, "roll")
    add("ojo_der", ojo(-1), cq.Color(0.05, 0.05, 0.05), True, "roll")
    add("ojo_izq", ojo(1), cq.Color(0.05, 0.05, 0.05), True, "roll")

    # Cadena cinemática: roll → pitch → yaw
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


# El horn calza sobre el eje estriado: esa superposición es a propósito
IGNORAR = {("servo_yaw_rds3218", "horn_yaw"), ("servo_pitch_hs7955tg", "horn_pitch"),
           ("servo_roll_mg996r", "horn_roll")}


def interferencias(piezas, tol=1.0):
    """Pares de piezas que se superponen más de `tol` mm³ (los contactos de apoyo dan volumen ~0)."""
    res = []
    for i in range(len(piezas)):
        for j in range(i + 1, len(piezas)):
            if (piezas[i][0], piezas[j][0]) in IGNORAR:
                continue
            a, b = piezas[i][1], piezas[j][1]
            ba, bb = a.BoundingBox(), b.BoundingBox()
            if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
                    or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
                continue
            try:
                v = a.intersect(b).Volume()
            except Exception:
                continue
            if v > tol:
                res.append((piezas[i][0], piezas[j][0], round(v, 1)))
    return res


def exportar(raiz: Path):
    (raiz / "step").mkdir(parents=True, exist_ok=True)
    (raiz / "stl").mkdir(parents=True, exist_ok=True)
    piezas = ensamble()
    asm = cq.Assembly(name="keepon_v2")
    for nombre, forma, color, impresa, _ in piezas:
        asm.add(forma, name=nombre, color=color)
        if impresa:
            cq.exporters.export(forma, str(raiz / "step" / f"{nombre}.step"))
            cq.exporters.export(forma, str(raiz / "stl" / f"{nombre}.stl"), tolerance=0.05, angularTolerance=0.2)
    asm.save(str(raiz / "step" / "keepon_v2_ensamble.step"))
    return piezas


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    piezas = exportar(raiz)
    print(f"plato a z={Z_PLATO0:.1f}, eje de pitch a z={Z_PITCH:.1f}, alza del rodamiento {ALZA_ROD:.1f} mm, "
          f"separadores de la cámara {CAM_SEPARADOR:.1f} mm")
    for nombre, forma, _, impresa, _ in piezas:
        bb = forma.BoundingBox()
        if impresa:
            print(f"  {nombre:20s} {bb.xlen:6.1f} × {bb.ylen:6.1f} × {bb.zlen:6.1f} mm, {forma.Volume() / 1000:6.1f} cm³")
