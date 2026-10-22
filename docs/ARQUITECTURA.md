# Arquitectura del software

Movido desde `CLAUDE.md` el 22/10/2026.

## Arquitectura (Python puro; ROS 2 solo como fuente de cámara)
```
camera_ros → keepon/perception.py (2 procesos) → World → Focus → behaviors → Arbiter → Actuators → Link → ESP32-C3
```
| Módulo | Qué hace |
|---|---|
| `protocol.py` | Protocolo serie v1 (`docs/PROTOCOLO.md`): sesión HELLO, `J S CANCEL PING STOP RESUME HOME`, ACK/DONE/ERR/STATE, validación estricta |
| `sim_esp32.py` | ESP32 simulado = **especificación ejecutable del firmware** (STOP enclavado, watchdog de 500 ms, dedupe de sonidos por seq, `reboot()`) |
| `firmware/keepon_fw/` | Firmware de la ESP32-C3: `nucleo.cpp` (C++ portable, copia de `sim_esp32`/`trajectory`/`protocol`, probado contra el simulador en `tests/test_firmware_nucleo.py`) + `keepon_fw.ino` (serie, LEDC, buzzer). `generado.h` sale de `config.yaml` y del simulador de sonidos (`scripts/generar_firmware.py`). Ver `firmware/README.md` |
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
