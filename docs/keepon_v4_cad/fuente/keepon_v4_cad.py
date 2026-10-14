"""Modelo mecánico de Keepon pro v4: cabeza de la v3 sobre el cuello compacto de la v1, y las baterías en la base.

- Cabeza, servos, soportes de pitch, horquilla y brazos: los de la v3 (../../keepon_v3_cad/fuente/keepon_v3_cad.py),
  sin cambios.
- Disposición de los motores: la de la v1 (../../keepon_mg996r_step/): el eje de pitch pasa justo por encima del eje
  de yaw (en la v3 estaba 20 mm adelante) y el plato de Ø146 se reemplaza por una base en U compacta. El centro de
  masa de la cabeza queda más cerca del eje del yaw, que no tiene rodamiento.
- Alimentación: la LiPo Zeee 3S 8000 mAh alimenta los servos (por el regulador de 6 V) y el powerbank Xiaomi
  PB2020MI alimenta la Pi 5 (5 V por el GPIO). Las dos van en la caja base, con el regulador, la ESP32 y el buzzer.

    ~/cq_env/bin/python keepon_v4_cad.py [--verificar]   # escribe ../step, ../stl, ../solidworks y ../vistas

Convenciones (mm): origen en el eje de yaw, a nivel del piso de la caja; +X adelante (hacia la persona),
+Y a la izquierda del robot, +Z arriba. Pitch > 0 baja la nariz; roll > 0 gira la cabeza hacia la derecha.
"""
from pathlib import Path
import math
import sys

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "keepon_v3_cad" / "fuente"))
import keepon_v3_cad as k3   # noqa: E402
import keepon_cad as v2      # noqa: E402
from keepon_cad import V, caja, cil, cil_eje, unir, restar, rot, M3, M3_ROSCA, RDS3218, YAW  # noqa: E402

# ============================================================================================
# PARÁMETROS
# ============================================================================================

# --- Disposición de la v1: el eje de pitch sobre el eje de yaw -------------------------------
DX = -k3.X_PITCH       # todo lo que va arriba del plato de la v3 se corre esto en X (queda el pitch en x = 0)
X_PITCH = 0.0
Z_PITCH = k3.Z_PITCH   # misma altura que en la v3 (la caja base mide lo mismo)

# --- Baterías (docs/Fotos/bateria zee y docs/Fotos/Bateria powerbank xiaomi) ----------------
ZEEE = (138.0, 47.0, 36.0)      # LiPo Zeee 3S 8000 mAh 100C, 11,1 V, Deans, 493 g
XIAOMI = (128.0, 73.0, 32.0)    # powerbank Xiaomi PB2020MI 20000 mAh, 5 V 3 A, 342 g (medidas aproximadas: MEDIR)

# --- Caja base ---------------------------------------------------------------------------------
CAJA_X, CAJA_Y, CAJA_Z = 182.0, 133.0, 70.0    # exterior sin la tapa: las dos baterías acostadas, lado a lado
PARED, PISO, TAPA_T = 3.0, 3.0, 4.0
X_IN0, X_IN1 = -CAJA_X / 2 + PARED, CAJA_X / 2 - PARED
Y_IN0, Y_IN1 = -CAJA_Y / 2 + PARED, CAJA_Y / 2 - PARED
# Baterías acostadas, a lo largo de X, contra la pared de atrás; adelante queda la bahía de la electrónica
ZEEE_POS = (X_IN0, Y_IN0 + 0.5)                     # esquina (x, y): lado derecho del robot (−Y)
XIAOMI_POS = (X_IN0, ZEEE_POS[1] + ZEEE[1] + 5.0)    # lado izquierdo, con un tabique de 3 mm en el medio
TOPE_ALTO = 10.0                                    # altura de los topes y del tabique
X_BAHIA = ZEEE_POS[0] + ZEEE[0] + 4.0               # desde acá hacia adelante: regulador, ESP32, buzzer
REG6 = (25.0, 65.0, 50.0)                           # regulador 12 → 6 V 20 A, PARADO (espesor × largo × alto)
# Las columnas de la tapa cuelgan de la pared: las de atrás por encima de las baterías, las de adelante del regulador
COLUMNA_Z0 = (PISO + ZEEE[2] + 2.0, PISO + REG6[2] + 2.0)

# --- Base en U (reemplaza al plato de Ø146) --------------------------------------------------
PLATO_X = (-32.0, 32.0)          # adelante, la cabeza baja hasta acá con la nariz abajo
PLATO_Y = (-66.0, 50.0)          # asimétrica: el HS-7955TG sale del soporte izquierdo hacia −Y
PLATO_R = 10.0
PASO_ANG = -90.0                 # paso de cables: arco centrado hacia −Y (adelante y atrás no hay lugar)
PASO_R, PASO_ANCHO, PASO_ARCO = 26.0, 10.0, 72.0   # ±72° cubre el yaw de ±70°

# ============================================================================================
# Cotas derivadas
# ============================================================================================
Z_TAPA0, Z_TAPA1 = CAJA_Z, CAJA_Z + TAPA_T
Z_PLATO0, Z_PLATO1 = k3.Z_PLATO0, k3.Z_PLATO1
assert abs(Z_TAPA0 - v2.Z_TAPA0) < 1e-9, "la caja tiene que medir lo mismo que en la v3 (el yaw se monta igual)"
Y_SOP_IZQ, Y_SOP_DER = v2.Y_SOP_IZQ, v2.Y_SOP_DER
PASO_XY = (PASO_R * math.cos(math.radians(PASO_ANG)), PASO_R * math.sin(math.radians(PASO_ANG)))

# El servo de yaw cuelga de la tapa: no puede tocar las baterías
_z_servo = Z_TAPA0 - RDS3218.Fb
assert _z_servo > PISO + ZEEE[2] + 2, "el servo de yaw toca la LiPo"


def esquinas_tapa():
    ex, ey = CAJA_X / 2 - 8, CAJA_Y / 2 - 8
    return [(sx * ex, sy * ey) for sx in (-1, 1) for sy in (-1, 1)]


# ============================================================================================
# Piezas impresas nuevas
# ============================================================================================


def caja_base():
    """Caja con las dos baterías acostadas atrás y la bahía de la electrónica adelante.
    Se imprime boca arriba; las columnas de las esquinas cuelgan por encima de las baterías (con soporte)."""
    ext = caja(-CAJA_X / 2, CAJA_X / 2, -CAJA_Y / 2, CAJA_Y / 2, 0, CAJA_Z)
    c = restar(ext, caja(X_IN0, X_IN1, Y_IN0, Y_IN1, PISO, CAJA_Z + 1))
    # Columnas de la tapa (M3 autorroscante), arriba de las baterías
    for x, y in esquinas_tapa():
        sx, sy = math.copysign(1, x), math.copysign(1, y)
        z0 = COLUMNA_Z0[0] if x < 0 else COLUMNA_Z0[1]
        col = unir(cil(5.0, z0, CAJA_Z, x, y), caja(*sorted((x, x + sx * 6)), *sorted((y, y + sy * 6)), z0, CAJA_Z))
        c = unir(c, restar(col, cil(M3_ROSCA / 2, CAJA_Z - 16, CAJA_Z + 1, x, y)))
    # Topes de las baterías: tabique entre las dos y topes adelante (no se deslizan)
    zx, zy = ZEEE_POS
    xx, xy = XIAOMI_POS
    c = unir(c, caja(zx + 10, zx + ZEEE[0] - 10, zy + ZEEE[1] + 1, xy - 1, PISO, PISO + TOPE_ALTO),
             caja(zx + ZEEE[0] + 0.5, zx + ZEEE[0] + 3.5, zy, zy + ZEEE[1], PISO, PISO + TOPE_ALTO),
             caja(xx + XIAOMI[0] + 0.5, xx + XIAOMI[0] + 3.5, xy, xy + XIAOMI[1], PISO, PISO + TOPE_ALTO))
    # Rieles del regulador (va parado, con el disipador hacia arriba)
    rx0, ry0 = X_BAHIA + 3, Y_IN0 + 1
    for x in (rx0 - 2, rx0 + REG6[0]):
        c = unir(c, caja(x, x + 2, ry0, ry0 + REG6[1], PISO, PISO + 6))
    # Portabuzzer en la pared de adelante, con agujeros para el sonido
    bz = BUZZER_YZ
    c = unir(c, restar(cil_eje(7.5, (X_IN1 - 9, *bz), (X_IN1 + 0.1, *bz)), cil_eje(6.1, (X_IN1 - 10, *bz), (X_IN1, *bz))))
    c = restar(c, *[cil_eje(1.0, (X_IN1 - 1, bz[0] + dy, bz[1] + dz), (CAJA_X / 2 + 1, bz[0] + dy, bz[1] + dz))
                    for dy, dz in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3))])
    # Pared de atrás: interruptor de balancín (corte estándar 19,2 × 12,8), por encima del powerbank
    c = restar(c, caja(-CAJA_X / 2 - 1, X_IN0 + 1, LLAVE_Y - 9.6, LLAVE_Y + 9.6, LLAVE_Z, LLAVE_Z + 12.8))
    # Ventilación del regulador (los dos laterales de la bahía)
    for k in range(4):
        x = X_BAHIA + 5 + k * 6
        c = restar(c, caja(x, x + 3, -CAJA_Y / 2 - 1, Y_IN0 + 1, 15, 50))
        c = restar(c, caja(x, x + 3, Y_IN1 - 1, CAJA_Y / 2 + 1, 15, 50))
    # Lateral izquierdo: ranura para el cable del powerbank (cargarlo sin abrir) y su botón
    c = restar(c, caja(xx + 20, xx + 50, Y_IN1 - 1, CAJA_Y / 2 + 1, PISO + 8, PISO + 22))
    return c


def tapa_base():
    t = caja(-CAJA_X / 2, CAJA_X / 2, -CAJA_Y / 2, CAJA_Y / 2, Z_TAPA0, Z_TAPA1)
    recortes = [YAW(v2.servo_ventana(RDS3218))] + [YAW(h) for h in v2.servo_agujeros(RDS3218, -1, TAPA_T + 1)]
    recortes.append(cil(PASO_ANCHO / 2, Z_TAPA0 - 1, Z_TAPA1 + 1, *PASO_XY))       # paso de cables fijo
    recortes += [cil(M3 / 2, Z_TAPA0 - 1, Z_TAPA1 + 1, x, y) for x, y in esquinas_tapa()]
    return restar(t, *recortes)


def plato_yaw():
    """Base en U (como el soporte de pan de la v1): se atornilla al brazo del RDS3218 y lleva los soportes de pitch."""
    x0, x1 = PLATO_X
    y0, y1 = PLATO_Y
    p = (cq.Workplane("XY").center((x0 + x1) / 2, (y0 + y1) / 2).rect(x1 - x0, y1 - y0).extrude(Z_PLATO1 - Z_PLATO0)
         .edges("|Z").fillet(PLATO_R).val().translate(V(0, 0, Z_PLATO0)))
    recortes = [YAW(h) for h in k3.brazo_agujeros(RDS3218, espesor=v2.PLATO_T + 1)]
    ranura = None
    for k in range(17):    # ranura en arco: sigue cubriendo el paso fijo de la tapa en todo el rango de yaw
        ang = math.radians(PASO_ANG - PASO_ARCO + 2 * PASO_ARCO * k / 16)
        cc = cil(PASO_ANCHO / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, PASO_R * math.cos(ang), PASO_R * math.sin(ang))
        ranura = cc if ranura is None else ranura.fuse(cc)
    recortes.append(ranura.clean())
    for y in (Y_SOP_IZQ - 7, Y_SOP_DER + 7):        # soportes de pitch (los de la v3, corridos a x = 0)
        recortes += [cil(M3 / 2, Z_PLATO0 - 1, Z_PLATO1 + 1, X_PITCH + dx, y) for dx in (-7, 7)]
    return restar(p, *recortes)


def porta_esp32():
    """La ESP32-C3 va parada en la bahía, tomada de los extremos cortos (los pines quedan libres)."""
    x, (y0, y1), z0 = ESP_X, ESP_Y, PISO
    base = caja(x - 10, x + 8, y0 - 4, y1 + 4, z0, z0 + 3)
    postes = [caja(x - 4, x + 4, y0 - 4, y0 + 1, z0, ESP_Z1 + 2), caja(x - 4, x + 4, y1 - 1, y1 + 4, z0, ESP_Z1 + 2)]
    p = unir(base, *postes)
    ranuras = [caja(x - 0.9, x + 0.9, y0 - 0.5, y1 + 0.5, ESP_Z0, ESP_Z1 + 3)]
    ranuras.append(caja(x - 5, x + 5, y1 - 2, y1 + 5, ESP_Z0 + 6, ESP_Z1 - 6))   # paso del micro-USB
    return restar(p, *ranuras)


# ============================================================================================
# Componentes de la base (comprados)
# ============================================================================================
ESP_X = X_BAHIA + 16.0                      # plano de la placa de la ESP32 (parada, normal a X), al lado del regulador
ESP_Y = (Y_IN0 + 1 + REG6[1] + 8, Y_IN0 + 1 + REG6[1] + 8 + 48.3)
ESP_Z0 = PISO + 5.0
ESP_Z1 = ESP_Z0 + 25.4
BUZZER_YZ = (35.0, 55.0)
LLAVE_Y, LLAVE_Z = 30.0, 48.0
assert ESP_Y[1] + 4 < Y_IN1, "la ESP32 no entra en la bahía"
assert LLAVE_Z > PISO + XIAOMI[2] + 2, "el interruptor toca el powerbank"


def base_componentes():
    zx, zy = ZEEE_POS
    xx, xy = XIAOMI_POS
    zeee = caja(zx, zx + ZEEE[0], zy, zy + ZEEE[1], PISO, PISO + ZEEE[2])
    xiaomi = (cq.Workplane("XY").box(XIAOMI[0], XIAOMI[1], XIAOMI[2]).edges("|Z").fillet(10).val()
              .translate(V(xx + XIAOMI[0] / 2, xy + XIAOMI[1] / 2, PISO + XIAOMI[2] / 2)))
    rx0, ry0 = X_BAHIA + 3, Y_IN0 + 1
    reg = caja(rx0, rx0 + REG6[0], ry0, ry0 + REG6[1], PISO, PISO + REG6[2])
    x = ESP_X
    esp = unir(caja(x - 0.8, x + 0.8, ESP_Y[0], ESP_Y[1], ESP_Z0, ESP_Z1),
               caja(x + 0.8, x + 3.2, ESP_Y[0] + 30, ESP_Y[0] + 46, ESP_Z0 + 6, ESP_Z1 - 6),     # módulo
               caja(x - 8.5, x - 0.8, ESP_Y[0] + 5, ESP_Y[0] + 43, ESP_Z0 + 0.5, ESP_Z0 + 3),    # pines
               caja(x - 8.5, x - 0.8, ESP_Y[0] + 5, ESP_Y[0] + 43, ESP_Z1 - 3, ESP_Z1 - 0.5))
    buzzer = cil_eje(6.0, (X_IN1 - 9.5, *BUZZER_YZ), (X_IN1, *BUZZER_YZ))
    llave = caja(-CAJA_X / 2 - 3, X_IN0 + 19, LLAVE_Y - 9.4, LLAVE_Y + 9.4, LLAVE_Z + 0.2, LLAVE_Z + 12.6)
    usbc = caja(X_IN1 - 9, X_IN1 - 1, Y_IN0 + REG6[1] + 4, Y_IN0 + REG6[1] + 16, PISO, PISO + 1.6)   # bornera USB-C del powerbank
    return zeee, xiaomi, reg, esp, buzzer, llave, usbc


# ============================================================================================
# Ensamble
# ============================================================================================
NO_VAN = {"plato_yaw", "esp32c3", "cuna_esp32", "porta_buzzer", "buzzer"}   # de la v3: van distinto en la v4
SIN_CORRER = {"servo_yaw_rds3218", "horn_yaw"}                              # el yaw queda donde estaba


def ensamble(yaw=0.0, pitch=0.0, roll=0.0, con_base=True):
    """Lista [nombre, forma, color, impresa, grupo] en la pose pedida (grados)."""
    piezas = []

    def add(nombre, forma, color, impresa=False, grupo="base"):
        piezas.append([nombre, forma, color, impresa, grupo])

    if con_base:
        add("caja_base", caja_base(), k3.COLOR_IMPRESO, True)
        add("tapa_base", tapa_base(), k3.COLOR_TAPA, True)
        zeee, xiaomi, reg, esp, buzzer, llave, usbc = base_componentes()
        add("bateria_zeee_3s_8000", zeee, cq.Color(0.2, 0.2, 0.25))
        add("powerbank_xiaomi_pb2020mi", xiaomi, cq.Color(0.75, 0.76, 0.78))
        add("regulador_6v_20a", reg, cq.Color(0.15, 0.35, 0.75))
        add("esp32c3", esp, cq.Color(0.1, 0.1, 0.12))
        add("porta_esp32", porta_esp32(), k3.COLOR_IMPRESO, True)
        add("buzzer", buzzer, cq.Color(0.1, 0.1, 0.1))
        add("interruptor", llave, cq.Color(0.8, 0.1, 0.1))
        add("usb_c_bornera", usbc, cq.Color(0.1, 0.4, 0.2))
    add("plato_yaw", plato_yaw(), k3.COLOR_IMPRESO, True, "yaw")
    # Todo lo de la v3 por encima del plato (en la pose pedida de pitch y roll), corrido a la disposición de la v1
    for nombre, forma, color, impresa, grupo in k3.ensamble(pitch=pitch, roll=roll, con_base=False):
        if nombre in NO_VAN:
            continue
        if nombre not in SIN_CORRER:
            forma = forma.translate(V(DX, 0, 0))
        add(nombre, forma, color, impresa, grupo)
    for p in piezas:
        if p[4] != "base":
            p[1] = rot(p[1], (0, 0, 0), (0, 0, 1), yaw)
    return piezas


# Contactos a propósito (los de la v3)
IGNORAR = k3.IGNORAR


def verificar():
    problemas = {(0, 0): k3.interferencias(ensamble())}
    for pitch in (-k3.PITCH_ARRIBA, -k3.PITCH_ARRIBA / 2, k3.PITCH_ABAJO / 2, k3.PITCH_ABAJO):
        for roll in (-k3.ROLL_MAX, 0.0, k3.ROLL_MAX):
            problemas[(pitch, roll)] = k3.interferencias(ensamble(pitch=pitch, roll=roll), solo_entre_grupos=True)
    for roll in (-k3.ROLL_MAX, k3.ROLL_MAX):
        problemas[(0.0, roll)] = k3.interferencias(ensamble(roll=roll), solo_entre_grupos=True)
    for yaw in (-70.0, 70.0):    # el yaw: lo que gira contra la caja
        problemas[("yaw", yaw)] = k3.interferencias(ensamble(yaw=yaw, pitch=k3.PITCH_ABAJO), solo_entre_grupos=True)
    return problemas


def holgura_minima():
    fijos = [p for p in ensamble() if p[4] in ("base", "yaw")]
    res = []
    for pitch in (-k3.PITCH_ARRIBA, k3.PITCH_ABAJO):
        for roll in (-k3.ROLL_MAX, k3.ROLL_MAX):
            mov = [p for p in ensamble(pitch=pitch, roll=roll) if p[4] in ("pitch", "roll")]
            d = min((a[1].distance(b[1]), a[0], b[0]) for a in mov for b in fijos
                    if (a[0], b[0]) not in IGNORAR and (b[0], a[0]) not in IGNORAR
                    and a[1].BoundingBox().zmin < b[1].BoundingBox().zmax + 30)
            res.append((pitch, roll, round(d[0], 1), d[1], d[2]))
    return res


def carga_yaw():
    """Peso y momento de vuelco sobre el eje del RDS3218 (no hay rodamiento). Misma estimación que en la v3."""
    masas = {"servo_pitch_hs7955tg": 65, "servo_roll_mg996r": 55, "camara_pcb": 4, "pi5_pcb": 46,
             "pi5_active_cooler": 24, "horn_yaw": 3, "horn_pitch": 3, "horn_roll": 3}
    peor = None
    for pitch in (-k3.PITCH_ARRIBA, 0.0, k3.PITCH_ABAJO):
        for roll in (-k3.ROLL_MAX, 0.0, k3.ROLL_MAX):
            m_tot = mx = my = 0.0
            for n, forma, _, impresa, grupo in ensamble(pitch=pitch, roll=roll, con_base=False):
                if grupo == "base":
                    continue
                m = forma.Volume() / 1000 * 1.24 * 0.5 if impresa else masas.get(n, 0.0)
                c = forma.Center()
                m_tot, mx, my = m_tot + m, mx + m * c.x, my + m * c.y
            r = math.hypot(mx, my) / m_tot
            fila = (pitch, roll, round(m_tot), round(r, 1), round(m_tot * r / 10000, 2))
            if peor is None or fila[4] > peor[4]:
                peor = fila
    return peor


# Relaciones de posición para SolidWorks: las de la v3 con el eje de pitch en x = 0
BISAGRAS = [
    ("yaw", ("plato_yaw", 3.5), ("servo_yaw_rds3218", 3.0), (0.0, 0.0, 0.0), (0, 0, 1), ("plato_yaw", "caja_base")),
    ("pitch", ("horquilla_cabeza", v2.M4 / 2), ("soporte_pitch_der", v2.M4 / 2), (X_PITCH, 0.0, Z_PITCH), (0, 1, 0),
     ("horquilla_cabeza", "plato_yaw")),
    ("roll", ("horn_roll", k3.BRAZO_CUBO_D / 2), ("servo_roll_mg996r", 3.0), (0.0, 0.0, Z_PITCH), (1, 0, 0),
     ("placa_roll", "horquilla_cabeza")),
]


def macro_solidworks(piezas):
    """La macro de la v3 con las bisagras de la v4."""
    viejas = k3.BISAGRAS
    k3.BISAGRAS = BISAGRAS
    try:
        problemas = k3.verificar_relaciones(piezas)
        if problemas:
            raise SystemExit("relaciones de posición: " + "; ".join(problemas))
        texto = k3.macro_solidworks(piezas)
    finally:
        k3.BISAGRAS = viejas
    return texto.replace("Keepon pro v3", "Keepon pro v4").replace("keepon_v3", "keepon_v4") \
                .replace("fuente/keepon_v3_cad.py", "fuente/keepon_v4_cad.py")


def exportar(raiz: Path):
    for d in ("step", "stl", "solidworks", "step/componentes"):
        (raiz / d).mkdir(parents=True, exist_ok=True)
    piezas = ensamble()
    asm = cq.Assembly(name="keepon_v4")
    for nombre, forma, color, impresa, _ in piezas:
        asm.add(forma, name=nombre, color=color)
        if impresa:
            cq.exporters.export(forma, str(raiz / "step" / f"{nombre}.step"))
            cq.exporters.export(forma, str(raiz / "stl" / f"{nombre}.stl"), tolerance=0.05, angularTolerance=0.2)
        else:
            cq.exporters.export(forma, str(raiz / "step" / "componentes" / f"{nombre}.step"))
    asm.save(str(raiz / "step" / "keepon_v4_ensamble.step"))
    macro = macro_solidworks(piezas)
    (raiz / "solidworks" / "keepon_v4_relaciones.bas").write_bytes(macro.encode("cp1252"))
    (raiz / "solidworks" / "keepon_v4_relaciones_PEGAR.txt").write_bytes(macro.split("\r\n", 1)[1].encode("cp1252"))
    return piezas


# Lo que no está modelado (tornillería, cables, conectores), para la lista de componentes
OTROS = [
    ("Tornillo M3 × 10–12 + tuerca", 12, "M3", "Bridas de los servos (4 por servo)."),
    ("Tornillo M3 × 16 autorroscante", 4, "M3", "Tapa a las columnas de la caja."),
    ("Tornillo M3 × 10 + tuerca", 4, "M3", "Soportes de pitch a la base en U."),
    ("Tornillo M2 × 8 autorroscante", 6, "M2", "Base en U, horquilla y placa de roll a los brazos (2 por brazo)."),
    ("Tornillo M4 × 20 + 2 arandelas + tuerca autofrenante", 1, "M4", "Pivote del pitch."),
    ("Tornillo M2,5 × 6 autorroscante", 4, "M2,5", "Pi 5 a la placa de roll."),
    ("Tornillo M2,5 × 12 autorroscante", 4, "M2,5", "Caja de la cabeza a la placa de roll."),
    ("Tornillo M2 × 5", 4, "M2", "Cámara a la cara."),
    ("Velcro adhesivo", 2, "≈ 100 × 20", "Debajo de cada batería (además de los topes)."),
    ("Conector Deans (T) hembra + fusible 10 A en línea", 1, "—", "LiPo → interruptor → regulador de 6 V."),
    ("Cable USB-C macho → bornera (o bornera USB-C)", 1, "10 × 12 placa", "Powerbank → 5 V y GND hacia la Pi."),
    ("Cable rojo/negro 20 AWG", "1 m", "—", "5 V de la Pi: de la base a la cabeza (cruza yaw, pitch y roll)."),
    ("Cable 16 AWG rojo/negro", "0,5 m", "—", "LiPo → regulador → bus de 6 V."),
    ("Alargues de servo macho-hembra", 2, "≈ 30 cm", "Pitch y roll hasta la ESP32 (cruzan el yaw)."),
    ("Cable USB-A acodado → micro-USB, flexible", 1, "≈ 50 cm", "Pi (en la cabeza) → ESP32 (en la base)."),
    ("Capacitor 2200 µF / 16 V + 100 nF", 1, "Ø13 × 25", "Bus de 6 V, junto al regulador."),
    ("2N2222 + 1 kΩ + 10 kΩ (+ 1N4148)", 1, "TO-92", "Buzzer desde el GPIO10."),
    ("Alarma de tensión LiPo", 1, "≈ 40 × 25 × 10", "En el balanceador de la Zeee."),
]


def escribir_lista(raiz, piezas):
    """componentes_v4.txt: todas las piezas del modelo con sus medidas, y lo que no está modelado."""
    L = ["KEEPON PRO v4 · COMPONENTES Y DIMENSIONES", "Generado por docs/keepon_v4_cad/fuente/keepon_v4_cad.py", "",
         "Medidas en mm: caja envolvente en la posición del robot, X (hacia la cara) × Y (de lado a lado) × Z (alto).",
         "IMPRIMIR = pieza propia (step/ y stl/); COMPRADO = componente (step/componentes/).", ""]
    grupos = {"base": "CAJA BASE (fija)", "yaw": "GIRA CON EL YAW", "pitch": "GIRA CON EL PITCH",
              "roll": "GIRA CON EL ROLL (la cabeza)"}
    for g, titulo in grupos.items():
        L += ["=" * 96, titulo, "=" * 96, f"{'Pieza':32s} {'X × Y × Z':24s} {'Volumen':10s} Tipo"]
        for nombre, forma, _, impresa, grupo in piezas:
            if grupo != g:
                continue
            bb = forma.BoundingBox()
            dim = f"{bb.xlen:.1f} × {bb.ylen:.1f} × {bb.zlen:.1f}".replace(".", ",")
            vol = f"{forma.Volume() / 1000:.1f} cm³".replace(".", ",") if impresa else ""
            L.append(f"{nombre:32s} {dim:24s} {vol:10s} {'IMPRIMIR' if impresa else 'COMPRADO'}")
        L.append("")
    L += ["=" * 96, "BATERÍAS (de docs/Fotos)", "=" * 96,
          f"Zeee LiPo 3S 8000 mAh 100C: {ZEEE[0]:.0f} × {ZEEE[1]:.0f} × {ZEEE[2]:.0f}, 11,1 V (12,6 V cargada), Deans, "
          "493 g → servos (por el regulador de 6 V)",
          f"Xiaomi PB2020MI 20000 mAh: {XIAOMI[0]:.0f} × {XIAOMI[1]:.0f} × {XIAOMI[2]:.0f} (aprox., MEDIR), 5 V 3 A por "
          "puerto, 342 g → Pi 5 por el GPIO", "",
          "=" * 96, "NO MODELADO: TORNILLERÍA, CABLES Y CONECTORES", "=" * 96,
          f"{'Elemento':52s} {'Cant.':6s} {'Medida':16s} Dónde va"]
    L += [f"{n:52s} {str(c):6s} {m:16s} {d}" for n, c, m, d in OTROS]
    (raiz / "componentes_v4.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    piezas = exportar(raiz)
    escribir_lista(raiz, piezas)
    alto = max(p[1].BoundingBox().zmax for p in piezas)
    print(f"altura total {alto:.1f} mm; caja base {CAJA_X:.0f} × {CAJA_Y:.0f} × {CAJA_Z + TAPA_T:.0f} mm")
    for nombre, forma, _, impresa, _ in piezas:
        bb = forma.BoundingBox()
        print(f"  {'*' if impresa else ' '} {nombre:28s} {bb.xlen:6.1f} × {bb.ylen:6.1f} × {bb.zlen:6.1f} mm"
              + (f", {forma.Volume() / 1000:6.1f} cm³" if impresa else ""))
    if "--verificar" in sys.argv:
        pitch, roll, m, r, mom = carga_yaw()
        print(f"carga sobre el eje del yaw (peor: pitch {pitch}, roll {roll}): {m} g a {r} mm → {mom} kgf·cm")
        for pose, lista in verificar().items():
            print("pose", pose, "OK" if not lista else lista)
        for fila in holgura_minima():
            print("holgura mínima", fila)
