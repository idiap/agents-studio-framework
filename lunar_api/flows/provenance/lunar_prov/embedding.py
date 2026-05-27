# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Helpers for embedding payloads into prov:value safely.

Why this exists
---------------
In real Lunar runs, some inputs/outputs (and especially human-edited reports)
can be *very* large. Blindly embedding full payloads inside `prov:value` can:

* create multi‑MB RDF files that are hard to version-control,
* slow down visualization/interactive inspection,
* risk leaking sensitive data when sharing provenance.

This module provides bounded embedding helpers: when payloads exceed a byte
threshold, we embed a small preview and attach integrity metadata (SHA‑256,
byte length, and a truncation flag) so the provenance stays auditable.

The full payload can be stored elsewhere (artifact store) and linked via the
source system if desired.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from rdflib import Literal, URIRef, XSD

from .hashing import sha256_bytes


RDF_JSON = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON")


@dataclass(frozen=True)
class EmbedMeta:
    """Integrity/size metadata when a payload is truncated."""

    sha256: str
    byte_length: int
    truncated: bool = True


def _to_bytes(s: str) -> bytes:
    return s.encode("utf-8", errors="strict")


def embed_json(
    value: Any,
    max_bytes: Optional[int] = None,
) -> Tuple[Literal, Optional[EmbedMeta]]:
    """Return a Literal for a JSON-serializable value.

    If max_bytes is provided and the canonical JSON encoding exceeds that
    size, we return a *string preview* (xsd:string) and EmbedMeta.
    """
    s = json.dumps(value, ensure_ascii=False, sort_keys=True)
    b = _to_bytes(s)
    if max_bytes is None or len(b) <= max_bytes:
        return Literal(s, datatype=RDF_JSON), None

    sha = sha256_bytes(b)
    preview = s[: max(0, int(max_bytes))]
    # Preview may not be valid JSON; keep it as a string.
    return Literal(preview, datatype=XSD.string), EmbedMeta(
        sha256=sha, byte_length=len(b)
    )


def embed_text(
    text: str,
    max_bytes: Optional[int] = None,
) -> Tuple[Literal, Optional[EmbedMeta]]:
    """Return a Literal for text.

    If max_bytes is provided and the UTF‑8 encoding exceeds that size, we
    return a preview string literal and EmbedMeta.
    """
    s = text if isinstance(text, str) else str(text)
    b = _to_bytes(s)
    if max_bytes is None or len(b) <= max_bytes:
        return Literal(s, datatype=XSD.string), None
    sha = sha256_bytes(b)
    preview = s[: max(0, int(max_bytes))]
    return Literal(preview, datatype=XSD.string), EmbedMeta(
        sha256=sha, byte_length=len(b)
    )
