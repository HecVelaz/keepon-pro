"""scripts/panel_web.py: el panel del celular (lista cerrada de comandos, FIFO y servidor HTTP)."""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from panel_web import crear_handler, enviar, systemctl, validar  # noqa: E402

SONIDOS = {"R2D2": 1.6, "POLCA": 7.1, "PIROPO": 1.2}


def test_solo_comandos_permitidos():
    assert validar("t", SONIDOS) == "t"
    assert validar("  STOP ", SONIDOS) == "stop"
    assert validar("sonido polca", SONIDOS) == "sonido POLCA"
    assert validar(" Arrancar ", SONIDOS) == "arrancar"
    assert validar("parar", SONIDOS) == "parar"
    for malo in ("rm -rf /", "sonido NOEXISTE", "t; reboot", "sonido", "", "home now",
                 "arrancar; reboot", "restart", "parar keepon"):
        assert validar(malo, SONIDOS) is None, malo


def test_enviar_sin_robot_no_bloquea(tmp_path):
    fifo = tmp_path / "comandos"
    assert enviar("t", fifo) is False   # no existe
    os.mkfifo(fifo)
    assert enviar("t", fifo) is False   # existe pero nadie lo lee: no se queda esperando


class CtlFalso:
    """Hace de systemctl: anota las acciones y simula el estado del servicio keepon."""

    def __init__(self):
        self.acciones, self.estado, self.falla = [], "inactive", False

    def __call__(self, accion):
        self.acciones.append(accion)
        if accion == "is-active":
            return self.estado == "active", self.estado
        if self.falla:
            return False, "Unit keepon.service not found."
        self.estado = {"start": "activating", "stop": "deactivating"}[accion]
        return True, ""


@pytest.fixture
def servidor(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    ctl = CtlFalso()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), crear_handler(SONIDOS, run=run, ctl=ctl))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", run, ctl
    srv.shutdown()


def pedir(url, cuerpo=None):
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_pagina_y_estado(servidor):
    url, run, _ = servidor
    codigo, html = pedir(url + "/")
    assert codigo == 200 and b"Keepon" in html
    assert pedir(url + "/manifest.webmanifest")[0] == 200
    assert json.loads(pedir(url + "/estado")[1]) == {"vivo": False, "servicio": "inactive"}   # sin robot
    (run / "estado.json").write_text(json.dumps({"t": time.time(), "modo": "TIMIDO"}))
    d = json.loads(pedir(url + "/estado")[1])
    assert d["vivo"] and d["modo"] == "TIMIDO"


def test_no_sirve_archivos_fuera_del_panel(servidor):
    url, _, _ = servidor
    for ruta in ("/../panel_web.py", "/%2e%2e/panel_web.py", "/../../config.yaml"):
        assert pedir(url + ruta)[0] == 404, ruta


def test_comando_llega_al_fifo(servidor):
    url, run, _ = servidor
    assert pedir(url + "/comando", {"comando": "t"})[0] == 503   # robot apagado
    fifo = run / "comandos"
    os.mkfifo(fifo)
    fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)  # como robot_vivo.py
    codigo, cuerpo = pedir(url + "/comando", {"comando": "sonido polca"})
    assert codigo == 200 and json.loads(cuerpo) == {"enviado": "sonido POLCA"}
    assert os.read(fd, 100) == b"sonido POLCA\n"
    assert pedir(url + "/comando", {"comando": "reboot"})[0] == 400
    os.close(fd)


def test_encender_y_apagar_desde_el_celular(servidor):
    """Con el robot apagado no hay FIFO: arrancar/parar van a systemctl, no al robot."""
    url, run, ctl = servidor
    codigo, cuerpo = pedir(url + "/comando", {"comando": "arrancar"})
    assert codigo == 200 and json.loads(cuerpo) == {"enviado": "arrancar"}
    assert ctl.acciones == ["start"]
    assert json.loads(pedir(url + "/estado")[1])["servicio"] == "activating"
    assert pedir(url + "/comando", {"comando": "parar"})[0] == 200
    assert ctl.acciones[-1] == "stop"
    assert not (run / "comandos").exists()   # no tocó el FIFO


def test_encender_falla_y_lo_dice(servidor):
    url, _, ctl = servidor
    ctl.falla = True
    codigo, cuerpo = pedir(url + "/comando", {"comando": "arrancar"})
    assert codigo == 500 and "not found" in json.loads(cuerpo)["error"]


def test_systemctl_sin_shell_y_sin_bloquear(monkeypatch):
    """start/stop con --no-block (el pedido HTTP no espera los ~5 s del apagado); is-active sin él."""
    llamadas = []

    class R:
        returncode, stdout, stderr = 3, "inactive\n", ""

    def falso_run(args, **kw):
        llamadas.append((args, kw))
        return R()

    monkeypatch.setattr("panel_web.subprocess.run", falso_run)
    assert systemctl("is-active") == (False, "inactive")
    systemctl("start")
    assert llamadas[0][0] == ["systemctl", "--user", "is-active", "keepon"]
    assert llamadas[1][0] == ["systemctl", "--user", "--no-block", "start", "keepon"]
    assert all("shell" not in kw and kw["timeout"] <= 5 for _, kw in llamadas)
