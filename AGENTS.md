# AGENTS.md: Keepon pro

Instrucciones para agentes de código (Codex y otros). **La fuente de verdad es `CLAUDE.md`**: hardware, acceso a la Pi, arquitectura, decisiones tomadas, comandos y estado de la última sesión. Leerlo antes de hacer cualquier cosa. Este archivo resume solo lo imprescindible (al 14/10/2026).

## Proyecto
Cabeza robótica social de 3 GDL (yaw/pitch/roll) con visión artificial, µTP de Robótica II (FIUNA). Demo física obligatoria el 30/10/2026. Enunciado: `docs/2026S2uTP_RoboticaSocial.md`. Plan: `docs/HOJA_DE_RUTA.md`.

## Reglas
- Español en código, comentarios, docs y commits. Código claro y comentado: todos los integrantes tienen que poder explicarlo en la defensa.
- El árbitro, los comportamientos y el control de la cabeza son desarrollo propio. Los modelos preentrenados (YOLO, MediaPipe) se citan.
- El repo es privado. No guardar imágenes de personas (`capturas/` está en `.gitignore`).
- Todos los parámetros van en `config.yaml`. `config.local.yaml` (por máquina) no se commitea.
- Los bugs encontrados se convierten en tests de regresión. Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q` (121; 34 compilan el firmware con g++).
- En la Pi (`ssh r2d2@100.116.96.71`), todo va en `~/keepon` y `~/keepon_env`. **No modificar** `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`.
- Las revisiones de Codex se piden en modo solo lectura y se guardan en `docs/REVISION_CODEX*.md`.

## Hardware
| Eje | Servo | GPIO (ESP32-C3) | Sin pulso |
|---|---|---|---|
| yaw | DSSERVO RDS3218 n.º 2 | 0 | mantiene la posición |
| pitch | Hitec HS-7955TG | 1 | mantiene la posición con fuerza |
| roll | TowerPro MG996R (banda muerta ~10°) | 4 | queda flojo: seguir mandando el último pulso |

- Buzzer **pasivo** en GPIO10 con 2N2222, 1 kΩ, 10 kΩ y 1N4148 (`pruebas_buzzer/README.md`). Todavía no está comprado.
- ESP32-C3-DevKitM-1 (clon con CH340), conectada a la Pi: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`. Abrir el puerto no la reinicia; un pulso de RTS sí.
- Alimentación: fuente de laboratorio a 6,0 V (límite 4–5 A) para los servos y powerbank Xiaomi para la Pi, con GND común. La LiPo salió del diseño.
- Calibración (centro, °/µs, límites, `signo`) en `neck.servos` de `config.yaml`. Planilla de banco en `pruebas_servos/README.md`. El `signo` de cada eje se define al montar.
- Modelo mecánico vigente: `docs/keepon_v4_cad/`. Diagrama eléctrico: `docs/diagrama_sistema/index.html`.

## Firmware (hecho el 14/10)
- `firmware/keepon_fw/`: `nucleo.cpp` tiene toda la lógica en C++ portable y es copia de `keepon/sim_esp32.py`, `trajectory.py` y `protocol.py`, la especificación ejecutable; `keepon_fw.ino` es solo hardware. `generado.h` lo escribe `scripts/generar_firmware.py` desde `config.yaml` y `pruebas_buzzer/simulador_sonidos.html`: no editarlo a mano.
- Si se cambia el comportamiento en Python o en C++, hay que cambiar el otro: `tests/test_firmware_nucleo.py` los compara paso a paso.
- Cargar: `bash scripts/cargar_firmware.sh`. Probar la placa real: `scripts/prueba_firmware_real.py` en la Pi (30 de 30 OK, latencia de 4,4 ms).

## Qué falta (ver "Próximos pasos" en CLAUDE.md)
1. Unir la percepción con el robot (`DetResult` → `World`, ME_MIRA sostenido, SALUDO) y correr el robot sobre la ESP32 real (`SerialLink`, con reconexión).
2. Modos de personalidad (Tímido, Atrevido, Maleducado, Neutro) con su comando y sonido, y el evento SALIENDO.
3. Detección de camisetas con la NoIR.
4. Overlay completo (T7), calibración de ME_MIRA y de la cámara, y la prueba con los servos montados.
- **La cámara no está conectada a la Pi** desde el 14/10: no lanzar nada de percepción sin confirmarlo.
