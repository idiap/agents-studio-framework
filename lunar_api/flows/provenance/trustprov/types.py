# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Core data structures used throughout `trustprov`.

This module now re-exports Pydantic models from the Icebrook provenance_models module,
ensuring type consistency across the application.

All types are defined in lunar_api.flows.provenance.provenance_models and re-exported here
for backward compatibility with existing trustprov code.
"""

from __future__ import annotations
from lunar_api.flows.provenance.provenance_models import (
    Edge,
    LLMMetadata,
    ProvenanceRun,
    Step,
    StepRun,
    TrustReport,
    Workflow,
)

__all__ = [
    "Edge",
    "LLMMetadata",
    "ProvenanceRun",
    "Step",
    "StepRun",
    "TrustReport",
    "Workflow",
]
