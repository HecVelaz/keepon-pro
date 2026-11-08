"""keepon/camiseta.py: reglas de Olimpia y Cerro, falsos positivos, filtro de 6 cuadros y evento en Eventos.

Las remeras son sintéticas, pintadas con los colores que midió la NoIR el 04/11 (config.yaml, sección camiseta),
con ruido. Incluyen la remera blanca lisa que nombra la guía y que todavía no se grabó.
"""

import cv2
import numpy as np
import pytest

from keepon import load_config
from keepon.camiseta import CERRO, OLIMPIA, OTRA, FiltroCamiseta, detectar
from keepon.eventos import Eventos
from keepon.perception import DetResult
from keepon.world import Person, World

CFG = load_config()

# Colores HSV (OpenCV) medidos con la NoIR
ROJO, AZUL, BLANCO, FRANJA, PIEL = (178, 200, 130), (130, 60, 45), (90, 10, 150), (160, 20, 45), (12, 90, 150)
HOMBROS = ((220.0, 150.0), (420.0, 150.0))  # 200 px de ancho: ~1,8 m


def kp(hombros=HOMBROS, vis=0.99):
    (xi, yi), (xd, yd) = hombros
    return {"nariz": (320, 90, 0.99), "hombro_i": (xi, yi, vis), "hombro_d": (xd, yd, vis)}


def remera(pintar, ruido=8, semilla=0):
    """Cuadro 640x480: fondo gris claro y el torso (desde los hombros hasta abajo) pintado con pintar(hsv, x1, x2,
    y1, y2), con ruido gaussiano. Devuelve BGR."""
    hsv = np.zeros((480, 640, 3), np.uint8)
    hsv[:] = (0, 0, 200)
    x1, x2, y1, y2 = 200, 440, 150, 480
    pintar(hsv, x1, x2, y1, y2)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR).astype(np.int16)
    bgr += np.random.default_rng(semilla).normal(0, ruido, bgr.shape).astype(np.int16)
    return np.clip(bgr, 0, 255).astype(np.uint8)


def lisa(color):
    def p(hsv, x1, x2, y1, y2):
        hsv[y1:y2, x1:x2] = color
    return p


def olimpia(hsv, x1, x2, y1, y2):
    hsv[y1:y2, x1:x2] = BLANCO
    hsv[y1 + 90:y1 + 170, x1:x2] = FRANJA                     # franja a la altura del pecho
    hsv[y1 + 110:y1 + 150, x1 + 80:x1 + 160] = BLANCO         # el logo blanco dentro de la franja


def cerro_mitades(hsv, x1, x2, y1, y2):
    m = (x1 + x2) // 2
    hsv[y1:y2, x1:m], hsv[y1:y2, m:x2] = ROJO, AZUL
    hsv[y1 + 120:y1 + 170, m - 60:m + 60] = BLANCO            # sponsor blanco en el medio


def cerro_rayas(hsv, x1, x2, y1, y2):
    for i, x in enumerate(range(x1, x2, 40)):
        hsv[y1:y2, x:x + 40] = ROJO if i % 2 == 0 else AZUL


def roja_arriba_azul_abajo(hsv, x1, x2, y1, y2):
    hsv[y1:y2, x1:x2] = AZUL
    hsv[y1:(y1 + y2) // 2 + 20, x1:x2] = ROJO


def blanca_con_sombra(hsv, x1, x2, y1, y2):
    """Blanca lisa con luz que cae de arriba: se oscurece hacia abajo, pero sin franja."""
    for y in range(y1, y2):
        hsv[y, x1:x2] = (90, 10, int(170 - 90 * (y - y1) / (y2 - y1)))


def blanca_y_brazos_cruzados(hsv, x1, x2, y1, y2):
    hsv[y1:y2, x1:x2] = BLANCO
    hsv[y1 + 150:y1 + 200, x1:x2] = PIEL                      # antebrazos de piel, no una franja negra


@pytest.mark.parametrize("pintar, esperada", [
    (olimpia, OLIMPIA),
    (cerro_mitades, CERRO),
    (cerro_rayas, CERRO),
])
def test_titulares(pintar, esperada):
    for semilla in range(3):
        assert detectar(remera(pintar, semilla=semilla), kp(), CFG).clase == esperada


@pytest.mark.parametrize("pintar", [
    lisa(ROJO), lisa(AZUL), lisa(BLANCO), lisa(FRANJA),       # lisas: roja, azul marino, BLANCA, negra
    blanca_con_sombra, blanca_y_brazos_cruzados, roja_arriba_azul_abajo,
], ids=["roja", "azul_marino", "blanca", "negra", "blanca_sombra", "blanca_brazos", "roja_y_azul_horizontal"])
def test_falsos_positivos(pintar):
    """La guía: una lisa roja o azul no es de Cerro, ni una blanca lisa es de Olimpia."""
    for semilla in range(3):
        assert detectar(remera(pintar, semilla=semilla), kp(), CFG).clase == OTRA


def test_olimpia_con_menos_luz():
    """Las reglas comparan brillos entre sí: con 30 % menos de luz la franja se sigue encontrando."""
    img = (remera(olimpia).astype(np.float32) * 0.7).astype(np.uint8)
    assert detectar(img, kp(), CFG).clase == OLIMPIA


def test_sin_torso_es_desconocida():
    img = remera(olimpia)
    assert detectar(img, kp(vis=0.2), CFG).clase is None                                  # hombros dudosos
    assert detectar(img, kp(((300, 150), (320, 150))), CFG).clase is None                  # muy lejos
    assert detectar(img, kp(((220, 470), (420, 470))), CFG).clase is None                  # torso fuera del cuadro


# ------------------------------------------------------------------ filtro de cuadros (T6 d)
def test_filtro_necesita_6_cuadros_seguidos():
    f = FiltroCamiseta(6, 6)
    assert [f.actualizar(OLIMPIA) for _ in range(6)] == [None] * 5 + [OLIMPIA]


def test_filtro_un_cuadro_suelto_no_cambia_nada():
    f = FiltroCamiseta(6, 6)
    for c in [CERRO] * 5 + [OTRA] + [CERRO] * 5:
        assert f.actualizar(c) is None
    for _ in range(6):
        f.actualizar(CERRO)
    for c in [OTRA] * 5 + [CERRO] + [OTRA] * 5:
        assert f.actualizar(c) == CERRO


def test_filtro_suelta_con_6_sin_camiseta():
    f = FiltroCamiseta(6, 6)
    for _ in range(6):
        f.actualizar(OLIMPIA)
    assert [f.actualizar(OTRA) for _ in range(6)] == [OLIMPIA] * 5 + [None]


def test_filtro_cuadros_sin_torso_no_cuentan():
    """Pose que no ve los hombros un instante (None) no suma ni resta."""
    f = FiltroCamiseta(6, 6)
    for c in [OLIMPIA] * 3 + [None] * 10 + [OLIMPIA] * 3:
        f.actualizar(c)
    assert f.activa == OLIMPIA
    for c in [OTRA] * 3 + [None] * 10 + [OTRA] * 2:
        f.actualizar(c)
    assert f.activa == OLIMPIA


# ------------------------------------------------------------------ evento en Eventos → World.shirt
def test_evento_camiseta_por_persona_y_en_el_log():
    log = []
    ev = Eventos(CFG, log=lambda t, m: log.append(m))
    caja = {1: (150, 40, 490, 480)}
    pose_kp = kp()

    def paso(n, clase):
        w = World.from_cfg(CFG, t=n * 0.1)
        w.persons[1] = Person(1, 320.0, 90.0, 400.0, last_seen=n * 0.1)
        det = DetResult("pose", n, 0.0, 0.0, 10.0, poses=[pose_kp], camisetas=[(clase, (0, 0, 1, 1))])
        return ev.aplicar(w, det, caja).persons[1].shirt

    assert [paso(n, CERRO) for n in range(6)] == [None] * 5 + [CERRO]
    assert "EVENTO CAMISETA_CERRO persona=1 SI" in log
    assert [paso(n, OTRA) for n in range(6, 12)] == [CERRO] * 5 + [None]
    assert "EVENTO CAMISETA_CERRO persona=1 NO" in log
