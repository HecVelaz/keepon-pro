#!/usr/bin/env python3
"""Panel web para comandar a Keepon desde el celular (se instala como app: "Agregar a pantalla de inicio").

Sirve scripts/panel/ (página, manifiesto e ícono) y dos rutas:
  GET  /estado    el estado que publica robot_vivo.py (~/keepon/run/estado.json), más el estado del
                  servicio keepon ("servicio": active / activating / inactive / failed...)
  POST /comando   {"comando": "t"} → lo escribe en el FIFO del robot (~/keepon/run/comandos)
                  {"comando": "arrancar"} / {"comando": "parar"} → systemctl --user start/stop keepon

Sólo acepta una lista cerrada de comandos (encender/apagar el robot, modos, stop/resume/home, sonidos de
config.yaml y volumen 0..100): desde la página no se puede ejecutar ninguna otra cosa en la Pi.

Corre como servicio propio (scripts/keepon-panel.service, 'keepon panel-on'), independiente del robot:
así el celular puede encender a Keepon. Si ese servicio no está, lo arranca scripts/robot_vivo.sh.

    ~/keepon_env/bin/python scripts/panel_web.py [--puerto 8081]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from keepon import load_config  # noqa: E402

PANEL = RAIZ / "scripts" / "panel"
RUN = Path.home() / "keepon" / "run"
TIPOS = {".html": "text/html; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml",
         ".webmanifest": "application/manifest+json", ".js": "text/javascript"}
FIJOS = {"n", "t", "a", "m", "stop", "resume", "home", "ejes"}
# Encender / apagar el robot entero (el servicio systemd). No confundir "parar" con "stop": "stop" es el
# STOP enclavado del robot que sigue corriendo; "parar" lo apaga (vuelve a HOME y suelta cámara y ESP32).
SERVICIO = {"arrancar": "start", "parar": "stop"}
UNIDAD = "keepon"


def validar(cmd: str, sonidos) -> str | None:
    """El comando normalizado si está permitido; None si no."""
    s = " ".join(str(cmd).split()).lower()
    if s in FIJOS or s in SERVICIO:
        return s
    partes = s.split(" ")
    if len(partes) == 2 and partes[0] == "sonido" and partes[1].upper() in sonidos:
        return f"sonido {partes[1].upper()}"
    # isascii(): isdigit() también acepta dígitos de otros alfabetos ("²", "٣")
    if len(partes) == 2 and partes[0] == "volumen" and partes[1].isascii() and partes[1].isdigit() \
            and len(partes[1]) <= 3 and int(partes[1]) <= 100:
        return f"volumen {int(partes[1])}"
    return None


def enviar(cmd: str, fifo: Path) -> bool:
    """Escribe el comando en el FIFO sin bloquear. False si el robot no está escuchando."""
    try:
        fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
    except OSError:  # no existe, o nadie lo tiene abierto para leer
        return False
    try:
        os.write(fd, (cmd + "\n").encode())
    finally:
        os.close(fd)
    return True


def systemctl(accion: str) -> tuple[bool, str]:
    """Corre 'systemctl --user <accion> keepon' (sin shell, con tiempo máximo) → (salió bien, salida).

    start/stop van con --no-block: el pedido HTTP vuelve enseguida y la página sigue el arranque con
    /estado (parar tarda unos segundos: el robot vuelve a HOME antes de soltar la ESP32)."""
    args = ["systemctl", "--user"]
    if accion in ("start", "stop"):
        args.append("--no-block")
    try:
        r = subprocess.run(args + [accion, UNIDAD], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout.strip() or r.stderr.strip())


def crear_handler(sonidos, run: Path = RUN, panel: Path = PANEL, ctl=systemctl):
    """ctl(accion) → (ok, salida): systemctl de verdad; los tests le pasan uno falso."""
    class Panel(BaseHTTPRequestHandler):
        def _json(self, codigo: int, datos: dict) -> None:
            cuerpo = json.dumps(datos, ensure_ascii=False).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_GET(self):  # noqa: N802
            if self.path == "/estado":
                try:
                    datos = json.loads((run / "estado.json").read_text(encoding="utf-8"))
                    datos["vivo"] = time.time() - datos.get("t", 0) < 3.0
                except (OSError, ValueError):
                    datos = {"vivo": False}
                # is-active sale con código ≠ 0 si no está activo, pero igual escribe el estado
                datos["servicio"] = ctl("is-active")[1] or "desconocido"
                return self._json(200, datos)
            nombre = "index.html" if self.path in ("/", "/index.html") else self.path.lstrip("/")
            archivo = (panel / nombre).resolve()
            if archivo.parent != panel.resolve() or not archivo.is_file():  # sólo archivos de scripts/panel/
                return self._json(404, {"error": "no existe"})
            cuerpo = archivo.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", TIPOS.get(archivo.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_POST(self):  # noqa: N802
            if self.path != "/comando":
                return self._json(404, {"error": "no existe"})
            try:
                largo = min(int(self.headers.get("Content-Length", 0)), 256)
                cmd = json.loads(self.rfile.read(largo) or b"{}").get("comando", "")
            except (ValueError, AttributeError):
                return self._json(400, {"error": "pedido inválido"})
            ok = validar(cmd, sonidos)
            if ok is None:
                return self._json(400, {"error": f"comando no permitido: {cmd!r}"})
            if ok in SERVICIO:
                bien, salida = ctl(SERVICIO[ok])
                if not bien:
                    return self._json(500, {"error": f"no se pudo {ok}: {salida}"})
                return self._json(200, {"enviado": ok})
            if not enviar(ok, run / "comandos"):
                return self._json(503, {"error": "el robot no está corriendo"})
            return self._json(200, {"enviado": ok})

        def log_message(self, *a):  # sin una línea por pedido en el log del servicio
            pass

    return Panel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8081)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("0.0.0.0", a.puerto), crear_handler(load_config()["sounds"]))
    print(f"Panel del celular en http://<IP de la Pi>:{a.puerto}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
