# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from lunarflow.flows import Flow
from lunarflow.dsl.flow_compiler import FlowCompiler


@dataclass(frozen=True)
class ExecutionLog:
    status: str
    started_at: str
    completed_at: str
    metadata: Dict[str, Any]
    event_log: List[Dict[str, Any]]
    result_value: Any


def load_workflow(path: str) -> Flow:
    """Load a workflow from a YAML file using Lunarflow's FlowCompiler.

    This keeps compatibility with YAML-defined flows (the compiler
    supports the same `steps:` format) and returns a proper `Flow`.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    compiler = FlowCompiler()
    flow = compiler.load(text)
    return flow


def load_execution_log(path: str) -> ExecutionLog:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", {}) or {}
    # Handle nested execution_result structure
    exec_result = result.get("execution_result", {}) or {}
    event_log = exec_result.get("event_log") or result.get("event_log", []) or []
    result_value = exec_result.get("value") or result.get("value")
    return ExecutionLog(
        status=str(data.get("status", "")),
        started_at=str(data.get("started_at", "")),
        completed_at=str(data.get("completed_at", "")),
        metadata=dict(data.get("metadata", {})),
        event_log=list(event_log),
        result_value=result_value,
    )


def index_events(event_log: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index step events by step id for started/finished/result."""
    idx: Dict[str, Dict[str, Any]] = {}
    for e in event_log:
        et = e.get("type")
        md = e.get("metadata") or {}
        payload = e.get("payload") or {}
        step_id = md.get("id") or payload.get("id")
        if et in ("step:started", "step:finished") and step_id:
            idx.setdefault(step_id, {})[et] = e
        elif et == "step:result":
            step_id = (md.get("id") if isinstance(md, dict) else None) or None
            if step_id:
                idx.setdefault(step_id, {})[et] = e
    return idx


def flow_start_event(event_log: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in event_log:
        if e.get("type") == "flow:started":
            return e
    return None


def flow_finish_event(event_log: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in reversed(event_log):
        if e.get("type") == "flow:finished":
            return e
    return None
