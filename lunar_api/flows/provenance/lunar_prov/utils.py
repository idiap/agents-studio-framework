# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Iterable, Optional, Tuple

ISO_DT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
)


def parse_iso(dt: str) -> datetime:
    """Parse an ISO8601 datetime string.

    Accepts:
      - naive timestamps: 2025-12-28T12:34:56
      - UTC 'Z' suffix:   2025-12-28T12:34:56Z
      - offsets:          2025-12-28T12:34:56+01:00

    Returns a `datetime` (timezone-aware if an offset was provided).
    """
    if not isinstance(dt, str) or not dt.strip():
        raise ValueError("datetime must be a non-empty ISO8601 string")
    s = dt.strip()
    # Python's fromisoformat doesn't accept a bare 'Z'
    if s.endswith("Z"):
        s_parse = s[:-1] + "+00:00"
    else:
        s_parse = s
    try:
        return datetime.fromisoformat(s_parse)
    except Exception as e:
        raise ValueError(f"invalid ISO8601 datetime: {dt}") from e


def is_iso_datetime(dt: str) -> bool:
    """Return True if dt looks like an xsd:dateTime lexical form."""
    if not isinstance(dt, str):
        return False
    return bool(ISO_DT_RE.match(dt.strip()))


def safe_id(text: str) -> str:
    """Make a safe identifier component for IRIs."""
    text = (text or "").strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9._~-]", "-", text)
    return text or "id"


def find_step_refs(value: Any) -> Iterable[Tuple[str, Optional[str]]]:
    """Yield (step_id, field) references from Lunar-style strings like:
    - "$step"
    - "$step.field.subfield"
    """
    if not isinstance(value, str):
        return []
    if not value.startswith("$"):
        return []
    ref = value[1:]
    if not ref:
        return []
    parts = ref.split(".")
    step = parts[0]
    field = ".".join(parts[1:]) if len(parts) > 1 else None
    return [(step, field)]


def find_flow_input_refs(value: Any) -> Iterable[str]:
    """Yield flow-input references from Lunar-style strings like "&var"."""
    if not isinstance(value, str):
        return []
    if not value.startswith("&"):
        return []
    name = value[1:].strip()
    return [name] if name else []
