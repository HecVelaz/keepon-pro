#!/bin/bash
# Matriz de benchmark en la Raspberry Pi 5 (docs/ESTADO_PI.md).
# Arranca su propia cámara (camera_ros, cámara 0) y la corta al terminar.
# Resultados: logs/benchmark.csv
# Uso: bash scripts/pi_bench.sh [segundos_por_corrida] [rapido]
#   rapido: sólo las configuraciones candidatas (~2 min), para medir con personas en escena
# (sin set -u: el setup.bash de ROS usa variables sin definir)
SECS=${1:-15}
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY=~/keepon_env/bin/python
source /opt/ros/jazzy/setup.bash
source ~/camera_ws/install/setup.bash
cd "$DIR"

if pgrep -x camera_node > /dev/null; then
    echo "Hay un camera_node corriendo (¿ver_personas.sh o vision_estereo?): cortarlo antes." >&2
    exit 1
fi
setsid ros2 run camera_ros camera_node --ros-args -r __node:=keepon_cam \
    -p camera:=0 -p width:=640 -p height:=480 > /tmp/keepon_cam.log 2>&1 &
CAM=$!
trap 'kill -INT -- -$CAM 2>/dev/null; sleep 2; kill -KILL -- -$CAM 2>/dev/null' EXIT
sleep 5

run() { "$PY" scripts/benchmark.py --secs "$SECS" "$@" 2>&1 | grep -vE "^(W0000|I0000|INFO:)|inference_feedback|^\s*$"; }

M=models
if [ "${2:-}" = rapido ]; then
    run --label "P_yolo256_t4" --model "$M/yolo26n_256_ncnn_model" --imgsz 256 --no-face --no-pose
    run --label "P_mediapipe" --no-yolo
    run --label "P_full256" --model "$M/yolo26n_256_ncnn_model" --imgsz 256
    run --label "P_full320" --model "$M/yolo26n_320_ncnn_model" --imgsz 320
    echo; echo "CSV: $DIR/logs/benchmark.csv"; exit 0
fi
# A) Sólo YOLO: resolución x hilos
for S in 480 320 256; do
    MOD=$M/yolo26n_${S}_ncnn_model
    [ "$S" = 480 ] && MOD=/home/r2d2/vision_estereo/modelos/yolo26n_ncnn_model   # el existente (sólo lectura)
    for T in 4 2; do run --label "A_yolo${S}_t${T}" --model "$MOD" --imgsz "$S" --threads "$T" --no-face --no-pose; done
done
# B) Sólo MediaPipe (rostro + pose, 2 personas)
run --label "B_mediapipe" --no-yolo
# C) Pipeline completo
for S in 320 256; do
    for T in 2 3; do run --label "C_full${S}_t${T}" --model "$M/yolo26n_${S}_ncnn_model" --imgsz "$S" --threads "$T"; done
done
echo; echo "CSV: $DIR/logs/benchmark.csv"
