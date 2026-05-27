# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
I/O utilities: loading workflow YAML and provenance JSON.

The package is built around a simple ingestion contract:

- Workflow file (optional): YAML that describes steps/components in a human-friendly way.
  This can help *classification* (e.g., detecting LLM steps when provenance is sparse).

- Provenance file (required): JSON that captures what happened in an execution.
  In this package we currently target a lightweight "view_model" shape:

    {
      "provenance": {
        "view_model": {
          "run_id": "...",
          "steps": [
             {"id": "...", "component": "...", "depends_on": [...], ...},
             ...
          ],
          "edges": [
             {"from_step": "...", "to_step": "...", ...},
             ...
          ]
        }
      }
    }

If your system emits a different format, create an adapter that maps it into the
dataclasses in `trustprov.types`.

Design note: permissive parsing
-------------------------------
We avoid hard schema validation in the parser because a key requirement is that
the Trust Index still works when metadata is missing. Validation and missingness
handling happen later in `trustprov.score`.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from .types import Edge, LLMMetadata, ProvenanceRun, Step, StepRun, Workflow


def _normalize_kv_list(x: Any) -> Dict[str, Any]:
    """
    Normalize inputs/outputs that may be represented in multiple shapes.

    Many log formats serialize inputs as either:
      - a dict: {"param": value, ...}
      - a list of key/value objects: [{"name": "param", "value": ...}, ...]

    This helper converts both into a dict. Unknown shapes degrade gracefully
    (returning an empty dict).
    """
    if x is None:
        return {}
    if isinstance(x, dict):
        return x
    if isinstance(x, list):
        out: Dict[str, Any] = {}
        for item in x:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not name:
                continue
            # Some logs store a pre-parsed "value"; others store raw JSON under "raw".
            val = item.get("value", item.get("raw"))
            out[name] = val
        return out
    return {}


def load_workflow_yaml(path: str | Path) -> Workflow:
    """
    Load a workflow YAML file into a :class:`~trustprov.types.Workflow`.

    The workflow is optional but recommended. Even if it doesn't contain much
    runtime metadata, it can help the classifier infer step categories.

    Expected YAML shape (minimal):
        id: my_workflow
        steps:
          step_a:
            component: llm_summarize
            llm: true
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Workflow(
        id=data.get("id"),
        name=data.get("name"),
        description=data.get("description"),
        steps=data.get("steps") or {},
    )


def load_provenance_json(path: str | Path) -> Dict[str, Any]:
    """
    Load a provenance JSON file and return the raw parsed object.

    We keep the raw dict so that downstream debugging/adapters can inspect it
    (`ProvenanceRun.raw`).
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_view_model(prov_json: Dict[str, Any]) -> ProvenanceRun:
    """
    Parse a `provenance.view_model` structure into a :class:`~trustprov.types.ProvenanceRun`.

    This is the only concrete adapter shipped in this package. It supports:
      - `steps`: list of step objects
      - `edges`: list of explicit edges (optional)
      - `depends_on`: lightweight lineage for each step

    Missing fields are accepted. The scoring layer will interpret missingness.
    """
    view = (((prov_json or {}).get("provenance") or {}).get("view_model")) or {}
    run = ProvenanceRun(
        run_id=view.get("run_id"),
        base_uri=view.get("base_uri"),
        recent_outputs=view.get("recent_outputs") or [],
        raw=prov_json,
    )

    # Steps are normalized into our `Step` dataclass.
    for s in view.get("steps") or []:
        step_id = s.get("id")
        if not step_id:
            continue

        llm_meta = s.get("llm_metadata") or {}
        run_meta = s.get("run") or {}

        step = Step(
            id=step_id,
            component=s.get("component"),
            generative=bool(s.get("generative")),
            plan=s.get("plan"),
            inputs=_normalize_kv_list(s.get("inputs")),
            output=s.get("output"),
            uri=s.get("uri"),
            depends_on=list(s.get("depends_on") or []),
            run=StepRun(
                started_at=run_meta.get("started_at"),
                ended_at=run_meta.get("ended_at"),
                duration_s=run_meta.get("duration_s"),
            ),
            llm=LLMMetadata(
                model=llm_meta.get("model"),
                input_tokens=llm_meta.get("input_tokens"),
                output_tokens=llm_meta.get("output_tokens"),
                total_tokens=llm_meta.get("total_tokens"),
            ),
        )
        run.steps[step_id] = step

    # Optional explicit edges. Not all runs provide these.
    for e in view.get("edges") or []:
        run.edges.append(
            Edge(
                type=e.get("type", ""),
                from_step=e.get("from_step", ""),
                to_step=e.get("to_step", ""),
                via=e.get("via"),
                field=e.get("field"),
            )
        )

    return run


def load_inputs(
    workflow_path: Optional[str | Path],
    provenance_path: str | Path,
) -> Tuple[Optional[Workflow], ProvenanceRun]:
    """
    Convenience helper: load workflow (optional) + provenance (required).

    Returns:
        (workflow_or_none, run)

    The typical entrypoint is:
        wf, run = load_inputs(workflow_path, provenance_path)
        report = score_run(run, wf=wf, ...)
    """
    wf = load_workflow_yaml(workflow_path) if workflow_path else None
    prov_json = load_provenance_json(provenance_path)
    run = parse_view_model(prov_json)
    return wf, run
