"""05/11: kp y ema del control de mirada por eje [yaw, pitch].
Con kp = 2,5 para los dos ejes el yaw quedó PEOR (el RDS3218 vibra si se mueve lento): por eso
cada eje lleva su ganancia. Un número sigue valiendo para los dos ejes."""
import copy

from keepon import load_config
from keepon.gaze import GazeController
from keepon.world import Person, World


def _velocidades(kp, ema):
    """Velocidad que pide el control (yaw, pitch) [°/s] con la persona corrida en los dos ejes."""
    cfg = copy.deepcopy(load_config())
    cfg["gaze"].update(kp=kp, ema=ema, mirar_abajo_deg=0.0)
    g = GazeController(cfg)
    w = World(0.0, 640, 480, 66.0)
    p = Person(1, 320 + 150, 240 - 150, 200)   # a la derecha y arriba del centro
    dt = 0.025
    ref = g.update([0.0, 0.0, 0.0], p, w, dt)
    return ref[0] / dt, ref[1] / dt


def test_un_numero_vale_para_los_dos_ejes():
    vy_lista, vp_lista = _velocidades([3.0, 3.0], [0.5, 0.5])
    vy, vp = _velocidades(3.0, 0.5)
    assert (vy, vp) == (vy_lista, vp_lista)


def test_kp_y_ema_por_eje():
    vy_a, vp_a = _velocidades([4.0, 2.0], [0.5, 0.5])
    vy_b, vp_b = _velocidades([4.0, 4.0], [0.5, 0.5])
    assert vy_a == vy_b                  # el yaw no cambia si solo cambia el kp del pitch
    assert 0 < vp_a < vp_b               # el pitch va más lento con menos kp
    vy_c, vp_c = _velocidades([4.0, 4.0], [0.5, 0.25])
    assert vy_c == vy_b and 0 < vp_c < vp_b   # menos ema en pitch: el error filtrado sube más despacio


def test_config_yaw_mantiene_su_ganancia():
    """El yaw no se tiene que volver lento al suavizar el pitch."""
    kp = load_config()["gaze"]["kp"]
    assert isinstance(kp, list) and kp[0] >= 4.0 and kp[1] < kp[0]
