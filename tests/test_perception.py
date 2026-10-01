"""Geometría de ME_MIRA (solvePnP) y recorte de cabeza, con caras sintéticas."""

import math

import cv2
import numpy as np
import pytest

from keepon import load_config
from keepon.perception import FACE6_3D, FACE_3D, face_orientation, head_crop, intrinsics

CFG = load_config()
K, DIST = intrinsics(CFG)


def synth_face(yaw_deg: float, pitch_deg: float, pos_mm=(0.0, 0.0, 1500.0), model=FACE_3D) -> np.ndarray:
    """Proyecta el modelo de cara girado yaw/pitch respecto de mirar a la cámara."""
    face_to_cam = cv2.Rodrigues(np.array([math.pi, 0.0, 0.0]))[0]    # la cara mira a la cámara
    ry = cv2.Rodrigues(np.array([0.0, math.radians(yaw_deg), 0.0]))[0]
    rx = cv2.Rodrigues(np.array([math.radians(pitch_deg), 0.0, 0.0]))[0]
    R = ry @ rx @ face_to_cam
    pts, _ = cv2.projectPoints(model, cv2.Rodrigues(R)[0], np.array(pos_mm, dtype=np.float64), K, DIST)
    return pts.reshape(-1, 2)


@pytest.mark.parametrize("yaw,pitch", [(0, 0), (10, 0), (-25, 0), (0, 12), (20, -10), (40, 0)])
def test_deviation_matches_rotation(yaw, pitch):
    f = face_orientation(synth_face(yaw, pitch), K, DIST, 15.0)
    expected = math.degrees(math.acos(math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))))
    assert f.dev_deg == pytest.approx(expected, abs=1.0)
    assert f.looking == (expected < 15.0)


def test_looking_at_camera_from_the_side():
    """Persona a un costado que gira la cabeza hacia la cámara: SÍ mira (el desvío es
    respecto de la línea cara->cámara, no del eje óptico)."""
    x = 200.0
    turn = math.degrees(math.atan2(x, 1500.0))
    f = face_orientation(synth_face(turn, 0, (x, 0.0, 1500.0)), K, DIST, 15.0)  # +yaw: gira hacia la cámara
    assert f.dev_deg < 3.0 and f.looking


def test_head_crop_inside_image():
    for box in [(0, 0, 100, 300), (600, 50, 640, 480), (200, 100, 440, 480), (10, 400, 30, 480)]:
        x0, y0, s = head_crop(box, 640, 480)
        assert 0 <= x0 and 0 <= y0 and x0 + s <= 640 and y0 + s <= 480 and s >= 64


@pytest.mark.parametrize("yaw,pitch", [(0, 0), (12, 0), (-30, 0), (0, 10), (15, -8)])
def test_six_point_model(yaw, pitch):
    """Mismo cálculo con los 6 puntos de Face Detector (BlazeFace)."""
    f = face_orientation(synth_face(yaw, pitch, model=FACE6_3D), K, DIST, 15.0, FACE6_3D)
    expected = math.degrees(math.acos(math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))))
    assert f.dev_deg == pytest.approx(expected, abs=1.0)
