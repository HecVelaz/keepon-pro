#!/bin/bash
# Grabación de las camisetas reales con la cámara del robot (en la Pi). El robot tiene que estar apagado:
# un solo dueño de la cámara a la vez.
#   bash ~/keepon/pruebas_camisetas/grabar.sh camara            prende la cámara y la vista en vivo (queda en segundo plano)
#   bash ~/keepon/pruebas_camisetas/grabar.sh <nombre> [seg]    graba una toma (60 s; pitido cada 10 s, PITIDO=0 los quita) en ~/keepon/capturas/camisetas/<nombre>.mp4
#   bash ~/keepon/pruebas_camisetas/grabar.sh lista             muestra las tomas grabadas
#   bash ~/keepon/pruebas_camisetas/grabar.sh stop              apaga la cámara y la vista
PUERTO=8080
DIR="$(cd "$(dirname "$0")/.." && pwd)"

case "$1" in
  stop)
    pkill -INT -f "[_]_node:=keepon_cam"; pkill -INT -f "[w]eb_video_server.*port:=$PUERTO"
    sleep 2
    pkill -KILL -f "[_]_node:=keepon_cam"; pkill -KILL -f "[w]eb_video_server.*port:=$PUERTO"
    echo "Cámara apagada."; exit 0 ;;
  lista)
    ls -lh "$DIR/capturas/camisetas/" 2>/dev/null || echo "(sin tomas)"; exit 0 ;;
  camara)
    if systemctl --user is-active --quiet keepon; then
        echo "El robot está corriendo y usa la cámara: apagarlo antes (keepon stop o el panel)." >&2; exit 1
    fi
    if pgrep -x camera_node > /dev/null; then echo "La cámara ya está en uso." >&2; exit 1; fi
    read -r CAMARA ORIENTACION < <(cd "$DIR" && ~/keepon_env/bin/python -c \
        'from keepon import load_config; c = load_config()["camera"]; print(c["ros_camera"], c.get("orientation_deg", 0))')
    source /opt/ros/jazzy/setup.bash
    source ~/camera_ws/install/setup.bash
    setsid ros2 run camera_ros camera_node --ros-args -r __node:=keepon_cam \
        -p camera:="$CAMARA" -p orientation:="$ORIENTACION" -p width:=640 -p height:=480 \
        > /tmp/keepon_cam.log 2>&1 < /dev/null &
    setsid ros2 run web_video_server web_video_server --ros-args -p port:=$PUERTO \
        > /tmp/keepon_web.log 2>&1 < /dev/null &
    sleep 4
    IP=$(tailscale ip -4 2>/dev/null | head -1)
    echo "Vista en vivo: http://$IP:$PUERTO/stream_viewer?topic=/keepon_cam/image_raw"
    exit 0 ;;
  ""|-h|--help)
    sed -n '2,7p' "$0"; exit 0 ;;
esac

if ! pgrep -f "[_]_node:=keepon_cam" > /dev/null; then
    echo "Primero: grabar.sh camara" >&2; exit 1
fi
source /opt/ros/jazzy/setup.bash
cd "$DIR" && ~/keepon_env/bin/python -u pruebas_camisetas/grabar.py "$1" --segundos "${2:-60}" --espera 3 --pitido "${PITIDO:-10}" \
    2>&1 | grep -vE "^(W0000|I0000|INFO:|WARNING: Logging)"
