"""Trayectorias suaves. Se verifican las POSICIONES emitidas (lo que ve el servo),
no la variable interna de velocidad."""

import random

import pytest

from keepon.trajectory import Axis

DT = 0.01


def kinematics(pos):
    v = [(b - a) / DT for a, b in zip(pos, pos[1:])]
    acc = [(b - a) / DT for a, b in zip(v, v[1:])]
    return max(abs(x) for x in v), max(abs(x) for x in acc)


def run(ax, steps, pos=None):
    pos = pos if pos is not None else [ax.pos]
    for _ in range(steps):
        ax.step(DT)
        pos.append(ax.pos)
    return pos


@pytest.mark.parametrize("target", [20.0, -70.0, 0.3, 55.5, 69.9])
def test_reaches_target_exactly_within_limits(target):
    ax = Axis(-70, 70, vmax=180, amax=600)
    ax.set_target(target)
    pos = run(ax, 300)
    vmax, amax = kinematics(pos)
    assert ax.pos == pytest.approx(target, abs=1e-9)
    assert vmax <= 180 + 1e-6 and amax <= 600 + 1e-6
    assert max(pos) <= max(target, 0) + 1e-9 and min(pos) >= min(target, 0) - 1e-9  # sin sobrepaso


def test_random_retargets_and_brakes_never_exceed_limits():
    rng = random.Random(1)
    ax = Axis(-70, 70, vmax=180, amax=600)
    pos = [ax.pos]
    for i in range(3000):
        if i % 37 == 0:
            ax.set_target(rng.uniform(-70, 70))
        if i % 500 == 250:
            ax.target = ax.brake_target()
        run(ax, 1, pos)
    vmax, amax = kinematics(pos)
    assert vmax <= 180 + 1e-6 and amax <= 600 + 1e-6


def test_brake_stops_without_hitting_amax():
    ax = Axis(-70, 70, vmax=180, amax=600)
    ax.set_target(70)
    pos = run(ax, 25)
    ax.target = ax.brake_target()
    run(ax, 100, pos)
    assert kinematics(pos)[1] <= 600 + 1e-6
    assert ax.vel == 0 or abs(ax.vel) < 1e-9
    assert ax.pos == ax.target


def test_target_clipped():
    ax = Axis(-20, 30, vmax=100, amax=300)
    assert ax.set_target(45) is True
    assert ax.target == 30


# ------------------------------------------------------------------ curva S (promedio de N pasos del trapecio)
def jerk(pos):
    v = [(b - a) / DT for a, b in zip(pos, pos[1:])]
    acc = [(b - a) / DT for a, b in zip(v, v[1:])]
    return max(abs(b - a) / DT for a, b in zip(acc, acc[1:]))


@pytest.mark.parametrize("target", [25.0, -70.0, 0.3, 55.5, 69.9])
def test_curva_s_llega_exacta_sin_pasar_vmax_amax_ni_jerk(target):
    ax = Axis(-70, 70, vmax=180, amax=600, ventana=10)
    ax.set_target(target)
    pos = run(ax, 300)
    vmax, amax = kinematics(pos)
    assert ax.pos == target                       # exacto, no "casi"
    assert vmax <= 180 + 1e-6 and amax <= 600 + 1e-6
    assert jerk(pos) <= 2 * 600 / 0.1 + 1e-3      # 2·amax / ventana: la aceleración cambia en rampa
    assert max(pos) <= max(target, 0) + 1e-9 and min(pos) >= min(target, 0) - 1e-9


def test_curva_s_suaviza_el_trapecio():
    """Mismo movimiento con y sin curva S: el trapecio cambia la aceleración de golpe en un paso (25° de yaw:
    70000 °/s³), la curva S lo reparte en 0,1 s (≤ 2·amax/ventana = 12000). El movimiento dura 0,1 s más."""
    duros, suaves = Axis(-70, 70, 180, 600), Axis(-70, 70, 180, 600, ventana=10)
    for ax in (duros, suaves):
        ax.set_target(25.0)
    p_duro, p_suave = run(duros, 100), run(suaves, 100)
    assert jerk(p_duro) > 50000 and jerk(p_suave) <= 12000 + 1e-3
    llega = [next(k for k, x in enumerate(p) if x == 25.0) for p in (p_duro, p_suave)]
    assert llega[1] - llega[0] == 9               # 0,1 s más (la ventana menos el paso en que ya llegaba)


def test_curva_s_reobjetivos_y_frenadas_al_azar():
    """Cambios de objetivo en pleno movimiento (seguimiento) y STOP: siempre dentro de límites y sin pasar
    vmax/amax; el jerk queda en 2·amax/ventana."""
    rng = random.Random(2)
    ax = Axis(-70, 70, vmax=180, amax=600, ventana=10)
    pos = [ax.pos]
    for i in range(3000):
        if i % 23 == 0:
            ax.set_target(rng.uniform(-80, 80))
        if i % 500 == 250:
            ax.target = ax.brake_target()
        run(ax, 1, pos)
    vmax, amax = kinematics(pos)
    assert vmax <= 180 + 1e-6 and amax <= 600 + 1e-6
    assert jerk(pos) <= 2 * 600 / 0.1 + 1e-3
    assert -70 <= min(pos) and max(pos) <= 70


def test_curva_s_frenada_sin_golpe():
    ax = Axis(-70, 70, vmax=180, amax=600, ventana=10)
    ax.set_target(70)
    pos = run(ax, 25)
    ax.target = ax.brake_target()
    run(ax, 100, pos)
    assert kinematics(pos)[1] <= 600 + 1e-6 and jerk(pos) <= 2 * 600 / 0.1 + 1e-3
    assert ax.pos == ax.target and pos[-1] == pos[-2]   # quieta


def test_fijar_deja_quieto_en_la_posicion():
    """Resincronización del espejo (link.py): plan, ventana y salida en el mismo lugar, sin movimiento."""
    ax = Axis(-70, 70, vmax=180, amax=600, ventana=10)
    ax.set_target(50)
    run(ax, 20)
    ax.fijar(12.0)
    assert run(ax, 50)[1:] == [12.0] * 50


def test_suavizado_mas_largo_que_el_firmware_se_rechaza():
    from keepon.trajectory import pasos_ventana
    assert pasos_ventana(0.0) == 1 and pasos_ventana(0.1) == 10
    with pytest.raises(ValueError):
        pasos_ventana(0.6)
