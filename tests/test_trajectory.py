"""Trayectorias suaves: límites de velocidad, aceleración y posición."""

import pytest

from keepon.trajectory import Axis


def run(ax, secs, dt=0.01):
    vs, poss = [], []
    for _ in range(int(secs / dt)):
        ax.step(dt)
        vs.append(ax.vel)
        poss.append(ax.pos)
    return vs, poss


def test_reaches_target_without_overshoot():
    ax = Axis(-70, 70, vmax=180, amax=600)
    ax.set_target(60)
    vs, poss = run(ax, 2.0)
    assert ax.pos == pytest.approx(60)
    assert max(poss) <= 60 + 1e-6


def test_respects_vmax_and_amax():
    ax = Axis(-70, 70, vmax=180, amax=600)
    ax.set_target(-70)
    vs, _ = run(ax, 2.0)
    assert max(abs(v) for v in vs) <= 180 + 1e-6
    acc = [abs(b - a) / 0.01 for a, b in zip(vs, vs[1:])]
    assert max(acc) <= 600 + 1e-3


def test_retarget_mid_motion_is_smooth():
    ax = Axis(-70, 70, vmax=180, amax=600)
    ax.set_target(60)
    vs, _ = run(ax, 0.2)
    ax.set_target(-60)                 # cambio brusco de objetivo
    vs2, _ = run(ax, 1.0)
    allv = vs + vs2
    acc = [abs(b - a) / 0.01 for a, b in zip(allv, allv[1:])]
    assert max(acc) <= 600 + 1e-3      # sin saltos de velocidad


def test_target_clipped():
    ax = Axis(-20, 30, vmax=100, amax=300)
    assert ax.set_target(45) is True
    assert ax.target == 30
