"""Modos de personalidad (T5): comando, confirmación con sonido y reacciones; y el evento SALIENDO."""

import sys
from pathlib import Path

from keepon import load_config
from keepon.eventos import Eventos
from keepon.link import SimLink
from keepon.robot import EventLog, Robot
from keepon.world import Person, World

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from robot_vivo import comando  # noqa: E402

CFG = load_config()
M = CFG["modos"]


class Banco:
    """Robot completo sobre el ESP32 simulado, con una persona puesta a mano en el mundo."""

    def __init__(self):
        self.link = SimLink(CFG, realtime=False)
        self.robot = Robot(CFG, self.link, log=EventLog(to_file=False, echo=False))
        self.w0 = World.from_cfg(CFG)
        self.sonidos: list[str] = []

    def correr(self, segundos, mira=False, saliendo=False, u=None, dt=0.025):
        fin = self.link.now() + segundos
        while self.link.now() < fin:
            t = self.link.now()
            w = World.from_cfg(CFG, t=t)
            w.persons[1] = Person(1, self.w0.cx if u is None else u, self.w0.cy, 350, looking=mira,
                                  leaving=saliendo, last_seen=t)
            self.robot.tick(w)
            s = self.link.esp.sound
            if s and (not self.sonidos or self.sonidos[-1] != s):
                self.sonidos.append(s)
            self.link.advance(dt)

    def log(self):
        return [m for _, m in self.robot.log.rows]


def test_comando_cambia_el_modo_y_confirma_con_sonido():
    b = Banco()
    b.correr(1.0)  # sesión abierta, siguiendo a la persona
    assert comando("t", b.robot) == "modo TIMIDO" and b.robot.modo == "TIMIDO"
    b.correr(0.5)
    assert "BEEP_TIMIDO" in b.sonidos
    assert comando("MODE atrevido", b.robot) == "modo ATREVIDO"
    b.correr(0.5)
    assert "BEEP_ATREVIDO" in b.sonidos
    assert any("OPERADOR modo TIMIDO -> ATREVIDO" in m for m in b.log())


def test_la_confirmacion_no_le_quita_el_cuello_al_seguimiento():
    b = Banco()
    b.correr(1.0)
    comando("m", b.robot)
    b.correr(0.2)
    assert b.robot.arb.owner["NECK"].behavior == "SEGUIMIENTO"
    assert b.robot.arb.owner["BUZZER"].behavior == "OPERADOR"


def test_comando_desconocido_muestra_la_ayuda_y_no_cambia_nada():
    b = Banco()
    assert "Comandos" in comando("xyz", b.robot) and b.robot.modo == M["inicial"]


def test_timido_desvia_la_mirada_y_vuelve_gradualmente():
    b = Banco()
    b.correr(1.0)
    comando("t", b.robot)
    b.correr(1.5, mira=True)  # lo mira: 0,5 s de ME_MIRA ya filtrado no aplica acá (looking directo)
    assert b.robot.arb.owner["NECK"].behavior == "MODO"
    assert abs(b.robot.act.ref[0]) > 0.8 * M["timido"]["desvio_yaw_deg"]   # desviado al costado
    assert b.robot.act.ref[1] < -0.8 * M["timido"]["desvio_pitch_deg"]      # y abajo
    b.correr(M["timido"]["sostener_s"] + M["timido"]["regreso_s"], mira=False)
    assert b.robot.arb.owner["NECK"].behavior == "SEGUIMIENTO"             # volvió a seguir
    assert abs(b.robot.act.ref[0]) < 3 and abs(b.robot.act.ref[1]) < 3


def test_atrevido_levanta_el_menton_sin_dejar_de_seguir_en_yaw():
    b = Banco()
    b.correr(1.0)
    comando("a", b.robot)
    pitch_max, yaw = 0.0, []
    for _ in range(int(M["atrevido"]["periodo_s"] / 0.05)):
        b.correr(0.05, mira=True, u=b.w0.cx + 120)  # la persona está a la derecha: el yaw tiene que ir hacia ella
        pitch_max = max(pitch_max, b.robot.act.ref[1])
        yaw.append(b.robot.act.ref[0])
    assert b.robot.arb.owner["NECK"].behavior == "MODO"
    assert pitch_max > 0.8 * M["atrevido"]["menton_deg"]  # mentón arriba
    assert yaw[-1] > yaw[0] + 1                           # sigue girando hacia la persona


def test_maleducado_piropo_una_vez_por_salida_y_cooldown_global():
    b = Banco()
    b.correr(1.0)
    comando("m", b.robot)
    b.correr(1.0)
    b.correr(2.0, saliendo=True)
    assert b.sonidos.count("PIROPO") == 1
    b.correr(1.0, saliendo=False)
    b.correr(2.0, saliendo=True)  # otra salida, pero dentro de los 40 s
    assert b.sonidos.count("PIROPO") == 1


def test_neutro_no_reacciona():
    b = Banco()
    b.correr(1.0)
    b.correr(3.0, mira=True, saliendo=True)
    assert b.robot.arb.owner["NECK"].behavior == "SEGUIMIENTO" and "PIROPO" not in b.sonidos


# ------------------------------------------------------------------ SALIENDO
def _mundo(t, u):
    w = World.from_cfg(CFG, t=t)
    w.persons[1] = Person(1, u, 240, 300, last_seen=t)
    return w


def test_saliendo_cerca_del_borde_y_alejandose():
    ev, t, u = Eventos(CFG), 0.0, 500.0
    while t < 1.0:
        w = ev.aplicar(_mundo(t, u), ref=(0, 0, 0))
        t, u = t + 0.05, u + 300 * 0.05  # 300 px/s hacia la derecha
    assert w.persons[1].leaving


def test_quieto_en_el_borde_no_es_saliendo():
    ev = Eventos(CFG)
    for k in range(20):
        w = ev.aplicar(_mundo(k * 0.05, 620.0), ref=(0, 0, 0))
    assert not w.persons[1].leaving


def test_saliendo_por_el_limite_de_yaw():
    ev = Eventos(CFG)
    hi = CFG["neck"]["limits"]["yaw"][1]
    for k in range(20):  # el cuello ya no puede girar más a la derecha y la persona sigue a la derecha
        w = ev.aplicar(_mundo(k * 0.05, 500.0), ref=(hi, 0, 0))
    assert w.persons[1].leaving
