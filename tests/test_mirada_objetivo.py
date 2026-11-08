"""05/11: mirada por objetivo (gaze.modo = objetivo) y Observador por miradas (observer.modo = miradas).

En el robot real, los tres servos vibraban moviéndose LENTO (quietos no): el control en velocidad hacía
avanzar la referencia de a poco en cada ciclo, y el barrido del Observador era una senoide lenta. Ahora la
referencia salta adonde hay que mirar, el firmware hace el movimiento con vmax/amax y después queda quieta.
"""
import copy

import pytest

from keepon import load_config
from keepon.arbiter import NECK
from keepon.gaze import GazeController
from keepon.robot import EventLog, Robot
from keepon.link import SimLink
from keepon.synthetic import SynthPerson, const
from keepon.world import Person, World
from test_regresiones_codex import DT, Rig

CFG = load_config()


def test_config_usa_los_modos_nuevos():
    assert CFG["gaze"]["modo"] == "objetivo"
    assert CFG["observer"]["modo"] == "miradas"


def correr(rig, t_fin):
    """Corre hasta t_fin y devuelve [(t, ref_yaw, pos_yaw, dueño del cuello)] en cada tick."""
    traza = []
    while rig.t < t_fin:
        rig.run_until(rig.t + DT)
        traza.append((rig.t, rig.robot.act.ref[0], rig.link.neck_pos[0], rig.owner(NECK)))
    return traza


def cambios(refs):
    return sum(1 for a, b in zip(refs, refs[1:]) if abs(a - b) > 1e-9)


def test_persona_quieta_la_referencia_queda_quieta():
    rig = Rig([SynthPerson(1, appear=0.2, az=const(15.0))])
    traza = correr(rig, 6.0)
    assert abs(rig.link.neck_pos[0] - 15.0) <= CFG["gaze"]["umbral_deg"][0]
    refs = [r for t, r, _, d in traza if t >= 3.0 and d == "SEGUIMIENTO"]
    assert refs and cambios(refs) == 0      # sin correcciones chicas: el cuello no se mueve


@pytest.mark.parametrize("latencia", [0.06, 0.15])
def test_el_atraso_de_la_percepcion_no_lo_hace_pasar(latencia):
    """Con el error de la imagen sumado a la posición del cuello AL SACAR LA FOTO, el atraso no importa.
    En modo velocidad, con 150 ms se pasaba ~4° de 25° y volvía."""
    rig = Rig([SynthPerson(1, appear=0.2, az=const(25.0))])
    rig.cam.latency = latencia
    traza = correr(rig, 8.0)  # desde el centro no la ve: la encuentra el Observador al pasar por +15 (~5 s)
    assert max(p for _, _, p, _ in traza) <= 25.0 + 1.0
    assert abs(rig.link.neck_pos[0] - 25.0) <= 1.0


def test_persona_que_camina_pocos_movimientos_firmes():
    rig = Rig([SynthPerson(1, appear=0.2, az=lambda t: 8.0 * t)])   # 8 °/s
    traza = correr(rig, 6.0)
    seg = [(t, r, p) for t, r, p, d in traza if d == "SEGUIMIENTO"]
    assert cambios([r for _, r, _ in seg]) < len(seg) / 6     # en velocidad cambiaba en cada tick
    assert abs(seg[-1][2] - 8.0 * seg[-1][0]) < 6.0           # y la sigue


def test_persona_mas_alla_del_limite_y_vuelve():
    """El objetivo se recorta al límite: si no, el cuello nunca "llega" y no vuelve a corregir."""
    hi = CFG["neck"]["limits"]["yaw"][1]

    def az(t):  # camina a 15 °/s hasta 15° más allá del límite, espera y vuelve caminando hasta 20°
        return min(15.0 * t, hi + 15.0) if t < 8.0 else max(20.0, hi + 15.0 - 15.0 * (t - 8.0))

    rig = Rig([SynthPerson(1, appear=0.2, az=az)])
    correr(rig, 7.5)
    assert abs(rig.robot.act.ref[0] - hi) < 1e-6
    correr(rig, 14.0)
    assert abs(rig.link.neck_pos[0] - 20.0) <= CFG["gaze"]["umbral_deg"][0]


def test_sin_posicion_del_cuello_sigue_en_velocidad():
    cfg = copy.deepcopy(CFG)
    cfg["gaze"]["mirar_abajo_deg"] = 0.0
    g = GazeController(cfg)
    w = World(0.0, 640, 480, 66.0)
    p = Person(1, 320 + 100, 240, 200)
    ref = g.update([0.0, 0.0, 0.0], p, w, 0.025, cuello=None)
    assert 0.0 < ref[0] < 1.0 and g.objetivo is None          # un pasito, como antes
    ref = g.update([0.0, 0.0, 0.0], p, w, 0.025, cuello=(0.0, 0.0, 0.0))
    assert ref[0] > 5.0                                        # con la posición: salta adonde está


def test_posicion_del_cuello_en_la_captura_interpola_la_historia():
    robot = Robot(CFG, SimLink(CFG, realtime=False), log=EventLog(to_file=False, echo=False))
    robot._historia.extend([(1.0, (0.0, 0.0, 0.0)), (2.0, (10.0, -4.0, 2.0))])
    assert robot._cuello_en(1.5) == (5.0, -2.0, 1.0)
    assert robot._cuello_en(3.0) == (10.0, -4.0, 2.0)          # más nuevo que la historia: la última
    assert robot._cuello_en(0.5) is None                       # más viejo: no se sabe


def test_observador_por_miradas_quieto_entre_una_y_otra():
    """08/11: entre una mirada y la otra, yaw va con la curva de mínimo jerk en transicion_s (sin saltos ni
    pasarse) y después queda QUIETO el resto de pausa_s (quieto no vibra)."""
    o = CFG["observer"]
    T, P = o["transicion_s"], o["pausa_s"]
    assert 0 < T < P
    rig = Rig([])
    traza = correr(rig, 0.5 + P * 4)
    refs = [(t, r) for t, r, _, d in traza if d == "OBSERVADOR"]
    assert all(r == 0.0 for t, r in refs if t < P)                 # al arrancar: quieto en el centro
    paso_max = max(abs(b[0] - a[0]) for a, b in zip(o["miradas"], o["miradas"][1:] + o["miradas"][:1]))
    v_pico = 1.875 * max(paso_max, 40.0) / T                      # mínimo jerk: pico 1,875·D/T
    saltos = [abs(b - a) / DT for (_, a), (_, b) in zip(refs, refs[1:])]
    assert max(saltos) <= v_pico * 1.05                            # sin saltos
    t0 = refs[0][0]
    for k in range(1, 4):                                          # en cada pausa, después de T: quieto
        quietos = {r for t, r in refs if t0 + k * P + T + 2 * DT <= t < t0 + (k + 1) * P - DT}
        assert len(quietos) == 1


def test_minimo_jerk_arranca_y_frena_sin_tirones():
    from keepon.behaviors import minimo_jerk
    assert minimo_jerk(0.0) == 0.0 and minimo_jerk(1.0) == 1.0 and minimo_jerk(-1) == 0.0 and minimo_jerk(2) == 1.0
    h = 1e-4
    d1 = lambda t: (minimo_jerk(t + h) - minimo_jerk(t - h)) / (2 * h)
    d2 = lambda t: (minimo_jerk(t + h) - 2 * minimo_jerk(t) + minimo_jerk(t - h)) / h ** 2
    assert abs(d1(h)) < 1e-6 and abs(d1(1 - h)) < 1e-6             # velocidad nula en los extremos
    assert abs(d2(2 * h)) < 0.05 and abs(d2(1 - 2 * h)) < 0.05     # y aceleración ~0 (el pico es 5,77): sin tirón
    assert abs(d1(0.5) - 1.875) < 1e-6                             # pico 1,875·D/T a la mitad
    assert all(minimo_jerk(a / 100) <= minimo_jerk((a + 1) / 100) for a in range(100))  # no se pasa


class _Act:
    """Actuadores de mentira: guarda la última referencia que manda el comportamiento."""

    def __init__(self, ref):
        self.ref = list(ref)

    def neck(self, g, yaw, pitch, roll):
        self.ref = [yaw, pitch, roll]


def _secuencia_observador(ref_inicial, pasos):
    """Posturas en las que el Observador se QUEDA (las de cada pausa, sin las intermedias de la transición), en
    orden, durante `pasos` pausas."""
    from types import SimpleNamespace

    from keepon.behaviors import Observer
    obs = Observer(CFG)
    ctx = SimpleNamespace(now=0.0, act=_Act(ref_inicial))
    obs.on_start(None, ctx)
    vistas = [tuple(ctx.act.ref)]
    while ctx.now < CFG["observer"]["pausa_s"] * pasos:
        fase, antes = obs.fase, tuple(ctx.act.ref)
        obs.act(None, ctx)
        if obs.fase != fase and vistas[-1] != antes:   # cambió de fase: la postura que sostenía
            vistas.append(antes)
        ctx.now += DT
    if vistas[-1] != tuple(ctx.act.ref):
        vistas.append(tuple(ctx.act.ref))
    return vistas


def test_observador_quieto_despues_centra_y_despues_explora():
    """07/11 (Tabla 1: "centra la vista y explora"): al perder a la persona se queda quieto donde quedó,
    después va al centro y recién ahí recorre las miradas, empezando por la más cercana al centro."""
    puntos = [tuple(p) for p in CFG["observer"]["miradas"]]
    vistas = _secuencia_observador((35.0, 10.0, 0.0), 4)
    cercana = min(puntos, key=lambda p: abs(p[0]))
    assert vistas[:3] == [(35.0, 10.0, 0.0), tuple(CFG["neck"]["home"]), cercana]


def test_observador_ya_centrado_empieza_por_el_centro():
    vistas = _secuencia_observador(tuple(CFG["neck"]["home"]), 2)
    assert vistas[0] == tuple(CFG["neck"]["home"])
    assert len(vistas) == 2                      # sin una pausa extra quieto en el mismo lugar


def test_observador_inclina_poco_el_roll_y_nunca_de_lado_a_lado():
    """Pequeñas variaciones de roll para encuadrar: chicas, y siempre pasando por 0 (un salto de +5 a −5 es
    un movimiento de 10° en el eje con más zona muerta)."""
    vistas = _secuencia_observador(tuple(CFG["neck"]["home"]), 2 + 2 * len(CFG["observer"]["miradas"]))
    rolls = [v[2] for v in vistas]
    assert any(r != 0 for r in rolls) and max(abs(r) for r in rolls) <= 6.0
    assert all(a * b >= 0 for a, b in zip(rolls, rolls[1:]))
