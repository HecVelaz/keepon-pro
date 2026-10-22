# Raspberry Pi: acceso, comandos y visores

Movido desde `CLAUDE.md` el 22/10/2026. Estado del sistema de la Pi y benchmarks: `docs/ESTADO_PI.md`.

## Acceso a la Pi
- `ssh r2d2@100.116.96.71` por Tailscale. Hostname `r2d2-desktop`. La clave SSH ya está autorizada (`-o BatchMode=yes` funciona).
- Proyecto en la Pi: `~/keepon/`. Se sincroniza desde la notebook con:
  `rsync -a --exclude .venv --exclude .git --exclude logs --exclude __pycache__ --exclude models/ --exclude config.local.yaml ./ r2d2@100.116.96.71:keepon/`
  En Claude Code, `/pi-sync` hace ese rsync y anota el commit sincronizado en `~/keepon/.commit`; `/verificar` lo compara con `HEAD`.
- Entorno: `~/keepon_env` (venv `--system-site-packages`, para ver `rclpy`). Tiene MediaPipe, OpenCV 4.11, pyyaml, pyserial, pytest y lap. **ultralytics/torch/ncnn se toman de `~/yolo_env`** mediante `zz_yolo_env.pth` (solo lectura, para no duplicar sus 5,5 GB).
- `~/keepon/config.local.yaml` (fuera de git) contiene `camera: {backend: ros2}`.
- **NO modificar** `~/vision_estereo`, `~/yolo_env`, `~/camera_ws` ni `~/yolo_ws`: son de otros proyectos. Todo lo de Keepon va en `~/keepon` / `~/keepon_env`.
- La cámara funciona por `camera_ros` (libcamera compilada en `~/camera_ws`); no hay rpicam ni picamera2. Un solo dueño de la cámara a la vez: verificar con `pgrep -x camera_node` antes de lanzar algo.
- **Trampa de `pkill -f`:** si el patrón aparece en tu propio comando SSH, se mata a sí mismo. Usar la forma con corchetes: `pkill -f "[_]_node:=keepon_"`.
- Al hacer `source /opt/ros/jazzy/setup.bash`, no usar `set -u` (el script de ROS usa variables sin definir).

## Comandos en la Pi
```bash
bash ~/keepon/scripts/ver_percepcion.sh          # visor en el navegador: http://100.116.96.71:8080/stream_viewer?topic=/keepon/percepcion
bash ~/keepon/scripts/ver_percepcion.sh stop
~/keepon/ver_personas.sh [stop]                  # solo YOLO (detector_node de vision_estereo), IMGSZ=256 por defecto
~/keepon_env/bin/python scripts/perception_bench.py --secs 20   # (con camera_node corriendo)
bash scripts/pi_bench.sh 15 [rapido]             # matriz de benchmark → logs/benchmark.csv
```

## Visores en la Pi (uno a la vez: comparten cámara y puerto 8080)
| | `scripts/ver_percepcion.sh` | `ver_personas.sh` (raíz del repo) |
|---|---|---|
| Qué muestra | Percepción completa de Keepon: personas (YOLO + tracker propio), rostros/ME_MIRA, pose con brazos (MediaPipe) | Solo recuadros de personas (YOLO26n 256 NCNN) |
| Código | `scripts/ver_percepcion.py` → `keepon/perception.py` (2 procesos) | `detector_node` de `~/yolo_ws` (vision_estereo, sin modificar) |
| Ver en | `/stream_viewer?topic=/keepon/percepcion` | `/stream_viewer?topic=/yolo/left/image_annotated` (cámara cruda: `/keepon_cam/image_raw`) |
| Velocidad (07/10) | El tópico del overlay llega a ~5 Hz (es solo el video; la percepción se mide con `perception_bench.py`) | **30 FPS**, detecta 1–2 personas |
| Uso | Calibrar ME_MIRA, ver brazos/SALUDO | Chequeo rápido de que cámara + YOLO andan |

Para cambiar de visor, primero `stop` del que está corriendo (`pgrep -x camera_node` tiene que dar vacío). Logs en `/tmp/keepon_*.log`.
