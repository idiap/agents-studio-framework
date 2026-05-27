# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
TrustProv Service for computing trust indexes from provenance data.

This module integrates the trustprov package to compute trust indexes
and explanations for workflow executions based on their provenance.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

# Import trustprov scoring functions
from .trustprov.score import (
    TrustConfig,
    score_run,
    compute_step_risk,
    compute_step_missingness,
)
from .trustprov.classify import classify_step
from .trustprov.graph import (
    build_adjacency,
    ancestors_of,
    compute_depths,
)

# Import types from provenance_models (trustprov will re-export these)
from lunar_api.flows.provenance.provenance_models import (
    Edge,
    LLMMetadata,
    ProvenanceRun,
    Step,
    StepRun,
    ViewModel,
    StepTrustScore,
    TrustScoreData,
    StepTrustData,
)

logger = logging.getLogger(__name__)


def view_model_to_provenance_run(view_model: ViewModel) -> ProvenanceRun:
    """
    Convert a ViewModel to a ProvenanceRun for trustprov scoring.

    Args:
        view_model: The view model from provenance generation.

    Returns:
        ProvenanceRun compatible with trustprov.
    """
    run = ProvenanceRun(
        run_id=view_model.run_id,
        base_uri=view_model.base_uri,
        recent_outputs=[
            {"step": ro.step, "ended_at": ro.ended_at, "summary": ro.summary}
            for ro in view_model.recent_outputs
        ],
        raw=None,
    )

    # Convert steps
    for step in view_model.steps:
        llm_meta = step.llm_metadata
        trust_step = Step(
            id=step.id,
            component=step.component,
            generative=step.generative,
            plan=step.plan,
            inputs={
                binding.name: (
                    binding.value if binding.value is not None else binding.raw
                )
                for binding in step.inputs
            },
            output=step.output.model_dump() if step.output else None,
            uri=step.uri,
            depends_on=step.depends_on,
            run=StepRun(
                started_at=step.run.started_at if step.run else None,
                ended_at=step.run.ended_at if step.run else None,
                duration_s=step.run.duration_s if step.run else None,
            ),
            llm=LLMMetadata(
                model=llm_meta.model if llm_meta else None,
                input_tokens=llm_meta.input_tokens if llm_meta else None,
                output_tokens=llm_meta.output_tokens if llm_meta else None,
                total_tokens=llm_meta.total_tokens if llm_meta else None,
            ),
        )
        run.steps[step.id] = trust_step

    # Convert edges
    for edge in view_model.edges:
        run.edges.append(
            Edge(
                type=edge.type,
                from_step=edge.from_step,
                to_step=edge.to_step,
                via=edge.via,
                field=edge.field,
            )
        )

    return run


def compute_step_trust_scores(
    view_model: ViewModel,
    target: Optional[str] = None,
    cfg: Optional[TrustConfig] = None,
) -> Dict[str, StepTrustData]:
    """Compute trust scores for each step in the view model.

    Args:
        view_model: The view model from provenance generation.
        target: Optional target step id for scoring context.
        cfg: Optional TrustConfig for scoring parameters.

    Returns:
        Dictionary mapping step IDs to their trust data.
    """
    cfg = cfg or TrustConfig()
    run = view_model_to_provenance_run(view_model)

    if not run.steps:
        return {}

    # Build adjacency and determine target
    fwd, rev = build_adjacency(run)

    # Choose target (use the most recent output or first step)
    if not target:
        if run.recent_outputs:
            target = run.recent_outputs[0].get("step")
        if not target:
            target = next(iter(run.steps.keys()))

    # Get ancestor subgraph
    sub = ancestors_of(target, rev) if target in run.steps else set(run.steps.keys())

    # Compute depths
    depths = compute_depths(fwd, sub, roots=[target] if target else [])

    # Classify and score each step
    step_trust_data: Dict[str, StepTrustData] = {}

    for step_id, step in run.steps.items():
        step.depth = depths.get(step_id, 0)
        step.kind = classify_step(step, None)
        step.missingness = compute_step_missingness(step)
        step.risk = compute_step_risk(step, cfg, mitigation=0.0)

        # Compute individual step trust (1 - risk)
        step_trust = 1.0 - step.risk
        step_confidence = 1.0 - step.missingness

        base_risk_val = _base_risk(step.kind or "DET", cfg)

        step_trust_data[step_id] = StepTrustData(
            trust_index=int(round(100 * step_trust)),
            confidence=int(round(100 * step_confidence)),
            band=_compute_band(step_trust, step_confidence),
            risk=round(step.risk, 4),
            step_kind=step.kind or "DET",
            depth=step.depth,
            missingness=round(step.missingness, 4),
            risk_factors={
                "base_risk": round(base_risk_val, 6),
                "depth": step.depth,
                "missingness": round(step.missingness, 4),
            },
            subscores={
                "trust": round(step_trust, 4),
                "confidence": round(step_confidence, 4),
            },
            drivers=[
                {
                    "factor": "step_kind",
                    "value": step.kind,
                    "impact": round(base_risk_val, 4),
                },
                {
                    "factor": "depth",
                    "value": step.depth,
                    "impact": round(step.depth * 0.05, 4),
                },
                {
                    "factor": "missingness",
                    "value": round(step.missingness, 4),
                    "impact": round(step.missingness * 0.3, 4),
                },
            ],
            actions=_compute_actions(step, step_trust, step_confidence),
            summary=_compute_step_summary(step, step_trust, step_confidence),
            details={
                "component": step.component,
                "generative": step.generative,
                "has_llm_metadata": bool(step.llm.model or step.llm.total_tokens),
            },
        )

    return step_trust_data


def _base_risk(kind: str, cfg: TrustConfig) -> float:
    """Return the baseline risk for a step kind."""
    return {
        "GEN": cfg.base_risk_gen,
        "RET": cfg.base_risk_ret,
        "DET": cfg.base_risk_det,
        "VER": cfg.base_risk_ver,
        "HUM": cfg.base_risk_hum,
    }.get(kind, cfg.base_risk_det)


def _compute_band(trust: float, confidence: float) -> str:
    """Compute trust band based on trust and confidence scores."""
    trust_index = int(round(100 * trust))
    conf_index = int(round(100 * confidence))
    if trust_index >= 80 and conf_index >= 70:
        return "green"
    elif trust_index < 50 or conf_index < 40:
        return "red"
    else:
        return "amber"


def _compute_actions(step: Step, trust: float, confidence: float) -> list[str]:
    """Compute recommended actions for a step based on its trust and confidence."""
    actions = []
    trust_index = int(round(100 * trust))
    conf_index = int(round(100 * confidence))

    if trust_index < 50:
        actions.append("Review step output for quality issues")
    if conf_index < 50:
        actions.append("Add more metadata to improve confidence")
    if step.generative and not step.llm.model:
        actions.append("Capture LLM model information")
    if step.kind == "GEN" and trust_index < 70:
        actions.append("Consider adding verification step after generation")
    if step.depth > 5:
        actions.append("Deep dependency chain - review data lineage")

    return actions


def _compute_step_summary(step: Step, trust: float, confidence: float) -> str:
    """Generate a human-readable summary of step trust."""
    trust_index = int(round(100 * trust))
    band = _compute_band(trust, confidence)

    kind_desc = {
        "GEN": "generative",
        "RET": "retrieval",
        "DET": "deterministic",
        "VER": "verification",
        "HUM": "human-reviewed",
    }.get(step.kind or "DET", "unknown")

    if band == "green":
        return f"High confidence {kind_desc} step with trust index {trust_index}"
    elif band == "red":
        return f"Low confidence {kind_desc} step with trust index {trust_index} - review recommended"
    else:
        return f"Medium confidence {kind_desc} step with trust index {trust_index}"


def _step_trust_data_to_step_trust_score(
    step_id: str, trust_data: StepTrustData
) -> StepTrustScore:
    """Convert StepTrustData to StepTrustScore for backward compatibility."""
    return StepTrustScore(
        step_id=step_id,
        trust_index=trust_data.trust_index,
        risk=trust_data.risk,
        kind=trust_data.step_kind,
        depth=trust_data.depth,
        missingness=trust_data.missingness,
        band=trust_data.band,
        risk_factors=trust_data.risk_factors,
    )


def compute_trust_score(
    view_model: ViewModel,
    target: Optional[str] = None,
    cfg: Optional[TrustConfig] = None,
) -> TrustScoreData:
    """
    Compute the overall trust score for a workflow execution.

    This function converts the view model to a provenance run and
    computes the trust index using the trustprov scoring engine.

    Args:
        view_model: The view model from provenance generation.
        target: Optional target step id for scoring.
        cfg: Optional TrustConfig for scoring parameters.

    Returns:
        TrustScoreData with overall and per-step trust information.
    """
    cfg = cfg or TrustConfig()
    run = view_model_to_provenance_run(view_model)

    if not run.steps:
        logger.warning("No steps found in view model for trust scoring")
        return TrustScoreData(
            trust_index=100,
            confidence=0,
            band="amber",
            subscores={},
            drivers=[],
            actions=["No steps to analyze"],
            summary="No steps found in provenance",
            step_scores={},
        )

    try:
        # Use trustprov's score_run for overall scoring
        report = score_run(run, workflow=None, target=target, cfg=cfg)

        # Compute per-step scores
        step_trust_data = compute_step_trust_scores(view_model, target=target, cfg=cfg)

        # Convert StepTrustData to StepTrustScore for backward compatibility
        step_scores = {
            step_id: _step_trust_data_to_step_trust_score(step_id, trust_data)
            for step_id, trust_data in step_trust_data.items()
        }

        return TrustScoreData(
            trust_index=report.trust_index,
            confidence=report.confidence,
            band=report.band,
            subscores=report.subscores,
            drivers=report.drivers,
            actions=report.actions,
            summary=report.summary,
            step_scores=step_scores,
            details=report.details,
        )
    except Exception as e:
        logger.error(f"Failed to compute trust score: {e}", exc_info=True)
        # Return a conservative default score
        return TrustScoreData(
            trust_index=50,
            confidence=0,
            band="amber",
            subscores={},
            drivers=[],
            actions=["Trust score computation failed; manual review recommended"],
            summary=f"Error computing trust score: {str(e)}",
            step_scores={},
        )
