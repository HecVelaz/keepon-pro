#!/usr/bin/env python3
"""Mover los servos del cuello escribiendo ángulos en grados (prueba de banco, con la cabeza montada).

Necesita el programa de banco cargado en la ESP32 (pruebas_servos/prueba_servo/prueba_servo.ino), no el
firmware del robot. Abre el puerto serie y lo deja abierto mientras corre: en la Pi abrir el puerto no
reinicia la ESP32. Pasa de grados a µs con pulso = centro + signo · grados / grados_por_us.

Uso (en la Pi):  ~/keepon_env/bin/python ~/keepon/pruebas_servos/mover_servos.py
  20, -20, 0, 12.5 ...  mover el eje seleccionado a ese ángulo (yaw + = derecha, pitch + = arriba)
  y / p / r             seleccionar yaw / pitch / roll
  c <us>                cambiar el centro (el 0°) del eje seleccionado
  us <us>               mandar un pulso directo, en µs
  w <us/s>              velocidad de la rampa de este eje (arranca en 300 µs/s ≈ 28 °/s)
  v <us/s>              velocidad de la rampa de todos los ejes
  s                     estado de la ESP32
  q                     salir (los servos quedan donde están, con pulso)

Ojo: el primer pulso de cada eje después de encender salta a velocidad máxima (el servo no sabe dónde
está). Sostener la cabeza cerca de la postura neutra antes del primer movimiento de cada eje.
"""
import sys
import threading
import time

import serial

PUERTO = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

# Parámetros por eje (los de config.yaml al 05/11):
#   num: número de eje en prueba_servo.ino; gpus: °/µs, [lado de pulsos < centro, lado > centro];
#   lim: ángulos permitidos (neck.limits); lim_us: recorte que se le fija a la ESP32 al arrancar.
EJES = {
    "y": {"nombre": "yaw", "num": 0, "centro": 1500, "gpus": (0.13, 0.136), "signo": -1,
          "lim": (-70.0, 70.0), "lim_us": (950, 2020)},
    "p": {"nombre": "pitch", "num": 1, "centro": 1500, "gpus": (0.092, 0.092), "signo": -1,
          "lim": (-20.0, 30.0), "lim_us": (1100, 1800)},
    # Roll: MG996R nuevo (05/11). Centro y signo SIN VERIFICAR montado: confirmar y corregir acá.
    "r": {"nombre": "roll", "num": 2, "centro": 1500, "gpus": (0.092, 0.092), "signo": 1,
          "lim": (-20.0, 20.0), "lim_us": (1250, 1750)},
}


def leer_respuestas(puerto):
    """Hilo que muestra todo lo que contesta la ESP32."""
    while True:
        datos = puerto.read(256)
        if datos:
            sys.stdout.write("\n  esp32: " + datos.decode(errors="replace").replace("\n", "\n  esp32: "))
            sys.stdout.flush()


def grados_a_us(e, grados):
    """pulso = centro + signo · grados / gpus, con la pendiente del lado del centro al que cae el pulso."""
    sentido = e["signo"] * grados
    gpus = e["gpus"][0] if sentido < 0 else e["gpus"][1]
    return round(e["centro"] + sentido / gpus)


def main():
    puerto = serial.Serial(PUERTO, 115200, timeout=0.1)

    def mandar(texto):
        puerto.write(texto.encode())
        time.sleep(0.05)

    threading.Thread(target=leer_respuestas, args=(puerto,), daemon=True).start()
    # Límites de seguridad en la ESP32 para cada eje (no mueve nada)
    for e in EJES.values():
        mandar(f"e {e['num']}\nl {e['lim_us'][0]} {e['lim_us'][1]}\n")
    sel = "y"
    mandar(f"e {EJES[sel]['num']}\n")
    print(__doc__)
    while True:
        e = EJES[sel]
        try:
            linea = input(f"\n[{e['nombre']} centro={e['centro']}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        partes = linea.split()
        if not partes:
            continue
        cmd = partes[0]
        try:
            if cmd == "q":
                break
            elif cmd in EJES:
                sel = cmd
                mandar(f"e {EJES[sel]['num']}\n")
            elif cmd == "c" and len(partes) == 2:
                e["centro"] = int(partes[1])
                print(f"centro de {e['nombre']} = {e['centro']} µs")
            elif cmd == "us" and len(partes) == 2:
                mandar(f"p {int(partes[1])}\n")
            elif cmd in ("w", "v") and len(partes) == 2:
                vel = int(partes[1])
                if 20 <= vel <= 5000:
                    mandar(f"{cmd} {vel}\n")
                else:
                    print("Velocidad fuera de rango: 20..5000 µs/s")
            elif cmd == "s":
                mandar("?\n")
            else:
                grados = float(cmd)
                lo, hi = e["lim"]
                if not lo <= grados <= hi:
                    print(f"Fuera de rango para {e['nombre']}: [{lo}, {hi}]°")
                    continue
                pulso = grados_a_us(e, grados)
                print(f"{e['nombre']} -> {grados:+.1f}° = {pulso} µs")
                mandar(f"p {pulso}\n")
        except ValueError:
            print("No entendí. Escribí un ángulo (ej. 20, -20, 0), y, p, r, c <us>, us <us>, w, v, s o q.")
    puerto.close()


if __name__ == "__main__":
    main()
