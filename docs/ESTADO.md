# Estado del proyecto (03/11/2026)

Foto del estado actual. La historia está en `docs/BITACORA.md`; lo que falta, en `docs/PENDIENTES.md`.
Al cerrar una sesión (`/cerrar`) se actualiza este archivo, no `CLAUDE.md`.

## Rama y repo
- Todo el trabajo del 03/11 está en la rama **`diseno-v6-vigente`** (PR #3, sin integrar a `main`). La Pi está
  sincronizada con esa rama (`~/keepon/.commit`).
- Tests: **164** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`), 36 comparan el firmware con el simulador.

## Mecánica y hardware
- Modelo vigente: **v6 R4** (`docs/diseno_v6/LEEME_GIT.md`), armado. yaw = RDS3218 en la base, pitch = HS-7955TG en la
  horquilla, roll = MG996R en la cuna (disco de 25T).
- Calibración (`neck.servos`): ceros yaw 1500 / pitch 1400 / roll 1450 µs; signos −1 / +1 / −1; límites yaw ±70°,
  pitch −20/+30°, **roll ±20°**; compensación de zona muerta del roll `[0, 151]` µs.
- **Pitch**: oscila al empujarlo y zumba quieto (juego del brazo simple en su bolsillo). **Yaw**: vibra al moverse lento.
  El seguimiento oscila un poco. El grupo va a cambiar un servo.
- Cámara NoIR en **`i2c@88000`**, montada invertida (`orientation_deg: 180`). Intrínsecos **provisorios**: fx/fy de otra
  cámara, cx/cy = centro de la imagen (sin calibrar con tablero).
- ESP32-C3 en la Pi con el **firmware del robot** (watchdog corregido, compensación, buzzer en GPIO7 desde el 04/11, volumen 0,12).
- **Buzzer** (MH-FMD, I/O en **GPIO7** desde el 04/11, VCC 3V3): en el GPIO5 sonaba con los servos quietos, **se cortaba cuando se movían** y el 04/11 dejó de sonar (el firmware lo tocaba: DONE a tiempo). Se pasó al GPIO7.

## Software del robot (en la Pi)
- `scripts/robot_vivo.sh`: cámara + servidor web + panel + `robot_vivo.py` (percepción → eventos → robot → ESP32).
  Medido: lazo 39–40 Hz, personas 13–20 Hz, pose 9–13 Hz, edad del cuadro 64–255 ms. Sin ERR WATCHDOG desde el arreglo.
- Funciona en real: seguimiento con foco e histéresis, observador (barrido), SALUDO (cabeceos + R2D2), ME_MIRA sostenido,
  curiosidad (roll ±15° con la persona quieta), modos Neutro/Tímido/Atrevido/Maleducado con su beep, overlay T7, log CSV.
- Implementado pero **sin probar en real**: SALIENDO + piropo del modo Maleducado.
- **Falta**: detector de camisetas (la reacción POLCA/ABUCHEO ya existe), sacadas y roll del observador,
  desaprobación, medición de latencia evento → respuesta.

## Cómo se usa
- Notebook: `scripts/k arrancar | parar | estado | log | t | a | m | n | stop | resume | home | sonido POLCA`.
- Celular: panel en `http://100.116.96.71:8081` (Tailscale) o la IP local de la Pi en la misma Wi-Fi; instalable como app.
- Overlay: `http://100.116.96.71:8080/stream_viewer?topic=/keepon/overlay`.
- Servicio `keepon` instalado en la Pi, **no activado al encender** (`scripts/k demo-on` para la demo; además, una vez,
  `sudo loginctl enable-linger r2d2`). Con el servicio corriendo, la cámara y la ESP32 están ocupadas.
- Cargar firmware: `scripts/k parar` y `bash scripts/cargar_firmware.sh`. Detalle de todo en `docs/PI.md`.

## Rendimiento de referencia (30/09, 1 persona)
- Personas + rostros 16,9 Hz (YOLO 34 ms + rostros 10 ms), pose 10 Hz, CPU 239 % de 400 %. Detalle en `docs/ESTADO_PI.md`.
