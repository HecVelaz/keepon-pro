# Pendientes

Movido desde `CLAUDE.md` el 22/10/2026.

## Próximos pasos (hacia M1, el 8/10: el robot sigue a una persona con detecciones reales)
1. Con lo que reporten del visor: validar ME_MIRA y ajustar `looking_deg`; medir con 2–3 personas.
2. **Integrar la percepción al robot:** de `DetResult` a `World` (timestamps por evidencia, filtros N-de-M), ME_MIRA sostenido ≥ 0,5 s, SALUDO (muñeca sobre el hombro + ≥ 2 oscilaciones), y el control de mirada con el centro óptico cx/cy en lugar del centro de la imagen.
3. **Firmware de la ESP32-C3: hecho (14/10).** Falta probarlo con los servos (fuente de 6 V, `signo` por eje, sentido de giro del MG996R); el buzzer ya está probado (26/10).
4. Camisetas: método decidido el 15/10 (reglas de color y patrón, ver "Dónde quedó la sesión"). Falta escribir el detector y grabar con la NoIR las prendas reales (Olimpia, Cerro, lisas blanca/roja/azul) a 0,8/1,5/2,5 m con la luz de la demo; si los colores no alcanzan con luz LED y balance fijo, pasar a la cámara estándar.
5. Pendientes técnicos: reconexión automática de `SerialLink`; autofoco (hoy `AfMode=0`, manual); secuencia de encendido de los servos; overlay completo (modo, dueño de recursos, ángulos) para T7; modos de personalidad y SALIENDO (M3).
6. `docs/hoja_de_ruta.html` sigue en la v2 (los .md están en la v3).

## Pendientes sueltos (estaban repartidos en las secciones de hardware y de sesiones)
- **Pitch (HS-7955TG) montado:** vibra al moverse lento, zumba quieto y **oscila al empujarlo**: juego entre el brazo simple y su bolsillo (la R4 sacó la retención) o el tornillo del horn. Calzar el brazo, volver a poner una retención o pasar a un horn redondo.
- **Yaw montado:** vibra al moverse lento (≤ ~40 °/s); a ~100 °/s va suave. Revisar en el seguimiento de personas, que tiene movimientos lentos.
- **Roll:** con la compensación, −20 manda 1818 µs (antes −30 "al límite" era 1776 sin compensación): confirmar que a −20 no toca. Si la vuelta a 0 varía, ajustar `compensacion_us`.
- Cortes del USB de la ESP32 con servos trabados o vibrando: si siguen, volver a poner el capacitor de 2200 µF en la bornera de 6 V y revisar el cable USB y el GND común.
- Buzzer: **probado el 26/10** en el GPIO10 con el módulo MH-FMD (VCC a 3V3, salida invertida, volumen 0.25). El 03/11, con la cabeza v6 armada, no sonaba nada (el firmware confirmaba DONE): se pasó el I/O al **GPIO5**. Falta confirmar que suena; si tampoco, revisar VCC/GND del módulo y su cable por el cuello. `docs/diagrama_sistema/index.html` sigue diciendo GPIO10.
- Detector de camisetas: escribirlo y probarlo con `pruebas_camisetas/imagenes_referencia/`; falta una remera blanca lisa entre las imágenes de referencia. Para probar con la cámara: remera negra del usuario (negativa; con tiras rojas y azules = "Cerro" casero; con franja blanca = "Olimpia al revés", que no tiene que detectar).
- Sincronizar a la Pi las imágenes de las camisetas (la Pi no respondió por SSH el 15/10).
- Integrar `SerialLink` con el robot sobre la ESP32 real (`scripts/sim_scenario.py` usa SimLink) y agregarle reconexión automática.
- Medir en la Pi la cola nueva de percepción (`perception_bench.py`).
- Revisión de Codex (`docs/REVISION_CODEX_ARQ.md`): faltan los puntos 3 (asociar pose y persona por timestamp) y 6 (watchdog/reanudación).
- Verificar en la Pi: hacia qué extremo sale la cinta del conector (`PI_CSI_SALIDA`, se asumió el USB-C), el largo exacto de la cinta y la altura del Active Cooler. Si el USB-C queda libre, usar un cable USB-C acodado directo y eliminar el camino por el GPIO.
- Calibrar la cámara con un tablero: los intrínsecos de `config.yaml` (fx = 948 → 37°) probablemente no son de esta cámara a 640 × 480. Validar `looking_deg` (15°, sin validar).
- Revisar el flex de la segunda NoIR (`i2c@88000`) o desconectarla.
- `ver_personas.sh` quedó corriendo en la Pi el 07/10 (ocupa la cámara): detenerlo con `~/keepon/ver_personas.sh stop` si sigue.
- **Diseño v6 R4:** tomar las medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` (brazos y estriados reales, MG996R, cámara, buzzer, insertos, material) antes de imprimir las piezas estructurales. Con la cabeza armada, definir `signo` de los tres ejes en `neck.servos`.
- Subir `docs/diseno_v5/` al repo (`docs/diseno_v6/generar_v6.py` lo importa: sin él no se puede regenerar el CAD) y compartir `Keepon_V6_R4.zip` por Drive.
- `docs/diagrama_sistema/index.html` y el comentario de encendido de `firmware/keepon_fw/keepon_fw.ino` siguen apuntando a la v4.
- Medir ≥ 4,9 V en los pines de alimentación de la Pi una vez armada.
