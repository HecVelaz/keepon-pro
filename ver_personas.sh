#!/bin/bash
# Keepon: visor de detección de personas (cámara NoIR + YOLO26n NCNN) en el navegador de la notebook.
# Uso:  ~/keepon/ver_personas.sh          (Ctrl+C corta todo)
#       ~/keepon/ver_personas.sh stop     (corta una instancia lanzada en segundo plano)
# No usa ni modifica los scripts de vision_estereo.
PUERTO=8080
# Cámara por nombre (no por índice): si se conecta la segunda NoIR, los índices cambian.
CAMARA="${CAMARA:-/base/axi/pcie@120000/rp1/i2c@80000/imx708@1a}"
IMGSZ=${IMGSZ:-256}   # 256 = el de Keepon; IMGSZ=480 usa el modelo original de vision_estereo
MODELO=/home/r2d2/keepon/models/yolo26n_${IMGSZ}_ncnn_model
[ "$IMGSZ" = 480 ] && MODELO=/home/r2d2/vision_estereo/modelos/yolo26n_ncnn_model

if [ "$1" = "stop" ]; then
    pkill -INT -f "[_]_node:=keepon_" ; pkill -INT -f "[w]eb_video_server.*port:=$PUERTO"; sleep 2
    pkill -KILL -f "[_]_node:=keepon_" ; pkill -KILL -f "[w]eb_video_server.*port:=$PUERTO"
    echo "Visor detenido."; exit 0
fi

source /opt/ros/jazzy/setup.bash
source ~/camera_ws/install/setup.bash
source ~/yolo_ws/install/setup.bash
export PYTHONPATH=~/yolo_env/lib/python3.12/site-packages:$PYTHONPATH

GRUPOS=()
limpiar() {
    for pid in "${GRUPOS[@]}"; do kill -INT -- "-$pid" 2>/dev/null; done
    sleep 2
    for pid in "${GRUPOS[@]}"; do kill -KILL -- "-$pid" 2>/dev/null; done
}
trap limpiar EXIT
trap 'exit 130' INT TERM

setsid ros2 run camera_ros camera_node --ros-args -r __node:=keepon_cam \
    -p camera:="$CAMARA" -p width:=640 -p height:=480 > /tmp/keepon_cam.log 2>&1 &
GRUPOS+=($!)
sleep 4
setsid ros2 run yolo_ros detector_node --ros-args -r __node:=keepon_det \
    -p modelo:=$MODELO -p imagen:=/keepon_cam/image_raw -p imgsz:=$IMGSZ -p conf:=0.4 \
    -p "clases:=['person']" -p anotada:=true > /tmp/keepon_det.log 2>&1 &
GRUPOS+=($!)
setsid ros2 run web_video_server web_video_server --ros-args -p port:=$PUERTO > /tmp/keepon_web.log 2>&1 &
GRUPOS+=($!)

IP=$(tailscale ip -4 2>/dev/null | head -1)
echo "Detección:  http://$IP:$PUERTO/stream_viewer?topic=/yolo/left/image_annotated"
echo "Cámara:     http://$IP:$PUERTO/stream_viewer?topic=/keepon_cam/image_raw"
echo "Logs: /tmp/keepon_{cam,det,web}.log"
wait
