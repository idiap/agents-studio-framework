# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Step classification (taxonomy).

The scoring model uses a coarse step kind:
- GEN: generative model use (LLM free-form generation, summarization, synthesis)
- RET: retrieval / evidence acquisition (DB queries, web fetch, vector search)
- DET: deterministic compute (parsing, stats, transforms)
- VER: verification / validation (claim checks, schema checks, exec checks)
- HUM: human-in-the-loop operations (manual edits, approvals)

We deliberately use a simple classifier so the system remains usable with sparse logs.
Classification is based on:
1) step.component (primary signal)
2) step.generative flag (if present)
3) workflow YAML hints (if provided)

To adapt to your ecosystem, extend the component sets below or add workflow tags.
"""

from __future__ import annotations
from typing import Optional
from .types import Step, Workflow

# -----------------------------------------------------------------------------
# Component name heuristics
# -----------------------------------------------------------------------------
# These sets are conservative and intentionally small. They exist so that:
# - the synthetic fixtures classify correctly, and
# - real provenance logs with similar component naming patterns can be scored
#   without requiring extra schema work.
#
# If your system uses different names, update these sets or provide an adapter.

RETRIEVAL_COMPONENTS = {
    # RAG / retrieval
    "vector_search",
    "bm25_search",
    "sparql_query",
    "sql_query",
    "sparql_to_table",
    "sql_to_table",
    "sparql_to_chart_data",
    "sql_to_chart_data",
    # fetching files / web resources
    "web_fetch",
    "pdf_fetch",
    "file_load",
    "document_load",
}

VERIFICATION_COMPONENTS = {
    "claim_check",
    "exec_check",
    "schema_check",
    "consistency_check",
    "unit_test",
}

HUMAN_COMPONENTS = {
    "human_edit",
    "expert_review",
    "approval",
}

# A broad pattern for LLM-ish components. We keep it simple: if a component
# name contains "llm" we treat it as generative unless it's explicitly VER.
GEN_SUBSTRINGS = ("llm", "gpt", "chat", "synthesize", "summarize", "extract")


def classify_step(step: Step, wf: Optional[Workflow] = None) -> str:
    """
    Classify a step into one of: GEN, RET, DET, VER, HUM.

    Args:
        step: Parsed step from provenance.
        wf: Optional workflow (YAML) that may provide additional hints.

    Returns:
        Kind code as a string.

    Notes:
        - If `step.generative` is True, we treat it as GEN regardless of component name.
        - VER wins over GEN if a step is explicitly in `VERIFICATION_COMPONENTS`.
    """
    comp = (step.component or "").strip()

    if comp in HUMAN_COMPONENTS:
        return "HUM"
    if comp in VERIFICATION_COMPONENTS:
        return "VER"
    if step.generative:
        return "GEN"

    # Heuristic: component names that obviously indicate LLM use.
    if any(s in comp.lower() for s in GEN_SUBSTRINGS):
        return "GEN"

    if comp in RETRIEVAL_COMPONENTS:
        return "RET"

    # If workflow YAML exists, use its hints. This is helpful when provenance
    # is sparse and doesn't label steps as generative.
    if wf and step.id in wf.steps:
        wf_step = wf.steps[step.id] or {}
        if bool(wf_step.get("llm")):
            return "GEN"
        comp2 = (wf_step.get("component") or "").strip()
        if comp2 in VERIFICATION_COMPONENTS:
            return "VER"
        if comp2 in RETRIEVAL_COMPONENTS:
            return "RET"

    # Default: deterministic compute.
    return "DET"
