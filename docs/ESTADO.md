# Estado del proyecto

Movido desde `CLAUDE.md` el 22/10/2026. Lo más reciente va arriba. Al cerrar una sesión (`/cerrar`) se actualiza este archivo, no `CLAUDE.md`.

## Estado del hardware (al 15/10/2026)
- La ESP32-C3 **desde el 14/10 está conectada a la Pi y tiene cargado el firmware del robot** (`firmware/keepon_fw/`).
- **La cámara no está conectada a la Pi** (14/10): no lanzar nada de percepción sin confirmarlo.
- Los tres servos juntos andan bien a velocidad alta (12/10, fuente de laboratorio a 6 V).
- Conectado directo por USB-C, el powerbank alimenta bien a la Pi (14/10, en el banco): 5,08 V, `throttled=0x0`.

## Dónde quedó la sesión (14/10/2026 noche y 15/10)
- **Firmware del robot hecho y cargado** en la ESP32-C3, conectada a la Pi (`firmware/`, ver su README). El núcleo da exactamente las mismas respuestas y posiciones que `SimESP32` (34 tests, con fuzzing). En la ESP32 real, `prueba_firmware_real.py`: **30 de 30 OK**, latencia PING→ACK de 4,4 ms y el movimiento llega en el mismo tiempo que en el simulador. Sin servos ni buzzer conectados: falta probarlo con la fuente de 6 V (y definir `signo` al montar) y con el buzzer.
- `sim_esp32.py`: el watchdog y el fin del sonido comparan con un margen de 1e-9 (el tiempo acumulado en float saltaba un paso según el redondeo; el firmware cuenta ms enteros).
- `docs/PROTOCOLO.md` pasado a la ESP32-C3 con CH340; `config.yaml` → `serial.port` es el by-id del CH340.
- Alimentación: fuente de laboratorio para los servos y powerbank para la Pi (ver Hardware). La Pi por USB-C desde el powerbank: 5,08 V, `throttled=0x0`.
- Buzzer: simulador de sonidos en `pruebas_buzzer/` (publicado en https://claude.ai/artifact/7wyNPrzj6QqcPJQvrpaPwB), POLCA de Olimpia transcrita de la partitura (compases 1–8, 7,104 s), POLCA_CERRO es un marcador. Comprar el buzzer **pasivo** de electronica.com.py.
- **La cámara no está conectada a la Pi** (14/10): no lanzar nada de percepción.
- **Compatibilidad con Windows:** Git for Windows no restauraba `docs/micro servo mg90s ` ni `docs/micro servo sg90 ` (terminaban en espacio). Se arregló en el **PR #1** (rama `compatibilidad-windows`, integrado en `main`) y después se pasaron a guion bajo **todas** las carpetas y archivos con espacios (`docs/micro_servo_mg90s/`, `docs/servo_HS-7955TG_titanium_gear/`, `docs/Fotos/camera_Noir_module_3/`, `pruebas_buzzer/notas_polca_de_olimpia/`, `Captura_desde_...png`, etc.). Ya no hay rutas con espacios en el repo ni en la Pi. La carpeta del proyecto en la notebook (`Keepon pro `) sí termina en espacio, pero está fuera del repo.
- **Camisetas (15/10):** plan decidido: **reglas de color y patrón sobre el torso** (la guía las permite expresamente), no una red entrenada. Torso debajo de la cara (BlazeFace) o en el centro del recuadro de YOLO, reducido a ~48×48; cada píxel → blanco/negro/rojo/azul/otro; **Olimpia** = franja horizontal negra con blanco arriba y abajo; **Cerro** = rojo **y** azul en partes grandes del torso separados por bordes verticales (no exigir rayas); filtro 6 cuadros para confirmar y 6 para soltar, por persona. Para la NoIR: luz LED en la demo, balance de blancos y exposición fijos; si no alcanza, la Camera Module 3 estándar (mismo tamaño y cinta). **El detector todavía no está escrito.**
  - Imágenes de referencia en `pruebas_camisetas/imagenes_referencia/` (`olimpia/`, `cerro/`, `suplentes/`, `trampas/`, sin personas, con `fuentes.txt`; ver su README). Mostraron: la **titular 2026 de Cerro es mitad roja y mitad azul, sin rayas**; el azul de Cerro es **marino oscuro** (con la NoIR puede parecer negro) y el rojo casi bordó; **el Barcelona es casi igual a Cerro** (limitación a explicar en la defensa); las suplentes no tienen el patrón titular. Falta una remera blanca lisa.
  - Para probar con la cámara: el usuario tiene una **remera negra** (prueba negativa; con tiras rojas y azules pegadas sirve de "Cerro" casero, y con una franja blanca de "Olimpia al revés", que no tiene que detectar).
- **La Pi no respondió por SSH el 15/10** (timeout por Tailscale): falta sincronizarle las imágenes de las camisetas.
- Próximo: el detector de camisetas (probado con las imágenes de referencia), integrar `SerialLink` con el robot sobre la ESP32 real (`scripts/sim_scenario.py` usa SimLink), reconexión automática de `SerialLink`, y la prueba con los servos.

## Rendimiento medido en la Pi (30/09, 1 persona)
- Personas + rostros: **16,9 Hz** (YOLO 34 ms + rostros 10 ms), edad del resultado 74 ms.
- Pose: **10,0 Hz**, edad 149 ms. CPU total: 239 % de 400 %.
- Rostro encontrado en el 80 % de las detecciones; ID estable. Detalle completo en `docs/ESTADO_PI.md`.

## Sesión anterior (14/10/2026, tarde)
- **Revisión de arquitectura de Codex** en `docs/REVISION_CODEX_ARQ.md`: mantener la ESP32 (el enunciado pide microcontrolador + protocolo; watchdog independiente de Linux), Pi en la cabeza por la cinta de 150 mm, cara plana. **Sus 4 fallos de código se corrigieron el 14/10** (tests 7–10 de `tests/test_regresiones_codex.py`): el control de mirada y el foco usan cx/cy (`World.from_cfg`, `World.K`); una cola por proceso de tamaño 2 con `_put_latest` (descarta lo viejo, nunca bloquea); `nod_period_s` 1,0 s (≈ 237 °/s²); `Robot.stop()` enclava primero y reintenta el STOP si el enlace falla. **Falta medir en la Pi la cola nueva** (`perception_bench.py`): la Pi no respondía por SSH. Quedan sin hacer los puntos 3 (asociar pose y persona por timestamp) y 6 (watchdog/reanudación) de la misma lista. `docs/diagrama_sistema/index.html` ya está en la v3.
- **Modelo mecánico v4** en `docs/keepon_v4_cad/` (14/10, el vigente): cabeza, servos, soportes y horquilla de la v3 sin cambios, con la disposición de la v1 (eje de pitch sobre el de yaw, base en U de 64 × 116 en lugar del plato Ø146: el vuelco sobre el yaw baja a 0,81 kgf·cm). Caja base de 182 × 133 × 74 con el **powerbank Xiaomi PB2020MI** (128 × 73 × 32, 5 V/3 A a la Pi por el GPIO), los **bornes de la fuente de laboratorio** y el interruptor en la pared de atrás, y la bornera de 6 V con el capacitor, la ESP32 y el buzzer en una bahía adelante. El lugar de la LiPo quedó libre (se podría achicar la caja ~50 mm en Y; ver el README). Script `fuente/keepon_v4_cad.py` (importa la v3), macro de relaciones y `componentes_v4.txt`. `docs/diagrama_sistema/index.html` ya está en la v4 con la alimentación nueva.
- **Modelo mecánico v3** en `docs/keepon_v3_cad/` (reemplaza al v2 para imprimir; el cuello se importa del v2): cabeza de 75 × 104 × 40 mm con la **Pi parada adentro** sobre la placa de roll y **la cámara como nariz**, en el centro de la cara (a 38 mm sobre el eje de roll), con los ojos decorativos arriba. En la Pi 5, los conectores CAM/DISP son perpendiculares al borde de los HDMI: la cinta sale a lo largo del lado largo, corrida 19 mm del centro. Cinta fija con una U de radio 6,5 mm y un doblez en Z (dos pliegues a 45°) que la lleva al centro (147 de 150 mm). Sin interferencias en 15 poses.
  - Consecuencias: **la Pi se alimenta por el GPIO** (el USB-C queda tapado por la cinta), los USB-A quedan arriba (cable acodado a la ESP32), y **el pitch se monta con +30° arriba y −20° abajo** (más de ~22° abajo la cara toca el plato).
  - **Falta verificar en la Pi:** hacia qué extremo sale la cinta del conector (`PI_CSI_SALIDA`, se asumió el USB-C), el largo exacto de la cinta y la altura del Active Cooler.
- Los intrínsecos de `config.yaml` (fx = 948 → 37°) probablemente no son de esta cámara a 640 × 480 (la estándar tiene 66°): hay que calibrar con un tablero.
- La Pi no respondió por SSH en toda la sesión (timeout por Tailscale).
- CadQuery 2.8 en `~/cq_env` (con VTK para las vistas: `docs/keepon_v3_cad/fuente/vistas.py`).

## Sesión anterior (13/10/2026)
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

## Sesión del 07/10/2026
- Al cambiar servos, apagar antes la fuente: enchufar uno con la fuente prendida desconectó la ESP32 del USB (y otra vez se reinició por pérdida de alimentación, `rst:0x1 (POWERON)` en el log).
- Si el puerto está ocupado, es casi siempre un `serial-monitor` abierto por el usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.
- Todo commiteado y subido. Los dos visores eligen la cámara por nombre (la segunda NoIR había corrido los índices); ambos probados con la cámara real.
- **`ver_personas.sh` quedó corriendo en la Pi** y ocupa la cámara. Detenerlo con `~/keepon/ver_personas.sh stop`.
- Pendiente: revisar el flex de la segunda NoIR (`i2c@88000`) o desconectarla.
- Se les pidió a los usuarios probar el visor (mirar / no mirar, girar la cabeza, levantar la mano, cruzarse) y anotar los grados de desvío para calibrar el umbral de ME_MIRA.
