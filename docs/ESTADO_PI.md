# Estado de la Raspberry Pi 5 (relevado el 30/09/2026)

Acceso: SSH por Tailscale, `r2d2@100.116.96.71` (hostname `r2d2-desktop`).

## Sistema

- Raspberry Pi 5 Model B Rev 1.0, 4 GB (3,1 GB libres en reposo), 4 núcleos, 45–55 °C.
- Ubuntu 24.04.5 LTS, kernel 6.8.0-1064-raspi, ROS 2 Jazzy. **No se puede cambiar el SO:** la Pi se usa en otros proyectos.
- Python del sistema 3.12.3 (cv2 4.6.0).

## Cámara (resuelto)

- La cámara CSI **funciona en Ubuntu 24.04** porque el dueño compiló `libcamera` + `camera_ros` en `~/camera_ws`. No hay `rpicam-apps` ni `picamera2`, y no hacen falta.
- Hay 1 IMX708 (Camera Module 3 NoIR) conectada en `i2c@88000`: índice `camera:=0`. La segunda cámara está desconectada.
- `camera_ros` a 640×480: **30 Hz** sola. `FrameDurationLimits` = 33333 µs, `AeEnable` = true, `AfMode` = 0 (foco manual).
- ⇒ La captura para Keepon se hace **por ROS 2** (tópico `sensor_msgs/Image`), no con picamera2/GStreamer.

## YOLO existente (proyecto `~/vision_estereo`, no modificar)

- Modelo **YOLO26n**: `~/vision_estereo/modelos/yolo26n.pt` y `yolo26n_ncnn_model` (NCNN, entrada fija **480 px**).
- Venv `~/yolo_env`: ultralytics 8.4.153, torch 2.14.0, ncnn 1.0.20260526. **Sin MediaPipe.**
- Paquete ROS 2 `yolo_ros` (compilado en `~/yolo_ws`). Su `detector_node` publica `/yolo/detecciones` (`vision_msgs/Detection2DArray`) y `/yolo/left/image_annotated`, con parámetros `modelo`, `imagen`, `imgsz`, `conf`, `clases` y `anotada`.
- `web_video_server` instalado.

## Mediciones (cámara NoIR + detector_node NCNN 480, solo `person`)

| Medición | Valor |
|---|---|
| Cámara sola | 30 Hz |
| Detección de personas | 8,4–11 Hz |
| Cámara mientras corre YOLO | ~11 Hz (compite por CPU) |
| CPU del detector | ~275 % (≈3 de 4 núcleos) |
| Temperatura con carga | 55 °C |

**Conclusión:** YOLO26n a 480 casi satura la CPU. Sin optimizar, no queda margen para MediaPipe (ME_MIRA por Face Landmarker y SALUDO por Pose) y el pipeline completo quedaría por debajo de los 10 Hz.

## Benchmark de Keepon en la Pi (30/09, sin personas en escena)

Entorno `~/keepon_env` (MediaPipe 1.0.1 propio + ultralytics/ncnn tomados de `yolo_env` vía `.pth`, sin modificarlo). Cámara vía ROS 2 (`camera.backend: ros2`). Modelos YOLO26n re-exportados en `~/keepon/models/` a 320 y 256. Datos: `docs/benchmark_pi_20260930_sin_personas.csv`.

| Configuración | YOLO ms | Face ms | Pose ms | Hz procesados | CPU | Edad del cuadro |
|---|---|---|---|---|---|---|
| YOLO 480 (el actual) | 79 | – | – | 11,2 | 283 % | 110 ms |
| YOLO 320 | 32 | – | – | 22,5 | 251 % | 50 ms |
| **YOLO 256** | **18** | – | – | **29,9** (límite de la cámara) | 201 % | 34 ms |
| Solo MediaPipe (rostro + pose) | – | 6 | 33 | 25,7 | 126 % | 68 ms |
| Completo en serie, 320 | 49 | 6 | 34 | 11,1 | 202 % | 122 ms |
| **Completo en serie, 256** | 34 | 6 | 34 | **13,4** | 185 % | 105 ms |

⚠️ Sin personas frente a la cámara: el rostro y la pose salen **optimistas** (no hay landmarks que calcular). Hay que repetir con 1 y 2 personas.

Observaciones:
- Bajar YOLO de 480 a 256 lo hace **4,3 veces más rápido**. Falta verificar que siga detectando a 2,5 m.
- Fijar los hilos de NCNN después de cargar el modelo funciona a medias: NCNN avisa que las convoluciones usan el valor del momento de carga. 4 hilos fue siempre lo más rápido.
- En serie sobra CPU (185–213 % de 400 %): conviene correr YOLO y MediaPipe **en paralelo**.

## Benchmark con 2 personas a ~1,5 m (30/09)

Datos: `docs/benchmark_pi_20260930_2personas.csv`. Modelos en serie en un solo proceso.

| Configuración | YOLO ms | Face ms | Pose ms | Hz procesados | CPU | Edad del cuadro | Personas / rostros / poses |
|---|---|---|---|---|---|---|---|
| YOLO 256 solo | 18,6 | – | – | **29,9** | 203 % | 34 ms | 2,00 / – / – |
| MediaPipe solo | – | 22,6 | 63,5 | 11,5 | 120 % | 119 ms | – / 0,72 / 1,28 |
| Completo 256 | 20,2 | 24,2 | 66,4 | **9,0** ❌ | 153 % | 145 ms | 2,00 / **0,39** / 1,96 |
| Completo 320 | 29,5 | 26,1 | 68,7 | 8,0 ❌ | 166 % | 156 ms | 2,00 / 0,62 / 1,95 |

Conclusiones:
- **YOLO 256 detecta a las 2 personas en el 100 % de los cuadros** a 1,5 m. Queda elegido como detector de PERSONA.
- Con personas, **la pose se duplica (≈66 ms)** y pasa a ser el cuello de botella. El rostro sube a ≈24 ms.
- **Face Landmarker sobre la imagen completa encuentra solo 0,4–0,7 de los 2 rostros**: su detector interno es de corto alcance. Hay que pasarle **recortes de la cabeza** a partir de las cajas de YOLO. Eso además resuelve la asociación rostro↔ID.
- En serie da 9 Hz y usa solo 153–166 % de CPU: **hay que paralelizar** (YOLO, rostro y pose en hilos o procesos separados, con el último cuadro).
- La frecuencia de CPU leída fue 1,5–1,9 GHz (el máximo de la Pi 5 es 2,4). Revisar el governor, aunque es un ajuste del sistema que afecta a otros proyectos.

## Percepción en paralelo (`keepon/perception.py`), 30/09

Arquitectura: 2 procesos (personas+rostros en los núcleos 0-1, pose en los núcleos 2-3); cada uno lee el último cuadro del tópico ROS 2. Medido con 1 persona en escena (`scripts/perception_bench.py`):

| Proceso | Hz | ms/cuadro | Edad del resultado | CPU |
|---|---|---|---|---|
| Personas (YOLO 256 + tracker propio) + rostros | **16,9** | 44 (YOLO 34 + rostros 10) | 74 ms | 127 % |
| Pose (MediaPipe lite) | **10,0** | 97 | 149 ms | 107 % |
| Total | | | | 239 % de 400 % |

Calidad: rostro encontrado en el 80 % de las detecciones de persona; el ID se mantuvo estable (1 solo ID en 20 s); ME_MIRA crudo, desvío mediano 11,6°.

Cómo se llegó (cada paso medido en la Pi):

| Problema | Efecto | Solución |
|---|---|---|
| Modelos en serie en 1 proceso | 9,0 Hz | Procesos separados (los hilos no sirven: NCNN y MediaPipe no liberan el GIL; medido 2,11 s vs 2,04 s) |
| Face Landmarker sobre la imagen completa | Solo 0,4 de 2 rostros encontrados | Recorte de cabeza desde la caja de YOLO → 92–100 % |
| Face Landmarker (478 puntos) | ~49 ms por rostro | Face Detector BlazeFace (6 puntos) + solvePnP → ~5–10 ms |
| NCNN y MediaPipe usaban los 4 núcleos cada uno | Se estorbaban | Afinidad por proceso + volver a fijar los hilos (NCNN los reubica en 0-3) |
| **Tracker de ultralytics (ByteTrack)** | **YOLO pasaba de 20 a 89 ms** | **Tracker IoU propio (`keepon/tracker.py`), <1 ms** |

Pendiente: repetir con 2 y 3 personas; validar ME_MIRA contra la realidad (mirar / no mirar la cámara a propósito) y calibrar el umbral; verificar que la calibración usada es la de esta cámara.

## Visor para la notebook

`~/keepon/ver_personas.sh` (nuevo, no toca `vision_estereo`) arranca la cámara 0, el `detector_node` NCNN (solo personas, imagen anotada) y `web_video_server`:
- Detección: http://100.116.96.71:8080/stream_viewer?topic=/yolo/left/image_annotated
- Cámara: http://100.116.96.71:8080/stream_viewer?topic=/keepon_cam/image_raw
- Para detenerlo: `~/keepon/ver_personas.sh stop`

## Reglas para trabajar en esta Pi

- No modificar `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`: los usan otros proyectos.
- Todo lo de Keepon va en `~/keepon/` y, si hace falta, en un venv propio `~/keepon_env` (con `--system-site-packages` para ver `rclpy`).
- Mientras corre `ver_personas.sh` o Keepon, la cámara 0 está ocupada.
