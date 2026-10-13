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
- **ESP32-C3-DevKitM-1** (no S3) para los 3 servos y el buzzer, por el micro-USB con puente UART (`/dev/ttyUSB0`; preferir `/dev/serial/by-id/...`). Pines: yaw GPIO0, pitch GPIO1, roll **GPIO4** (antes GPIO3; se cambió el 12/10 buscando una vibración que al final era del servo, y quedó así: el GPIO3 está al lado del GPIO2, de strapping), buzzer GPIO10; evitar 2/8/9 (strapping), 18/19 (USB) y 20/21 (UART0). Análisis completo en `docs/REVISION_CODEX_HW.md` (escrito para microservos). Es un **clon con conversor CH340** (`1a86:7523`, `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`). Por ahora está conectada a la **notebook**, no a la Pi, y tiene cargado `pruebas_servos/prueba_servo.ino`. El firmware del robot no existe (`firmware/` está vacío).
- **Servos (asignación del 12/10, todos en `neck.servos` de `config.yaml`; planilla completa en `pruebas_servos/README.md`):**
  - **yaw = DSSERVO RDS3218 n.º 2** (GPIO0): 270°, asimétrico 0,13/0,136 °/µs (lista `[lado <1500, lado >1500]`), ±70° ≈ 960/2010 µs, límites 950/2020 (no tiene tope: los límites protegen el cableado), banda muerta ≤ 2 µs abajo y 4–6 µs arriba, picos de ~1 A a 260 °/s. **Sin pulso mantiene la posición.**
  - **pitch = Hitec HS-7955TG** (GPIO1, ~18 kgf·cm): 0,090 °/µs lineal, límites electrónicos 750/2250 µs (≈ ±68°; en el firmware 760/2240), banda muerta ≤ 2 µs, holgura ≤ 1°, 6 mA en reposo. **Sin pulso mantiene la posición con fuerza**: el STOP/watchdog la congela, no la afloja (para aflojarlo hay que cortar los 6 V). El primer pulso después de encender salta a velocidad máxima: el firmware tiene que arrancar en una postura conocida. Es el servo que más ruido mete en la alimentación.
  - **roll = TowerPro MG996R** (GPIO4, desde el 13/10): lineal y simétrico 0,092 °/µs, límites 1000/2000 µs (roll pide ±20°), sin tope hasta 800/2300 µs. **Banda muerta de ~100–110 µs (≈ 10°) e intermitente**: de +10° a 0° no volvió en 3 de 10 intentos; pasos de 20° andan siempre. Se aceptó porque roll hace gestos grandes; el firmware tiene que mandarle el objetivo de un solo movimiento. **Sin pulso queda flojo**. Pesa 55 g. Sentido de giro sin anotar. El MG90S (0,090/0,085 °/µs, banda muerta 20–30 µs, al máximo de su tensión a 6 V) queda de repuesto.
  - **Sentido de giro** (12/10, visto de frente al eje): pulso mayor = **antihorario** en los RDS3218 y el MG90S (el MG996R, sin anotar); **horario** en el HS. Para que yaw y pitch giren juntos en el banco hay que mandarle al HS el pulso en espejo (1500 − Δ). En el robot lo resuelve `signo` por eje, que se define al montar.
  - **Descartado: RDS3218 n.º 1.** Vibra (≈ 0,5 A) al quedar quieto cerca de 1500 µs, sobre todo con el HS activo; intercambiándolo con el n.º 2, la vibración siguió al servo (no era pin, señal ni cableado). Repuestos: SG90 (0,090 °/µs, engranajes plásticos, sin pulso queda flojo). El SM-S4315R es de rotación continua.
  - Los tres juntos andan bien a velocidad alta (12/10, fuente de laboratorio a 6 V). Recomendado igual: capacitor de 1000–2200 µF + 100 nF cerca de los servos y GND en estrella. **Sin GND común entre la ESP32 y la fuente, ningún servo se mueve.** Como son servos estándar (13–65 g), el rodamiento de yaw tiene que soportar el peso y el vuelco.
- **Fuente de servos:** 6 V, separada de la de la Pi, con GND común; ≥ 6 A para los tres juntos (2,5–4,2 A por servo con el eje trabado). La ALP002 ajustable (3–24 V, **1,5 A**, **entrada 100–120 V de alterna: no enchufar a 220 V sin transformador**) sirve solo para probar un servo sin carga. Para las pruebas individuales, mejor la fuente de laboratorio con límite de corriente.
- Pruebas de banco de los servos: `pruebas_servos/`: README con conexionado, procedimiento y planilla; `prueba_servo.ino` (comandos por serie a 115200: `e <eje>`, `c`, `p <us>`, `+`/`-`, `b <us1> <us2>`, `s`, `o`/`O`, `v <us/s>` (todos los ejes), `w <us/s>` (solo el eje elegido: para sincronizar recorridos distintos, `w` = recorrido / tiempo), `l <min> <max>`, `?`, `h`); `simulador_hs7955tg.html` (diagrama de conexiones + ESP32 y fuente simuladas, se abre en el navegador).
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

## Dónde quedó la sesión (13/10/2026)
- **Roll pasó al MG996R** (decisión del grupo; MG90S de repuesto). Se caracterizó en el banco: ver la sección "MG996R (13/10)" de `pruebas_servos/README.md`. Falta anotar su sentido de giro.
- **El banco ya quedó conectado como en el robot:** RDS3218 n.º 2 en GPIO0 (yaw), HS-7955TG en GPIO1 (pitch), MG996R en GPIO4 (roll). Barrido 0 ↔ 45° los tres juntos a ≈ 180 °/s, sincronizados con `w`: bien. `prueba_servo.ino` sigue en la ESP32-C3, conectada a la notebook.
- Manejo por serie sin reiniciar la ESP32: un proceso Python deja el puerto abierto y reenvía los comandos de un FIFO. Para mandar varios ejes **a la vez**, escribir todas las líneas juntas (`printf 'e 0\nb 1500 1843\ne 1\nb 1500 1000\n' > fifo`). Abrir el puerto de cero reinicia la ESP32 una vez (todos los ejes quedan sin pulso).
- **Próxima sesión: empezar el firmware del robot** (`firmware/`, hoy vacío; Arduino con arduino-cli, como `prueba_servo`). Puntos de partida:
  - **Especificación:** `docs/PROTOCOLO.md` + `keepon/sim_esp32.py` (sesión HELLO, `J S CANCEL PING STOP RESUME HOME`, ACK/DONE/ERR/STATE, STOP enclavado, watchdog de 500 ms, dedupe de sonidos por seq) + `keepon/trajectory.py` (copiar la fórmula cerrada `_v_max_to_stop`, rampa a 100 Hz).
  - **Grados → µs** con `neck.servos` de `config.yaml` (centro, `grados_por_us` simple o `[lado <1500, lado >1500]`, min/max, `signo`). Pines: yaw GPIO0, pitch GPIO1, roll GPIO4, buzzer GPIO10, en timers LEDC separados (servos 50 Hz / 14 bits, buzzer aparte). Se puede reusar `escribir()` y `ledcAttach` de `prueba_servo.ino`.
  - **Por servo:** el HS (y el RDS) sin pulso **se quedan firmes**, el MG996R **queda flojo** → en STOP/watchdog seguir mandando el último pulso a los tres. El primer pulso después de encender salta a velocidad máxima → arrancar en una postura conocida (home). **Roll (MG996R):** banda muerta de ~10° → mandarle el objetivo de un solo movimiento en vez de acercarse de a poco.
  - **Pruebas de conformidad:** correr los mismos escenarios contra `SimESP32` y contra la ESP32 real por `SerialLink`.
  - Antes de empezar: anotar el sentido de giro del MG996R (pulso mayor = ¿horario o antihorario?, de frente al eje) y corregir `serial.port` de `config.yaml`, que todavía dice `/dev/ttyACM0` (ESP32-S3): es `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` (CH340).
  - La ESP32 sigue en la notebook; para la integración hay que pasarla a la Pi.

## Sesión anterior (07/10/2026)
- Al cambiar servos, apagar antes la fuente: enchufar uno con la fuente prendida desconectó la ESP32 del USB (y otra vez se reinició por pérdida de alimentación, `rst:0x1 (POWERON)` en el log).
- Si el puerto está ocupado, es casi siempre un `serial-monitor` abierto por el usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.
- Todo commiteado y subido. Los dos visores eligen la cámara por nombre (la segunda NoIR había corrido los índices); ambos probados con la cámara real.
- **`ver_personas.sh` quedó corriendo en la Pi** y ocupa la cámara. Detenerlo con `~/keepon/ver_personas.sh stop`.
- Pendiente: revisar el flex de la segunda NoIR (`i2c@88000`) o desconectarla.
- Se les pidió a los usuarios probar el visor (mirar / no mirar, girar la cabeza, levantar la mano, cruzarse) y anotar los grados de desvío para calibrar el umbral de ME_MIRA.

## Próximos pasos (hacia M1, el 8/10: el robot sigue a una persona con detecciones reales)
1. Con lo que reporten del visor: validar ME_MIRA y ajustar `looking_deg`; medir con 2–3 personas.
2. **Integrar la percepción al robot:** de `DetResult` a `World` (timestamps por evidencia, filtros N-de-M), ME_MIRA sostenido ≥ 0,5 s, SALUDO (muñeca sobre el hombro + ≥ 2 oscilaciones), y el control de mirada con el centro óptico cx/cy en lugar del centro de la imagen.
3. **Firmware de la ESP32-C3:** los servos ya están elegidos y caracterizados (falta el sentido de giro del MG996R). Portar `sim_esp32.py` + `trajectory.py`; timers LEDC separados para servos y buzzer; pruebas de conformidad contra el simulador. Necesita el ESP32 conectado a la Pi.
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
