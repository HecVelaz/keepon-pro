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


def test_apagar_lleva_a_home_aunque_haya_stop():
    """Regresión (04/11): con el STOP enclavado, "Apagar" mandaba HOME, la ESP32 lo rechazaba
    (ERR STOP_ACTIVE) y la cabeza quedaba donde estaba. Además, sin esperar, el watchdog de 500 ms
    puede cortar la vuelta a medio camino."""
    from robot_vivo import ir_a_home_y_esperar
    from keepon import load_config
    from keepon.link import SimLink

    cfg = load_config()
    home = cfg["neck"]["home"]

    def lejos_y_en_stop():
        link = SimLink(cfg, realtime=False)
        link.hello()
        link.advance(0.1)
        link.poll()
        link.send("J", 60.0, 25.0, -15.0)
        for _ in range(100):          # 2,5 s con keepalive: llega a la postura lejana
            link.poll()
            link.advance(0.025)
        link.send("STOP")
        link.advance(0.1)
        return link

    # Como antes: HOME solo, con el STOP enclavado → rechazado, la cabeza no se mueve.
    link = lejos_y_en_stop()
    link.send("HOME")
    link.advance(2.0)
    assert any(r.name == "ERR" and "STOP_ACTIVE" in r.args for r in link.poll())
    assert max(abs(a - h) for a, h in zip(link.neck_pos, home)) > 5.0

    # Ahora: llega a HOME.
    link = lejos_y_en_stop()
    assert ir_a_home_y_esperar(link, home, dormir=link.advance)
    assert max(abs(a - h) for a, h in zip(link.neck_pos, home)) < 1.0
