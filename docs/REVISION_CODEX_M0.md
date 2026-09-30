# Revisión del código M0 por Codex

> codex-cli 0.158.0, 30/09/2026, sobre el commit 267e20c. Las correcciones aplicadas están en el commit siguiente (ver tabla al final de docs/HOJA_DE_RUTA.md).

**1) Veredicto general**

**M0 tiene una base funcional, pero no lo daría por cerrado todavía.** Cumple el entregable mínimo de protocolo escrito, árbitro y escenario sintético integrado. La separación percepción → propuestas → arbitraje → actuadores está bien planteada, y la adquisición atómica de recursos funciona en los casos probados.

Sin embargo, la “especificación ejecutable del firmware” conserva fallos de trayectoria, protocolo y sincronización. Conviene corregirlos antes de portarla al ESP32.

**Validación:** los **37 tests pasan**. Ejecuté pytest con captura en memoria, sin caché ni escritura de bytecode por el entorno de solo lectura. También ejecuté reproducciones adicionales en memoria. No modifiqué archivos.

El M0 completo sigue pendiente: faltan el benchmark en la Pi y las comprobaciones físicas que el propio plan reconoce.

**2) Bugs concretos, ordenados por severidad**

**1. Alta — Un reinicio del ESP32 no resincroniza el controlador.**  
[keepon/actuators.py:56](</home/hecvelaz/Documentos/Keepon pro /keepon/actuators.py:56>), [keepon/link.py:87](</home/hecvelaz/Documentos/Keepon pro /keepon/link.py:87>).

- `HELLO` únicamente se registra. No se comprueba la versión ni se invalidan acciones, sonidos pendientes o referencias anteriores. `SerialLink` tampoco implementa recuperación de desconexiones.
- **Reproducción:** reiniciar el simulador durante POLCA deja `CAMISETA` como dueño del buzzer en la Pi, pero el ESP32 ya no reproduce nada. El seguimiento conserva su referencia previa al reinicio.
- **Corrección:** introducir estados de conexión/sincronización; ante arranque nuevo, suspender comandos ordinarios, invalidar acciones pendientes, verificar protocolo y reconciliar estado y referencias. Preservar explícitamente el STOP del operador durante esa recuperación.

**2. Alta — La trayectoria todavía incumple `amax` en las posiciones emitidas.**  
[keepon/trajectory.py:49](</home/hecvelaz/Documentos/Keepon pro /keepon/trajectory.py:49>).

- El ajuste final `pos = target` rompe la coherencia entre `vel` y el desplazamiento realmente comandado.
- **Reproducción:** `Axis(-70,70,180,600)`, objetivo `20°`, pasos de `0,01 s`: la aceleración calculada mediante diferencias de posición alcanza **674,806 °/s²**, aunque `amax=600`.
- Los tests verifican principalmente la variable interna `vel`; por eso pasan.
- **Corrección:** resolver el tramo final respetando simultáneamente posición, velocidad y aceleración discretas. Añadir comprobaciones sobre las posiciones emitidas, incluyendo cambios de objetivo y STOP. La corrección documentada del “golpe final” está incompleta.

**3. Alta — Mensajes mal formados pueden abortar el procesamiento.**  
[keepon/protocol.py:85](</home/hecvelaz/Documentos/Keepon pro /keepon/protocol.py:85>), [keepon/protocol.py:112](</home/hecvelaz/Documentos/Keepon pro /keepon/protocol.py:112>).

- **Reproducción:** `SimESP32.feed("HELLO abc")` lanza `ValueError`, que `feed()` no captura.
- En recepción, `ACK abc` también produce `ValueError`; `STATE 1` se acepta sin argumentos y termina provocando `IndexError` al procesarlo.
- `HELLO` tampoco exige cantidad exacta de argumentos ni comprueba compatibilidad.
- **Corrección:** validar estructura, tipos y versión; convertir todos los errores de entrada en `ProtocolError`. Validar también las respuestas antes de entregarlas a `Actuators`.

**4. Alta — Una cámara caída puede entregar indefinidamente el último cuadro.**  
[keepon/camera.py:91](</home/hecvelaz/Documentos/Keepon pro /keepon/camera.py:91>), [keepon/camera.py:102](</home/hecvelaz/Documentos/Keepon pro /keepon/camera.py:102>).

- Tras recibir un cuadro, los fallos posteriores se silencian y `latest()` sigue devolviendo ese cuadro sin límite de antigüedad. Su `timeout` solo protege la espera inicial.
- Además, `Robot.tick()` no comprueba la edad del `World`: reutilizar un mundo detenido mantiene personas aparentemente visibles y puede seguir integrando órdenes de mirada.
- **Corrección:** establecer edad máxima, publicar estado de fallo y usar tiempo monotónico actual para caducar observaciones. Mantener identificadores y timestamps separados para captura, percepción y control.

**5. Media — Una nueva clasificación de camiseta modifica una acción que ya está ejecutándose.**  
[keepon/arbiter.py:127](</home/hecvelaz/Documentos/Keepon pro /keepon/arbiter.py:127>), [keepon/behaviors.py:169](</home/hecvelaz/Documentos/Keepon pro /keepon/behaviors.py:169>).

- La renovación sobrescribe `g.params` también para acciones episódicas.
- **Reproducción:** iniciar OLIMPIA y cambiar a CERRO durante la polca. El sonido sigue siendo POLCA, pero el timeout pasa a usar ABUCHEO. A los **3,2 s**, el árbitro ya no tiene dueño del buzzer y la polca continúa sonando.
- **Corrección:** congelar los parámetros de acciones episódicas al iniciarlas. Al terminar por timeout, cancelar o reconciliar el sonido antes de liberar el recurso.

**6. Media — La deduplicación de sonidos solo recuerda el último sonido.**  
[keepon/sim_esp32.py:77](</home/hecvelaz/Documentos/Keepon pro /keepon/sim_esp32.py:77>).

- **Reproducción:** `S 10 POLCA`, `S 11 ABUCHEO`, `S 10 POLCA`: el último comando vuelve a reproducir POLCA e interrumpe ABUCHEO.
- Contradice el contrato de que un `seq` repetido no vuelve a ejecutarse.
- **Corrección:** definir sesiones y una política explícita para secuencias antiguas; usar un registro acotado o rechazar secuencias ya superadas dentro de la sesión.

**7. Media — El foco puede ignorar indefinidamente a la única persona que mira al robot.**  
[keepon/gaze.py:70](</home/hecvelaz/Documentos/Keepon pro /keepon/gaze.py:70>), [keepon/gaze.py:87](</home/hecvelaz/Documentos/Keepon pro /keepon/gaze.py:87>).

- **Reproducción con la configuración actual:** objetivo A centrado, tamaño `480`, no mira: score `1,0`. Aparece B en `u=630`, tamaño `30`, mirando: score `1,05`.
- B no supera el margen adicional `0,1`, por lo que nunca comienza la histéresis y A conserva el foco indefinidamente.
- **Corrección:** priorizar explícitamente el grupo de personas que miran; aplicar tamaño y centrado dentro del grupo. La histéresis debe retrasar el cambio, no anular esa preferencia.

**8. Media — La latencia presentada como “captura → resultado” excluye parte de la captura.**  
[keepon/camera.py:99](</home/hecvelaz/Documentos/Keepon pro /keepon/camera.py:99>), [scripts/benchmark.py:118](</home/hecvelaz/Documentos/Keepon pro /scripts/benchmark.py:118>).

- El timestamp se toma **después** de que `_read()` devuelve la imagen. No representa el instante de exposición.
- Una imagen retenida en el backend puede producir una latencia aparentemente baja.
- **Corrección:** usar metadata de captura con reloj compatible cuando exista; en los demás backends, nombrar la métrica “recepción → resultado” y medir por separado el retraso previo. No usarla como prueba de latencia completa.

**3) Cumplimiento T1–T7 dentro del alcance de M0**

| Requisito | Evidencia actual | Huecos |
|---|---|---|
| **T1 — Bajo nivel** | Tres ejes simulados, HOME, límites, protocolo, STOP enclavado y watchdog. | Aceleración pendiente de corregir; parser y recuperación incompletos. Firmware, calibración y seguridad física pendientes de M1. |
| **T2 — Percepción** | Contrato `World/Person`, eventos sintéticos y benchmark de modelos. | No hay percepción integrada, tracking, asociación ni filtros temporales reales. Es trabajo de M2; el benchmark no demuestra T2. |
| **T3 — Mirada** | Lazo sintético cerrado usando posición del cuello simulado; P, zona muerta suave, saturación y EMA. | Falta tratar datos obsoletos, calibrar cámara/signos y validar latencia real. No se compensa roll. |
| **T4 — Foco** | Selección por score e histéresis temporal. | Fallo de prioridad de ME_MIRA descrito arriba; faltan pruebas de candidatos extremos, oclusiones y cruces. |
| **T5 — Comportamientos** | Observador, seguimiento, saludo y camiseta integrados. | Los sonidos son nombres y duraciones simuladas: no existe todavía evidencia de melodías o buzzer real. Modos correctamente diferidos a M3. |
| **T6 — Arbitraje** | Exclusividad lógica, adquisición atómica, prioridades, cooldown al iniciar, cancelación y STOP. | La propiedad lógica puede divergir del ejecutor. Faltan recuperación y pruebas de fallos. ≥10 Hz y ≤300 ms no están acreditados en la Pi. |
| **T7 — Monitoreo** | Log temporal de transiciones y traza del escenario. | Falta overlay operativo, modo, eventos y telemetría integrada. Cobertura parcial razonable para M0. |

La ausencia de modos o percepción real **no invalida por sí sola M0**, porque están programados para otros hitos. Los fallos en el contrato del firmware y el núcleo ya declarado terminado sí requieren cierre.

**4) Riesgos del hardware real sin validar suficientemente**

- **Ubuntu 24.04 + cámara CSI:** el README simplifica demasiado la solución a “instalar libcamera y rpicam-apps”. La documentación actual de Canonical sitúa el soporte general de este stack desde **Ubuntu 25.04**; no acredita la instalación 24.04 del grupo. Hace falta fijar y probar kernel, firmware, pipeline PiSP, libcamera y bindings como conjunto. `check_pi.sh` enumera componentes, pero no demuestra captura sostenida. [Documentación de Ubuntu](https://ubuntu.com/hardware/docs/boards/how-to/special_hardware/rpi-camera/).

- **Dependencias ARM64 reproducibles:** `requirements.txt` no fija ninguna versión. Falta demostrar instalación y ejecución de MediaPipe Tasks, NCNN y OpenCV dentro del mismo entorno que accede a libcamera. La guía de MediaPipe menciona Raspberry OS de 64 bits; eso no prueba esta combinación concreta de Ubuntu, Python y paquetes. [Guía de MediaPipe](https://developers.google.cn/edge/mediapipe/solutions/setup_python).

- **Óptica y movimiento:** NoIR ya está identificado, pero faltan ensayos con prendas reales, exposición, balance de blancos y enfoque. Camera Module 3 incorpora autofocus; hay que elegir y validar su política durante el seguimiento. El simulador tampoco reproduce desenfoque, distorsión, movimiento durante exposición ni rotación de imagen por roll. [Manual de Picamera2](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf).

- **Presupuesto de la Pi de 4 GB:** los 11,6 Hz de notebook dejan poco margen y no incluyen tracking, asociación, filtros, overlay y control integrados. Falta medir RAM, swap, temperatura, frecuencia y latencias p95 bajo carga sostenida y con varias personas.

- **USB del ESP32-S3:** “WROOM” no identifica el circuito de la placa ni garantiza qué conector expone USB nativo. Confirmar esquema, puerto, modo USB y pines; USB usa GPIO19/20. Probar reconexión y nombre estable del dispositivo. [Documentación de Espressif](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/get-started/establish-serial-connection.html).

- **Servos y arranque:** el simulador presupone HOME inicial y seguimiento ideal de las referencias. Faltan offsets, inversión, límites de pulso, velocidad bajo carga y comportamiento al energizar/reiniciar fuera de HOME. STOP suave sigue permitiendo recorrido de frenado y manteniendo torque; debe validarse contra topes, carga y corte físico.

**5) Prioridades para el próximo hito**

1. **Cerrar el núcleo antes de portarlo:** corregir trayectoria, parser, parámetros episódicos, deduplicación y foco; incorporar las reproducciones anteriores como regresiones.
2. **Resolver inmediatamente cámara y entorno de la Pi:** captura sostenida desde Python, versiones fijadas, modelos locales y benchmark con una y varias personas. Registrar FPS, latencia, RAM y temperatura.
3. **Implementar el firmware con pruebas de conformidad:** mismos comandos y resultados esperados que el simulador; probar STOP en movimiento, watchdog, mensajes corruptos, resets y reconexiones.
4. **Integrar el seguimiento físico de M1:** captura/percepción separadas del control, caducidad explícita de observaciones y referencias calibradas. Verificar signos y límites primero a baja velocidad.
5. **Aceptar M1 con evidencia física:** tres ejes, cámara embarcada, seguimiento básico, buzzer concurrente y parada comprobada ante caída de cámara, proceso y enlace. Dejar un registro reproducible de las pruebas.