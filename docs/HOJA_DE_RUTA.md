# Hoja de ruta v3: µTP Robótica Social (cabeza 3 GDL)

**Plazo:** 30 sep 2026 → 30 oct 2026 (demo en el Segundo Parcial). Equipo: hasta 5 personas.
**Hardware del grupo:** Raspberry Pi 5 4 GB (Ubuntu 24.04 + ROS 2 Jazzy), 2 × Camera Module 3 NoIR, ESP32-S3 WROOM, 3 servos.
**Stack:** **todo en la Pi 5** (Python + OpenCV + YOLOv8n/NCNN + MediaPipe Tasks + pyserial) ⇄ USB CDC (`/dev/ttyACM0`) ⇄ ESP32-S3 (3 servos + buzzer pasivo LEDC). Python puro; ROS 2 es opcional y se evalúa más adelante. La notebook solo se usa para desarrollar.
**Principio rector:** el éxito se mide con el robot completo funcionando. Integración física el **8/10**, feature freeze el **22/10**.

> v2 incorpora la revisión de Codex (`REVISION_CODEX.md`). v3 incorpora el hardware real y el avance de M0. Vista interactiva: `hoja_de_ruta.html` (v2).

## Estado al 30/09/2026

| Hito | Estado |
|---|---|
| **M0 software** | ✅ Protocolo (`docs/PROTOCOLO.md`), ESP32 simulado (especificación del firmware), trayectorias suaves, árbitro, Observador/Seguimiento/Saludo/Camiseta, control de mirada P con zona muerta suave, foco con histéresis, log CSV, escenario sintético, 37 tests. |
| M0 benchmark | ⏳ Notebook: 11,6 Hz (YOLOv8n NCNN 320 + Face + Pose, 86 ms/cuadro). **Falta medir en la Pi 5.** |
| M0 hardware | ⏳ Ficha de carga, prueba de servos y fuente, camisetas reales. |
| M1–M5 | Pendientes |

Bugs encontrados en M0 y ya corregidos:
- Seguimiento a saltos: la zona muerta dura hacía avanzar el yaw en escalera. Se cambió a zona muerta suave.
- Golpe al llegar al objetivo (3800 °/s² en lugar de 600): se corrigió la fórmula de frenado discreto, y el firmware debe usar la misma.

## Frontera Hardware / Software

**La PC decide QUÉ hacer** (percepción, modelo del mundo, árbitro, comportamientos, modos).
**El ESP32 decide CÓMO hacerlo con seguridad** (límites, rampas, secuenciador de sonido, STOP, watchdog).
El control visual no escribe al puerto serie: genera propuestas y sólo el árbitro emite comandos.

## HARDWARE

### H0. Ficha mecánica y eléctrica (semana 0)
- Medir masa, centro de gravedad, torque (τ ≈ Σ m·g·d en la postura más desfavorable) y consumo con los 3 servos a la vez. Pitch es el eje más exigente.

### H1. Mecánica (cabeza + cuello 3 GDL)
- Serie yaw → pitch → roll; yaw sobre rodamiento. Rangos: yaw ±70°, pitch −20°/+30°, roll ±20°; topes mecánicos más allá del límite de software.
- Cabeza liviana (< 250 g) y equilibrada; ojos fijos grandes (LEDs al final). HOME = postura calibrada.
- **Tres ejes operativos el 8/10.**

### H2. Actuadores y electrónica
- Candidatos: yaw/pitch MG996R o DS3218; roll MG90S (el SG90 tiene engranajes plásticos). Confirmar con H0.
- **ESP32-S3 WROOM** por USB nativo (`/dev/ttyACM0`). **Timers LEDC separados** para servos (50 Hz) y buzzer.
- Fuente regulada dentro del rango de todos los servos, corriente verificada con movimiento simultáneo; GND común; borneras (no protoboard); switch de emergencia.
- Buzzer pasivo + NPN 2N2222 + R de base.
- **Cámara: Camera Module 3 NoIR** en la cabeza. Hace falta un cable CSI 22→15 pines de 30–50 cm, con holgura alrededor del eje de yaw. Calibrar intrínsecos.
  - ⚠️ **NoIR = sin filtro infrarrojo:** los colores se corren (rojos y blancos rosados) con luz solar o incandescente, lo que afecta a las camisetas. Probar ya con las camisetas reales bajo luz LED. Si falla, usar una Camera Module 3 estándar o una webcam USB.
  - ⚠️ **Ubuntu 24.04 + Pi 5:** la IMX708 requiere un libcamera con soporte para la Pi 5. Es el primer bloqueo que hay que verificar con `scripts/check_pi.sh`.
  - La segunda cámara queda como repuesto.
- **Raspberry Pi 5:** cooler activo obligatorio (inferencia continua) y fuente de 27 W (5 V 5 A) propia, separada de la de los servos.

### H3. Firmware ESP32 (software embebido)
- Parser no bloqueante; límites; perfil trapezoidal (vmax, amax) a 50–100 Hz; `J` conserva sólo la referencia más reciente.
- **STOP enclavado hasta RESUME** (no va a HOME). Watchdog ~500 ms: detener secuencias y mantener postura segura.
- Motor de sonido: R2D2, polca, abucheo, piropo, beeps de modo; `CANCEL`.
- Sin lógica de personalidad (MODE vive en la PC).

## INTERFAZ — Protocolo serie (día 1)

```
PC → ESP32:  HELLO 1 | J seq yaw pitch roll | S seq SONIDO | CANCEL seq SOUND | PING seq | STOP seq | RESUME seq | HOME seq
ESP32 → PC:  ACK seq (aceptado) | DONE seq (terminado) | ERR seq MOTIVO | STATE seq ESTADO yaw pitch roll SONIDO | HELLO (tras reinicio)
```
ASCII por líneas, 115200 baud, grados. Validar entradas; no duplicar sonidos reenviados; la telemetría reporta referencias comandadas, no ángulos medidos. Simulador del ESP32 en Python con la misma API.

## SOFTWARE (PC)

### S0. Benchmark (semana 0)
- `scripts/benchmark.py` **en la Pi 5**: FPS con YOLOv8n (NCNN) + MediaPipe simultáneos; procesar siempre el último cuadro; modelos locales y versiones fijadas.

### S1. Percepción (≥10 Hz)
- **PERSONA:** YOLOv8n + ByteTrack (BoT-SORT si los IDs saltan al mover la cámara). Continuidad de ID en pérdidas breves.
- **Asociación por persona:** rostro, pose y torso ligados al mismo ID; ante ambigüedad, no generar eventos.
- **ME_MIRA:** Face Landmarker + solvePnP (orientación de cabeza, no ocular); ±15° sostenido ≥0,5 s; histéresis 15°/20°; evaluar también a candidatos no seleccionados.
- **SALUDO:** sólo Pose; muñeca sobre hombro, oscilación relativa al torso normalizada por ancho de hombros; definir amplitud, alternancias y duración.
- **CAMISETA:** desde el día 1 con las prendas reales. Clases OLIMPIA / CERRO / OTRA / DESCONOCIDA. Reglas diseñadas sobre las camisetas concretas; pruebas con lisas blancas, rojas y azules; 6 cuadros on/off. Si se entrena, separar por sesión/persona. **Cerrado el 15/10.**
- Distinguir evento nuevo (flanco) de predicado sostenido.

### S2. Modelo del mundo (+ SALIENDO)
- Tracks con ID, posición, velocidad, eventos, timestamps, cooldowns por (persona, comportamiento).
- **SALIENDO:** objetivo válido y borde + tendencia exterior sostenida, o saturación + error persistente hacia afuera; inhibido durante desvío tímido, saludo y cambio de foco.

### S3. Control de mirada
- Proporcional sin integral: `e = atan((u−cx)/fx)`, `v = sat(Kp·e)`, `ref += v·dt`; igual en pitch. Zona muerta 3–5 %, lazo 30–50 Hz.
- Pérdida < 1 s: mantener postura; > 1 s: liberar (+ desaprobación opcional). Cara a cara → roll; nadie → aburrimiento. Con roll ≠ 0, rotar el error.

### S4. Árbitro (núcleo evaluado)
- Recursos exclusivos: cuello completo y buzzer.
- Propuesta = {id, comportamiento, persona, prioridad, recursos, inicio, vencimiento, interrumpible, params}.
- Adquisición atómica; STOP interrumpe todo; propuestas vencidas se descartan; cooldown al iniciar la respuesta; cancelación + recuperación suave; log de cambios de dueño.
- Foco de atención con score (mira, tamaño, centrado) e histéresis ~1,5 s.

### S5. Comportamientos y modos
- Observador (barrido lento), Seguimiento, Saludo (2–3 cabeceos + R2D2), Hincha Olimpia (polca + sigue), Hincha Cerro (abucheo).
- Modos en la PC, cambio en runtime + beep: Neutro, Tímido (desvío→espera→regreso), **Atrevido (un único dueño del cuello compone yaw + mentón)**, Maleducado (piropo por salida, máx. 1 cada 40 s).

### S6. Monitoreo, métricas y log
- Overlay con IDs, objetivo, eventos, modo, dueño de recursos, ángulos. Teclas STOP/RESUME/MODE.
- Tres latencias: captura→percepción, evento→comando, comando→movimiento. Log CSV/JSON.

## Cronograma

| Fase | Fechas | Resultado verificable |
|---|---|---|
| F0 | 30/9–4/10 | Compras, ficha de carga, servos/fuente probados, benchmark, camisetas reales disponibles, protocolo escrito, árbitro mínimo con eventos sintéticos. **M0** |
| F1 | 5–8/10 | Tres ejes operativos, cámara en la cabeza, seguimiento físico básico; STOP y pérdida de comunicación probados. **M1 (8/10)** |
| F2 | 9–15/10 | IDs + asociación, selección entre dos personas, ME_MIRA, SALUDO, seguimiento + buzzer concurrentes; camisetas evaluadas. **M2 (15/10)** |
| F3 | 16–22/10 | Todos los modos y comportamientos, SALIENDO, cooldowns y recuperación. **M3 feature freeze (22/10)** |
| F4 | 23–27/10 | Pruebas negativas, iluminación, latencia, 20 min continuos, video e informe. **M4 (27/10)** |
| F5 | 28–30/10 | Ensayo general, repuestos, correcciones pequeñas. **M5 (30/10)** |

Informe Colab y matriz de aceptación T1–T7 se escriben de forma incremental desde F1. Todo entregado antes de la demo (consultar a la cátedra la contradicción entre el reglamento y §6.1).

## Roles
1. **R1 Mecánica + electrónica:** H0–H2, prueba de 20 min.
2. **R2 Firmware + protocolo + sonido:** H3, simulador, herramienta serie.
3. **R3 Percepción social:** benchmark, PERSONA, asociación, ME_MIRA, SALUDO.
4. **R4 Camisetas + métricas:** camisetas, pruebas negativas, overlay, latencias, log, video.
5. **R5 Árbitro + control + integración:** modelo del mundo, servoing, árbitro, foco, comportamientos, modos, SALIENDO.

Todos documentan su módulo y hacen al menos una defensa cruzada de otra parte.

## Top 5 riesgos
1. Integración tardía / integrador sobrecargado → integración física 8/10, demos completas semanales.
2. Torque, holgura o caída de tensión → ficha de carga, prueba de 20 min.
3. Latencia y tracking con cámara móvil → benchmark temprano, último cuadro, ganancias conservadoras.
4. Falsos positivos → clase DESCONOCIDA, filtros temporales, pruebas negativas desde F0.
5. Conflictos de recursos → árbitro único, adquisición atómica, caducidad, cancelación explícita.

## Si el tiempo aprieta (MVP)
Simplificar la implementación antes que eliminar requisitos: ojos fijos, control P, observador con barrido simple, Pose sin Hands, reglas conservadoras de camiseta, secuencias cortas por modo, overlay OpenCV. **No recortar:** 3 GDL, buzzer, árbitro propio, límites y suavizado, IDs y foco, modos en runtime, cooldowns, monitoreo, entregables.
