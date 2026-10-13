# CLAUDE.md: Keepon pro

Cabeza robótica social de 3 GDL (yaw/pitch/roll) con visión artificial. µTP de Robótica II, FIUNA. Grupo de hasta 5 personas.
**Demo física obligatoria el 30/10/2026** (Segundo Parcial). Sin demo física no hay puntaje.
Enunciado: `docs/2026S2uTP_RoboticaSocial.md`. Plan: `docs/HOJA_DE_RUTA.md` (v3).

## Reglas del curso que condicionan el código
- **El árbitro, los comportamientos y el control de la cabeza tienen que ser desarrollo propio.** Se pueden usar modelos preentrenados (YOLO, MediaPipe) citando la fuente. Todos los integrantes deben poder explicar cualquier parte en la defensa: código claro y comentado en español.
- Si hay copia entre grupos, se anula el trabajo: **el repo es privado** (github.com/HecVelaz/keepon-pro).
- No guardar imágenes de personas sin consentimiento: `capturas/` está en `.gitignore`. Las capturas de verificación se borran después de mirarlas.
- Requisitos duros: percepción ≥ 10 Hz y latencia evento→respuesta ≤ 300 ms; todo no bloqueante; recursos exclusivos (cuello y buzzer); prioridades, cooldowns, histéresis; overlay y log con marca de tiempo (T7).

## Hardware real
- **Raspberry Pi 5, 4 GB**, Ubuntu 24.04 + ROS 2 Jazzy. **No se puede cambiar el SO**: la Pi se usa en otros proyectos.
- **Camera Module 3 NoIR** (IMX708) en `i2c@80000`. Es NoIR, sin filtro IR, así que hay riesgo con los colores de las camisetas. La segunda NoIR (`i2c@88000`) aparece en libcamera pero no transmite ("Camera frontend has timed out": revisar el flex) y corre los índices: los scripts eligen la cámara **por nombre** (`CAMARA=/base/axi/pcie@120000/rp1/i2c@80000/imx708@1a`), no con `camera:=0`.
- **ESP32-C3-DevKitM-1** (no S3) para los 3 servos y el buzzer, por el micro-USB con puente UART (`/dev/ttyUSB0`; preferir `/dev/serial/by-id/...`). Pines: yaw GPIO0, pitch GPIO1, roll **GPIO4** (antes GPIO3, cambiado el 12/10 porque el roll temblaba con los tres en movimiento), buzzer GPIO10; evitar 2/8/9 (strapping), 18/19 (USB) y 20/21 (UART0). Análisis completo en `docs/REVISION_CODEX_HW.md` (escrito para microservos). Es un **clon con conversor CH340** (`1a86:7523`, `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`). Por ahora está conectada a la **notebook**, no a la Pi, y tiene cargado `pruebas_servos/prueba_servo.ino`. El firmware del robot no existe (`firmware/` está vacío).
- **Servos (09/10):** pitch **Hitec HS-7955TG** (~18 kgf·cm a 4,8 V); yaw **RDS3218 n.º 2** (desde el 12/10, en `config.yaml`: 270°, asimétrico 0,13/0,136 °/µs como lista `[lado <1500, lado >1500]`, ±70° ≈ 960/2010 µs, límites 950/2020, sin tope, banda muerta ≤ 2 µs abajo y 4–6 µs arriba, mantiene la posición sin pulso, picos de ~1 A a 260 °/s; el MG90S queda de repuesto; los dos RDS3218 no son intercambiables sin recalibrar). roll **MG90S** (desde el 12/10, a 6 V, el máximo de su hoja de datos; en `config.yaml` 0,090/0,085 °/µs, límites 1000/2000 µs; sin pulso queda flojo). El RDS3218 n.º 1 queda descartado. Sentido medido el 12/10, visto de frente al eje: en los dos RDS3218, pulso mayor = antihorario; en el HS, al revés (horario); en el MG90S (probado a 6 V), antihorario, como los RDS. Se compensa con `signo` por eje. Antes: MG90S provisorio (caracterizado el 09/10 a 5 V: ≥ 177°, asimétrico 0,090/0,085 °/µs, banda muerta 20–30 µs, silencioso, **sin pulso queda flojo**: en el STOP hay que seguir mandando el último pulso). El SG90 (antes en roll, caracterizado el 09/10 a 5 V: 0,090 °/µs simétrico, banda muerta 10–20 µs, silencioso, sin pulso queda flojo, tirón de pocos grados al encender; engranajes plásticos) queda de repuesto. El SM-S4315R es de rotación continua (confirmado). **HS-7955TG caracterizado el 09/10** (planilla completa y `neck.servos.pitch` en `config.yaml`): 0,090 °/µs lineal, límites electrónicos 750/2250 µs (≈ ±68°, 137° en total), banda muerta ≤ 2 µs, holgura ≤ 1°, 6 mA en reposo y silencioso. **Sin pulso mantiene la posición con fuerza**: el STOP/watchdog la congela, no la afloja (para aflojarlo hay que cortar los 6 V). Al encender sin pulso no se mueve, pero el primer pulso salta a velocidad máxima: el firmware tiene que arrancar en una postura conocida. Los tres juntos andan bien con la fuente de laboratorio (12/10); el roll (RDS n.º 1) vibra cuando el HS recibe pulso: el n.º 2 no, y el n.º 1 vibró una vez solo: confirmado intercambiándolos: la vibración (≈ 0,5 A al quedar quieto cerca de 1500 µs) sigue al n.º 1, que queda **descartado**; falta elegir otro servo para el roll (detalle en `pruebas_servos/README.md`). Pendiente: capacitor cerca de los servos y GND en estrella. Como son servos estándar (55–65 g), el rodamiento de yaw tiene que soportar el peso y el vuelco.
- **Fuente de servos:** 6 V, separada de la de la Pi, con GND común; ≥ 6 A para los tres juntos (2,5–4,2 A por servo con el eje trabado). La ALP002 ajustable (3–24 V, **1,5 A**, **entrada 100–120 V de alterna: no enchufar a 220 V sin transformador**) sirve solo para probar un servo sin carga. Para las pruebas individuales, mejor la fuente de laboratorio con límite de corriente.
- Pruebas de banco de los servos: `pruebas_servos/`: README con conexionado, procedimiento y planilla; `prueba_servo.ino` (comandos por serie a 115200: `e <eje>`, `c`, `p <us>`, `+`/`-`, `b <us1> <us2>`, `s`, `o`, `v <us/s>`, `l <min> <max>`, `?`); `simulador_hs7955tg.html` (diagrama de conexiones + ESP32 y fuente simuladas, se abre en el navegador).
- La rampa del programa de prueba arranca en `v 300` (≈27 °/s con 0,09 °/µs supuestos): **el giro lento es a propósito**. El HS-7955TG da ~315 °/s sin carga; `config.yaml` limita pitch a 120 °/s (Codex recomendó empezar con 60 °/s ≈ `v 700`).
- La notebook (x86, GPU vieja, sin CUDA) sirve solo para desarrollar.

## Acceso a la Pi
- `ssh r2d2@100.116.96.71` por Tailscale. Hostname `r2d2-desktop`. La clave SSH ya está autorizada (`-o BatchMode=yes` funciona).
- Proyecto en la Pi: `~/keepon/`. Se sincroniza desde la notebook con:
  `rsync -a --exclude .venv --exclude .git --exclude logs --exclude __pycache__ --exclude models/ --exclude config.local.yaml ./ r2d2@100.116.96.71:keepon/`
- Entorno: `~/keepon_env` (venv `--system-site-packages`, para ver `rclpy`). Tiene MediaPipe, OpenCV 4.11, pyyaml, pyserial, pytest y lap. **ultralytics/torch/ncnn se toman de `~/yolo_env`** mediante `zz_yolo_env.pth` (solo lectura, para no duplicar sus 5,5 GB).
- `~/keepon/config.local.yaml` (fuera de git) contiene `camera: {backend: ros2}`.
- **NO modificar** `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`: son de otros proyectos. Todo lo de Keepon va en `~/keepon` / `~/keepon_env`.
- La cámara funciona por `camera_ros` (libcamera compilada en `~/camera_ws`); no hay rpicam ni picamera2. Un solo dueño de la cámara a la vez: verificar con `pgrep -x camera_node` antes de lanzar algo.
- **Trampa de `pkill -f`:** si el patrón aparece en tu propio comando SSH, se mata a sí mismo. Usar la forma con corchetes: `pkill -f "[_]_node:=keepon_"`.
- Al hacer `source /opt/ros/jazzy/setup.bash`, no usar `set -u` (el script de ROS usa variables sin definir).

## Arquitectura (Python puro; ROS 2 solo como fuente de cámara)
```
camera_ros → keepon/perception.py (2 procesos) → World → Focus → behaviors → Arbiter → Actuators → Link → ESP32-C3
```
| Módulo | Qué hace |
|---|---|
| `protocol.py` | Protocolo serie v1 (`docs/PROTOCOLO.md`): sesión HELLO, `J S CANCEL PING STOP RESUME HOME`, ACK/DONE/ERR/STATE, validación estricta |
| `sim_esp32.py` | ESP32 simulado = **especificación ejecutable del firmware** (STOP enclavado, watchdog de 500 ms, dedupe de sonidos por seq, `reboot()`) |
| `trajectory.py` | Planificación discreta exacta (fórmula cerrada `_v_max_to_stop`): amax se respeta en las posiciones emitidas. El firmware tiene que copiarla |
| `link.py` | `SimLink` / `SerialLink`, misma interfaz. `SerialLink` todavía **no** reconecta solo |
| `arbiter.py` | Recursos NECK/BUZZER, prioridades 0–5, adquisición atómica, cooldown al empezar, propuestas que vencen, retarget, STOP |
| `behaviors.py` | Observador, Seguimiento, Saludo, Camiseta. **Faltan los modos** (Tímido/Atrevido/Maleducado/Neutro) y SALIENDO |
| `gaze.py` | Control P con zona muerta suave (sin integral) + foco con prioridad estricta a ME_MIRA e histéresis de 1,5 s |
| `robot.py` | Lazo principal, resincronización por reinicio del ESP32, edad máxima del mundo (0,3 s), EventLog CSV en `logs/` |
| `perception.py` | Proceso "personas" (YOLO26n 256 + tracker propio + rostros BlazeFace sobre recortes + solvePnP → ME_MIRA) y proceso "pose" (MediaPipe lite). Fijados a núcleos |
| `tracker.py` | Tracker IoU propio (el ByteTrack de ultralytics costaba ~68 ms/cuadro en la Pi) |
| `camera.py` | Backends ros2/picamera2/gstreamer/opencv; siempre entrega el último cuadro; `StaleFrame` |
| `synthetic.py` | Personas y cámara virtuales, en lazo cerrado con el cuello simulado |

`config.yaml` concentra **todos** los parámetros. `config.local.yaml` (por máquina, fuera de git) los sobreescribe.

## Decisiones tomadas (no volver a discutir sin datos nuevos)
- Todo corre en la Pi; Python puro; `rclpy` solo para leer la cámara. Codex coincidió (`docs/REVISION_CODEX_PI.md`).
- YOLO26n exportado a NCNN con **entrada de 256 px** (`~/keepon/models/yolo26n_256_ncnn_model`): detectó 2 de 2 personas a 1,5 m, a 30 Hz solo.
- Procesos separados, no hilos: NCNN y MediaPipe no liberan el GIL (medido: 2,11 s en serie vs 2,04 s en hilos).
- Afinidad de núcleos: personas `[0,1]` con NCNN de 2 hilos y `openmp_blocktime=0`; pose `[2,3]`. NCNN y MediaPipe reubican sus hilos en 0-3, por eso `_repin_threads()` los vuelve a fijar cada 50 cuadros.
- Rostros: BlazeFace (6 puntos) sobre un recorte de la cabeza en lugar de Face Landmarker (478 puntos, ~49 ms/cara).
- ME_MIRA = ángulo entre el eje de la cara y la línea cara→cámara < `looking_deg` (15°, **sin validar**).
- Intrínsecos tomados de `~/vision_estereo/config/calibracion/right_corregida.yaml` (fx=948 → **HFOV 37,3°**, no los 66° nominales: camera_ros a 640×480 recorta el sensor). cx=428 queda descentrado, así que el centro óptico no es el centro de la imagen. **Verificar que esa calibración corresponde a esta cámara.**

## Comandos
```bash
# Notebook (venv en .venv). La variable evita que se carguen los plugins de pytest de ROS 2:
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q        # 81 tests
.venv/bin/python scripts/sim_scenario.py --plot                        # escenario simulado de 30 s

# ESP32-C3 desde la notebook (arduino-cli 1.1.1 en ~/.local/bin, núcleo esp32:esp32 3.3.12 en ~/.arduino15)
cd pruebas_servos && ~/.local/bin/arduino-cli compile --fqbn esp32:esp32:esp32c3 --output-dir /tmp/build_servo prueba_servo
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32c3 --input-dir /tmp/build_servo
~/.local/bin/arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200   # uno solo a la vez en el puerto

# Pi
bash ~/keepon/scripts/ver_percepcion.sh          # visor en el navegador: http://100.116.96.71:8080/stream_viewer?topic=/keepon/percepcion
bash ~/keepon/scripts/ver_percepcion.sh stop
~/keepon/ver_personas.sh [stop]                  # solo YOLO (detector_node de vision_estereo), IMGSZ=256 por defecto
~/keepon_env/bin/python scripts/perception_bench.py --secs 20   # (con camera_node corriendo)
bash scripts/pi_bench.sh 15 [rapido]             # matriz de benchmark → logs/benchmark.csv
```

## Visores en la Pi (uno a la vez: comparten cámara y puerto 8080)
| | `scripts/ver_percepcion.sh` | `ver_personas.sh` (raíz del repo) |
|---|---|---|
| Qué muestra | Percepción completa de Keepon: personas (YOLO + tracker propio), rostros/ME_MIRA, pose con brazos (MediaPipe) | Solo recuadros de personas (YOLO26n 256 NCNN) |
| Código | `scripts/ver_percepcion.py` → `keepon/perception.py` (2 procesos) | `detector_node` de `~/yolo_ws` (vision_estereo, sin modificar) |
| Ver en | `/stream_viewer?topic=/keepon/percepcion` | `/stream_viewer?topic=/yolo/left/image_annotated` (cámara cruda: `/keepon_cam/image_raw`) |
| Velocidad (07/10) | El tópico del overlay llega a ~5 Hz (es solo el video; la percepción se mide con `perception_bench.py`) | **30 FPS**, detecta 1–2 personas |
| Uso | Calibrar ME_MIRA, ver brazos/SALUDO | Chequeo rápido de que cámara + YOLO andan |

Para cambiar de visor, primero `stop` del que está corriendo (`pgrep -x camera_node` tiene que dar vacío). Logs en `/tmp/keepon_*.log`.

## Rendimiento medido en la Pi (30/09, 1 persona)
- Personas + rostros: **16,9 Hz** (YOLO 34 ms + rostros 10 ms), edad del resultado 74 ms.
- Pose: **10,0 Hz**, edad 149 ms. CPU total: 239 % de 400 %.
- Rostro encontrado en el 80 % de las detecciones; ID estable. Detalle completo en `docs/ESTADO_PI.md`.

## Dónde quedó la sesión (07/10/2026)
- **Servos (09/10):** `prueba_servo.ino` flasheado en la ESP32-C3 (conectada a la notebook). **HS-7955TG (6 V), MG90S y SG90 (5 V) caracterizados**: los tres ejes tienen servo (planilla en `pruebas_servos/README.md`, calibración en `neck.servos`). Al cambiar servos, apagar antes la fuente: enchufar uno con la fuente prendida desconectó la ESP32 del USB. Para manejar la prueba por serie sin que la ESP32 se reinicie en cada comando, sirve un proceso que deje el puerto abierto y reciba los comandos por un FIFO.
- Si el puerto está ocupado, es casi siempre un `serial-monitor` abierto por el usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.
- Todo commiteado y subido. Los dos visores eligen la cámara por nombre (la segunda NoIR había corrido los índices); ambos probados con la cámara real.
- **`ver_personas.sh` quedó corriendo en la Pi** y ocupa la cámara. Detenerlo con `~/keepon/ver_personas.sh stop`.
- Pendiente: revisar el flex de la segunda NoIR (`i2c@88000`) o desconectarla.
- Se les pidió a los usuarios probar el visor (mirar / no mirar, girar la cabeza, levantar la mano, cruzarse) y anotar los grados de desvío para calibrar el umbral de ME_MIRA.

## Próximos pasos (hacia M1, el 8/10: el robot sigue a una persona con detecciones reales)
1. Con lo que reporten del visor: validar ME_MIRA y ajustar `looking_deg`; medir con 2–3 personas.
2. **Integrar la percepción al robot:** de `DetResult` a `World` (timestamps por evidencia, filtros N-de-M), ME_MIRA sostenido ≥ 0,5 s, SALUDO (muñeca sobre el hombro + ≥ 2 oscilaciones), y el control de mirada con el centro óptico cx/cy en lugar del centro de la imagen.
3. **Firmware de la ESP32-C3:** antes, pasar cada servo por `pruebas_servos/` y completar la planilla (centro, extremos, grados/µs). Después, portar `sim_esp32.py` + `trajectory.py`; timers LEDC separados para servos y buzzer; pruebas de conformidad contra el simulador. Necesita el ESP32 conectado a la Pi.
4. Camisetas: grabar con la NoIR las prendas reales (Olimpia, Cerro, lisas) a 0,8/1,5/2,5 m; **decisión el 4/10** (luz LED controlada, filtro IR-cut o cámara normal).
5. Pendientes técnicos: reconexión automática de `SerialLink`; autofoco (hoy `AfMode=0`, manual); secuencia de encendido de los servos; overlay completo (modo, dueño de recursos, ángulos) para T7; modos de personalidad y SALIENDO (M3).
6. `docs/hoja_de_ruta.html` sigue en la v2 (los .md están en la v3).

## Colaboración con Codex
Se usa `codex exec --skip-git-repo-check -s read-only -o <salida.md> "<prompt>"` para revisiones. Revisiones guardadas: `docs/REVISION_CODEX.md` (plan), `docs/REVISION_CODEX_M0.md` (código; sus 8 fallos están corregidos y tienen tests en `tests/test_regresiones_codex.py`), `docs/REVISION_CODEX_PI.md` (hardware real).

## Convenciones
- Español en código, comentarios, docs y commits. Commits con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Git local: `user.email = hvelazquez@fiuna.edu.py` (el email global era un texto de relleno).
- Cada cambio de rendimiento se **mide en la Pi** antes de darlo por bueno; los resultados van a `docs/ESTADO_PI.md`.
- Los bugs encontrados se convierten en tests de regresión.
