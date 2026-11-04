#!/bin/bash
# Prueba visual de la percepción en el navegador de la notebook.
# Uso (en la Pi):  bash ~/keepon/scripts/ver_percepcion.sh        (Ctrl+C corta todo)
#                  bash ~/keepon/scripts/ver_percepcion.sh stop   (si quedó en segundo plano)
PUERTO=8080
DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Cámara por nombre (no por índice): si se conecta la segunda NoIR, los índices cambian.
# Cámara y orientación desde config.yaml (+ config.local.yaml); CAMARA=... en el entorno la cambia.
read -r CAM_CFG ORIENTACION < <(cd "$DIR" && ~/keepon_env/bin/python -c \
    'from keepon import load_config; c = load_config()["camera"]; print(c["ros_camera"], c.get("orientation_deg", 0))')
CAMARA="${CAMARA:-$CAM_CFG}"

if [ "$1" = "stop" ]; then
    pkill -INT -f "[v]er_percepcion.py"; pkill -INT -f "[_]_node:=keepon_cam"; pkill -INT -f "[w]eb_video_server.*port:=$PUERTO"
    sleep 3
    pkill -KILL -f "[v]er_percepcion.py"; pkill -KILL -f "[_]_node:=keepon_cam"; pkill -KILL -f "[w]eb_video_server.*port:=$PUERTO"
    pkill -KILL -f "[m]ultiprocessing.spawn" 2>/dev/null
    echo "Visor detenido."; exit 0
fi

source /opt/ros/jazzy/setup.bash
source ~/camera_ws/install/setup.bash
if pgrep -x camera_node > /dev/null; then
    echo "La cámara ya está en uso (¿ver_personas.sh o vision_estereo?). Cortarlo antes." >&2
    exit 1
fi

GRUPOS=()
limpiar() {
    for pid in "${GRUPOS[@]}"; do kill -INT -- "-$pid" 2>/dev/null; done
    sleep 3
    for pid in "${GRUPOS[@]}"; do kill -KILL -- "-$pid" 2>/dev/null; done
}
trap limpiar EXIT
trap 'exit 130' INT TERM

setsid ros2 run camera_ros camera_node --ros-args -r __node:=keepon_cam \
    -p camera:="$CAMARA" -p orientation:="$ORIENTACION" -p width:=640 -p height:=480 > /tmp/keepon_cam.log 2>&1 &
GRUPOS+=($!)
setsid ros2 run web_video_server web_video_server --ros-args -p port:=$PUERTO > /tmp/keepon_web.log 2>&1 &
GRUPOS+=($!)
sleep 4

IP=$(tailscale ip -4 2>/dev/null | head -1)
echo "Abrí en el navegador:  http://$IP:$PUERTO/stream_viewer?topic=/keepon/percepcion"
echo "(los modelos tardan ~15 s en cargar)"
cd "$DIR"
setsid ~/keepon_env/bin/python scripts/ver_percepcion.py 2>&1 | grep -vE "^(W0000|I0000|INFO:|WARNING: Logging)|inference_feedback|opt.num_threads" &
GRUPOS+=($!)
wait
