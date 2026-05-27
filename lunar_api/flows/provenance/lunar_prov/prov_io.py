# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""I/O helpers for PROV RDF datasets.

We use rdflib.Dataset for TriG / JSON-LD serialization.
"""

from __future__ import annotations
from typing import Optional, Tuple
from rdflib import Dataset


def guess_rdf_format(path: str) -> str:
    p = path.lower()
    if p.endswith(".jsonld") or p.endswith(".json-ld"):
        return "json-ld"
    # default to trig for multi-graph provenance
    return "trig"


def load_dataset(path: str, fmt: Optional[str] = None) -> Dataset:
    ds = Dataset()
    ds.parse(path, format=fmt or guess_rdf_format(path))
    return ds


def save_dataset(ds: Dataset, path: str, fmt: Optional[str] = None) -> None:
    ds.serialize(destination=path, format=fmt or guess_rdf_format(path))


def infer_base_and_run_id(ds: Dataset) -> Tuple[str, str]:
    """Best-effort inference of base URI and run_id from an existing dataset."""
    base_uri = "http://lunarbase.ai/prov"
    run_id = "run"

    # Infer base from any bundle identifier.
    for ctx in ds.contexts():
        iri = str(ctx.identifier)
        if "/bundle/" in iri:
            base_uri = iri.split("/bundle/")[0]
            break

    # Infer run id from any /run/<id>/ pattern.
    for ctx in ds.contexts():
        for s, p, o in ctx.triples((None, None, None)):
            for term in (s, o):
                t = str(term)
                if "/run/" in t:
                    # take the segment after /run/
                    rest = t.split("/run/")[1]
                    seg = rest.split("/")[0]
                    if seg:
                        run_id = seg
                        return base_uri, run_id

    return base_uri, run_id
