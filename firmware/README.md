# Firmware de Keepon pro (ESP32-C3)

Implementa el protocolo de `docs/PROTOCOLO.md`: sesión HELLO, `J S CANCEL PING STOP RESUME HOME`, respuestas
`ACK DONE ERR STATE`, STOP enclavado, watchdog de 500 ms, trayectoria a 100 Hz y sonidos en el buzzer.
Se comporta igual que `keepon/sim_esp32.py`, que es la especificación ejecutable.

## Archivos

| Archivo | Qué hace |
|---|---|
| `keepon_fw/keepon_fw.ino` | Capa de hardware: puerto serie, pulsos LEDC de los servos (GPIO0/1/4) y tono del buzzer (GPIO10) |
| `keepon_fw/nucleo.h`, `nucleo.cpp` | Toda la lógica, en C++ portable (sin Arduino): protocolo, trayectoria, estados, sonidos, grados → µs |
| `keepon_fw/generado.h` | **Generado** por `scripts/generar_firmware.py` desde `config.yaml` y `pruebas_buzzer/simulador_sonidos.html`. No editar a mano |
| `pruebas_host/arnes.cpp` | Corre el núcleo en la notebook para compararlo con el simulador (lo usa `tests/test_firmware_nucleo.py`) |

Cada función de `nucleo.cpp` indica de qué función de Python es copia (`trajectory.py`, `protocol.py`, `sim_esp32.py`).
Si se cambia el comportamiento en un lado, hay que cambiarlo en el otro: los tests lo detectan.

## Uso

```bash
# Después de cambiar config.yaml o los sonidos del simulador:
.venv/bin/python scripts/generar_firmware.py

# Pruebas en la notebook (núcleo contra SimESP32, paso a paso; necesita g++):
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_firmware_nucleo.py

# Compilar en la notebook y cargar en la ESP32 conectada a la Pi (esptool de ~/keepon_env):
bash scripts/cargar_firmware.sh            # --local si la ESP32 está en la notebook

# Probar la ESP32 real (en la Pi; no necesita servos ni fuente de 6 V):
cd ~/keepon && ~/keepon_env/bin/python scripts/prueba_firmware_real.py
```

## Resultados en la ESP32 real (14/10/2026, por la Pi)

`prueba_firmware_real.py`: **30 de 30 OK**.

- Latencia PING → ACK, ida y vuelta: **4,4 ms** de media, 4,9 ms de máximo (50 PING).
- Un movimiento a 70/30/−20 llega en 0,68 s; el simulador dice 0,69 s (el lazo de 100 Hz va en tiempo).
- `BEEP_NEUTRO` (250 ms): `DONE` a los 258–262 ms. Watchdog: `ERR 0 WATCHDOG` a los ~490 ms del último comando.
- 304 KB de flash (23 %), 14 KB de RAM (4 %).

## Detalles

- **Arranque:** el cuello arranca en HOME y manda `HELLO 0 1 1`. Los servos no tienen realimentación: el primer pulso
  los lleva a HOME a toda velocidad. Encender los 6 V después que la Pi, con la cabeza cerca de HOME.
- **STOP y watchdog** frenan con amax hasta `brake_target()` y siguen mandando el pulso (el MG996R sin pulso queda flojo;
  el HS-7955TG sin pulso igual mantiene la posición). Para aflojar los servos hay que cortar los 6 V.
- **Buzzer:** tablas de segmentos `{f_inicio, f_fin, ms}`; en los barridos la frecuencia cambia cada 5 ms.
  `ledcWriteTone()` solo se llama cuando cambia la nota.
- **Pendiente:** probar con los servos y la fuente de 6 V (el `signo` de cada eje se define al montar), y con el buzzer
  cuando llegue. El roll (MG996R) tiene ~10° de banda muerta: no se le hace nada especial todavía.
