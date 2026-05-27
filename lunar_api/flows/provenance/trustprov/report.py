# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Report serialization helpers.

The scoring engine returns a :class:`trustprov.types.TrustReport` dataclass.
This module provides small utilities to convert it to dict/JSON and persist it.

We keep this separate from scoring so that:
- scoring stays pure and easy to unit test,
- the CLI can call `save_json()` without duplicating logic.
"""

from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .types import TrustReport


def to_dict(report: TrustReport) -> Dict[str, Any]:
    """Convert a TrustReport dataclass into a JSON-serializable dict."""
    return asdict(report)


def to_json(report: TrustReport, indent: int = 2) -> str:
    """
    Serialize a TrustReport to JSON.

    Args:
        report: TrustReport instance.
        indent: JSON indentation level (default: 2).

    Returns:
        JSON string (UTF-8 safe).
    """
    return json.dumps(to_dict(report), indent=indent, ensure_ascii=False)


def save_json(report: TrustReport, path: str | Path, indent: int = 2) -> None:
    """
    Write a TrustReport JSON file to disk.

    A trailing newline is added to make the output POSIX-friendly.
    """
    p = Path(path)
    p.write_text(to_json(report, indent=indent) + "\n", encoding="utf-8")
