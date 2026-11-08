"""SerialLink con espejo: el SimESP32 local sigue al ESP32 real y se corrige con sus STATE.

El "ESP32 real" es otro SimESP32 detrás de un puerto serie falso que avanza con el mismo reloj.
"""

import sys
import types

import pytest

from keepon import load_config
from keepon.link import SerialLink
from keepon.sim_esp32 import SimESP32


class Reloj:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class PuertoFalso:
    """Hace de pyserial: lo escrito va a un SimESP32 que avanza con el reloj compartido."""

    def __init__(self, reloj, esp):
        self.reloj, self.esp, self.t = reloj, esp, reloj()
        self.salida = b""

    def _avanzar(self):
        while self.t + 0.01 <= self.reloj() + 1e-9:
            self.esp.tick(0.01)
            self.t += 0.01
        self.salida += "".join(r.encode() for r in self.esp.read()).encode()

    def write(self, datos):
        self._avanzar()
        for linea in datos.decode().splitlines():
            self.esp.feed(linea)
        self._avanzar()

    @property
    def in_waiting(self):
        self._avanzar()
        return len(self.salida)

    def read(self, n):
        datos, self.salida = self.salida[:n], self.salida[n:]
        return datos


@pytest.fixture
def armar(monkeypatch):
    def _armar(real: SimESP32):
        reloj = Reloj()
        monkeypatch.setattr("keepon.link.time.monotonic", reloj)
        puerto = PuertoFalso(reloj, real)
        monkeypatch.setitem(sys.modules, "serial", types.SimpleNamespace(Serial=lambda *a, **k: puerto))
        link = SerialLink("falso", espejo_cfg=load_config())
        return link, reloj

    return _armar


def correr(link, reloj, segundos, paso=0.025):
    for _ in range(round(segundos / paso)):
        reloj.t += paso
        link.poll()


def test_espejo_sigue_al_real(armar):
    real = SimESP32(load_config())
    link, reloj = armar(real)
    link.hello()
    correr(link, reloj, 0.2)
    link.send("J", 40.0, 15.0, -10.0)
    for _ in range(60):  # mientras se mueve, el espejo da la misma posición que el "firmware"
        correr(link, reloj, 0.05)
        assert max(abs(a - b) for a, b in zip(link.neck_pos, real.neck.pos)) < 0.5
    assert link.neck_pos == pytest.approx((40.0, 15.0, -10.0))
    assert link.max_desvio < 0.5 and link.resyncs == 0


def test_espejo_adopta_la_posicion_real_si_arranca_fuera_de_home(armar):
    real = SimESP32(load_config())
    for eje, v in zip(real.neck.axes.values(), (30.0, 10.0, 5.0)):  # quedó ahí de una sesión anterior
        eje.fijar(v)
    link, reloj = armar(real)
    link.hello()
    correr(link, reloj, 0.5)  # llegan STATE por los PING de keepalive
    assert link.resyncs >= 1
    assert link.neck_pos == pytest.approx((30.0, 10.0, 5.0), abs=0.2)


def test_espejo_se_reinicia_con_el_real(armar):
    real = SimESP32(load_config())
    link, reloj = armar(real)
    link.hello()
    link.send("J", 50.0, 0.0, 0.0)
    correr(link, reloj, 1.5)
    real.reboot()  # p. ej. un corte del USB o de la alimentación de la ESP32
    correr(link, reloj, 0.1)
    assert link.neck_pos == pytest.approx(tuple(load_config()["neck"]["home"]))
