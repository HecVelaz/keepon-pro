#!/usr/bin/env python3
"""Keepon con la cámara y los servos de verdad (se corre en la Pi, con camera_node andando).

Cadena: Perception (procesos de personas —YOLO + tracker + rostros/ME_MIRA— y de pose) → World →
Eventos (ME_MIRA sostenido, SALUDO, SALIENDO y CAMISETA, keepon/eventos.py) → Robot (foco, comportamientos,
árbitro, control de mirada) → SerialLink → ESP32. La camiseta se clasifica en el proceso de pose
(keepon/camiseta.py).

    bash ~/keepon/scripts/robot_vivo.sh            # arranca camera_node y esto; Ctrl+C manda STOP
    ~/keepon_env/bin/python scripts/robot_vivo.py  # si camera_node ya está corriendo

Monitoreo (T7): el video con overlay (keepon/overlay.py) se publica en /keepon/overlay a ~10 Hz
(--sin-overlay lo apaga) y el log de transiciones va a logs/run_*.csv.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keepon import load_config  # noqa: E402
from keepon.world import Person, World  # noqa: E402


ATAJOS = {"n": "NEUTRO", "t": "TIMIDO", "a": "ATREVIDO", "m": "MALEDUCADO"}
AYUDA = ("Comandos (escribir y Enter): n/t/a/m = modo NEUTRO/TIMIDO/ATREVIDO/MALEDUCADO "
         "(o MODE TIMIDO), sonido NOMBRE (R2D2, POLCA, ABUCHEO, PIROPO...), volumen 0..100, stop, resume, home, ejes, "
         "? = esta ayuda")


def comando(linea: str, robot) -> str:
    """Interpreta un comando del operador (T5: cambio de modo en tiempo de ejecución). Devuelve qué hizo."""
    s = linea.strip()
    if not s:
        return ""
    palabras = s.split()
    if palabras[0].upper() in ("MODE", "MODO") and len(palabras) == 2:
        s = palabras[1]
    modo = ATAJOS.get(s.lower(), s)
    if robot.set_modo(modo):
        return f"modo {robot.modo}"
    if palabras[0].lower() in ("sonido", "s") and len(palabras) == 2:
        return f"sonido {palabras[1].upper()}" if robot.sonar(palabras[1]) else \
            f"no existe el sonido {palabras[1]}: {', '.join(robot.cfg['sounds'])}"
    if palabras[0].lower() in ("volumen", "vol", "v") and len(palabras) == 2:
        try:
            return f"volumen {robot.set_volumen(int(palabras[1]))} %"
        except ValueError:
            return "volumen: un entero de 0 a 100"
    if s.lower() == "stop":
        robot.stop()
        return "STOP (frena donde está; 'resume' para seguir)"
    if s.lower() in ("resume", "r"):
        robot.resume()
        return "RESUME"
    if s.lower() == "ejes":
        if robot.ejes():
            return "EJES (yaw, pitch y roll, ~15 s; después vuelve a lo que hacía)"
        return "EJES no: STOP activo ('resume' primero)"
    if s.lower() == "home":
        robot.home()
        return "HOME (se queda en 0 0 0; 'resume' para seguir)"
    return AYUDA


FIFO = Path.home() / "keepon" / "run" / "comandos"  # scripts/keepon escribe acá (corriendo como servicio)
ESTADO = FIFO.parent / "estado.json"                # lo lee el panel del celular (scripts/panel_web.py)
VOLUMEN = FIFO.parent / "volumen"                   # último volumen del operador: sobrevive a apagar y encender


def resumen_mira(angulos: list[float], umbral: float) -> str:
    """Para la línea ESTADO: cómo dio el ángulo cara→cámara de la persona seguida (validar looking_deg)."""
    if not angulos:
        return ""
    a = sorted(angulos)
    bajo = sum(x < umbral for x in a)
    return f", mira mín {a[0]:.0f}° mediana {a[len(a) // 2]:.0f}° (<{umbral:.0f}°: {bajo}/{len(a)})"


def leer_volumen(ruta: Path, defecto: int) -> int:
    """El volumen que dejó el operador la última vez; si no hay (o está roto), el de config.yaml."""
    try:
        return int(ruta.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return defecto


def escribir_estado(ruta: Path, **datos) -> None:
    """Estado para el panel, escrito de forma atómica (el panel nunca lee un archivo a medias)."""
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, ruta)


class Comandos:
    """Comandos del operador desde la terminal (si hay) y desde el FIFO, sin bloquear el lazo."""

    def __init__(self, fifo: Path = FIFO):
        self.teclado = sys.stdin.isatty()
        fifo.parent.mkdir(parents=True, exist_ok=True)
        if not fifo.exists():
            os.mkfifo(fifo)
        # O_RDWR: el FIFO no da fin de archivo cuando el que escribe lo cierra.
        self.fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        self._buf = b""

    def leer(self) -> list[str]:
        lineas = leer_teclado() if self.teclado else []
        try:
            while True:
                datos = os.read(self.fd, 4096)
                if not datos:
                    break
                self._buf += datos
        except BlockingIOError:
            pass
        *nuevas, self._buf = self._buf.split(b"\n")
        return lineas + [x.decode(errors="replace") for x in nuevas]


def leer_teclado() -> list[str]:
    """Líneas escritas en la terminal, sin bloquear el lazo (stdin con buffer de línea: hace falta Enter)."""
    lineas = []
    while select.select([sys.stdin], [], [], 0)[0]:
        linea = sys.stdin.readline()
        if not linea:  # stdin cerrado (p. ej. corriendo sin terminal)
            break
        lineas.append(linea)
    return lineas


def mundo_desde(det, cfg: dict, t: float) -> World:
    """Un resultado del proceso de personas → World en el instante t (reloj del enlace).

    Person.u/v es el centro del rostro: la nariz si se encontró la cara; si no, un punto a la altura
    de la cabeza dentro de la caja (el 12 % superior), para seguir igual a quien está de espaldas."""
    w = World.from_cfg(cfg, t=t)
    if det is None:
        return w
    for p in det.persons:
        x1, y1, x2, y2 = p.box
        if p.face is not None:
            u, v = p.face.nose[0], p.face.nose[1]
        else:
            u, v = (x1 + x2) / 2, y1 + 0.12 * (y2 - y1)
        w.persons[p.id] = Person(p.id, float(u), float(v), float(y2 - y1),
                                 looking=bool(p.face.looking) if p.face else False, last_seen=t)
    return w


class Monitor:
    """Overlay T7: dibuja el estado del robot sobre el último cuadro y lo publica en /keepon/overlay
    (web_video_server lo sirve al navegador). Usa su propia suscripción a la cámara."""

    TOPICO = "/keepon/overlay"

    def __init__(self, cfg: dict, hz: float = 10.0):
        from sensor_msgs.msg import Image

        from keepon.camera import Camera

        self.Image = Image
        self.cam = Camera(cfg)
        self.pub = self.cam._node.create_publisher(Image, self.TOPICO, 2)
        self.periodo, self.t_ultimo = 1.0 / hz, 0.0
        self.abajo_deg = cfg["gaze"].get("mirar_abajo_deg", 0.0)

    def publicar(self, **estado) -> None:
        """Como mucho a `hz`; si todavía no hay cuadro (o la cámara se cortó), no hace nada."""
        from keepon import overlay

        if time.monotonic() - self.t_ultimo < self.periodo:
            return
        self.t_ultimo = time.monotonic()
        try:
            frame, _, _ = self.cam.latest(timeout=0)
        except Exception:  # noqa: BLE001 - sin cuadro: el robot sigue igual
            return
        img = overlay.dibujar(frame.copy(), abajo_deg=self.abajo_deg, **estado)
        msg = self.Image()
        msg.header.stamp = self.cam._node.get_clock().now().to_msg()
        msg.height, msg.width = img.shape[:2]
        msg.encoding, msg.step = "bgr8", img.shape[1] * 3
        msg.data = img.tobytes()
        self.pub.publish(msg)

    def close(self) -> None:
        self.cam.close()


def ir_a_home_y_esperar(link, home, tol_deg: float = 1.0, limite_s: float = 5.0, dormir=time.sleep) -> bool:
    """Al apagar: lleva la cabeza a HOME y sigue hablando con la ESP32 hasta que llegue.

    - RESUME antes del HOME: con el STOP enclavado la ESP32 rechaza el HOME (ERR STOP_ACTIVE) y la
      cabeza quedaba donde estaba (04/11: STOP y después "Apagar"). Apagar ya es una decisión del operador.
    - Esperar: si el programa sale apenas manda HOME, a los 500 ms el watchdog de la ESP32 frena la
      trayectoria. link.poll() manda un PING cada 200 ms, que rearma el watchdog y trae un STATE con
      las referencias actuales.
    True si llegó a menos de tol_deg en los tres ejes antes de limite_s."""
    link.send("RESUME")
    link.send("HOME")
    fin = link.now() + limite_s
    while link.now() < fin:
        for r in link.poll():
            if r.name == "STATE" and len(r.args) >= 4:
                angulos = [float(v) for v in r.args[1:4]]
                if all(abs(a - h) <= tol_deg for a, h in zip(angulos, home)):
                    return True
        dormir(0.05)
    return False


def main() -> None:
    from keepon.arbiter import BUZZER, NECK
    from keepon.eventos import Eventos
    from keepon.link import SerialLink
    from keepon.overlay import Salud
    from keepon.perception import Perception
    from keepon.robot import Robot

    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default=load_config()["serial"]["port"])
    ap.add_argument("--duracion", type=float, default=0.0, help="segundos (0 = hasta Ctrl+C)")
    ap.add_argument("--sin-overlay", action="store_true", help="no publicar el video con overlay (T7)")
    a = ap.parse_args()

    cfg = load_config()
    link = SerialLink(a.puerto, espejo_cfg=cfg)
    robot = Robot(cfg, link)
    robot.resume()  # un Ctrl+C de una corrida anterior deja el STOP enclavado en la ESP32: liberarlo
    robot.set_volumen(leer_volumen(VOLUMEN, robot.volumen))
    eventos = Eventos(cfg, log=robot.log)
    per = Perception(cfg, workers=("personas", "pose"))
    monitor = None if a.sin_overlay else Monitor(cfg)
    periodo = 1.0 / cfg["control"]["rate_hz"]
    print("Cargando modelos (~15 s). Ctrl+C manda STOP y sale.")
    print(AYUDA)
    comandos = Comandos()
    print(f"También por FIFO: echo t > {FIFO}  (o scripts/keepon t)")
    # systemctl stop (SIGTERM): terminar el lazo normalmente y volver a HOME, no quedar congelado.
    terminar = []
    signal.signal(signal.SIGTERM, lambda *_: terminar.append(True))
    if monitor:
        print(f"Overlay en el navegador: http://<IP de la Pi>:8080/stream_viewer?topic={Monitor.TOPICO}")
    t0 = link.now()
    det = pose = None
    salud = Salud()
    cuenta = {"lazo": 0, "personas": 0, "pose": 0}
    t_hz, t_log = time.monotonic(), time.monotonic()
    tick_max, hueco_max, inicio_ant = 0.0, 0.0, None  # trabas del lazo (ERR WATCHDOG de la ESP32)
    t_estado = 0.0
    angulos_mira: list[float] = []  # ángulo cara→cámara de la persona seguida en los últimos 10 s
    ultimo_cmd = ""
    try:
        while (not a.duracion or link.now() - t0 < a.duracion) and not terminar:
            inicio = link.now()
            if inicio_ant is not None:  # entre inicios de ticks: si pasa de 500 ms, salta el watchdog
                hueco_max = max(hueco_max, inicio - inicio_ant)
            inicio_ant = inicio
            for r in per.poll():
                cuenta[r.kind] += 1
                if r.kind == "personas":
                    det = r
                    # Ángulo cara→cámara de la persona seguida, para validar perception.looking_deg
                    cara = next((po.face for po in r.persons if po.id == robot.focus.target and po.face), None)
                    if cara is not None:
                        angulos_mira.append(cara.dev_deg)
                else:
                    pose = r
            # Edad: desde que se capturó el cuadro (stamp, reloj de pared). Sin resultados todavía: viejo.
            edad = time.time() - det.stamp if det is not None else 1e9
            cajas = {p.id: p.box for p in det.persons} if det is not None else {}
            mundo = eventos.aplicar(mundo_desde(det, cfg, inicio), pose, cajas, ref=robot.act.ref)
            for linea in comandos.leer():
                volumen_antes = robot.volumen
                if (r := comando(linea, robot)):
                    print(f">> {r}")
                    robot.log(link.now(), f"COMANDO {linea.strip()} -> {r}")
                    ultimo_cmd = r
                if robot.volumen != volumen_antes:
                    VOLUMEN.write_text(f"{robot.volumen}\n", encoding="utf-8")
            robot.tick(mundo, world_age=edad)
            cuenta["lazo"] += 1

            if time.monotonic() - t_hz >= 1.0:  # tasas del último segundo
                dt = time.monotonic() - t_hz
                salud.lazo_hz, salud.personas_hz, salud.pose_hz = (cuenta[k] / dt for k in ("lazo", "personas", "pose"))
                cuenta, t_hz = {k: 0 for k in cuenta}, time.monotonic()
            salud.edad_ms, salud.desvio_espejo = edad * 1000, link.max_desvio
            if monitor:
                monitor.publicar(mundo=mundo, det=det, pose=pose, objetivo=robot.focus.target,
                                 dueños={"CUELLO": robot.arb.owner[NECK], "BUZZER": robot.arb.owner[BUZZER]},
                                 ref=robot.act.ref, modo=robot.modo, stop=robot.arb.stopped,
                                 saludo_reciente=lambda pid: eventos.saludo_reciente(pid, inicio), salud=salud)
            if time.monotonic() - t_estado >= 0.5:  # para el panel del celular
                t_estado = time.monotonic()
                g_cuello, g_buzzer = robot.arb.owner[NECK], robot.arb.owner[BUZZER]
                obj = mundo.persons.get(robot.focus.target) if robot.focus.target is not None else None
                escribir_estado(ESTADO, t=time.time(), modo=robot.modo, stop=robot.arb.stopped, home=robot.en_home,
                                foco=robot.focus.target, me_mira=bool(obj and obj.looking),
                                cuello=g_cuello.behavior if g_cuello else "-",
                                buzzer=g_buzzer.behavior if g_buzzer else "-",
                                ref=[round(v, 1) for v in robot.act.ref], personas=len(mundo.persons),
                                volumen=robot.volumen,
                                lazo_hz=round(salud.lazo_hz), personas_hz=round(salud.personas_hz, 1),
                                pose_hz=round(salud.pose_hz, 1), edad_ms=round(salud.edad_ms),
                                ultimo_comando=ultimo_cmd, sonidos=list(cfg["sounds"]))
            tick_max = max(tick_max, link.now() - inicio)
            if time.monotonic() - t_log >= 10.0:  # cada 10 s al log: salud del lazo y de la percepción
                n = len(det.persons) if det else 0
                robot.log(link.now(), f"ESTADO lazo {salud.lazo_hz:.0f} Hz (tick máx {tick_max * 1000:.0f} ms, "
                                      f"hueco máx {hueco_max * 1000:.0f} ms), personas {salud.personas_hz:.1f} Hz, "
                                      f"pose {salud.pose_hz:.1f} Hz, edad {salud.edad_ms:.0f} ms, personas vistas {n}, "
                                      f"espejo {link.max_desvio:.2f}° ({link.resyncs} resinc.)"
                                      + resumen_mira(angulos_mira, cfg["perception"]["looking_deg"]))
                t_log, tick_max, hueco_max = time.monotonic(), 0.0, 0.0
                angulos_mira.clear()
            time.sleep(max(0.0, inicio + periodo - link.now()))
    except KeyboardInterrupt:
        robot.stop()
        robot.tick(World.from_cfg(cfg, t=link.now()), world_age=1e9)  # asegura que el STOP salga
        print("\nSTOP enviado (frenó donde estaba). Para seguir: RESUME y HOME.")
    else:
        # Sin otro tick del robot: el observador mandaría un J encima del HOME.
        robot.log(link.now(), "FIN: HOME")
        llego = ir_a_home_y_esperar(link, cfg["neck"]["home"])
        robot.log(link.now(), "FIN: en HOME" if llego else "FIN: no llegó a HOME a tiempo")
    finally:
        per.close()
        if monitor:
            monitor.close()


if __name__ == "__main__":
    main()
