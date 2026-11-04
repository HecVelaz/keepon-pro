"""keepon/overlay.py: dibuja el estado T7 sin romperse con cualquier combinación de datos."""

import numpy as np

from keepon import load_config
from keepon.arbiter import Grant
from keepon.overlay import Salud, dibujar
from keepon.perception import DetResult, FaceObs, PersonObs
from keepon.world import Person, World

CFG = load_config()


def escena():
    w = World.from_cfg(CFG, t=1.0)
    w.persons[3] = Person(3, 300, 140, 380, looking=True, shirt="OLIMPIA", last_seen=1.0)
    w.persons[5] = Person(5, 520, 160, 300, last_seen=1.0)
    cara = FaceObs(5.0, 2.0, 1.0, (300.0, 140.0), True)
    det = DetResult("personas", 1, 0, 0, 10, persons=[PersonObs(3, (220, 80, 380, 460), 0.9, cara),
                                                      PersonObs(5, (460, 100, 600, 400), 0.8)])
    kp = {"nariz": (300, 140, .9), "hombro_i": (260, 220, .9), "hombro_d": (340, 220, .9), "codo_i": (240, 280, .9),
          "codo_d": (370, 170, .9), "muneca_i": (230, 330, .9), "muneca_d": (380, 110, .9)}
    pose = DetResult("pose", 1, 0, 0, 10, poses=[kp])
    return w, det, pose


def test_dibuja_todo_el_estado():
    w, det, pose = escena()
    g = Grant(7, "SEGUIMIENTO", 4, frozenset({"NECK"}), True, None, 3, 0.0, {})
    img = np.zeros((480, 640, 3), np.uint8)
    out = dibujar(img, mundo=w, det=det, pose=pose, objetivo=3, dueños={"CUELLO": g, "BUZZER": None},
                  ref=(12.3, -4.0, 0.0), modo="NEUTRO", stop=False, saludo_reciente=lambda pid: pid == 3,
                  salud=Salud(40, 15, 10, 120, 0.1))
    assert out is img and img.any()


def test_sin_percepcion_ni_dueños():
    img = np.zeros((480, 640, 3), np.uint8)
    dibujar(img, mundo=World.from_cfg(CFG, t=0.0), det=None, pose=None, objetivo=None, dueños={},
            ref=(0, 0, 0), modo="NEUTRO", stop=True, saludo_reciente=lambda pid: False, salud=Salud())
    assert img.any()
