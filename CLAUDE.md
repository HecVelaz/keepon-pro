# CLAUDE.md: Keepon pro

## Proyecto
Cabeza robótica social de 3 GDL (yaw/pitch/roll) con visión artificial. µTP de Robótica II, FIUNA. Grupo de hasta 5 personas.
**Demo física obligatoria el 30/10/2026** (Segundo Parcial). Sin demo física no hay puntaje.
Enunciado: `docs/2026S2uTP_RoboticaSocial.md`. Plan: `docs/HOJA_DE_RUTA.md` (v3).
- **Pi 5 (4 GB)**, Ubuntu 24.04 + ROS 2 Jazzy (no se puede cambiar el SO: la Pi se usa en otros proyectos), con Camera Module 3 NoIR estándar (IMX708). Todo corre en la Pi, en **Python puro**; `rclpy` solo para leer la cámara.
- **ESP32-C3-DevKitM-1** (clon CH340, `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`) para los 3 servos (yaw RDS3218 GPIO0, pitch HS-7955TG GPIO1, roll MG996R GPIO4) y el buzzer (GPIO10), con el protocolo serie v1 (`docs/PROTOCOLO.md`).
- Servos con fuente de laboratorio a 6 V; la Pi con powerbank Xiaomi PB2020MI. GND común. La notebook (x86, sin CUDA) es solo para desarrollar.

## Reglas
- El estado va en `docs/ESTADO.md`, nunca en `CLAUDE.md`. Este archivo solo cambia si cambia una regla.
- Al cerrar una sesión: `/cerrar`; al empezar: `/retomar`.
- **El árbitro, los comportamientos y el control de la cabeza tienen que ser desarrollo propio.** Se pueden usar modelos preentrenados (YOLO, MediaPipe) citando la fuente. Todos los integrantes deben poder explicar cualquier parte en la defensa: código claro y comentado en español.
- Si hay copia entre grupos, se anula el trabajo: **el repo es privado** (github.com/HecVelaz/keepon-pro).
- No guardar imágenes de personas sin consentimiento: `capturas/` está en `.gitignore`. Las capturas de verificación se borran después de mirarlas.
- Requisitos duros: percepción ≥ 10 Hz y latencia evento→respuesta ≤ 300 ms; todo no bloqueante; recursos exclusivos (cuello y buzzer); prioridades, cooldowns, histéresis; overlay y log con marca de tiempo (T7).
- `config.yaml` concentra **todos** los parámetros. `config.local.yaml` (por máquina, fuera de git) los sobreescribe.
- Las decisiones de `docs/DECISIONES.md` no se vuelven a discutir sin datos nuevos.
- Español en código, comentarios, docs y commits. Commits con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Git local: `user.email = hvelazquez@fiuna.edu.py` (el email global era un texto de relleno).
- Cada cambio de rendimiento se **mide en la Pi** antes de darlo por bueno; los resultados van a `docs/ESTADO_PI.md`.
- Los bugs encontrados se convierten en tests de regresión.
- **Nombres de archivos y carpetas sin espacios** (guion bajo en su lugar): Windows no admite nombres que terminan en espacio o punto. Al renombrar, usar `git mv`, buscar las referencias con `git grep` y actualizarlas. El `rsync` a la Pi no borra: la copia vieja queda allá y hay que borrarla a mano, después de comparar con `cmp` que la nueva es idéntica.
- Cambios que el grupo tiene que revisar: rama + pull request con `gh`. `gh pr edit` falla por un error de GitHub con "Projects (classic)" y no guarda nada: editar el PR con `gh api -X PATCH repos/HecVelaz/keepon-pro/pulls/<n>`.
- Codex: Se usa `codex exec --skip-git-repo-check -s read-only -o <salida.md> "<prompt>"` para revisiones. Revisiones guardadas: `docs/REVISION_CODEX.md` (plan), `docs/REVISION_CODEX_M0.md` (código; sus 8 fallos están corregidos y tienen tests en `tests/test_regresiones_codex.py`), `docs/REVISION_CODEX_PI.md` (hardware real).
- **En la Pi** (`ssh r2d2@100.116.96.71`): todo lo de Keepon va en `~/keepon` / `~/keepon_env`. **NO modificar** `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`. Un solo dueño de la cámara a la vez (`pgrep -x camera_node`). Trampas de `pkill -f` y `set -u`: ver `docs/PI.md`.
- **Encender:** primero el powerbank y después los 6 V, con la cabeza cerca de home. **Apagar:** al revés. Al cambiar servos, apagar antes la fuente.
- Puerto serie ocupado: casi siempre es un `serial-monitor` del usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.

## Comandos
```bash
# Notebook (venv en .venv). La variable evita que se carguen los plugins de pytest de ROS 2:
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q        # 121 tests (34 comparan el firmware con el simulador; necesitan g++)
.venv/bin/python scripts/sim_scenario.py --plot                        # escenario simulado de 30 s
```
Firmware: `firmware/CLAUDE.md`. Banco de servos: `pruebas_servos/CLAUDE.md`. Pi (sincronizar, visores, benchmarks): `docs/PI.md`.

## Qué leer para cada cosa
| Para… | Leer |
|---|---|
| Saber dónde quedó el trabajo | `docs/ESTADO.md` |
| Qué falta hacer | `docs/PENDIENTES.md` |
| Por qué se eligió algo | `docs/DECISIONES.md` |
| Módulos de `keepon/` y flujo de datos | `docs/ARQUITECTURA.md` |
| Hardware: cámara, ESP32, servos, alimentación | `docs/HARDWARE.md` |
| Acceso a la Pi, rsync, comandos y visores | `docs/PI.md` |
| Sistema de la Pi y rendimiento medido | `docs/ESTADO_PI.md` |
| Protocolo serie Pi ↔ ESP32 | `docs/PROTOCOLO.md` |
| Firmware de la ESP32-C3 | `firmware/CLAUDE.md`, `firmware/README.md` |
| Pruebas de banco de los servos | `pruebas_servos/CLAUDE.md`, `pruebas_servos/README.md` |
| Buzzer y sonidos | `pruebas_buzzer/README.md` |
| Detector de camisetas | `pruebas_camisetas/README.md` |
| Modelo mecánico (vigente: v4) | `docs/keepon_v4_cad/README.md` |
| Diagrama eléctrico / del sistema | `docs/diagrama_sistema/index.html` |
| Revisiones de Codex | `docs/REVISION_CODEX.md`, `docs/REVISION_CODEX_M0.md`, `docs/REVISION_CODEX_PI.md`, `docs/REVISION_CODEX_ARQ.md`, `docs/REVISION_CODEX_HW.md` |

## Estructura
```
camera_ros → keepon/perception.py (2 procesos) → World → Focus → behaviors → Arbiter → Actuators → Link → ESP32-C3
```
- `keepon/`: el robot en Python (`sim_esp32.py` es la especificación ejecutable del firmware). `tests/`: pytest (regresiones de Codex en `tests/test_regresiones_codex.py`).
- `firmware/`: ESP32-C3. `scripts/`: generación de firmware, carga, benchmarks, visores. `pruebas_*/`: banco de servos, buzzer, camisetas. `docs/`: enunciado, plan, CAD, revisiones.
