# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Configuration loader for scoring.

The scoring model is parameterized by :class:`trustprov.score.TrustConfig`.

A configuration file is optional. If not provided, `TrustConfig` defaults are used.

Supported formats:
- YAML (.yaml/.yml)
- JSON (.json)

Unknown keys are ignored (by design). This allows you to keep a single config file
across versions while only specifying the parameters you want to override.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from .score import TrustConfig


def load_config(path: str | Path) -> TrustConfig:
    """
    Load a config file and return a `TrustConfig` instance.

    Args:
        path: YAML/JSON config file path.

    Returns:
        TrustConfig with any recognized keys overridden.

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the file content is not a mapping/dict
        json.JSONDecodeError / yaml.YAMLError: if parsing fails
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    if p.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    else:
        data = json.loads(p.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping/dict.")

    # Only keep known fields. This is safer than passing arbitrary keys.
    allowed = {f.name for f in TrustConfig.__dataclass_fields__.values()}
    kwargs: Dict[str, Any] = {k: v for k, v in data.items() if k in allowed}
    return TrustConfig(**kwargs)
