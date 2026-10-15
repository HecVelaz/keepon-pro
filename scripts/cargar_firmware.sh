#!/usr/bin/env bash
# Compila el firmware en la notebook y lo carga en la ESP32-C3, que está conectada a la Pi.
#
#   bash scripts/cargar_firmware.sh            # generar generado.h, compilar, copiar y cargar
#   bash scripts/cargar_firmware.sh --local    # cargar en una ESP32 conectada a la notebook (/dev/ttyUSB0)
#
# En la Pi usa esptool de ~/keepon_env (pip install esptool==4.8.1). El puerto no puede estar abierto
# por otro programa (un monitor serie o el robot).
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PI="r2d2@100.116.96.71"
PUERTO_PI="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
BUILD="/tmp/build_keepon_fw"
CLI="$HOME/.local/bin/arduino-cli"
FQBN="esp32:esp32:esp32c3"

"$RAIZ/.venv/bin/python" "$RAIZ/scripts/generar_firmware.py"
"$CLI" compile --fqbn "$FQBN" --warnings all --output-dir "$BUILD" "$RAIZ/firmware/keepon_fw"

if [[ "${1:-}" == "--local" ]]; then
  "$CLI" upload -p /dev/ttyUSB0 --fqbn "$FQBN" --input-dir "$BUILD"
  exit 0
fi

ssh -o BatchMode=yes "$PI" "mkdir -p ~/keepon/firmware_build"
scp -q "$BUILD/keepon_fw.ino.merged.bin" "$PI:keepon/firmware_build/"
ssh -o BatchMode=yes "$PI" "if fuser $PUERTO_PI >/dev/null 2>&1; then echo 'el puerto está ocupado:'; fuser -v $PUERTO_PI; exit 1; fi
  ~/keepon_env/bin/python -m esptool --chip esp32c3 -p $PUERTO_PI -b 460800 write_flash 0x0 ~/keepon/firmware_build/keepon_fw.ino.merged.bin"
