# AGENTS.md: Keepon pro

Instrucciones para agentes de código (Codex y otros). **La fuente de verdad es `CLAUDE.md`**: hardware, acceso a la Pi, arquitectura, decisiones tomadas, comandos y estado de la última sesión. Leerlo antes de hacer cualquier cosa. Este archivo resume solo lo imprescindible.

## Proyecto
Cabeza robótica social de 3 GDL (yaw/pitch/roll) con visión artificial, µTP de Robótica II (FIUNA). Demo física obligatoria el 30/10/2026. Enunciado: `docs/2026S2uTP_RoboticaSocial.md`. Plan: `docs/HOJA_DE_RUTA.md`.

## Reglas
- Español en código, comentarios, docs y commits. Código claro y comentado: todos los integrantes tienen que poder explicarlo en la defensa.
- El árbitro, los comportamientos y el control de la cabeza son desarrollo propio. Los modelos preentrenados (YOLO, MediaPipe) se citan.
- El repo es privado. No guardar imágenes de personas (`capturas/` está en `.gitignore`).
- Todos los parámetros van en `config.yaml`. `config.local.yaml` (por máquina) no se commitea.
- Los bugs encontrados se convierten en tests de regresión. Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`.
- En la Pi (`ssh r2d2@100.116.96.71`), todo va en `~/keepon` y `~/keepon_env`. **No modificar** `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`.
- Las revisiones de Codex se piden en modo solo lectura y se guardan en `docs/REVISION_CODEX*.md`.

## Hardware de los servos (12/10/2026)
| Eje | Servo | GPIO (ESP32-C3) | Sin pulso |
|---|---|---|---|
| yaw | DSSERVO RDS3218 n.º 2 | 0 | mantiene la posición |
| pitch | Hitec HS-7955TG | 1 | mantiene la posición con fuerza |
| roll | TowerPro MG90S | 4 | queda flojo: seguir mandando el último pulso |

- Fuente de servos de 6,0 V (máximo del MG90S), separada de la Pi, con GND común con la ESP32.
- Sentido de giro, visto de frente al eje: pulso mayor = antihorario en el RDS3218 y el MG90S, horario en el HS. Se compensa con `signo` por eje en `config.yaml`.
- Calibración (centro, °/µs, límites) en `neck.servos` de `config.yaml`. Planilla y procedimiento de banco en `pruebas_servos/README.md`.
- El firmware del robot todavía no existe (`firmware/` vacío). Su especificación ejecutable es `keepon/sim_esp32.py` + `keepon/trajectory.py`, y el protocolo está en `docs/PROTOCOLO.md`.
