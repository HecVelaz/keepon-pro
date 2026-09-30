"""Regresiones de los fallos encontrados por Codex en la revisión de M0
(docs/REVISION_CODEX_M0.md). Cada test reproduce el escenario que fallaba."""

import pytest

from keepon import load_config
from keepon.arbiter import BUZZER, NECK
from keepon.gaze import Focus
from keepon.link import SimLink
from keepon.protocol import ProtocolError, parse_reply
from keepon.robot import EventLog, Robot
from keepon.sim_esp32 import SimESP32
from keepon.synthetic import SynthCamera, SynthPerson, const
from keepon.world import Person, World

DT = 1 / 40


class Rig:
    """Robot + ESP32 simulado + cámara sintética en tiempo simulado."""

    def __init__(self, persons):
        self.cfg = load_config()
        self.link = SimLink(self.cfg, realtime=False)
        self.robot = Robot(self.cfg, self.link, log=EventLog(to_file=False, echo=False))
        self.cam = SynthCamera(self.cfg, persons)
        self.t = 0.0

    def run_until(self, t_end, world_age=0.0):
        while self.t < t_end:
            self.robot.tick(self.cam.observe(self.t, self.link.neck_pos), world_age)
            self.link.advance(DT)
            self.t += DT

    def owner(self, r):
        g = self.robot.arb.owner[r]
        return g.behavior if g else None

    @property
    def log(self):
        return [m for _, m in self.robot.log.rows]


# 1. Reinicio del ESP32 durante la polca -------------------------------------------
def test_esp32_reboot_resyncs():
    rig = Rig([SynthPerson(1, appear=0.5, az=const(10.0), shirt=[(1.0, 99, "OLIMPIA")])])
    rig.run_until(2.0)
    assert rig.owner(BUZZER) == "CAMISETA" and rig.link.esp.sound == "POLCA"
    rig.link.esp.reboot()
    rig.run_until(rig.t + DT)                            # el ciclo que detecta el reinicio
    assert rig.owner(BUZZER) is None                     # la Pi ya no cree que suena la polca
    assert rig.robot.act.ref == rig.cfg["neck"]["home"]  # referencia reconciliada con HOME
    assert not rig.robot.act.session                     # nada se comanda hasta reabrir sesión
    assert "ESP32 se REINICIÓ" in rig.log
    rig.run_until(3.5)
    assert rig.robot.act.session and rig.owner(NECK) == "SEGUIMIENTO"  # recupera el seguimiento
    assert rig.robot.act.violations == 0


def test_operator_stop_survives_reboot():
    rig = Rig([SynthPerson(1, appear=0.5, az=const(10.0))])
    rig.run_until(1.0)
    rig.robot.stop()
    rig.link.esp.reboot()
    rig.run_until(2.0)
    assert rig.link.esp.state == "STOPPED"


# 2. Mensajes mal formados ----------------------------------------------------------
@pytest.mark.parametrize("line", ["HELLO abc", "HELLO", "HELLO 1 2", "J", "S -1 R2D2"])
def test_bad_commands_never_raise(line):
    esp = SimESP32(load_config())
    esp.read()
    esp.feed(line)
    assert esp.read()[0].name == "ERR"


def test_hello_wrong_version_rejected():
    esp = SimESP32(load_config())
    esp.read()
    esp.feed("HELLO 9")
    assert esp.read()[0].args == ("BAD_VERSION",)


@pytest.mark.parametrize("line", ["ACK abc", "ACK 1 FOO", "STATE 1", "STATE 1 RUN 1 2 3", "STATE 1 X 1 2 3 NONE",
                                  "STATE 1 RUN nan 0 0 NONE", "HELLO 0 a b", "DONE", "FOO 1"])
def test_bad_replies_rejected(line):
    with pytest.raises(ProtocolError):
        parse_reply(line)


def test_good_replies_parse():
    assert parse_reply("STATE 3 RUN 1.5 -2.0 0.0 POLCA").args == ("RUN", 1.5, -2.0, 0.0, "POLCA")
    assert parse_reply("ACK 4 CLIPPED").args == ("CLIPPED",)


# 3. Cambio de camiseta a mitad de la polca -----------------------------------------
def test_episodic_params_frozen():
    rig = Rig([SynthPerson(1, appear=0.5, az=const(5.0),
                           shirt=[(1.0, 2.0, "OLIMPIA"), (2.0, 99, "CERRO")])])
    rig.run_until(1.1)
    rig.run_until(1.0 + 3.2)  # antes el timeout usaba la duración del ABUCHEO (2,5 s)
    assert rig.owner(BUZZER) == "CAMISETA" and rig.link.esp.sound == "POLCA"
    assert rig.robot.arb.owner[BUZZER].params["sound"] == "POLCA"


# 4. Deduplicación de sonidos --------------------------------------------------------
def test_old_sound_seq_not_replayed():
    esp = SimESP32(load_config())
    for line in ("S 10 POLCA", "S 11 ABUCHEO", "S 10 POLCA"):
        esp.feed(line)
    assert esp.sound == "ABUCHEO"


# 5. Foco: quien mira tiene prioridad estricta ---------------------------------------
def test_looker_always_wins_after_hysteresis():
    cfg = load_config()
    f = Focus(cfg)
    w = World(0.0, 640, 480, 66.0)
    w.persons[1] = Person(1, 320, 240, 480, looking=False, last_seen=0.0)  # grande y centrado
    f.update(w)
    assert f.target == 1
    for i in range(1, 100):
        w.t = i * 0.05
        w.persons[1].last_seen = w.t
        w.persons[2] = Person(2, 630, 240, 30, looking=True, last_seen=w.t)  # chico, en el borde, mira
        f.update(w)
    assert f.target == 2


# 6. Percepción caída: no seguir un mundo congelado -----------------------------------
def test_stale_world_releases_target():
    rig = Rig([SynthPerson(1, appear=0.2, az=const(15.0))])
    rig.run_until(1.0)
    assert rig.owner(NECK) == "SEGUIMIENTO"
    frozen = rig.cam.observe(rig.t, rig.link.neck_pos)
    for i in range(80):  # 2 s entregando SIEMPRE el mismo mundo, cada vez más viejo
        rig.robot.tick(frozen, world_age=(i + 1) * DT)
        rig.link.advance(DT)
    assert any(m.startswith("PERCEPCION sin datos") for m in rig.log)
    assert rig.robot.focus.target is None and rig.owner(NECK) == "OBSERVADOR"
