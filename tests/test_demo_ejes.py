"""08/11: botón "Ejes" del panel (comando "ejes"): demostración de yaw, pitch y roll para el video.

Comando del operador (prioridad 0, sólo el cuello): recorre ejes.secuencia de config.yaml y vuelve a HOME;
después retoma el Observador o el seguimiento.
"""
import sys
from pathlib import Path

import pytest

from keepon.arbiter import NECK
from keepon.synthetic import SynthPerson, const
from test_regresiones_codex import DT, Rig

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from robot_vivo import comando  # noqa: E402


def duracion(cfg):
    e = cfg["ejes"]
    return sum(p[3] + e["pausa_s"] for p in e["secuencia"])


def correr_ejes(rig):
    """Pide los ejes y devuelve [(t, posición del cuello, ref, dueño del cuello)] hasta que termina (+1 s)."""
    assert comando("ejes", rig.robot).startswith("EJES (")
    traza, fin = [], rig.t + duracion(rig.cfg) + 1.0
    while rig.t < fin:
        rig.run_until(rig.t + DT)
        traza.append((rig.t, rig.link.neck_pos, tuple(rig.robot.act.ref), rig.owner(NECK)))
    return traza


def test_dura_unos_15_segundos():
    assert 12.0 <= duracion(Rig([]).cfg) <= 18.0          # la escena del video es de 15 s


def test_recorre_los_tres_ejes_y_vuelve_a_home():
    rig = Rig([])
    rig.run_until(3.0)                                     # el Observador ya está barriendo
    traza = correr_ejes(rig)
    durante = [p for _, p, _, d in traza if d == "EJES"]   # arranca desde donde estaba barriendo
    for y, p, r, _ in rig.cfg["ejes"]["secuencia"]:          # y la cabeza llega a cada postura
        assert any(pos == pytest.approx((y, p, r), abs=0.3) for pos in durante), f"no llegó a {y}/{p}/{r}"
    fin_ejes = max(k for k, (_, _, _, d) in enumerate(traza) if d == "EJES")
    assert traza[fin_ejes][2] == (0.0, 0.0, 0.0)         # la última referencia es HOME


def test_yaw_y_pitch_sin_saltos():
    rig = Rig([])
    rig.run_until(1.0)
    refs = [r for _, _, r, d in correr_ejes(rig) if d == "EJES"]
    for eje in (0, 1):                                     # el roll va con el perfil del firmware (salta)
        v = max(abs(b[eje] - a[eje]) / DT for a, b in zip(refs, refs[1:]))
        assert v < 120.0                                   # mínimo jerk: 60° en 1,8 s → pico 62 °/s


def test_al_terminar_vuelve_el_observador():
    rig = Rig([])
    rig.run_until(1.0)
    traza = correr_ejes(rig)
    assert traza[-1][3] == "OBSERVADOR"


def test_le_saca_el_cuello_al_seguimiento_y_se_lo_devuelve():
    rig = Rig([SynthPerson(1, appear=0.2, az=const(0.0))])
    rig.run_until(3.0)
    assert rig.owner(NECK) == "SEGUIMIENTO"
    traza = correr_ejes(rig)
    assert any(d == "EJES" for _, _, _, d in traza)
    rig.run_until(rig.t + 2.0)
    assert rig.owner(NECK) == "SEGUIMIENTO"


def test_desde_home_arranca_y_con_stop_no():
    rig = Rig([])
    rig.run_until(2.0)
    rig.robot.home()
    rig.run_until(4.0)
    assert any(d == "EJES" for _, _, _, d in correr_ejes(rig))   # HOME se reanuda solo
    rig.robot.stop()
    assert comando("ejes", rig.robot).startswith("EJES no")      # el STOP de seguridad, no
    rig.run_until(rig.t + 3.0)
    assert rig.owner(NECK) is None


def test_stop_durante_los_ejes_frena():
    rig = Rig([])
    rig.run_until(1.0)
    comando("ejes", rig.robot)
    rig.run_until(rig.t + 2.0)
    assert rig.owner(NECK) == "EJES"
    rig.robot.stop()
    assert rig.owner(NECK) is None and rig.robot.arb.stopped
