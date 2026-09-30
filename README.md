# Keepon pro: cabeza social de 3 GDL

µTP Robótica Social, Robótica II, FIUNA. Hardware: Raspberry Pi 5 (4 GB, Ubuntu 24.04), Camera Module 3 NoIR, ESP32-S3 WROOM y 3 servos.

Toda la IA y la lógica corren en la Pi. El ESP32 solo ejecuta los movimientos de los servos y los sonidos del buzzer, de forma segura. La arquitectura y el plan están en `docs/HOJA_DE_RUTA.md` y `docs/hoja_de_ruta.html`.

```
cámara ─► percepción ─► World ─► Focus ─► comportamientos ─► Árbitro ─► Actuators ─► Link ─► ESP32
          (M2)          world.py  gaze.py  behaviors.py       arbiter.py actuators.py link.py  sim_esp32.py
```

| Módulo | Qué hace |
|---|---|
| `keepon/protocol.py` | Protocolo serie (ver `docs/PROTOCOLO.md`) |
| `keepon/sim_esp32.py` | ESP32 simulado: **especificación ejecutable del firmware** |
| `keepon/trajectory.py` | Trayectorias suaves (vmax, amax, límites). El firmware porta esta lógica. |
| `keepon/link.py` | `SimLink` / `SerialLink` con la misma interfaz |
| `keepon/arbiter.py` | Árbitro: recursos exclusivos, prioridades, adquisición atómica, cooldowns, STOP |
| `keepon/behaviors.py` | Observador, Seguimiento, Saludo, Camiseta (los modos llegan en M3) |
| `keepon/gaze.py` | Control de mirada P con zona muerta suave + foco de atención con histéresis |
| `keepon/actuators.py` | Descarta cualquier comando de quien no sea dueño del recurso |
| `keepon/robot.py` | Lazo principal + log CSV de transiciones (`logs/`) |
| `keepon/synthetic.py` | Personas y cámara sintéticas para probar sin mecánica |
| `keepon/camera.py` | Captura de cámara (picamera2 / GStreamer / OpenCV) que siempre entrega el último cuadro |
| `config.yaml` | **Todos** los parámetros (límites, ganancias, cooldowns, prioridades) |

## Uso rápido (notebook o Pi)

```bash
uv venv .venv --python 3.12 && . .venv/bin/activate
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # sólo x86
uv pip install -r requirements.txt

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest     # 37 tests (la variable evita los plugins de ROS 2)
python scripts/sim_scenario.py --plot                  # escenario completo simulado -> logs/sim_scenario.png
python scripts/benchmark.py                            # Hz de la percepción (correr EN LA PI)
```

## Raspberry Pi 5 (Ubuntu 24.04)

> ⚠️ No probado todavía en la Pi del grupo. En Ubuntu, la Camera Module 3 depende de tener un libcamera con soporte para la Pi 5.

1. `bash scripts/check_pi.sh` informa qué hay: cámaras, picamera2/GStreamer, ESP32 y temperatura.
2. Si `rpicam-hello --list-cameras` no detecta la IMX708, hay que instalar el libcamera y rpicam-apps de Raspberry Pi. Es el **primer bloqueo que hay que resolver**.
3. Crear el entorno con `uv venv .venv --python 3.12 --system-site-packages`, para que el venv vea `picamera2`/`libcamera` si están instalados por apt.
4. En la Pi no hace falta torch-cpu aparte: `ultralytics` lo trae, y el benchmark exporta YOLO a NCNN la primera vez.
5. Se necesita **cooler activo** y una fuente de 27 W (5 V 5 A) solo para la Pi, separada de la fuente de los servos.
6. `sudo usermod -aG dialout $USER` para acceder al ESP32 sin sudo.

### Hardware: puntos a tener en cuenta

- **Cámara NoIR:** no tiene filtro infrarrojo, así que los colores salen corridos (rojos y blancos rosados) con luz solar o incandescente. Esto afecta directamente a **CAMISETA_OLIMPIA/CERRO**. Probar desde el día 1 con las camisetas reales y bajo iluminación LED. Si falla, conseguir una Camera Module 3 estándar o una webcam USB para la cabeza.
- **Cable de cámara:** la Pi 5 usa conector de 22 pines y la Camera Module 3 de 15, por lo que hace falta un cable 22→15. Tiene que ser **largo (30–50 cm) y con holgura** alrededor del eje de yaw (±70°).
- **ESP32-S3:** conectarlo por el puerto USB nativo (aparece como `/dev/ttyACM0`). Usar un timer LEDC distinto para servos y buzzer.

## Estado

- [x] **M0 software:** protocolo, simulador del ESP32, árbitro, 4 comportamientos, control de mirada, foco de atención, log, escenario sintético, 37 tests y benchmark.
- [ ] M0 en la Pi: `check_pi.sh` + `benchmark.py` (objetivo ≥ 10 Hz). Notebook de referencia: 11,6 Hz.
- [ ] Firmware ESP32-S3 (portar `sim_esp32.py` + `trajectory.py`)
- [ ] M2: percepción real (PERSONA + tracking, asociación por ID, ME_MIRA, SALUDO, camisetas)
- [ ] M3: modos de personalidad, SALIENDO, overlay de monitoreo

La lógica del árbitro, de los comportamientos y del control es desarrollo propio, y **todos** los integrantes deben poder explicarla en la defensa.
