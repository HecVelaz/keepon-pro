"""08/11: Observador en modo "exploracion", el de la Tabla 1 de la guía: "centra la vista y explora la escena:
barridos lentos, sacadas (cambios rápidos de mirada) a puntos de interés, pequeñas variaciones de roll para
encuadrar. Nada de movimiento aleatorio brusco".

Antes (modo "miradas") iba de punto en punto y se paraba en cada uno: se veía "para y gira, para y gira".
"""
from types import SimpleNamespace

from keepon import load_config
from keepon.behaviors import Observer

CFG = load_config()
E = CFG["observer"]["exploracion"]
HOME = tuple(CFG["neck"]["home"])
DT = 1 / 40  # lazo del robot (control.rate_hz)


class _Act:
    """Actuadores de mentira: guarda la última referencia que manda el comportamiento."""

    def __init__(self, ref):
        self.ref = list(ref)

    def neck(self, g, yaw, pitch, roll):
        self.ref = [yaw, pitch, roll]


def traza(ref_inicial, segundos):
    """[(t, (yaw, pitch, roll), tipo de tramo)] en cada tick del Observador."""
    obs = Observer(CFG)
    ctx = SimpleNamespace(now=0.0, act=_Act(ref_inicial))
    obs.on_start(None, ctx)
    out = []
    while ctx.now < segundos:
        obs.act(None, ctx)
        out.append((ctx.now, tuple(ctx.act.ref), obs.tramo.tipo))
        ctx.now += DT
    return out


def tramos(ref_inicial, segundos):
    """Tipos de los tramos en el orden en que se ejecutaron (uno por tramo, aunque dos seguidos sean iguales)."""
    obs = Observer(CFG)
    ctx = SimpleNamespace(now=0.0, act=_Act(ref_inicial))
    obs.on_start(None, ctx)
    out, ultimo = [], None
    while ctx.now < segundos:
        obs.act(None, ctx)
        if obs.tramo is not ultimo:
            out.append(obs.tramo.tipo)
            ultimo = obs.tramo
        ctx.now += DT
    return out


def test_config_usa_la_exploracion():
    assert CFG["observer"]["modo"] == "exploracion"


def test_centra_la_vista_y_barre_sin_pararse_en_el_medio():
    tr = traza(HOME, 20.0)
    quieto = [r for t, r, _ in tr if t < E["pausa_centro_s"] - DT]
    assert set(quieto) == {HOME}                                   # primero centrado y quieto
    # El primer barrido: del centro a −amp, continuo y sin detenerse antes de llegar
    barrido = [(t, r[0]) for t, r, tipo in tr if tipo == "suave" and t < E["pausa_centro_s"] + E["amp_deg"] / E["vel_barrido"]]
    yaws = [y for _, y in barrido]
    assert yaws[-1] < -0.9 * E["amp_deg"]
    pasos = [b - a for a, b in zip(yaws, yaws[1:])]
    assert all(p <= 1e-9 for p in pasos)                           # siempre hacia el mismo lado: no se pasa
    medio = pasos[len(pasos) // 5: -len(pasos) // 5]               # sin las puntas (ahí frena para dar la vuelta)
    assert all(abs(p) / DT > 0.4 * E["vel_barrido"] for p in medio)  # nunca se para en el medio


def test_barrido_lento_y_sin_saltos():
    tr = traza(HOME, 25.0)
    suaves = [(r, tipo) for _, r, tipo in tr]
    vel = [abs(b[0][0] - a[0][0]) / DT for a, b in zip(suaves, suaves[1:]) if a[1] == b[1] == "suave"]
    assert max(vel) <= 1.875 * E["vel_barrido"] * 1.05             # mínimo jerk: pico 1,875 · media
    assert max(vel) < 60.0                                          # "barridos lentos"


def test_sacadas_rapidas_a_los_puntos_de_interes_y_fija():
    tr = traza(HOME, 40.0)
    sacadas = [(t, r) for t, r, tipo in tr if tipo == "sacada"]
    assert sacadas, "en 40 s tiene que haber al menos una sacada"
    puntos = [(p[0], p[1], p[2] if len(p) > 2 else 0.0) for p in E["puntos_interes"]]
    assert {r for _, r in sacadas} <= set(puntos)
    # Rápida: la referencia salta (el firmware hace el movimiento con vmax/amax) y queda quieta fijacion_s
    i = next(k for k, (_, _, tipo) in enumerate(tr) if tipo == "sacada")
    assert abs(tr[i][1][0] - tr[i - 1][1][0]) > 10.0
    fija = next(k for k, (_, _, tipo) in enumerate(tr[i:]) if tipo != "sacada")
    assert fija * DT >= E["fijacion_s"] - DT                        # y la sostiene
    assert len({r for _, r, tipo in tr[i:i + fija]}) == 1
    # Cada sacada_cada barridos, una sacada (después de la cola inicial: quieto en el centro)
    t = tramos(HOME, 60.0)
    assert t[0] == "quieto"
    resto = t[1:]
    n = E["sacada_cada"]
    assert resto[:n + 1] == ["suave"] * n + ["sacada"]
    for k, tipo in enumerate(resto):
        if tipo == "sacada" and k + n < len(resto):
            assert resto[k + 1:k + 1 + n] == ["suave"] * n


def test_roll_chico_y_nunca_de_un_lado_al_otro():
    rolls = [r[2] for _, r, _ in traza(HOME, 60.0)]
    assert any(x != 0 for x in rolls) and max(abs(x) for x in rolls) <= 6.0
    distintos = [x for k, x in enumerate(rolls) if k == 0 or x != rolls[k - 1]]
    assert all(a * b >= 0 for a, b in zip(distintos, distintos[1:]))  # siempre pasa por 0


def test_despues_de_seguir_a_alguien_mira_ahi_y_centra_suave():
    """Al perder a la persona, el lugar donde estaba es un punto de interés: lo fija, después va al centro."""
    donde = (35.0, 8.0, 0.0)
    tr = traza(donde, E["fijacion_s"] + E["centrar_s"] + E["pausa_centro_s"])
    assert {r for t, r, _ in tr if t < E["fijacion_s"] - DT} == {donde}
    centrar = [r for _, r, tipo in tr if tipo == "suave"]
    assert max(abs(b[0] - a[0]) for a, b in zip(centrar, centrar[1:])) / DT < 1.875 * 35.0 / E["centrar_s"] * 1.05
    assert tr[-1][1] == HOME
