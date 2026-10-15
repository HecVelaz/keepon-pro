"""Modelo mecánico de Keepon pro v4: cabeza de la v3 sobre el cuello compacto de la v1, y la alimentación en la base.

- Cabeza, servos, soportes de pitch, horquilla y brazos: los de la v3 (../../keepon_v3_cad/fuente/keepon_v3_cad.py),
  sin cambios.
- Disposición de los motores: la de la v1 (../../keepon_mg996r_step/): el eje de pitch pasa justo por encima del eje
  de yaw (en la v3 estaba 20 mm adelante) y el plato de Ø146 se reemplaza por una base en U compacta. El centro de
  masa de la cabeza queda más cerca del eje del yaw, que no tiene rodamiento.
- Alimentación (decisión del 14/10): una fuente de laboratorio externa da los 6 V de los servos (entra por dos bornes
  de panel en la pared de atrás) y el powerbank Xiaomi PB2020MI alimenta la Pi 5 (5 V por el GPIO). En la caja base
  van el powerbank, la bornera de 6 V con el capacitor, la ESP32 y el buzzer. La LiPo y el regulador de 6 V salieron:
  su lugar queda libre.

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

# --- Powerbank (docs/Fotos/Bateria_powerbank_xiaomi) -------------------------------------------
XIAOMI = (128.0, 73.0, 32.0)    # powerbank Xiaomi PB2020MI 20000 mAh, 5 V 3 A, 342 g (medidas aproximadas: MEDIR)

# --- Caja base ---------------------------------------------------------------------------------
CAJA_X, CAJA_Y, CAJA_Z = 182.0, 133.0, 70.0    # exterior sin la tapa (medida pensada para la LiPo y el powerbank)
PARED, PISO, TAPA_T = 3.0, 3.0, 4.0
X_IN0, X_IN1 = -CAJA_X / 2 + PARED, CAJA_X / 2 - PARED
Y_IN0, Y_IN1 = -CAJA_Y / 2 + PARED, CAJA_Y / 2 - PARED
# Powerbank acostado, a lo largo de X, contra la pared de atrás y del lado izquierdo (+Y). Del lado derecho (−Y)
# queda libre el hueco de 138 × 47 donde iba la LiPo (pasan los cables de los bornes y el bucle del yaw).
HUECO = (138.0, 47.0)                               # lugar libre de la LiPo, del lado derecho
XIAOMI_POS = (X_IN0, Y_IN0 + 0.5 + HUECO[1] + 5.0)   # esquina (x, y), con un tabique de 3 mm del lado del hueco
TOPE_ALTO = 10.0                                    # altura de los topes y del tabique
X_BAHIA = X_IN0 + HUECO[0] + 4.0                    # desde acá hacia adelante: bornera de 6 V, ESP32, buzzer
BORNERA6 = (20.0, 40.0, 16.0)                       # bornera de distribución de 6 V y GND (x × y × z), en el piso
CAP = (6.5, 25.0)                                   # capacitor de 2200 µF / 16 V parado (radio, alto)
Y_ESP0 = Y_IN0 + 74.0                               # la ESP32 queda donde estaba (al lado del viejo regulador)
# Las columnas de la tapa cuelgan de la pared: las de atrás por encima del powerbank, las de adelante de la bahía
COLUMNA_Z0 = (PISO + 38.0, PISO + 52.0)

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

# El servo de yaw cuelga de la tapa: no puede tocar el powerbank
_z_servo = Z_TAPA0 - RDS3218.Fb
assert _z_servo > PISO + XIAOMI[2] + 2, "el servo de yaw toca el powerbank"


def esquinas_tapa():
    ex, ey = CAJA_X / 2 - 8, CAJA_Y / 2 - 8
    return [(sx * ex, sy * ey) for sx in (-1, 1) for sy in (-1, 1)]


# ============================================================================================
# Piezas impresas nuevas
# ============================================================================================


def caja_base():
    """Caja con el powerbank acostado atrás, los bornes de 6 V en la pared de atrás y la bahía de la electrónica adelante.
    Se imprime boca arriba; las columnas de las esquinas cuelgan (con soporte)."""
    ext = caja(-CAJA_X / 2, CAJA_X / 2, -CAJA_Y / 2, CAJA_Y / 2, 0, CAJA_Z)
    c = restar(ext, caja(X_IN0, X_IN1, Y_IN0, Y_IN1, PISO, CAJA_Z + 1))
    # Columnas de la tapa (M3 autorroscante)
    for x, y in esquinas_tapa():
        sx, sy = math.copysign(1, x), math.copysign(1, y)
        z0 = COLUMNA_Z0[0] if x < 0 else COLUMNA_Z0[1]
        col = unir(cil(5.0, z0, CAJA_Z, x, y), caja(*sorted((x, x + sx * 6)), *sorted((y, y + sy * 6)), z0, CAJA_Z))
        c = unir(c, restar(col, cil(M3_ROSCA / 2, CAJA_Z - 16, CAJA_Z + 1, x, y)))
    # Topes del powerbank: tabique del lado del hueco y tope adelante (no se desliza)
    xx, xy = XIAOMI_POS
    c = unir(c, caja(xx + 10, xx + XIAOMI[0] - 10, xy - 4, xy - 1, PISO, PISO + TOPE_ALTO),
             caja(xx + XIAOMI[0] + 0.5, xx + XIAOMI[0] + 3.5, xy, xy + XIAOMI[1], PISO, PISO + TOPE_ALTO))
    # Portabuzzer en la pared de adelante, con agujeros para el sonido
    bz = BUZZER_YZ
    c = unir(c, restar(cil_eje(7.5, (X_IN1 - 9, *bz), (X_IN1 + 0.1, *bz)), cil_eje(6.1, (X_IN1 - 10, *bz), (X_IN1, *bz))))
    c = restar(c, *[cil_eje(1.0, (X_IN1 - 1, bz[0] + dy, bz[1] + dz), (CAJA_X / 2 + 1, bz[0] + dy, bz[1] + dz))
                    for dy, dz in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3))])
    # Pared de atrás: interruptor de balancín de los servos (corte estándar 19,2 × 12,8), por encima del powerbank
    c = restar(c, caja(-CAJA_X / 2 - 1, X_IN0 + 1, LLAVE_Y - 9.6, LLAVE_Y + 9.6, LLAVE_Z, LLAVE_Z + 12.8))
    # Pared de atrás, del lado del hueco: dos bornes de panel (banana de 4 mm) para la fuente de laboratorio
    for y in BORNES_Y:
        c = restar(c, cil_eje(BORNE_AGUJERO / 2, (-CAJA_X / 2 - 1, y, BORNES_Z), (X_IN0 + 1, y, BORNES_Z)))
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
ESP_X = X_BAHIA + 16.0                      # plano de la placa de la ESP32 (parada, normal a X)
ESP_Y = (Y_ESP0, Y_ESP0 + 48.3)
ESP_Z0 = PISO + 5.0
ESP_Z1 = ESP_Z0 + 25.4
BUZZER_YZ = (35.0, 55.0)
LLAVE_Y, LLAVE_Z = 30.0, 48.0
BORNES_Y, BORNES_Z = (-45.0, -26.0), 35.0   # rojo y negro, 19 mm entre centros (la medida estándar de las bananas)
BORNE_AGUJERO = 8.0                         # agujero de montaje del borne (MEDIR el que compren)
BORNERA_POS = (X_BAHIA + 3, Y_IN0 + 1)      # esquina de la bornera de 6 V, donde estaba el regulador
CAP_XY = (X_BAHIA + 13, Y_IN0 + 1 + BORNERA6[1] + 12)
assert ESP_Y[1] + 4 < Y_IN1, "la ESP32 no entra en la bahía"
assert LLAVE_Z > PISO + XIAOMI[2] + 2, "el interruptor toca el powerbank"
assert max(BORNES_Y) + 6 < XIAOMI_POS[1], "los bornes chocan con el powerbank"
assert CAP_XY[1] + CAP[0] + 2 < ESP_Y[0] - 4, "el capacitor toca el soporte de la ESP32"


def base_componentes():
    xx, xy = XIAOMI_POS
    xiaomi = (cq.Workplane("XY").box(XIAOMI[0], XIAOMI[1], XIAOMI[2]).edges("|Z").fillet(10).val()
              .translate(V(xx + XIAOMI[0] / 2, xy + XIAOMI[1] / 2, PISO + XIAOMI[2] / 2)))
    bx, by = BORNERA_POS
    bornera = caja(bx, bx + BORNERA6[0], by, by + BORNERA6[1], PISO, PISO + BORNERA6[2])
    capacitor = cil(CAP[0], PISO, PISO + CAP[1], *CAP_XY)
    # Bornes de panel: el cuerpo afuera de la pared de atrás y el vástago roscado adentro (hacia el hueco libre)
    bornes = unir(*[unir(cil_eje(5.5, (-CAJA_X / 2 - 14, y, BORNES_Z), (-CAJA_X / 2, y, BORNES_Z)),
                         cil_eje(2.0, (X_IN0, y, BORNES_Z), (X_IN0 + 15, y, BORNES_Z))) for y in BORNES_Y])
    x = ESP_X
    esp = unir(caja(x - 0.8, x + 0.8, ESP_Y[0], ESP_Y[1], ESP_Z0, ESP_Z1),
               caja(x + 0.8, x + 3.2, ESP_Y[0] + 30, ESP_Y[0] + 46, ESP_Z0 + 6, ESP_Z1 - 6),     # módulo
               caja(x - 8.5, x - 0.8, ESP_Y[0] + 5, ESP_Y[0] + 43, ESP_Z0 + 0.5, ESP_Z0 + 3),    # pines
               caja(x - 8.5, x - 0.8, ESP_Y[0] + 5, ESP_Y[0] + 43, ESP_Z1 - 3, ESP_Z1 - 0.5))
    buzzer = cil_eje(6.0, (X_IN1 - 9.5, *BUZZER_YZ), (X_IN1, *BUZZER_YZ))
    llave = caja(-CAJA_X / 2 - 3, X_IN0 + 19, LLAVE_Y - 9.4, LLAVE_Y + 9.4, LLAVE_Z + 0.2, LLAVE_Z + 12.6)
    # Bornera de 5 V (2 polos): llega el cable USB-A del powerbank y sale el de 20 AWG a los pines de la Pi
    bornera5 = caja(X_IN1 - 9, X_IN1 - 1, Y_IN0 + 69, Y_IN0 + 81, PISO, PISO + 10)
    return xiaomi, bornera, capacitor, bornes, esp, buzzer, llave, bornera5


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
        xiaomi, bornera, capacitor, bornes, esp, buzzer, llave, bornera5 = base_componentes()
        add("powerbank_xiaomi_pb2020mi", xiaomi, cq.Color(0.75, 0.76, 0.78))
        add("bornera_6v", bornera, cq.Color(0.15, 0.35, 0.75))
        add("capacitor_2200uf", capacitor, cq.Color(0.1, 0.2, 0.5))
        add("bornes_fuente_6v", bornes, cq.Color(0.75, 0.1, 0.1))
        add("esp32c3", esp, cq.Color(0.1, 0.1, 0.12))
        add("porta_esp32", porta_esp32(), k3.COLOR_IMPRESO, True)
        add("buzzer", buzzer, cq.Color(0.1, 0.1, 0.1))
        add("interruptor", llave, cq.Color(0.8, 0.1, 0.1))
        add("bornera_5v", bornera5, cq.Color(0.1, 0.4, 0.2))
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
    ("Velcro adhesivo", 1, "≈ 100 × 20", "Debajo del powerbank (además de los topes)."),
    ("Bornes de panel para banana de 4 mm, rojo y negro", 2, "agujero ≈ Ø8", "Pared de atrás: entrada de la fuente."),
    ("Cable banana–banana (o banana–cocodrilo) 18 AWG", 2, "≈ 1 m", "Fuente de laboratorio → bornes (rojo y negro)."),
    ("Cable USB-A macho → 2 hilos (≥ 22 AWG) + bornera de 2 polos", 1, "8 × 12 × 10", "Salida USB-A del powerbank "
     "→ 5 V y GND hacia la Pi (el USB-A da 5 V sin negociar: no hace falta placa con 5,1 kΩ)."),
    ("Cable rojo/negro 20 AWG", "1 m", "—", "5 V de la Pi: de la base a la cabeza (cruza yaw, pitch y roll)."),
    ("Cable 18 AWG rojo/negro", "0,5 m", "—", "Bornes → interruptor → bornera de 6 V."),
    ("Alargues de servo macho-hembra", 2, "≈ 30 cm", "Pitch y roll hasta la ESP32 (cruzan el yaw)."),
    ("Cable USB-A acodado → micro-USB, flexible", 1, "≈ 50 cm", "Pi (en la cabeza) → ESP32 (en la base)."),
    ("Capacitor 2200 µF / 16 V + 100 nF", 1, "Ø13 × 25", "Bus de 6 V, en la bornera (modelado el electrolítico)."),
    ("Tornillo M3 × 8 autorroscante", 2, "M3", "Bornera de 6 V al piso de la caja (o cinta doble faz)."),
    ("2N2222 + 1 kΩ + 10 kΩ (+ 1N4148)", 1, "TO-92", "Buzzer desde el GPIO10."),
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
    L += ["=" * 96, "ALIMENTACIÓN", "=" * 96,
          "Fuente de laboratorio (externa, sobre la mesa): 6,0 V, límite de corriente 4–5 A (ideal ≥ 6 A) → bornes de "
          "la pared de atrás → interruptor → bornera de 6 V → los 3 servos",
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
