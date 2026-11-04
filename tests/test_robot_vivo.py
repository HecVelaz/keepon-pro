"""scripts/robot_vivo.py: del resultado de la percepción al World que usa el robot."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from robot_vivo import mundo_desde  # noqa: E402

from keepon import load_config  # noqa: E402
from keepon.perception import DetResult, FaceObs, PersonObs  # noqa: E402


def test_sin_resultados_el_mundo_esta_vacio():
    w = mundo_desde(None, load_config(), t=3.0)
    assert w.t == 3.0 and not w.persons


def test_persona_con_rostro_usa_la_nariz_y_me_mira():
    cara = FaceObs(dev_deg=5.0, yaw_deg=2.0, pitch_deg=1.0, nose=(300.0, 150.0), looking=True)
    det = DetResult("personas", 1, 0.0, 0.0, 10.0, persons=[PersonObs(7, (250, 100, 350, 400), 0.9, cara)])
    w = mundo_desde(det, load_config(), t=5.0)
    p = w.persons[7]
    assert (p.u, p.v, p.size, p.looking) == (300.0, 150.0, 300.0, True)
    assert w.visible(7) is p  # last_seen = t: visible en este instante


def test_persona_sin_rostro_usa_la_altura_de_la_cabeza():
    det = DetResult("personas", 1, 0.0, 0.0, 10.0, persons=[PersonObs(3, (100, 50, 200, 450), 0.8)])
    p = mundo_desde(det, load_config(), t=1.0).persons[3]
    assert p.u == 150.0 and p.v == 50 + 0.12 * 400 and p.looking is False


def test_comandos_por_fifo_sin_bloquear(tmp_path, monkeypatch):
    import os
    import robot_vivo
    monkeypatch.setattr(robot_vivo.sys.stdin, "isatty", lambda: False, raising=False)
    c = robot_vivo.Comandos(tmp_path / "run" / "comandos")
    assert c.leer() == []  # nada escrito: no bloquea
    fd = os.open(tmp_path / "run" / "comandos", os.O_WRONLY | os.O_NONBLOCK)
    os.write(fd, b"t\nsonido PO")
    assert c.leer() == ["t"]          # la línea incompleta espera
    os.write(fd, b"LCA\n")
    os.close(fd)
    assert c.leer() == ["sonido POLCA"]
    assert c.leer() == []             # el que escribe cerró: sigue sin fin de archivo ni bloqueo
