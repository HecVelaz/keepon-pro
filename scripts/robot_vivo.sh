#!/bin/bash
# Keepon con cámara y servos de verdad: arranca camera_node, el servidor web (para mirar la cámara
# desde la notebook) y scripts/robot_vivo.py.
# Uso (en la Pi):  bash ~/keepon/scripts/robot_vivo.sh         (Ctrl+C: STOP del robot y corta todo)
#                  bash ~/keepon/scripts/robot_vivo.sh stop    (si quedó algo en segundo plano)
# Necesita: el firmware del robot en la ESP32, el puerto serie libre y la cámara libre.
PUERTO=8080
DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Cámara y orientación desde config.yaml (+ config.local.yaml); CAMARA=... en el entorno la cambia.
read -r CAM_CFG ORIENTACION < <(cd "$DIR" && ~/keepon_env/bin/python -c \
    'from keepon import load_config; c = load_config()["camera"]; print(c["ros_camera"], c.get("orientation_deg", 0))')
CAMARA="${CAMARA:-$CAM_CFG}"

if [ "$1" = "stop" ]; then
    pkill -INT -f "[r]obot_vivo.py"; pkill -INT -f "[_]_node:=keepon_cam"; pkill -INT -f "[w]eb_video_server.*port:=$PUERTO"
    sleep 3
    pkill -KILL -f "[r]obot_vivo.py"; pkill -KILL -f "[_]_node:=keepon_cam"; pkill -KILL -f "[w]eb_video_server.*port:=$PUERTO"
    pkill -KILL -f "[m]ultiprocessing.spawn" 2>/dev/null
    echo "Robot detenido."; exit 0
fi

source /opt/ros/jazzy/setup.bash
source ~/camera_ws/install/setup.bash
if pgrep -x camera_node > /dev/null; then
    echo "La cámara ya está en uso (¿ver_percepcion.sh o ver_personas.sh?). Cortarlo antes con su 'stop'." >&2
    exit 1
fi
if fuser /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 > /dev/null 2>&1; then
    echo "El puerto de la ESP32 está ocupado:" >&2; fuser -v /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 >&2
    exit 1
fi

GRUPOS=()
limpiar() {
    for pid in "${GRUPOS[@]}"; do kill -INT -- "-$pid" 2>/dev/null; done
    sleep 3
    for pid in "${GRUPOS[@]}"; do kill -KILL -- "-$pid" 2>/dev/null; done
}
trap limpiar EXIT
trap 'exit 130' TERM

setsid ros2 run camera_ros camera_node --ros-args -r __node:=keepon_cam \
    -p camera:="$CAMARA" -p orientation:="$ORIENTACION" -p width:=640 -p height:=480 > /tmp/keepon_cam.log 2>&1 &
GRUPOS+=($!)
setsid ros2 run web_video_server web_video_server --ros-args -p port:=$PUERTO > /tmp/keepon_web.log 2>&1 &
GRUPOS+=($!)
sleep 4

IP=$(tailscale ip -4 2>/dev/null | head -1)
echo "Overlay (T7) en el navegador:  http://$IP:$PUERTO/stream_viewer?topic=/keepon/overlay"
echo "Cámara cruda:                  http://$IP:$PUERTO/stream_viewer?topic=/keepon_cam/image_raw"
cd "$DIR"
# En primer plano: Ctrl+C le llega directo al robot, que manda STOP antes de salir. El filtro del ruido
# de los modelos ignora Ctrl+C: si muriera primero, el robot no podría escribir y el STOP podría no salir.
~/keepon_env/bin/python -u scripts/robot_vivo.py "$@" 2>&1 | \
    ( trap '' INT; exec grep --line-buffered -vE "^(W0000|I0000|INFO:|WARNING: Logging)|inference_feedback|opt.num_threads" )
