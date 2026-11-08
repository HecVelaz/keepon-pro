# Revisión de Codex: Pi 5 real y próximos pasos

> codex-cli 0.158.0, 30/09/2026, a partir de docs/ESTADO_PI.md. Codex no ejecutó mediciones en la Pi: sus números son estimaciones para contrastar.

**Sí: baja mucho el riesgo de captura y sube la prioridad del rendimiento. Recomiendo conservar Keepon en Python y usar `rclpy` exclusivamente como adaptador de cámara.** No cambiaría Ubuntu ni migraría ahora toda la aplicación a ROS.

Leí el estado de la Pi, las revisiones, la hoja de ruta y el código relevante. No modifiqué archivos ni ejecuté mediciones en la Pi; los números propuestos abajo son estimaciones para contrastar.

**1) Qué cambia en la evaluación de riesgos**

| Riesgo | Evaluación actual |
|---|---|
| Cámara CSI en Ubuntu 24.04 | **Resuelto para captura básica.** La evidencia real de 30 Hz reemplaza la incertidumbre anterior. Falta validar bajo carga y con la cámara montada. |
| CPU disponible | **Principal riesgo de software.** YOLO consume ~275 % y la cámara cae a ~11 Hz antes de añadir rostro y pose. |
| Dependencias ARM64 | **Sigue abierto.** MediaPipe no está instalado. Las versiones fijadas para notebook no prueban compatibilidad con Python 3.12/ARM64 ni con los paquetes ROS del sistema. |
| Núcleo M0 | Los ocho fallos constan como corregidos. La prioridad pasa a comprobar el contrato en firmware real, no a rediseñar el árbitro. |
| Mecánica, alimentación y USB | Siguen siendo críticos para M1; ninguna medición de visión los sustituye. |
| NoIR y camisetas | Riesgo concreto que debe resolverse esta semana con las prendas reales. |

La hoja de ruta quedó desactualizada en tres puntos: cámara pendiente, ROS opcional para esa captura y YOLOv8n como referencia. **El punto de partida efectivo es camera_ros + YOLO26n**, manteniendo los entornos ajenos intactos.

**2) Arquitectura recomendada**

```text
camera_ros existente → sensor_msgs/Image
                              ↓
                 adaptador rclpy: último cuadro
                              ↓
                  percepción → World/Person
                              ↓
                comportamientos → árbitro
                              ↓
                       USB → ESP32-S3
```

**Elegiría `rclpy` solo como fuente de cámara.** Técnicamente habrá un nodo suscriptor, pero `World`, comportamientos, árbitro y protocolo seguirán siendo Python independiente de ROS.

| Alternativa | Latencia y CPU | Complejidad | Decisión |
|---|---|---|---|
| Todo Keepon organizado en nodos ROS | No acelera los modelos; separar imágenes entre más procesos puede añadir copias y colas | Migración, mensajes y coordinación nuevos | No para este plazo |
| Adaptador mínimo `rclpy` | Un salto local ya necesario; sobrecosto medible y acotable | Conserva casi todo M0 | **Recomendada** |
| Evitar ROS | Ahorro hipotético a cambio de rehacer captura funcional | Reabre libcamera/bindings/backends | No ahora |

Implementación concreta:

- Añadir un backend ROS que conserve el contrato `latest()`, número de cuadro y `StaleFrame`.
- Callback breve: guardar el último mensaje y su recepción; inferencia fuera del callback. Convertir únicamente los cuadros que se procesarán.
- Suscripción `KEEP_LAST`, profundidad **1**, `BEST_EFFORT`, comprobando compatibilidad con el publicador. El perfil de sensores de ROS prioriza recibir datos recientes sobre recuperar todos los mensajes. [Documentación de QoS](https://repo.test.ros2.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html).
- Consumir imagen local sin compresión; reservar JPEG/web para monitoreo reducido. No asumir transporte sin copias entre `camera_ros` y Python.
- Guardar `header.stamp` y tiempo monotónico de recepción. Verificar qué representa el primero y su reloj antes de llamarlo “captura”; nunca restarlo directamente de `time.monotonic()`.
- Un solo propietario de cámara 0. No iniciar otra captura mientras corre `ver_personas.sh`.
- Todo desarrollo en `~/keepon/` y entorno propio. Probar allí importación conjunta de `rclpy`, OpenCV, NumPy e inferencia antes de instalar indiscriminadamente los requisitos de notebook.

El `detector_node` existente sirve para comparación y primeras pruebas. Para controlar resolución, hilos y planificación, conviene un ejecutor de inferencia propio de Keepon, usando **copias de los modelos**, sin editar paquetes ajenos.

**3) CPU: cómo intentar llegar a ≥10 Hz**

**Primero, definir honestamente qué se mide:** publicar `World` a 10 Hz repitiendo detecciones no demuestra percepción nueva a 10 Hz. Medir tasa y edad por PERSONA, ME_MIRA y SALUDO; las camisetas pueden actualizarse más lentamente, dejando explícito ese compromiso.

El enunciado exige percepción ≥10 Hz. Para evitar una interpretación débil, apuntaría a **PERSONA + rostro + pose con observaciones nuevas a 10 Hz**, inicialmente con dos personas; medir también tres y documentar la degradación.

**Reducir YOLO antes de paralelizar.**

El intervalo observado a 480 es aproximadamente **91–119 ms por resultado**. Si el costo escalara únicamente con el área:

| Entrada | Área relativa | Tiempo idealizado |
|---|---:|---:|
| 480 | 100 % | 91–119 ms |
| 320 | 44 % | 40–53 ms |
| 256 | 28 % | 26–34 ms |

Esto es una **extrapolación optimista**, no un benchmark: hay costos fijos, memoria, preprocesamiento y competencia con otros procesos. Como rangos iniciales de planificación usaría **45–70 ms a 320** y **30–50 ms a 256**, conservando condiciones comparables.

El modelo NCNN actual tiene entrada fija 480: **exportar artefactos nuevos a 320 y 256**, dentro de Keepon. Cambiar solo el parámetro de ejecución no acredita haber reducido la red. NCNN admite configurar `imgsz` en la exportación. [Documentación de Ultralytics](https://docs.ultralytics.com/integrations/ncnn).

Filtrar `person` reduce resultados y parte del posprocesamiento; **no elimina el costo principal de la red**.

**Presupuesto objetivo, no rendimiento demostrado:**

Aquí 100 % equivale a un núcleo y el total disponible es 400 %.

| Componente | Tasa propuesta | Presupuesto CPU objetivo |
|---|---:|---:|
| Cámara + transporte + conversión | Captura 20–30 Hz | 30–50 % |
| YOLO26n NCNN 320 | 10 Hz | 110–150 % |
| Rostros de dos personas + orientación | 10 Hz por persona | 40–60 % |
| Pose ligera para dos personas | 10 Hz | 60–90 % |
| Tracking, camisetas, control, serie y monitoreo reducido | Según tarea | 20–30 % |
| **Total** | | **260–380 %** |

**Buscaría ≤320 % sostenido.** El extremo superior deja poco margen y probablemente produzca picos de latencia. Si 320 no entra, probar 256 y verificar pérdida de detección a la distancia de demo.

El consumo actual implica aproximadamente **250–327 ms de CPU acumulada por resultado** (`2,75 / Hz`). La reducción ideal por área a 320 daría unos **111–145 ms de CPU por resultado**, origen del presupuesto de YOLO. Los presupuestos de rostro y pose son límites deseados que todavía deben validarse.

**ROI y tasas distintas:**

- Mantener captura **640×480** y reducir solo la entrada de YOLO. Sacar caras y torso de la imagen original.
- Rostro: evaluar objetivo **y candidatos**. Procesar solo al objetivo impediría descubrir quién empieza a mirar.
- Pose: incluir brazos y manos; una ROI ajustada al torso puede recortar precisamente el saludo.
- Recortar mejora la escala del rostro, pero no garantiza menos cómputo si el modelo siempre redimensiona a una entrada fija. Varias ROI también pueden resultar más caras que una inferencia multipersona.
- Al usar recortes para `solvePnP`, transformar coordenadas al cuadro original o ajustar los intrínsecos.
- Camisetas: empezar a **2–3 Hz por persona**, con reglas sobre torso. Sustituir filtros de “seis cuadros” por duraciones explícitas: seis muestras a 2 Hz tardan unos tres segundos.
- Si hace falta un modo degradado: PERSONA 10 Hz, rostro 5–10 Hz y pose 8–10 Hz. **No presentarlo como los tres detectores a 10 Hz.** Validar especialmente saludos rápidos.

Además, `World` necesita **timestamps por evidencia**. Una detección nueva de persona no debe rejuvenecer una mirada o camiseta vieja.

**¿Reemplazar YOLO por pose multipersona?**

Lo probaría como alternativa durante una jornada, sin convertirlo todavía en la base:

- Pose puede aportar PERSONA + SALUDO + ROI de torso, eliminando una red.
- MediaPipe permite `num_poses` y utiliza tracking en modo vídeo para evitar detección completa en cada cuadro; eso no garantiza rendimiento ni IDs persistentes. [Guía oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python).
- Probar personas sentadas, cuerpos parciales, perfiles, cruces y brazos fuera de imagen. Con cámara en una cabeza robótica, **no siempre habrá cuerpo completo**.
- Los puntos faciales de pose no sustituyen automáticamente una estimación validada de orientación dentro de ±15°.
- Si MediaPipe no resulta instalable rápidamente, comparar un modelo nano de pose exportable a NCNN en el entorno propio. Requiere otro benchmark; no hereda los 8–11 Hz del detector actual.

**Hilos y procesos:**

Empezaría con inferencia fuera del hilo de captura/control y límites explícitos de hilos nativos. Comparar **1, 2 y 3 hilos NCNN**, controlando también OpenCV/OpenMP cuando corresponda.

No lanzar tres modelos que cada uno intente ocupar cuatro núcleos. Los procesos aíslan el control del trabajo Python pesado, pero no crean CPU y añaden memoria/transferencias. Si se necesitan, usar una cola de último cuadro o memoria compartida, nunca una cola acumulativa.

**Qué medir primero, en este orden:**

1. Cámara + suscriptor mínimo, sin YOLO ni visor: tasas de publicación/recepción, CPU y edad del cuadro.
2. YOLO480 con anotación y servidor web desactivados; después activarlos para cuantificar su costo. La caída a ~11 Hz requiere separar captura real de recepción retrasada.
3. Matriz **480/320/256 × 1/2/3 hilos**, mismas escenas con una, dos y tres personas.
4. Rostro y pose por separado; después juntos. Medir tiempo real y CPU, no solo duración de llamadas asíncronas.
5. Pipeline completo: tasas efectivas, latencia p50/p95, cuadros descartados, RAM/swap, frecuencia y temperatura. Primero pruebas cortas; configuración final durante **20 minutos**.

El benchmark actual necesita adaptarse: usa YOLOv8n, no acepta cámara ROS y ejecuta Face/Pose completos en serie. Sus resultados actuales no describen esta configuración.

**4) NoIR y camisetas: prueba concreta esta semana**

La NoIR no incorpora filtro infrarrojo. Un balance de blancos puede corregir dominantes, pero no garantiza recuperar colores alterados por la contribución infrarroja. [Documentación de Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/camera.html).

Entre **1 y 3/10**:

- Conseguir las camisetas reales de Olimpia y Cerro, más lisas blanca, negra, roja y azul y una prenda con patrón parecido.
- Grabar con **la NoIR real**, a distancias de demo —por ejemplo 0,8, 1,5 y 2,5 m—, frontal y girado, quieto y moviéndose.
- Repetir con LED del aula, luz de ventana y mezcla de ambas. Añadir iluminación cálida/incandescente si puede aparecer en la demo.
- Incluir una y dos personas, torso parcialmente tapado y movimiento de cabeza.
- Verificar primero `encoding` y RGB/BGR con una referencia de colores: no atribuir a NoIR un intercambio de canales.
- `AfMode=0` implica foco manual: ajustar y registrar la posición de lente para las distancias elegidas. Comparar exposición/balance automáticos con valores estabilizados en la iluminación prevista.

Clasificar usando **distribución de colores y patrón de la prenda**, no “rojo = Cerro” o “blanco = Olimpia”. Mantener `OTRA` y `DESCONOCIDA`.

Evaluar por clips y por sesión independiente, no por cuadros vecinos del entrenamiento. Registrar aciertos, rechazos, confusiones y falsos disparos de comportamiento.

**Decisión el 4/10:** si funciona con LED controlado, fijar ese escenario. Si falla incluso allí, probar filtro IR-cut externo o cámara con filtro IR antes de insistir en umbrales. Cualquier cambio óptico exige repetir foco y color. La segunda NoIR sirve de repuesto, pero no resuelve este problema.

**5) Plan priorizado hasta M1, 8/10**

Desde el 30/9 hasta el 8/10 hay ocho días. Organizaría **siete jornadas del 1 al 7/10 y aceptación el 8/10**.

| Fecha | Requiere Pi | Requiere ESP32-S3 y hardware | Se puede hacer en notebook |
|---|---|---|---|
| **1/10 — P0** | Adaptador ROS mínimo, captura sostenida, entorno propio e importaciones. Registrar versiones del stack funcional | Identificar placa/USB/pines; puerto serie real; prueba de un servo con fuente adecuada | Adaptar interfaz de cámara y benchmark; preparar protocolo de medición y clips |
| **2/10 — P0** | Benchmark 480/320/256 e hilos, sin visor. Primera captura de prendas | Parser, HELLO, ACK, STOP enclavado, watchdog y límites | Exportar modelos en directorio propio; pruebas de conformidad basadas en simulador |
| **3/10 — P0** | Instalar/probar rostro y pose; medir una y dos personas. Prueba acotada de pose como detector | Tres ejes a baja velocidad; calibrar signos, HOME y límites; buzzer con temporización independiente | Asociación por ID, ROI, timestamps por señal, filtros temporales y casos negativos |
| **4/10 — P0** | Elegir pipeline medido; decisión NoIR/prendas; prueba sostenida | Medir consumo simultáneo, arranque y reinicio; revisar torque, holguras y recorrido del CSI | Reproducir grabaciones, ajustar umbrales y dejar configuración reproducible |
| **5/10 — P0** | Cámara montada + detección real → `World` → seguimiento | Cerrar lazo físico primero en yaw, luego pitch; ganancias conservadoras | Logs de latencia, herramientas de análisis y evidencias de integración |
| **6/10 — P0** | Seguimiento con dos personas y buzzer concurrente; cortes de cámara/proceso | STOP en movimiento, watchdog, desconexión USB, reinicio y resincronización | Revisar trazas y corregir fallos reproducidos |
| **7/10 — P0** | Ensayo de 20 min con configuración candidata y monitoreo activo | Tres GDL, cableado definitivo provisional, alimentación y parada física | Preparar matriz de aceptación, instrucciones de arranque y vídeo de respaldo |
| **8/10 — M1** | **Demostración integrada y mediciones guardadas** | **Validación física conjunta** | **Registro de resultados y pendientes para M2** |

**Criterio de M1:** tres ejes operativos, cámara embarcada, seguimiento con detecciones reales, buzzer concurrente y recuperación/parada comprobadas ante fallos. Buscar percepción básica sostenida ≥10 Hz y medir evento confirmado → comienzo físico de respuesta, con referencia de ≤300 ms; un ACK no acredita movimiento.

ME_MIRA, SALUDO y camisetas deben tener **viabilidad medida y primeras pruebas esta semana**. Su integración completa sigue correspondiendo a M2, el 15/10; no conviene posponer el primer seguimiento físico hasta terminarlos.