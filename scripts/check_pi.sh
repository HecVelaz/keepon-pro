#!/usr/bin/env bash
# Diagnóstico de la Raspberry Pi 5 (Ubuntu 24.04): cámara, ESP32, temperatura, Python.
# Uso:  bash scripts/check_pi.sh
set -u
ok()   { printf '  \e[32mOK\e[0m   %s\n' "$*"; }
warn() { printf '  \e[33m!!\e[0m   %s\n' "$*"; }

echo "== Placa"
[ -r /proc/device-tree/model ] && tr -d "\0" < /proc/device-tree/model && echo
grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null && ok "Raspberry Pi 5" || warn "no parece una Pi 5"
free -h | awk '/Mem:/{print "  RAM total: "$2}'
t=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null); [ -n "$t" ] && echo "  temperatura: $((t/1000)) °C"
command -v vcgencmd >/dev/null && vcgencmd get_throttled

echo "== Cámaras (libcamera)"
if command -v rpicam-hello >/dev/null; then rpicam-hello --list-cameras 2>&1 | head -20; ok "rpicam-apps instalado"
elif command -v libcamera-hello >/dev/null; then libcamera-hello --list-cameras 2>&1 | head -20
elif command -v cam >/dev/null; then cam -l 2>&1 | head -20
else warn "no hay rpicam-hello / cam: instalar libcamera (ver README, sección Raspberry Pi)"; fi
ls /dev/video* /dev/media* 2>/dev/null | tr '\n' ' '; echo
gst-inspect-1.0 libcamerasrc >/dev/null 2>&1 && ok "GStreamer libcamerasrc disponible" || warn "falta gstreamer1.0-libcamera"

echo "== Python"
PY=${PY:-.venv/bin/python}; [ -x "$PY" ] || PY=python3
$PY -c "import picamera2; print('  OK   picamera2', picamera2.__file__)" 2>/dev/null || warn "picamera2 no importable (se usará GStreamer si está)"
$PY -c "import cv2; print('  cv2', cv2.__version__, '| GStreamer:', 'YES' in [l.split(':')[-1].strip()[:3] for l in cv2.getBuildInformation().splitlines() if 'GStreamer' in l][:1])" 2>/dev/null
$PY -c "import mediapipe as m; print('  mediapipe', m.__version__)" 2>/dev/null || warn "falta mediapipe"
$PY -c "import ultralytics as u; print('  ultralytics', u.__version__)" 2>/dev/null || warn "falta ultralytics"

echo "== ESP32-S3"
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || warn "no se ve el ESP32 (¿cable de datos? ¿puerto USB nativo del S3?)"
id -nG | grep -qw dialout && ok "usuario en grupo dialout" || warn "agregar usuario a dialout: sudo usermod -aG dialout \$USER (y reloguear)"
