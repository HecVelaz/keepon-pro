"""Regresión (08/11): el botón HOME del panel no llevaba la cabeza a 0 0 0.

robot_vivo.py mandaba "HOME" directo a la ESP32, por fuera del árbitro: en el ciclo siguiente (25 ms) el
comportamiento dueño del cuello (Observador o seguimiento) mandaba su J y lo pisaba. Con un STOP enclavado,
además, la ESP32 rechazaba el HOME (STOP_ACTIVE). Ahora HOME es un comando del operador como STOP: detiene
el árbitro, manda RESUME + HOME y la cabeza se queda en HOME hasta RESUME.
"""
import sys
from pathlib import Path

import pytest

from keepon.arbiter import NECK
from keepon.synthetic import SynthPerson, const
from test_regresiones_codex import Rig

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from robot_vivo import comando  # noqa: E402


def lejos_de_home(rig, segundos):
    rig.run_until(rig.t + segundos)
    assert max(abs(v) for v in rig.link.neck_pos) > 10.0, "el escenario tiene que dejar el cuello lejos de HOME"


def en_home(rig):
    home = tuple(rig.cfg["neck"]["home"])
    return rig.link.neck_pos == pytest.approx(home, abs=1e-6) and rig.robot.act.ref == list(home)


def test_home_con_el_observador_barriendo():
    rig = Rig([])
    lejos_de_home(rig, 5.0)                       # barriendo hacia +45
    assert comando("home", rig.robot).startswith("HOME")
    rig.run_until(rig.t + 3.0)
    assert en_home(rig) and rig.owner(NECK) is None
    rig.run_until(rig.t + 5.0)                     # y se QUEDA ahí: nadie lo pisa
    assert en_home(rig) and rig.robot.en_home


def test_home_con_una_persona_siguiendola():
    rig = Rig([SynthPerson(1, appear=0.2, az=const(25.0))])
    lejos_de_home(rig, 9.0)                        # el Observador la encuentra y la sigue a 25°
    assert rig.owner(NECK) == "SEGUIMIENTO"
    rig.robot.home()
    rig.run_until(rig.t + 4.0)
    assert en_home(rig)                            # aunque la persona siga ahí


def test_home_con_el_stop_enclavado():
    rig = Rig([])
    lejos_de_home(rig, 5.0)
    rig.robot.stop()
    rig.run_until(rig.t + 1.0)
    rig.robot.home()                               # antes: ERR STOP_ACTIVE y no se movía
    rig.run_until(rig.t + 3.0)
    assert en_home(rig)


def test_resume_despues_de_home_vuelve_a_explorar():
    rig = Rig([])
    lejos_de_home(rig, 5.0)
    rig.robot.home()
    rig.run_until(rig.t + 3.0)
    rig.robot.resume()
    assert not rig.robot.en_home
    rig.run_until(rig.t + 4.0)
    assert rig.owner(NECK) == "OBSERVADOR" and abs(rig.link.neck_pos[0]) > 5.0


def test_stop_mientras_va_a_home_frena_ahi():
    rig = Rig([])
    lejos_de_home(rig, 5.0)
    rig.robot.home()
    rig.run_until(rig.t + 0.1)
    rig.robot.stop()                               # el STOP manda sobre el HOME
    assert not rig.robot.en_home and rig.robot.arb.stopped
    rig.run_until(rig.t + 3.0)
    assert not en_home(rig)                        # frenó a mitad de camino
