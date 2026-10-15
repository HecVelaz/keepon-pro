"""Conformidad del firmware: el núcleo en C++ (firmware/keepon_fw/nucleo.cpp) contra SimESP32.

Se compila el núcleo con g++ junto con firmware/pruebas_host/arnes.cpp y se corre el mismo guion
en los dos: tienen que dar las mismas respuestas en el mismo paso de 10 ms y las mismas posiciones.
Si no hay g++, los tests se saltean.
"""

import importlib.util
import math
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from keepon import load_config
from keepon.sim_esp32 import SimESP32

RAIZ = Path(__file__).resolve().parent.parent
FW = RAIZ / "firmware" / "keepon_fw"


@pytest.fixture(scope="module")
def arnes(tmp_path_factory):
    if not shutil.which("g++"):
        pytest.skip("no hay g++")
    exe = tmp_path_factory.mktemp("fw") / "arnes"
    subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Werror", "-I", str(FW),
                    str(RAIZ / "firmware" / "pruebas_host" / "arnes.cpp"), str(FW / "nucleo.cpp"), "-o", str(exe)],
                   check=True)
    return exe


def correr_firmware(exe, guion):
    salida = subprocess.run([str(exe)], input="\n".join(guion) + "\n", capture_output=True, text=True, check=True)
    resp, pos, extra = [], [], []
    for linea in salida.stdout.splitlines():
        tipo, resto = linea.split(" ", 1)
        if tipo == "R":
            paso, texto = resto.split(" ", 1)
            resp.append((int(paso), texto))
        elif tipo == "P":
            paso, *xyz = resto.split()
            pos.append((int(paso), *map(float, xyz)))
        else:
            extra.append(linea)
    return resp, pos, extra


def correr_sim(guion):
    esp = SimESP32(load_config())
    paso = 0
    resp, pos = [], []

    def volcar():
        resp.extend((paso, r.encode().strip()) for r in esp.read())

    volcar()
    for orden in guion:
        if orden.startswith("L"):
            esp.feed(orden[2:])
            volcar()
        elif orden.startswith("T"):
            for _ in range(int(orden[1:])):
                paso += 1
                esp.tick(0.01)
                volcar()
                pos.append((paso, *esp.neck.pos))
    return resp, pos


def comparar(arnes, guion):
    r_fw, p_fw, _ = correr_firmware(arnes, guion)
    r_sim, p_sim = correr_sim(guion)
    assert r_fw == r_sim
    assert len(p_fw) == len(p_sim)
    for a, b in zip(p_fw, p_sim):
        assert a[0] == b[0]
        assert a[1:] == pytest.approx(b[1:], abs=1e-9), f"paso {a[0]}"


def test_generado_al_dia():
    """generado.h tiene que corresponder a config.yaml y al simulador de sonidos."""
    spec = importlib.util.spec_from_file_location("gen_fw", RAIZ / "scripts" / "generar_firmware.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (FW / "generado.h").read_text(encoding="utf-8") == mod.generar(), \
        "generado.h está viejo: correr scripts/generar_firmware.py"


def test_movimientos_y_recorte(arnes):
    comparar(arnes, ["L HELLO 1", "L J 1 30 10 -5", "T 40", "L J 2 -60 -20 20", "T 15", "L J 3 10 25 0",
                     "T 80", "L J 4 200 -90 0", "T 30", "L PING 5", "L HOME 6", "T 150", "L PING 7"])


def test_stop_enclavado(arnes):
    comparar(arnes, ["L J 1 40 0 0", "T 20", "L STOP 2", "L J 3 -40 0 0", "L S 4 R2D2", "L HOME 5",
                     "L CANCEL 6 SOUND", "T 100", "L PING 7", "L RESUME 8", "L J 9 -40 0 0", "T 120", "L PING 10"])


def test_watchdog(arnes):
    comparar(arnes, ["L J 1 30 15 10", "L S 2 POLCA", "T 80", "L PING 3", "T 5", "L J 4 -30 0 0", "T 40",
                     "L PING 5", "T 60", "L STOP 6", "T 100", "L RESUME 7", "T 70"])


def test_sonidos(arnes):
    guion, seq = [], 0
    for nombre in load_config()["sounds"]:
        seq += 1
        guion += [f"L S {seq} {nombre}", "T 30", f"L S {seq} {nombre}", "L PING 999", "T 300", "L PING 998",
                  "T 300", "L PING 997", "T 300", "L PING 996"]
    guion += ["L S 1 R2D2", "L S 500 HIMNO", "L S 501 r2d2", "T 10", "L CANCEL 502 sound", "T 10", "L PING 503",
              "L HELLO 1", "L S 1 BEEP_NEUTRO", "T 30"]
    comparar(arnes, guion)


@pytest.mark.parametrize("linea", [
    "", "   ", "X 1", "J 1 1 2", "J a 1 2 3", "J -1 0 0 0", "J 1 nan 0 0", "J 1 inf 0 0", "J 1 1 x 0",
    "J 1 1e1 2.5 -.5", "CANCEL 1 NECK", "J 1 " + "1" * 80 + " 0 0", "PING", "PING 1 2", "hello 1", "HELLO",
    "HELLO x", "HELLO 2", "HELLO 1 2", "s 5 beep_timido", "j 6 +3 -4 5", "STOP x", "RESUME 7 8", "J 8 1 2 3 4",
    "J +9 0 0 0", "PING 0012",
])
def test_lineas_raras(arnes, linea):
    comparar(arnes, [f"L {linea}", "T 3", "L PING 100", "T 3", "L RESUME 101"])


def test_al_azar(arnes):
    rnd = random.Random(14102026)
    guion, seq = ["L HELLO 1"], 0
    for _ in range(400):
        seq += 1
        x = rnd.random()
        if x < 0.55:
            guion.append(f"L J {seq} {rnd.uniform(-90, 90):.1f} {rnd.uniform(-30, 40):.1f} {rnd.uniform(-30, 30):.1f}")
        elif x < 0.70:
            guion.append(f"L PING {seq}")
        elif x < 0.75:
            guion.append(f"L STOP {seq}")
        elif x < 0.83:
            guion.append(f"L RESUME {seq}")
        elif x < 0.88:
            guion.append(f"L HOME {seq}")
        elif x < 0.95:
            guion.append(f"L S {seq} {rnd.choice(list(load_config()['sounds']))}")
        else:
            guion.append(f"L CANCEL {seq} SOUND")
        guion.append(f"T {rnd.choice([1, 2, 3, 5, 8, 13, 30, 60])}")
    comparar(arnes, guion)


def test_pulsos(arnes):
    """Grados → µs con la calibración de config.yaml (neck.servos)."""
    s = load_config()["neck"]["servos"]

    def esperado(eje, g):
        c = s[eje]
        gpu = c["grados_por_us"] if isinstance(c["grados_por_us"], list) else [c["grados_por_us"]] * 2
        d = c["signo"] * g
        us = math.floor(c["centro_us"] + d / gpu[0 if d < 0 else 1] + 0.5)
        return max(c["min_us"], min(c["max_us"], us))

    for y, p, r in [(70, 30, 20), (-70, -20, -20), (12.3, -7.5, 4.4), (0, 0, 0)]:
        _, _, extra = correr_firmware(arnes, [f"L J 1 {y} {p} {r}", "T 400", "U"])
        assert extra[-1] == f"U {esperado('yaw', y)} {esperado('pitch', p)} {esperado('roll', r)}"


def test_frecuencias(arnes):
    """El buzzer sigue la tabla: notas fijas, barridos cada 5 ms y silencios (como el simulador)."""
    spec = importlib.util.spec_from_file_location("gen_fw", RAIZ / "scripts" / "generar_firmware.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tablas = mod.sonidos_del_simulador()
    for nombre in ("R2D2", "POLCA", "ABUCHEO"):
        tiempos = list(range(0, sum(x[2] for x in tablas[nombre]) + 20, 7))
        _, _, extra = correr_firmware(arnes, [f"L S 1 {nombre}"] + [f"F {t}" for t in tiempos])
        for linea, t in zip(extra, tiempos):
            acum, f = 0, 0
            for f0, f1, ms in tablas[nombre]:
                if t < acum + ms:
                    k = (t - acum) // 5 * 5
                    f = f0 if f0 == f1 else math.floor(f0 + (f1 - f0) * k / ms + 0.5)
                    break
                acum += ms
            assert linea == f"F {t} {f}", nombre
