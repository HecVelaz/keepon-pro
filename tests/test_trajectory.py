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


def test_target_clipped():
    ax = Axis(-20, 30, vmax=100, amax=300)
    assert ax.set_target(45) is True
    assert ax.target == 30
