"""Protocolo serie + simulador del ESP32 (especificación del firmware)."""

import pytest

from keepon import load_config
from keepon.protocol import Command, ProtocolError, parse_command, parse_reply
from keepon.sim_esp32 import SimESP32


@pytest.fixture
def esp():
    e = SimESP32(load_config())
    e.read()  # descarta HELLO de arranque
    return e


def names(replies):
    return [(r.name, r.seq, r.args) for r in replies]


def test_roundtrip():
    c = Command("J", 7, (10.0, -5.0, 0.0))
    assert c.encode() == "J 7 10.0 -5.0 0.0\n"
    assert parse_command(c.encode()) == c


@pytest.mark.parametrize("line,reason", [
    ("", "EMPTY"), ("X 1", "UNKNOWN_CMD"), ("J 1 1 2", "BAD_ARGS"), ("J a 1 2 3", "BAD_SEQ"),
    ("J 1 nan 0 0", "BAD_NUMBER"), ("J 1 1 x 0", "BAD_NUMBER"), ("CANCEL 1 NECK", "BAD_ARGS"),
    ("J 1 " + "1" * 80 + " 0 0", "TOO_LONG"),
])
def test_rejects_bad_lines(line, reason):
    with pytest.raises(ProtocolError) as e:
        parse_command(line)
    assert e.value.reason == reason


def test_bad_line_answers_err(esp):
    esp.feed("J 3 1 2")
    assert names(esp.read()) == [("ERR", 3, ("BAD_ARGS",))]


def test_joint_clipped_to_limits(esp):
    esp.feed("J 1 200 0 0")
    assert names(esp.read()) == [("ACK", 1, ("CLIPPED",))]
    for _ in range(300):
        esp.tick(0.01)
    assert esp.neck.pos[0] == pytest.approx(70.0)


def test_stop_is_latched_until_resume(esp):
    esp.feed("J 1 40 0 0")
    for _ in range(20):
        esp.tick(0.01)
    esp.feed("STOP 2")
    esp.feed("J 3 -40 0 0")
    esp.feed("S 4 R2D2")
    assert names(esp.read())[-2:] == [("ERR", 3, ("STOP_ACTIVE",)), ("ERR", 4, ("STOP_ACTIVE",))]
    for _ in range(100):
        esp.tick(0.01)
    frozen = esp.neck.pos[0]
    assert 0 < frozen < 40           # frenó donde estaba, no fue a HOME ni al objetivo
    esp.feed("RESUME 5")
    esp.feed("J 6 -40 0 0")
    assert names(esp.read())[-1] == ("ACK", 6, ())


def test_watchdog_holds_pose_and_cuts_sound(esp):
    esp.feed("J 1 30 0 0")
    esp.feed("S 2 POLCA")
    for _ in range(80):              # 0,8 s sin comandos
        esp.tick(0.01)
    out = names(esp.read())
    assert ("ERR", 0, ("WATCHDOG",)) in out
    assert esp.sound is None and esp.state == "WATCHDOG"
    pos = esp.neck.pos[0]
    for _ in range(100):
        esp.tick(0.01)
    assert abs(esp.neck.pos[0] - pos) < 5    # mantiene la postura (sólo termina de frenar)
    esp.feed("PING 3")
    assert esp.state == "RUN"


def test_sound_done_and_no_duplicate(esp):
    esp.feed("S 1 BEEP_NEUTRO")
    esp.tick(0.1)
    esp.feed("S 1 BEEP_NEUTRO")      # reenvío del mismo seq: no se reinicia
    for _ in range(20):
        esp.tick(0.01)
    out = names(esp.read())
    assert out.count(("DONE", 1, ())) == 1


def test_unknown_sound(esp):
    esp.feed("S 1 HIMNO")
    assert names(esp.read()) == [("ERR", 1, ("UNKNOWN_SOUND",))]


def test_state_reply_parses(esp):
    esp.feed("PING 9")
    r = [parse_reply(x.encode()) for x in esp.read()]
    assert r[1].name == "STATE" and r[1].args[0] == "RUN"
