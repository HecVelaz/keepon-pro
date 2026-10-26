"""Genera firmware/keepon_fw/generado.h a partir de config.yaml y del simulador de sonidos.

Así el firmware no tiene números copiados a mano: límites, HOME, vmax/amax, calibración de los
servos y watchdog salen de config.yaml, y las tablas de sonidos de pruebas_buzzer/simulador_sonidos.html
(la constante SONIDOS). Verifica que la duración de cada tabla coincida con `sounds:` de config.yaml.

    .venv/bin/python scripts/generar_firmware.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from keepon import load_config  # noqa: E402

SIMULADOR = RAIZ / "pruebas_buzzer" / "simulador_sonidos.html"
SALIDA = RAIZ / "firmware" / "keepon_fw" / "generado.h"
EJES = ("yaw", "pitch", "roll")
NOTAS = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}


def redondear(x: float) -> int:
    """Igual que Math.round de JavaScript (el simulador): mitad hacia arriba."""
    return math.floor(x + 0.5)


def frecuencia(tok: str) -> int | None:
    """Misma lectura que el simulador: Hz, nombre de nota (A4 = 440 Hz) o '-'/'0' para silencio."""
    if tok in ("-", "0"):
        return 0
    if re.fullmatch(r"\d+(\.\d+)?", tok):
        return redondear(float(tok))
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d)", tok)
    if not m:
        return None
    semis = NOTAS[m[1].upper()] + (1 if m[2] == "#" else -1 if m[2] == "b" else 0) + (int(m[3]) - 4) * 12
    return redondear(440 * 2 ** (semis / 12))


def leer_tabla(texto: str, nombre: str) -> list[tuple[int, int, int]]:
    segs = []
    for i, linea in enumerate(texto.split("\n"), 1):
        for parte in linea.split("#")[0].split(";"):
            t = parte.split()
            if not t:
                continue
            if len(t) not in (2, 3):
                raise SystemExit(f"{nombre}, línea {i}: '{parte.strip()}' no es 'f ms', 'f0 f1 ms' ni '- ms'")
            ms = int(t[-1])
            f0 = frecuencia(t[0])
            f1 = frecuencia(t[1]) if len(t) == 3 else f0
            if f0 is None or f1 is None or not 1 <= ms <= 65535 or (f0 == 0) != (f1 == 0):
                raise SystemExit(f"{nombre}, línea {i}: segmento inválido '{parte.strip()}'")
            segs.append((f0, f1, ms))
    return segs


def sonidos_del_simulador() -> dict[str, list[tuple[int, int, int]]]:
    html = SIMULADOR.read_text(encoding="utf-8")
    bloques = re.findall(r'nombre:\s*"([A-Z0-9_]+)".*?tabla:\s*`(.*?)`', html, flags=re.S)
    if not bloques:
        raise SystemExit(f"no encontré la constante SONIDOS en {SIMULADOR}")
    return {nombre: leer_tabla(texto, nombre) for nombre, texto in bloques}


def generar(cfg: dict | None = None) -> str:
    """Texto de generado.h. Sale con SystemExit si las fuentes no son coherentes."""
    cfg = cfg or load_config()
    n, s = cfg["neck"], cfg["neck"]["servos"]
    tablas = sonidos_del_simulador()

    faltan = [x for x in cfg["sounds"] if x not in tablas]
    if faltan:
        raise SystemExit(f"config.yaml tiene sonidos sin tabla en el simulador: {faltan}")
    for nombre, seg in cfg["sounds"].items():
        ms = sum(x[2] for x in tablas[nombre])
        if ms != round(seg * 1000):
            raise SystemExit(f"{nombre}: la tabla dura {ms} ms y config.yaml dice {seg} s")

    def gpu(eje):  # grados por µs: [lado de pulsos < 1500, lado > 1500]
        g = s[eje]["grados_por_us"]
        return g if isinstance(g, list) else [g, g]

    L = [
        "// GENERADO por scripts/generar_firmware.py a partir de config.yaml y",
        "// pruebas_buzzer/simulador_sonidos.html. No editar a mano: cambiar la fuente y volver a generar.",
        "#pragma once",
        "#include <stdint.h>",
        "",
        "namespace gen {",
        "",
        f"const uint32_t WATCHDOG_MS = {cfg['serial']['watchdog_ms']};",
        "",
        "// Volumen del buzzer: fracción del ciclo de trabajo máximo (1.0 = 50 %).",
        f"const double BUZZER_VOLUMEN = {float(cfg['buzzer']['volumen'])!r};",
        "",
        "// Cuello, en orden yaw, pitch, roll [grados, °/s, °/s²]",
        "const double LIM_MIN[3] = {" + ", ".join(f"{n['limits'][e][0]!r}" for e in EJES) + "};",
        "const double LIM_MAX[3] = {" + ", ".join(f"{n['limits'][e][1]!r}" for e in EJES) + "};",
        "const double HOME[3] = {" + ", ".join(repr(float(x)) for x in n["home"]) + "};",
        "const double VMAX[3] = {" + ", ".join(repr(float(x)) for x in n["vmax"]) + "};",
        "const double AMAX[3] = {" + ", ".join(repr(float(x)) for x in n["amax"]) + "};",
        "",
        "// Servos: pulso = centro + signo · grados / grados_por_us, recortado a [min, max] µs.",
        "// grados_por_us: [lado de pulsos < 1500, lado de pulsos > 1500].",
        "const double CENTRO_US[3] = {" + ", ".join(repr(float(s[e]["centro_us"])) for e in EJES) + "};",
        "const double GPU[3][2] = {" + ", ".join("{" + ", ".join(repr(float(x)) for x in gpu(e)) + "}" for e in EJES) + "};",
        "const uint16_t MIN_US[3] = {" + ", ".join(str(s[e]["min_us"]) for e in EJES) + "};",
        "const uint16_t MAX_US[3] = {" + ", ".join(str(s[e]["max_us"]) for e in EJES) + "};",
        "const int8_t SIGNO[3] = {" + ", ".join(str(s[e]["signo"]) for e in EJES) + "};",
        "",
        "// Sonidos: {f_inicio_Hz, f_fin_Hz, duracion_ms}. Iguales: nota fija; distintas: barrido; 0: silencio.",
        "struct Segmento { uint16_t f0, f1, ms; };",
        "struct Sonido { const char *nombre; const Segmento *seg; uint16_t n; uint32_t total_ms; };",
        "",
    ]
    for nombre in cfg["sounds"]:
        seg = tablas[nombre]
        L.append(f"const Segmento SND_{nombre}[] = {{")
        for i in range(0, len(seg), 6):
            L.append("  " + ", ".join(f"{{{a}, {b}, {c}}}" for a, b, c in seg[i:i + 6]) + ",")
        L.append("};")
    L += ["", f"const int NUM_SONIDOS = {len(cfg['sounds'])};", "const Sonido SONIDOS[NUM_SONIDOS] = {"]
    for nombre in cfg["sounds"]:
        seg = tablas[nombre]
        L.append(f'  {{"{nombre}", SND_{nombre}, {len(seg)}, {sum(x[2] for x in seg)}}},')
    L += ["};", "", "}  // namespace gen", ""]
    return "\n".join(L)


def main() -> None:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(generar(), encoding="utf-8")
    print(f"escrito {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
