# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from .utils import parse_iso

PROV = Namespace("http://www.w3.org/ns/prov#")


@dataclass
class Namespaces:
    base: Namespace
    prov: Namespace = PROV


def lit_json(value: Any) -> Literal:
    return Literal(
        json.dumps(value, ensure_ascii=False, sort_keys=True),
        datatype=URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON"),
    )


def add_bundle_header(g: Graph, bundle_iri: URIRef) -> None:
    g.add((bundle_iri, RDF.type, PROV.Bundle))
    g.add((bundle_iri, RDF.type, PROV.Entity))
    g.add((bundle_iri, RDFS.label, Literal(str(bundle_iri).split("/")[-1])))


def dt_literal(dt_str: str) -> Literal:
    """Create a typed xsd:dateTime literal.

    We validate that the input is parseable as ISO8601 (naive / Z / offset).
    We preserve the original lexical form when possible to avoid rewriting
    user-provided timestamps.
    """
    # Validate parseability
    parse_iso(dt_str)
    return Literal(dt_str, datatype=XSD.dateTime)
