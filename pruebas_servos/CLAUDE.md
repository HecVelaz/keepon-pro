# pruebas_servos/: reglas de las pruebas de banco

Movido desde el `CLAUDE.md` de la raíz el 22/10/2026. Conexionado, procedimiento y planilla en `pruebas_servos/README.md`.
Esto **no** es el firmware del robot (ese está en `firmware/`).

- Pruebas de banco de los servos: `pruebas_servos/`: README con conexionado, procedimiento y planilla; `prueba_servo/prueba_servo.ino` (comandos por serie a 115200: `e <eje>`, `c`, `p <us>`, `+`/`-`, `b <us1> <us2>`, `s`, `o`/`O`, `v <us/s>` (todos los ejes), `w <us/s>` (solo el eje elegido: para sincronizar recorridos distintos, `w` = recorrido / tiempo), `l <min> <max>`, `?`, `h`); `simulador_hs7955tg.html` (diagrama de conexiones + ESP32 y fuente simuladas, se abre en el navegador).
- La rampa del programa de prueba arranca en `v 300` (≈27 °/s con 0,09 °/µs supuestos): **el giro lento es a propósito**. El HS-7955TG da ~315 °/s sin carga; `config.yaml` limita pitch a 120 °/s (Codex recomendó empezar con 60 °/s ≈ `v 700`).

## Comandos (desde la notebook; arduino-cli 1.1.1 en ~/.local/bin, núcleo esp32:esp32 3.3.12 en ~/.arduino15)
```bash
cd pruebas_servos && ~/.local/bin/arduino-cli compile --fqbn esp32:esp32:esp32c3 --output-dir /tmp/build_servo prueba_servo
~/.local/bin/arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32c3 --input-dir /tmp/build_servo
~/.local/bin/arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200   # uno solo a la vez en el puerto
```

## Reglas
- Manejo por serie sin reiniciar la ESP32: un proceso Python deja el puerto abierto y reenvía los comandos de un FIFO. Para mandar varios ejes **a la vez**, escribir todas las líneas juntas (`printf 'e 0\nb 1500 1843\ne 1\nb 1500 1000\n' > fifo`). Abrir el puerto de cero reinicia la ESP32 una vez (todos los ejes quedan sin pulso).
- Al cambiar servos, apagar antes la fuente: enchufar uno con la fuente prendida desconectó la ESP32 del USB (y otra vez se reinició por pérdida de alimentación, `rst:0x1 (POWERON)` en el log).
- Si el puerto está ocupado, es casi siempre un `serial-monitor` abierto por el usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.
- Para volver a las pruebas de banco con la ESP32 del robot, cargar `prueba_servo/prueba_servo.ino` (el firmware del robot se vuelve a cargar con `bash scripts/cargar_firmware.sh`).
