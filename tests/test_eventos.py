"""keepon/eventos.py: ME_MIRA sostenido y SALUDO con filtro temporal."""

import math

from keepon import load_config
from keepon.eventos import Eventos
from keepon.perception import DetResult
from keepon.world import Person, World

CFG = load_config()
E = CFG["eventos"]
CAJA = {1: (200, 50, 440, 470)}  # persona 1 en el centro de la imagen


def mundo(t, mira=False, ids=(1,)):
    w = World.from_cfg(CFG, t=t)
    for i in ids:
        w.persons[i] = Person(i, 320.0, 120.0, 400.0, looking=mira, last_seen=t)
    return w


def pose(frame, muneca_d=None, muneca_i=None, hombros=((280, 200), (360, 200))):
    """Pose de MediaPipe con hombros a 80 px de ancho; las muñecas que no se dan quedan abajo (cintura)."""
    (xi, yi), (xd, yd) = hombros
    kp = {"nariz": (320, 130, 0.99), "hombro_i": (xi, yi, 0.99), "hombro_d": (xd, yd, 0.99),
          "muneca_i": (*(muneca_i or (xi, 330)), 0.99), "muneca_d": (*(muneca_d or (xd, 330)), 0.99)}
    return DetResult("pose", frame, 0.0, 0.0, 10.0, poses=[kp])


def saludar(ev, t0, ciclos, frec=2.0, amp_px=40.0, hz=10.0, frame0=0):
    """La mano derecha arriba del hombro, oscilando de costado; devuelve (wave_count final, t final)."""
    t, n = t0, 0
    while t < t0 + ciclos / frec:
        x = 360 + amp_px * math.sin(2 * math.pi * frec * (t - t0))
        w = ev.aplicar(mundo(t), pose(frame0 + n, muneca_d=(x, 120)), CAJA)
        t, n = t + 1 / hz, n + 1
    return w.persons[1].wave_count, t, frame0 + n


# ------------------------------------------------------------------ ME_MIRA
def test_me_mira_necesita_estar_sostenido():
    ev = Eventos(CFG)
    assert ev.aplicar(mundo(0.0, mira=True)).persons[1].looking is False
    assert ev.aplicar(mundo(E["mira_sostenida_s"] - 0.05, mira=True)).persons[1].looking is False
    assert ev.aplicar(mundo(E["mira_sostenida_s"] + 0.01, mira=True)).persons[1].looking is True


def test_me_mira_un_cuadro_suelto_no_lo_prende_ni_lo_apaga():
    ev = Eventos(CFG)
    ev.aplicar(mundo(0.0, mira=True))
    ev.aplicar(mundo(0.2, mira=False))  # se interrumpe: vuelve a contar
    assert ev.aplicar(mundo(0.6, mira=True)).persons[1].looking is False
    assert ev.aplicar(mundo(1.2, mira=True)).persons[1].looking is True
    assert ev.aplicar(mundo(1.3, mira=False)).persons[1].looking is True   # un cuadro sin mirar: sigue
    assert ev.aplicar(mundo(1.35, mira=True)).persons[1].looking is True
    ev.aplicar(mundo(1.4, mira=False))
    assert ev.aplicar(mundo(1.4 + E["mira_suelta_s"] + 0.01, mira=False)).persons[1].looking is False


def test_me_mira_es_por_persona():
    ev = Eventos(CFG)
    w = World.from_cfg(CFG, t=0.0)
    for t in (0.0, 0.6):
        w = World.from_cfg(CFG, t=t)
        w.persons[1] = Person(1, 300, 100, 300, looking=True, last_seen=t)
        w.persons[2] = Person(2, 500, 100, 300, looking=False, last_seen=t)
        ev.aplicar(w)
    assert w.persons[1].looking and not w.persons[2].looking


# ------------------------------------------------------------------ SALUDO
def test_dos_ciclos_con_la_mano_arriba_es_un_saludo():
    ev = Eventos(CFG)
    count, _, _ = saludar(ev, 0.0, ciclos=2.2)
    assert count == 1


def test_un_solo_vaiven_no_alcanza():
    ev = Eventos(CFG)
    count, _, _ = saludar(ev, 0.0, ciclos=0.9)
    assert count == 0


def test_oscilacion_chica_no_es_saludo():
    ev = Eventos(CFG)
    amp = 0.4 * E["saludo_amp_hombros"] * 80  # pico a pico menor que la amplitud mínima
    count, _, _ = saludar(ev, 0.0, ciclos=3, amp_px=amp)
    assert count == 0


def test_mano_abajo_no_es_saludo():
    ev = Eventos(CFG)
    t, n = 0.0, 0
    while t < 2.0:  # oscila a la altura de la cintura
        x = 360 + 40 * math.sin(2 * math.pi * 2 * t)
        w = ev.aplicar(mundo(t), pose(n, muneca_d=(x, 330)), CAJA)
        t, n = t + 0.1, n + 1
    assert w.persons[1].wave_count == 0


def test_un_gesto_largo_es_un_solo_saludo_y_bajar_la_mano_rearma():
    ev = Eventos(CFG)
    count, t, n = saludar(ev, 0.0, ciclos=5)  # sigue saludando mucho rato
    assert count == 1
    for k in range(int(E["saludo_mano_abajo_s"] / 0.1) + 2):  # baja la mano
        ev.aplicar(mundo(t), pose(n + k), CAJA)
        t += 0.1
    count, _, _ = saludar(ev, t, ciclos=2.2, frame0=n + 100)
    assert count == 2


def test_la_misma_pose_no_cuenta_dos_veces():
    """El robot corre a 40 Hz y la pose llega a ~10 Hz: el mismo resultado se ve en varios ticks."""
    ev = Eventos(CFG)
    t = 0.0
    for n in range(25):
        x = 360 + 40 * math.sin(2 * math.pi * 2 * n / 10)
        for _ in range(4):  # cuatro ticks con la misma pose
            w = ev.aplicar(mundo(t), pose(n, muneca_d=(x, 120)), CAJA)
            t += 0.025
    assert w.persons[1].wave_count == 1


def test_la_pose_se_asocia_a_la_persona_que_la_contiene():
    ev = Eventos(CFG)
    cajas = {1: (0, 0, 200, 470), 2: (220, 50, 440, 470)}
    t, n = 0.0, 0
    while t < 1.2:
        x = 360 + 40 * math.sin(2 * math.pi * 2 * t)
        w = ev.aplicar(mundo(t, ids=(1, 2)), pose(n, muneca_d=(x, 120)), cajas)
        t, n = t + 0.1, n + 1
    assert w.persons[2].wave_count == 1 and w.persons[1].wave_count == 0
