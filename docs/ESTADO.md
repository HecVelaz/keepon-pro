# Estado del proyecto (04/11/2026)

Foto del estado actual. La historia está en `docs/BITACORA.md`; lo que falta, en `docs/PENDIENTES.md`.
Al cerrar una sesión (`/cerrar`) se actualiza este archivo, no `CLAUDE.md`.

## Ramas y repo
- Ramas encadenadas, sin integrar a `main`: **`diseno-v6-vigente`** (PR #3) → **`panel-arranque`** (PR #4: panel,
  volumen, apagar a HOME) → **`camisetas`** (PR #5: detector de camisetas y mirada más abajo). Se integran en ese orden.
- La Pi está sincronizada con `camisetas` (`~/keepon/.commit`).
- Tests: **207** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`); 36+ comparan el firmware con el simulador.

## Mecánica y hardware
- Modelo vigente: **v6 R4** (`docs/diseno_v6/LEEME_GIT.md`), armado. yaw = RDS3218 en la base, pitch = HS-7955TG en la
  horquilla, roll = MG996R en la cuna (disco de 25T).
- Calibración (`neck.servos`): ceros yaw 1500 / pitch 1400 / roll 1450 µs; signos −1 / +1 / −1; límites yaw ±70°,
  pitch −20/+30°, **roll ±20°**; compensación de zona muerta del roll `[0, 151]` µs.
- **Pitch**: oscila al empujarlo y zumba quieto (juego del brazo simple en su bolsillo). **Yaw**: vibra al moverse lento.
  El seguimiento oscila un poco. El grupo va a cambiar un servo.
- Cámara NoIR en **`i2c@88000`**, montada invertida (`orientation_deg: 180`). Intrínsecos **provisorios**: fx/fy de otra
  cámara, cx/cy = centro de la imagen (sin calibrar con tablero). Campo ≈ 37° × 28°.
- ESP32-C3 en la Pi con el **firmware del robot, FW_VERSION 2** (comando `VOL`), buzzer en **GPIO5**.
- **Buzzer** (MH-FMD, VCC 3V3): **anda**. El corte intermitente era un cable jumper con falso contacto (cambiado).
  Volumen desde el panel (0–100 %, guardado en `~/keepon/run/volumen`).

## Software del robot (en la Pi)
- `keepon` (servicio de usuario): cámara + servidor web + `robot_vivo.py` (percepción → eventos → robot → ESP32).
  Medido: lazo 36–39 Hz, personas 12–17 Hz, pose 7–10 Hz, edad del cuadro 96–135 ms.
- Funciona en real: seguimiento con foco e histéresis (la cara queda **8° arriba del centro**, `gaze.mirar_abajo_deg`),
  observador, SALUDO (+ R2D2), ME_MIRA sostenido, curiosidad, modos con su beep, **CAMISETA_OLIMPIA → polca y
  CAMISETA_CERRO → abucheo** (roja y azul lisas: nada), overlay T7 (con `angulo N` de la mirada y el torso evaluado), log CSV.
- Apagar (panel, `k parar` o SIGTERM) libera el STOP y espera a que la cabeza llegue a HOME.
- Dudoso: el modo **Tímido** no desviaba la mirada (ME_MIRA casi no se activaba). Con la mirada corrida hacia abajo el
  ángulo dio mediana 8° (30/42 bajo 15°): falta volver a probarlo.
- Implementado pero **sin probar en real**: SALIENDO + piropo del modo Maleducado.
- Camisetas: videos de prueba (4 tomas) **solo en la Pi**, `~/keepon/capturas/camisetas/`; borrarlos al dar el detector
  por bueno. Resultados en `pruebas_camisetas/README.md`.

## Cómo se usa
- Celular: panel en `http://100.116.96.71:8081` (Tailscale) o la IP local de la Pi; **siempre prendido** (servicio
  `keepon-panel`, activado al encender; linger activo). Botones Encender / Apagar, modos, sonidos, volumen.
- Notebook: `scripts/k arrancar | parar | estado | log | t | a | m | n | stop | resume | home | sonido POLCA | volumen N`.
- Overlay: `http://100.116.96.71:8080/stream_viewer?topic=/keepon/overlay`.
- El servicio `keepon` **no arranca al encender** (`scripts/k demo-on` para la demo). Con el robot corriendo, la cámara y
  la ESP32 están ocupadas.
- Grabar prendas: `bash ~/keepon/pruebas_camisetas/grabar.sh camara`, luego `grabar.sh <nombre>` (60 s), luego `stop`.
- Cargar firmware: `scripts/k parar` y `bash scripts/cargar_firmware.sh`. Detalle de todo en `docs/PI.md`.

## Rendimiento de referencia (30/09, 1 persona)
- Personas + rostros 16,9 Hz (YOLO 34 ms + rostros 10 ms), pose 10 Hz, CPU 239 % de 400 %. Detalle en `docs/ESTADO_PI.md`.
