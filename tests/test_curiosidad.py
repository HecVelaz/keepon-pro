"""Inclinación de curiosidad (T3 d) dentro del SEGUIMIENTO."""

from types import SimpleNamespace

from keepon import load_config
from keepon.behaviors import Tracking
from keepon.world import Person, World

CFG = load_config()
CFG["gaze"]["mirar_abajo_deg"] = 0.0  # estos tests ponen la cara en el centro óptico
C = CFG["curiosidad"]


class ActFalso:
    """Lo mínimo de Actuators: la referencia, el comando de cuello y el log."""

    def __init__(self):
        self.ref, self.logs = [0.0, 0.0, 0.0], []

    def neck(self, g, y, p, r):
        self.ref = [y, p, r]

    def log(self, t, m):
        self.logs.append((t, m))


def correr(tr, act, t0, t1, u_de_t, dt=0.025):
    """Persona 1 visible en (u(t), cy); devuelve el roll comandado en cada tick."""
    g = SimpleNamespace(person=1)
    rolls, t = [], t0
    while t < t1:
        w = World.from_cfg(CFG, t=t)
        w.persons[1] = Person(1, u_de_t(t), w.cy, 300, last_seen=t)
        tr.act(g, SimpleNamespace(now=t, dt=dt, world=w, act=act))
        rolls.append((t, act.ref[2]))
        t += dt
    return rolls


def centrado(t):
    return World.from_cfg(CFG).cx


def test_quieto_inclina_sostiene_y_vuelve():
    tr, act = Tracking(CFG), ActFalso()
    rolls = correr(tr, act, 0.0, C["quieto_s"] + C["sostener_s"] + 1.0, centrado)
    antes = [r for t, r in rolls if t < C["quieto_s"] - 0.1]
    durante = [r for t, r in rolls if C["quieto_s"] + 0.1 < t < C["quieto_s"] + C["sostener_s"] - 0.1]
    despues = [r for t, r in rolls if t > C["quieto_s"] + C["sostener_s"] + 0.1]
    assert all(r == 0 for r in antes)
    assert durante and all(abs(r) == C["amp_deg"] for r in durante)
    assert despues and all(r == 0 for r in despues)
    assert any("inclina" in m for _, m in act.logs) and any("vuelve a 0" in m for _, m in act.logs)


def test_si_se_mueve_vuelve_enseguida():
    tr, act = Tracking(CFG), ActFalso()
    cx = World.from_cfg(CFG).cx
    t_mueve = C["quieto_s"] + 0.5
    rolls = correr(tr, act, 0.0, t_mueve + 1.0, lambda t: cx if t < t_mueve else cx + 250)
    assert any(abs(r) == C["amp_deg"] for t, r in rolls if t < t_mueve)
    assert rolls[-1][1] == 0
    assert any("se movió" in m for _, m in act.logs)


def test_persona_que_camina_no_inclina():
    tr, act = Tracking(CFG), ActFalso()
    cx = World.from_cfg(CFG).cx
    rolls = correr(tr, act, 0.0, 6.0, lambda t: cx + 150 + 60 * t)  # siempre lejos del centro
    assert all(r == 0 for _, r in rolls)


def test_espera_y_alterna_el_lado():
    tr, act = Tracking(CFG), ActFalso()
    total = 2 * (C["quieto_s"] + C["sostener_s"]) + C["espera_s"] + 1.0
    rolls = correr(tr, act, 0.0, total, centrado)
    inclinaciones = [m for _, m in act.logs if "inclina" in m]
    assert len(inclinaciones) == 2
    assert "+15" in inclinaciones[0] and "-15" in inclinaciones[1]
    # Entre la primera y la segunda pasan al menos sostener + espera
    t_incl = [t for t, m in act.logs if "inclina" in m]
    assert t_incl[1] - t_incl[0] >= C["sostener_s"] + C["espera_s"] - 0.05


def test_interrumpida_queda_en_el_log_y_espera():
    tr, act = Tracking(CFG), ActFalso()
    correr(tr, act, 0.0, C["quieto_s"] + 0.5, centrado)  # quedó inclinada
    t = C["quieto_s"] + 0.5
    tr.on_cancel(SimpleNamespace(person=1), SimpleNamespace(now=t, act=act))  # p. ej. un SALUDO toma el cuello
    assert any("interrumpida" in m for _, m in act.logs)
    tr.on_start(SimpleNamespace(person=1), SimpleNamespace(now=t))
    rolls = correr(tr, act, t, t + C["quieto_s"] + 0.5, centrado)  # quieto otra vez, pero dentro de la espera
    assert all(r == 0 for _, r in rolls)


def test_regresion_cabeza_que_oscila_alrededor_de_una_persona_quieta():
    """03/11, robot real: el seguimiento oscila un poco y el error del control salía de ±4° todo el tiempo,
    así que nunca se inclinaba. Lo que tiene que estar quieto es la persona, no el error."""
    import math
    tr, act = Tracking(CFG), ActFalso()
    w0 = World.from_cfg(CFG)
    g, t, dt, rolls = SimpleNamespace(person=1), 0.0, 0.025, []
    while t < C["quieto_s"] + 1.0:
        act.ref[0] = 6.0 * math.sin(2 * math.pi * 1.5 * t)  # la cabeza oscila ±6° (yaw)
        w = World.from_cfg(CFG, t=t)
        u = w0.cx + w0.fx * math.tan(math.radians(0.0 - act.ref[0]))  # persona quieta en yaw 0
        w.persons[1] = Person(1, u, w.cy, 300, last_seen=t)
        tr.act(g, SimpleNamespace(now=t, dt=dt, world=w, act=act))
        rolls.append(act.ref[2])
        t += dt
    assert any(abs(r) == C["amp_deg"] for r in rolls)
