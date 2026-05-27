# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Provenance Service for generating PROV-O provenance data from flow executions.

This module integrates the lunar_prov library to generate provenance data
following the PROV-O ontology standard. It converts lunarflow Flow objects
and execution results into provenance records.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lunarflow.flows import Flow

# Import from lunar_prov package
from lunar_api.flows.provenance.lunar_prov.parsers import ExecutionLog
from lunar_api.flows.provenance.lunar_prov.mapping import build_prov_dataset
from lunar_api.flows.provenance.lunar_prov.render import build_view_model, render_html
from lunar_api.flows.provenance.lunar_prov.hashing import graph_sha256_nt

# Import Pydantic models for type safety
from lunar_api.flows.provenance.provenance_models import (
    ProvenanceData,
    Manifest,
    ViewModel,
)

# Import trustprov service for trust scoring
from lunar_api.flows.provenance.trustprov_service import compute_trust_score

logger = logging.getLogger(__name__)

BASE_URI = "http://lunarbase.ai/prov"


def result_to_execution_log(
    result: Any,
    flow: Flow,
    inputs: Dict[str, Any],
    started_at: str,
    completed_at: str,
    status: str = "completed",
) -> ExecutionLog:
    """
    Convert a lunarflow execution result to a lunar_prov ExecutionLog dataclass.

    The ExecutionLog dataclass expects:
    - status: str
    - started_at: str
    - completed_at: str
    - metadata: Dict[str, Any]
    - event_log: List[Dict[str, Any]]
    - result_value: Any

    Args:
        result: The result from runner.run()
        flow: The executed Flow object
        inputs: The input values provided to the flow
        started_at: ISO format timestamp when execution started
        completed_at: ISO format timestamp when execution completed
        status: Execution status (completed, failed, etc.)

    Returns:
        ExecutionLog dataclass compatible with lunar_prov
    """
    event_log: List[Dict[str, Any]] = []

    if hasattr(result, "event_log") and result.event_log:
        for event in result.event_log:
            event_dict: Dict[str, Any] = {
                "type": (
                    event.type.value
                    if hasattr(event.type, "value")
                    else str(event.type)
                ),
                "timestamp": (
                    event.timestamp.isoformat()
                    if hasattr(event, "timestamp") and event.timestamp
                    else None
                ),
                "payload": (
                    _serialize_payload(event.payload)
                    if hasattr(event, "payload")
                    else None
                ),
                "metadata": (
                    dict(event.metadata)
                    if hasattr(event, "metadata") and event.metadata
                    else {}
                ),
            }
            event_log.append(event_dict)

    has_flow_started = any(e.get("type") == "flow:started" for e in event_log)
    if not has_flow_started:
        # Prepend flow:started event
        event_log.insert(
            0,
            {
                "type": "flow:started",
                "timestamp": started_at,
                "payload": {"inputs": inputs},
                "metadata": {"flow_id": flow.get_id()},
            },
        )
    else:
        # Update existing flow:started event to include inputs
        for e in event_log:
            if e.get("type") == "flow:started":
                if not e.get("payload"):
                    e["payload"] = {}
                if isinstance(e["payload"], dict):
                    e["payload"]["inputs"] = inputs
                break

    # Ensure we have flow:finished event
    has_flow_finished = any(e.get("type") == "flow:finished" for e in event_log)
    if not has_flow_finished:
        event_log.append(
            {
                "type": "flow:finished",
                "timestamp": completed_at,
                "payload": None,
                "metadata": {"flow_id": flow.get_id()},
            }
        )

    # Extract result value
    result_value = None
    if hasattr(result, "value") and result.value:
        result_value = _serialize_result_value(result.value)

    return ExecutionLog(
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        metadata={
            "flow_id": flow.get_id(),
            "flow_name": flow.get_name(),
        },
        event_log=event_log,
        result_value=result_value,
    )


def _serialize_payload(payload: Any) -> Any:
    """Serialize payload to JSON-compatible format."""
    if payload is None:
        return None
    if isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, dict):
        return {k: _serialize_payload(v) for k, v in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_serialize_payload(item) for item in payload]
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    if hasattr(payload, "__dict__"):
        return {
            k: _serialize_payload(v)
            for k, v in payload.__dict__.items()
            if not k.startswith("_")
        }
    return str(payload)


def _serialize_result_value(value: Any) -> Any:
    """Serialize result value to JSON-compatible format."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        serialized = {}
        for k, v in value.items():
            # Each step result may have a .value attribute
            if hasattr(v, "value"):
                serialized[k] = {"value": _serialize_result_value(v.value)}
            else:
                serialized[k] = _serialize_result_value(v)
        return serialized
    if isinstance(value, (list, tuple)):
        return [_serialize_result_value(item) for item in value]
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {
            k: _serialize_result_value(v)
            for k, v in value.__dict__.items()
            if not k.startswith("_")
        }
    return str(value)


def generate_provenance(
    flow: Flow,
    result: Any,
    inputs: Dict[str, Any],
    started_at: str,
    completed_at: str,
    status: str = "completed",
    base_uri: str = BASE_URI,
    embed_values: bool = True,
    max_embed_bytes: Optional[int] = 500_000,
    emit_redacted: bool = False,
) -> ProvenanceData:
    """
    Generate PROV-O provenance data from a flow execution.

    This function follows the same steps as the provenance notebook:
    1. Convert Flow to Workflow (prospective plan)
    2. Convert execution result to ExecutionLog (retrospective trace)
    3. Build PROV-O dataset with bundles
    4. Generate manifest with bundle hashes

    Args:
        flow: The executed Flow object
        result: The result from runner.run()
        inputs: The input values provided to the flow
        started_at: ISO format timestamp when execution started
        completed_at: ISO format timestamp when execution completed
        status: Execution status
        base_uri: Base URI for provenance entities
        embed_values: Whether to embed values in provenance
        max_embed_bytes: Maximum bytes for embedded values
        emit_redacted: Whether to emit redacted bundle

    Returns:
        Dictionary containing:
        - manifest: Provenance manifest with bundle info and hashes
        - trig: Serialized TriG RDF data
        - view_model: View model for HTML rendering (optional)
    """
    try:
        # Step 1: Convert result to ExecutionLog (retrospective provenance)
        log = result_to_execution_log(
            result=result,
            flow=flow,
            inputs=inputs,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
        )
        logger.debug(f"Created execution log: {len(log.event_log)} events")

        # Step 2: Build PROV-O dataset with bundles (Flow is passed directly)
        ds, manifest = build_prov_dataset(
            workflow=flow,
            log=log,
            base_uri=base_uri,
            embed_values=embed_values,
            max_embed_bytes=max_embed_bytes,
            emit_redacted=emit_redacted,
        )
        logger.debug(
            f"Built PROV dataset with bundles: {list(manifest.get('bundles', {}).keys())}"
        )

        # Step 3: Compute bundle hashes
        bundles_info = {}
        for ctx in ds.contexts():
            iri = str(ctx.identifier)
            h = graph_sha256_nt(ctx)
            bundles_info[iri] = {
                "sha256_nt_sorted": h,
                "triple_count": len(ctx),
            }

        # Step 4: Build complete manifest
        manifest_full = {
            **manifest,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bundle_hashes": bundles_info,
        }

        # Step 6: Serialize dataset to TriG format
        trig_data = ds.serialize(format="trig")

        # Step 5: Build view model for UI rendering
        view_model = None
        try:
            view_model = build_view_model(
                workflow=flow,
                log=log,
                base_uri=base_uri,
                embed_values=embed_values,
            )
        except Exception as e:
            logger.warning(f"Failed to build view model: {e}")

        # Validate and return as Pydantic models
        manifest_obj = Manifest(**manifest_full)
        view_model_obj = ViewModel(**view_model) if view_model else None

        # Step 7: Compute trust scores for steps and overall workflow
        trust_score_obj = None
        if view_model_obj:
            try:
                trust_score_obj = compute_trust_score(view_model_obj)

                # Enrich step views with trust data (nested trust object)
                from lunar_api.flows.provenance.trustprov_service import (
                    compute_step_trust_scores,
                )

                step_trust_data = compute_step_trust_scores(view_model_obj)
                for step in view_model_obj.steps:
                    if step.id in step_trust_data:
                        step.trust = step_trust_data[step.id]

            except Exception as e:
                logger.warning(f"Failed to compute trust scores: {e}")

        return ProvenanceData(
            manifest=manifest_obj,
            trig=trig_data,
            view_model=view_model_obj,
            trust_score=trust_score_obj,
        )

    except Exception as e:
        logger.error(f"Failed to generate provenance: {e}", exc_info=True)
        raise


def generate_provenance_html(
    flow: Flow,
    result: Any,
    inputs: Dict[str, Any],
    started_at: str,
    completed_at: str,
    status: str = "completed",
    base_uri: str = BASE_URI,
    embed_values: bool = True,
) -> str:
    """
    Generate an HTML visualization of the provenance data.

    Args:
        flow: The executed Flow object
        result: The result from runner.run()
        inputs: The input values provided to the flow
        started_at: ISO format timestamp when execution started
        completed_at: ISO format timestamp when execution completed
        status: Execution status
        base_uri: Base URI for provenance entities
        embed_values: Whether to embed values in visualization

    Returns:
        Self-contained HTML string with interactive provenance visualization
    """
    try:
        log = result_to_execution_log(
            result=result,
            flow=flow,
            inputs=inputs,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
        )

        view_model = build_view_model(
            workflow=flow,
            log=log,
            base_uri=base_uri,
            embed_values=embed_values,
        )

        return render_html(view_model)

    except Exception as e:
        logger.error(f"Failed to generate provenance HTML: {e}", exc_info=True)
        raise
