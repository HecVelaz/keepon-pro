"""Keepon pro: cabeza social de 3 GDL (µTP Robótica II, FIUNA)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        base[k] = _merge(base.get(k, {}), v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return base


def load_config(path: Path | str | None = None) -> dict:
    """config.yaml + config.local.yaml (opcional, por máquina, fuera de git: p. ej. en la Pi
    `camera: {backend: ros2}`)."""
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    local = ROOT / "config.local.yaml"
    if path is None and local.exists():
        with open(local, encoding="utf-8") as f:
            cfg = _merge(cfg, yaml.safe_load(f) or {})
    return cfg
