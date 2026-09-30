"""Keepon pro: cabeza social de 3 GDL (µTP Robótica II, FIUNA)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: Path | str | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
