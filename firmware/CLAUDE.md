# firmware/: reglas del firmware de la ESP32-C3

Movido desde el `CLAUDE.md` de la raíz el 22/10/2026. Detalle de archivos y resultados en `firmware/README.md`.

## Qué es
| `firmware/keepon_fw/` | Firmware de la ESP32-C3: `nucleo.cpp` (C++ portable, copia de `sim_esp32`/`trajectory`/`protocol`, probado contra el simulador en `tests/test_firmware_nucleo.py`) + `keepon_fw.ino` (serie, LEDC, buzzer). `generado.h` sale de `config.yaml` y del simulador de sonidos (`scripts/generar_firmware.py`). Ver `firmware/README.md` |

## Reglas
- `nucleo.cpp` es **copia** de `keepon/sim_esp32.py` (la especificación ejecutable), `keepon/trajectory.py` (fórmula cerrada `_v_max_to_stop`, rampa a 100 Hz) y `keepon/protocol.py`. Si se cambia el comportamiento en Python o en C++, hay que cambiar el otro: `tests/test_firmware_nucleo.py` los compara paso a paso. El hook `.claude/hooks/conformidad.sh` corre esos tests al editar el núcleo o `config.yaml`.
- `generado.h` no se edita a mano: sale de `config.yaml` y del simulador de sonidos (`scripts/generar_firmware.py`).
- **Grados → µs** con `neck.servos` de `config.yaml` (centro, `grados_por_us` simple o `[lado <1500, lado >1500]`, min/max, `signo`). Pines: yaw GPIO0, pitch GPIO1, roll GPIO4, buzzer GPIO10, en timers LEDC separados (servos 50 Hz / 14 bits, buzzer aparte).
- **Por servo:** el HS (y el RDS) sin pulso **se quedan firmes**, el MG996R **queda flojo** → en STOP/watchdog seguir mandando el último pulso a los tres. El primer pulso después de encender salta a velocidad máxima → arrancar en una postura conocida (home). **Roll (MG996R):** banda muerta de ~10° → mandarle el objetivo de un solo movimiento en vez de acercarse de a poco.
- **Pruebas de conformidad:** correr los mismos escenarios contra `SimESP32` y contra la ESP32 real por `SerialLink`.
- Abrir el puerto no reinicia la ESP32; un pulso de RTS (con DTR bajo) sí.

## Comandos
```bash
# Firmware del robot: generar generado.h, compilar en la notebook y cargar en la ESP32 de la Pi (esptool 4.8.1 en ~/keepon_env)
.venv/bin/python scripts/generar_firmware.py      # después de cambiar config.yaml o los sonidos
bash scripts/cargar_firmware.sh                   # --local si la ESP32 está en la notebook
~/keepon_env/bin/python scripts/prueba_firmware_real.py   # en la Pi (cd ~/keepon): 30 pruebas sobre la ESP32 real
```
