#!/usr/bin/env bash
# Hook PostToolUse: si Claude editó el núcleo (simulador, trayectoria, protocolo, firmware o config),
# corre los tests que comparan nucleo.cpp con SimESP32. Si fallan, sale con 2 para que Claude lo vea.
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */keepon/sim_esp32.py|*/keepon/trajectory.py|*/keepon/protocol.py|*/firmware/keepon_fw/nucleo.cpp|*/firmware/keepon_fw/nucleo.h|*/config.yaml) ;;
  *) exit 0 ;;
esac
cd "$CLAUDE_PROJECT_DIR" || exit 0
[[ -x .venv/bin/python ]] || exit 0   # sin el venv del proyecto no se puede probar: no bloquear
if ! salida=$(PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_firmware_nucleo.py 2>&1); then
  echo "El firmware y el simulador ya no coinciden (tests/test_firmware_nucleo.py):" >&2
  echo "$salida" | tail -30 >&2
  exit 2
fi
