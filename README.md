# Keepon pro: cabeza robótica social de 3 GDL

µTP **Robótica Social**, Robótica II, FIUNA (2026). Cabeza con ojos, cuello de 3 grados de libertad
(yaw, pitch, roll), cámara en la cabeza y buzzer pasivo. Detecta personas, las sigue con la mirada,
responde a saludos, a miradas y a camisetas de Olimpia y Cerro, y tiene cuatro modos de personalidad.

- Consigna: [`docs/2026S2uTP_RoboticaSocial.md`](docs/2026S2uTP_RoboticaSocial.md) (PDF en `docs/`).
- **Informe técnico (Cuaderno Colab):** [`docs/informe/Informe_Keepon_pro.ipynb`](docs/informe/Informe_Keepon_pro.ipynb).
- **Guía completa del proyecto (PDF, con diagramas):** [`docs/guia/Guia_Keepon_pro.pdf`](docs/guia/Guia_Keepon_pro.pdf):
  construcción, hardware, pines, control de los motores, software, decisiones y resultados. Fuente: `docs/guia/guia_keepon.html`.
- **Qué está hecho y qué falta:** [`docs/CHECKLIST_TP.md`](docs/CHECKLIST_TP.md) (casilla por casilla de la consigna;
  versión interactiva en `docs/checklist_robotica_social.html`), [`docs/ESTADO.md`](docs/ESTADO.md) y
  [`docs/PENDIENTES.md`](docs/PENDIENTES.md).

## Hardware

| Parte | Qué es |
|---|---|
| Procesamiento | Raspberry Pi 5 (4 GB), Ubuntu 24.04 + ROS 2 Jazzy (ROS 2 solo para leer la cámara) |
| Cámara | Camera Module 3 NoIR (IMX708), montada invertida en la cabeza |
| Microcontrolador | ESP32-C3-DevKitM-1 (USB serie CH340): genera los pulsos de los servos y los tonos del buzzer |
| Servos | yaw: RDS3218 (GPIO0) · pitch: MG996R (GPIO1) · roll: MG996R (GPIO4) |
| Buzzer | módulo pasivo MH-FMD a 3V3, en GPIO5 (frecuencia variable: melodías) |
| Alimentación | servos: fuente de laboratorio a 6 V · Pi: powerbank Xiaomi PB2020MI · GND común |
| Mecánica | diseño propio v6 R4 impreso en 3D: [`docs/diseno_v6/`](docs/diseno_v6/README.md) |

Detalle de conexiones y alimentación: [`docs/HARDWARE.md`](docs/HARDWARE.md).

## Arquitectura

Todo corre en la Pi en **Python puro**. La ESP32 solo ejecuta trayectorias suaves y sonidos, sin bloquear.

```
cámara ─► percepción (2 procesos) ─► World ─► Focus ─► comportamientos ─► Árbitro ─► Actuators ─► Link ─► ESP32-C3
           perception.py              world.py gaze.py  behaviors.py       arbiter.py actuators.py link.py  firmware/
           eventos.py, camiseta.py
```

| Módulo | Qué hace |
|---|---|
| `keepon/perception.py` | Proceso "personas" (YOLO + tracker propio + rostros + orientación de la cabeza) y proceso "pose" (MediaPipe) |
| `keepon/tracker.py` | Tracker IoU propio: mantiene el ID de cada persona entre cuadros |
| `keepon/eventos.py` | Eventos con filtros temporales: PERSONA, ME_MIRA, SALUDO, SALIENDO |
| `keepon/camiseta.py` | Detector de camisetas Olimpia / Cerro con reglas de color y patrón sobre el torso |
| `keepon/world.py` | Modelo del mundo: personas con ID, posición y eventos activos |
| `keepon/gaze.py` | Control de mirada (zona muerta, saturación, suavizado) y foco de atención con histéresis |
| `keepon/behaviors.py` | Observador, Seguimiento, Saludo, Camiseta y los modos Neutro / Tímido / Atrevido / Maleducado |
| `keepon/arbiter.py` | Árbitro: recursos exclusivos (cuello y buzzer), prioridades, interrupciones, cooldowns, STOP |
| `keepon/actuators.py` | Descarta cualquier comando de quien no sea dueño del recurso |
| `keepon/trajectory.py` | Trayectorias con límites de posición, velocidad y aceleración (el firmware porta esta lógica) |
| `keepon/protocol.py`, `link.py` | Protocolo serie v1 Pi ↔ ESP32 ([`docs/PROTOCOLO.md`](docs/PROTOCOLO.md)) |
| `keepon/sim_esp32.py` | ESP32 simulada: especificación ejecutable del firmware (los tests comparan las dos) |
| `keepon/overlay.py` | Monitoreo T7: personas e ID, objetivo, eventos, modo, dueño de cada recurso y ángulos |
| `keepon/robot.py` | Lazo principal y log CSV con marca de tiempo de cada transición (`logs/`) |
| `config.yaml` | **Todos** los parámetros: límites, ganancias, umbrales, cooldowns, prioridades, sonidos |

Prioridades (0 = la más alta): OPERADOR 0 · SALUDO 1 · CAMISETA 2 · MODO 3 · SEGUIMIENTO 4 · OBSERVADOR 5.
Más detalle en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md); las decisiones y sus porqués, en [`docs/DECISIONES.md`](docs/DECISIONES.md).

### Modelos preentrenados usados (con su fuente)

- **YOLO26n** de [Ultralytics](https://github.com/ultralytics/ultralytics), exportado a NCNN (`scripts/export_yolo.py`): detección de personas.
- **MediaPipe** de Google ([github.com/google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe)): BlazeFace (rostros) y Pose lite (brazos, para el saludo).

El árbitro, los comportamientos, el control de la cabeza, el tracker, los eventos y el detector de camisetas son desarrollo propio.

## Instalación

### Notebook (desarrollo y tests, sin hardware)

```bash
uv venv .venv --python 3.12 && . .venv/bin/activate
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # solo x86
uv pip install -r requirements.txt

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q   # 219 tests (la variable evita los plugins de ROS 2)
python scripts/sim_scenario.py --plot                   # escenario simulado de 30 s -> logs/sim_scenario.png
```

Algunos tests compilan el núcleo del firmware y lo comparan con el simulador: necesitan `g++`.

### Raspberry Pi 5

1. Copiar el repo a `~/keepon` (por ejemplo, con `rsync`; ver [`docs/PI.md`](docs/PI.md)).
2. Entorno `~/keepon_env`: `python3 -m venv --system-site-packages ~/keepon_env` (así ve `rclpy`) e instalar
   `requirements.txt`. La cámara se lee con el nodo `camera_ros` de ROS 2 Jazzy.
3. `sudo usermod -aG dialout $USER` para usar el puerto serie de la ESP32 sin `sudo`.
4. Firmware de la ESP32-C3: `bash scripts/cargar_firmware.sh` ([`firmware/README.md`](firmware/README.md)).
   **Sostener la cabeza** mientras carga: los MG996R quedan flojos sin pulso.
5. `bash ~/keepon/scripts/keepon instalar` instala los servicios de usuario (`keepon` y `keepon-panel`).

## Ejecución

**Encender:** primero el powerbank (Pi) y después los 6 V de los servos, con la cabeza cerca de HOME. **Apagar:** al revés.

En la Pi, `keepon` es `bash ~/keepon/scripts/keepon`.

| Qué | Cómo |
|---|---|
| Arrancar / parar el robot | panel del celular, o `keepon arrancar` / `keepon parar` (al parar vuelve a HOME) |
| Panel del celular | `http://<ip-de-la-pi>:8081`: Encender / Apagar, modos, STOP, sonidos y volumen |
| Monitoreo (overlay T7) | `http://<ip-de-la-pi>:8080/stream_viewer?topic=/keepon/overlay` |
| Cambiar de personalidad | `keepon n` (Neutro) · `keepon t` (Tímido) · `keepon a` (Atrevido) · `keepon m` (Maleducado); cada modo tiene su beep |
| STOP | `keepon stop` (queda enclavado: detiene cuello y buzzer) · `keepon resume` lo libera · `keepon home` |
| Sonidos | `keepon sonido POLCA` (también R2D2, ABUCHEO, PIROPO, DESAPROBACION) · `keepon volumen 0-100` |
| Estado y log | `keepon estado` · `keepon log` (log CSV con marca de tiempo en `logs/run_*.csv`) |
| Arranque al encender (demo) | `keepon demo-on` / `keepon demo-off` |

Desde una notebook con acceso SSH a la Pi, `scripts/k <comando>` hace lo mismo (`KEEPON_PI=usuario@host`).
Sin el servicio: `bash ~/keepon/scripts/robot_vivo.sh` (Ctrl+C = STOP y apaga todo).

## Comportamientos

| Evento | Respuesta |
|---|---|
| Sin personas | **Observador**: mira alrededor con miradas suaves |
| PERSONA | **Seguimiento**: centra el rostro con yaw y pitch; prioriza a quien mira al robot, con histéresis |
| SALUDO (mano que se mueve) | 3 cabeceos + sonido tipo R2D2 (cooldown de 5 s por persona) |
| CAMISETA_OLIMPIA | polca de Olimpia **mientras sigue** a la persona (cooldown de 25 s por persona) |
| CAMISETA_CERRO | abucheo; las prendas lisas rojas o azules no disparan nada |
| ME_MIRA en modo Tímido | aparta la mirada unos segundos y vuelve de a poco |
| ME_MIRA en modo Atrevido | sostiene la mirada y levanta el mentón, sin dejar de seguir en yaw |
| SALIENDO en modo Maleducado | silba un piropo, una vez por salida (cooldown global de 40 s) |

## Estructura del repo

```
keepon/             el robot en Python          tests/            pytest (regresiones en test_regresiones_codex.py)
firmware/           ESP32-C3 (Arduino)          scripts/          arranque, panel, carga de firmware, benchmarks, visores
pruebas_servos/     banco de servos             pruebas_buzzer/   buzzer y sonidos
pruebas_camisetas/  detector de camisetas       docs/             consigna, arquitectura, hardware, CAD, revisiones
```

Rendimiento medido en la Pi: lazo 36–39 Hz, personas 12–17 Hz, pose 7–10 Hz ([`docs/ESTADO_PI.md`](docs/ESTADO_PI.md)).
