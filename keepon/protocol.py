"""Protocolo serie PC <-> ESP32 (ver docs/PROTOCOLO.md).

Líneas ASCII terminadas en '\\n', campos separados por un espacio, ángulos en grados.
Cada comando lleva un número de secuencia (seq) para poder asociar respuestas
y no reproducir dos veces un sonido reenviado.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

PROTOCOL_VERSION = 1
MAX_LINE = 64

# Comandos PC -> ESP32 y cantidad de argumentos después de seq.
COMMANDS = {
    "J": 3,        # J seq yaw pitch roll   -> nueva referencia articular (reemplaza a la anterior)
    "S": 1,        # S seq NOMBRE           -> reproducir sonido
    "CANCEL": 1,   # CANCEL seq SOUND       -> cortar el sonido actual
    "PING": 0,     # PING seq               -> keepalive + pide STATE
    "STOP": 0,     # STOP seq               -> congela todo, enclavado hasta RESUME
    "RESUME": 0,   # RESUME seq             -> libera el STOP
    "HOME": 0,     # HOME seq               -> ir a la postura HOME (rampa suave)
}

# Respuestas ESP32 -> PC: cantidad mínima y máxima de argumentos después de seq.
REPLIES = {"HELLO": (2, 2), "ACK": (0, 1), "DONE": (0, 0), "ERR": (1, 1), "STATE": (5, 5)}
STATES = {"RUN", "STOPPED", "WATCHDOG"}


class ProtocolError(ValueError):
    """Línea mal formada. `reason` es el código que viaja en ERR."""

    def __init__(self, reason: str, seq: int = -1):
        super().__init__(reason)
        self.reason = reason
        self.seq = seq


@dataclass(frozen=True)
class Command:
    name: str
    seq: int
    args: tuple = ()

    def encode(self) -> str:
        parts = [self.name, str(self.seq)]
        for a in self.args:
            parts.append(f"{a:.1f}" if isinstance(a, float) else str(a))
        return " ".join(parts) + "\n"


@dataclass(frozen=True)
class Reply:
    name: str
    seq: int
    args: tuple = ()

    def encode(self) -> str:
        parts = [self.name, str(self.seq)]
        for a in self.args:
            parts.append(f"{a:.1f}" if isinstance(a, float) else str(a))
        return " ".join(parts) + "\n"


def _parse_seq(tok: str) -> int:
    try:
        seq = int(tok)
    except ValueError:
        raise ProtocolError("BAD_SEQ") from None
    if seq < 0:
        raise ProtocolError("BAD_SEQ")
    return seq


def parse_command(line: str) -> Command:
    """Valida una línea como la validará el firmware. Lanza ProtocolError."""
    if len(line) > MAX_LINE:
        raise ProtocolError("TOO_LONG")
    toks = line.strip().split()
    if not toks:
        raise ProtocolError("EMPTY")
    name = toks[0].upper()
    if name == "HELLO":  # HELLO <versión>: la PC abre sesión
        if len(toks) != 2 or not toks[1].isdigit():
            raise ProtocolError("BAD_ARGS")
        return Command("HELLO", 0, (int(toks[1]),))
    if name not in COMMANDS:
        raise ProtocolError("UNKNOWN_CMD")
    if len(toks) < 2:
        raise ProtocolError("BAD_ARGS")
    seq = _parse_seq(toks[1])
    if len(toks) - 2 != COMMANDS[name]:
        raise ProtocolError("BAD_ARGS", seq)
    raw = toks[2:]
    if name == "J":
        try:
            vals = tuple(float(x) for x in raw)
        except ValueError:
            raise ProtocolError("BAD_NUMBER", seq) from None
        if not all(math.isfinite(v) for v in vals):
            raise ProtocolError("BAD_NUMBER", seq)
        return Command(name, seq, vals)
    if name == "CANCEL" and raw[0].upper() != "SOUND":
        raise ProtocolError("BAD_ARGS", seq)
    return Command(name, seq, tuple(x.upper() for x in raw))


def parse_reply(line: str) -> Reply:
    """Valida una respuesta del ESP32 antes de entregarla al resto del sistema."""
    toks = line.strip().split()
    if len(toks) < 2 or toks[0] not in REPLIES:
        raise ProtocolError("UNKNOWN_REPLY")
    name = toks[0]
    seq = _parse_seq(toks[1])
    raw = toks[2:]
    lo, hi = REPLIES[name]
    if not lo <= len(raw) <= hi:
        raise ProtocolError("BAD_ARGS", seq)
    try:
        if name == "HELLO":
            args = tuple(int(x) for x in raw)
        elif name == "ACK":
            if raw and raw[0] != "CLIPPED":
                raise ProtocolError("BAD_ARGS", seq)
            args = tuple(raw)
        elif name == "STATE":
            if raw[0] not in STATES:
                raise ProtocolError("BAD_ARGS", seq)
            angles = tuple(float(x) for x in raw[1:4])
            if not all(math.isfinite(v) for v in angles):
                raise ProtocolError("BAD_NUMBER", seq)
            args = (raw[0], *angles, raw[4])
        else:
            args = tuple(raw)
    except ProtocolError:
        raise
    except ValueError:
        raise ProtocolError("BAD_NUMBER", seq) from None
    return Reply(name, seq, args)
