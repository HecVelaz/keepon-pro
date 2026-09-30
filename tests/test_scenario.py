"""Escenario integrado de M0: todo el sistema en simulación."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sim_scenario import run  # noqa: E402


@pytest.fixture(scope="module")
def result():
    robot, trace = run(echo=False)
    return robot, trace, [m for _, m in robot.log.rows]


def test_never_two_owners(result):
    robot, _, _ = result
    assert robot.act.violations == 0


def test_expected_sequence(result):
    _, _, log = result
    seq = [m for m in log if m.startswith("ARB start")]
    order = [m.split()[2].split("#")[0] for m in seq]
    assert order[:5] == ["OBSERVADOR", "SEGUIMIENTO", "SALUDO", "SEGUIMIENTO", "CAMISETA"]
    assert any("CAMISETA" in m and "interrumpido por SALUDO" in m for m in log)  # saludo corta la polca


def test_same_gesture_not_answered_twice(result):
    _, _, log = result
    # Saludos en 8, 13.5 y 14 (este último dentro del saludo en curso) -> 2 respuestas.
    assert sum(1 for m in log if m.startswith("ARB start SALUDO")) == 2


def test_tracking_converges(result):
    _, trace, _ = result
    # Persona quieta de 10 a 16 s: error < 5 % del ancho y sin oscilación.
    errs = [r[6] for r in trace if 11.0 <= r[0] <= 16.0 and r[4] == "SEGUIMIENTO"]
    assert errs and max(abs(e) for e in errs) < 32
    yaws = [r[1] for r in trace if 11.0 <= r[0] <= 13.4]
    assert max(yaws) - min(yaws) < 0.5


def test_focus_switch_has_hysteresis(result):
    robot, _, _ = result
    t_switch = next(t for t, m in robot.log.rows if m == "FOCO 1 -> 2")
    assert t_switch >= 16.0 + 1.5 - 0.05


def test_stop_freezes_neck(result):
    _, trace, _ = result
    yaws = [r[1] for r in trace if 22.2 <= r[0] <= 23.0]
    assert max(yaws) - min(yaws) < 0.5
    assert all(r[4] == "-" for r in trace if 22.1 <= r[0] <= 23.0)
