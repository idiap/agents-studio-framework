# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Report Provenance Service - tracks edits to reports and updates provenance data.

This service uses the lunar_prov manual_edits module to create provenance records
for each edit made to a report's markdown content.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from lunar_api.flows.provenance.lunar_prov.manual_edits import (
    diff_stats,
    unified_diff,
)
from lunar_api.flows.provenance.lunar_prov.utils import safe_id


def create_initial_provenance(
    report_id: UUID,
    content: str,
    username: str = "system",
) -> Dict[str, Any]:
    """Create initial provenance data for a new report.

    Args:
        report_id: The UUID of the report
        content: The initial content of the report
        username: The user who created the report

    Returns:
        Initial provenance data structure compatible with the view model
    """
    now = datetime.now(timezone.utc).isoformat()
    run_id = safe_id(f"report-{str(report_id)}-{now}")
    base_uri = f"http://lunarbase.ai/prov/report/{str(report_id)}"

    return {
        "manifest": {
            "base_uri": base_uri,
            "report_id": str(report_id),
            "run_id": run_id,
            "created_at": now,
            "version": 0,
        },
        "view_model": {
            "base_uri": base_uri,
            "run_id": run_id,
            "workflow": {
                "id": str(report_id),
                "name": "Report",
                "description": "Report editing workflow",
                "status": "created",
                "started_at": now,
                "completed_at": "",
                "uri": f"{base_uri}/plan/workflow/{safe_id(str(report_id))}",
            },
            "data_sources": [
                {
                    "id": "initial_content",
                    "uri": f"{base_uri}/run/{run_id}/entity/input/initial_content",
                    "value": content[:500] if len(content) > 500 else content,
                    "summary": f"Initial content ({len(content)} chars)",
                    "is_external": False,
                }
            ],
            "steps": [
                {
                    "id": "report_creation",
                    "component": "report_creation",
                    "plan": {"type": "creation"},
                    "depends_on": [],
                    "flow_inputs_used": ["initial_content"],
                    "run": {
                        "started_at": now,
                        "ended_at": now,
                        "duration_s": 0.0,
                    },
                    "inputs": [
                        {
                            "name": "content",
                            "raw": "initial_content",
                            "kind": "flow_input",
                            "ref": "initial_content",
                            "value": content[:500] if len(content) > 500 else content,
                            "value_summary": f"Initial content ({len(content)} chars)",
                        }
                    ],
                    "output": {
                        "value": content[:500] if len(content) > 500 else content,
                        "summary": f"Report v0 ({len(content)} chars)",
                    },
                    "uri": f"{base_uri}/run/{run_id}/activity/step/report_creation",
                }
            ],
            "edges": [],
            "recent_outputs": [
                {
                    "step": "report_creation",
                    "ended_at": now,
                    "summary": f"Report v0 ({len(content)} chars)",
                }
            ],
        },
        "versions": [
            {
                "version": 0,
                "content": content,
                "created_at": now,
                "username": username,
            }
        ],
    }


def add_edit_to_provenance(
    existing_provenance: Optional[Dict[str, Any]],
    report_id: UUID,
    old_content: str,
    new_content: str,
    username: str = "anonymous",
    note: str = "",
) -> Dict[str, Any]:
    """Add an edit to the provenance data.

    Args:
        existing_provenance: The current provenance data (if any)
        report_id: The UUID of the report
        old_content: The content before the edit
        new_content: The content after the edit
        username: The user who made the edit
        note: Optional note about the edit

    Returns:
        Updated provenance data with the new edit recorded
    """
    now = datetime.now(timezone.utc).isoformat()

    # If no existing provenance, create initial from old content then add edit
    if not existing_provenance:
        existing_provenance = create_initial_provenance(
            report_id=report_id,
            content=old_content,
            username="system",
        )

    # Get current version
    versions = existing_provenance.get("versions", [])
    current_version = len(versions)
    new_version = current_version

    # Compute diff stats
    stats = diff_stats(old_content, new_content)
    diff = unified_diff(old_content, new_content)

    # Get base info from existing provenance
    manifest = existing_provenance.get("manifest", {})
    view_model = existing_provenance.get("view_model", {})
    base_uri = manifest.get(
        "base_uri", f"http://lunarbase.ai/prov/report/{str(report_id)}"
    )
    run_id = manifest.get("run_id", safe_id(f"report-{str(report_id)}"))

    # Create new step for this edit
    edit_step_id = f"manual_edit_{new_version}"
    new_step = {
        "id": edit_step_id,
        "component": "manual_edit",
        "plan": {
            "type": "manual_edit",
            "username": username,
            "note": note,
        },
        "depends_on": (
            [versions[-1].get("step_id", "report_creation")]
            if versions
            else ["report_creation"]
        ),
        "flow_inputs_used": [],
        "run": {
            "started_at": now,
            "ended_at": now,
            "duration_s": 0.0,
        },
        "inputs": [
            {
                "name": "before_content",
                "raw": (
                    f"$report_v{current_version - 1}"
                    if current_version > 0
                    else "$initial_content"
                ),
                "kind": "step_output",
                "ref": (
                    versions[-1].get("step_id", "report_creation")
                    if versions
                    else "report_creation"
                ),
                "field": "output",
                "value": (
                    old_content[:200] + "..." if len(old_content) > 200 else old_content
                ),
                "value_summary": (
                    f"v{current_version - 1} ({len(old_content)} chars)"
                    if current_version > 0
                    else f"v0 ({len(old_content)} chars)"
                ),
            }
        ],
        "output": {
            "value": (
                new_content[:200] + "..." if len(new_content) > 200 else new_content
            ),
            "summary": f"v{new_version} ({len(new_content)} chars)",
        },
        "diff": {
            "stats": stats,
            "unified": diff[:1000] + "..." if len(diff) > 1000 else diff,
        },
        "uri": f"{base_uri}/run/{run_id}/activity/step/{edit_step_id}",
    }

    # Update view model
    steps = view_model.get("steps", [])
    steps.append(new_step)

    # Add edge from previous step to this one
    edges = view_model.get("edges", [])
    if versions:
        prev_step_id = versions[-1].get("step_id", "report_creation")
    else:
        prev_step_id = "report_creation"

    edges.append(
        {
            "type": "dependsOn",
            "from": prev_step_id,
            "to": edit_step_id,
            "via": "content",
            "field": "output",
        }
    )

    recent_outputs = view_model.get("recent_outputs", [])
    recent_outputs.insert(
        0,
        {
            "step": edit_step_id,
            "ended_at": now,
            "summary": f"Edit by {username}: {stats['lines_added']} lines added, {stats['lines_removed']} removed",
        },
    )

    recent_outputs = recent_outputs[:10]

    versions.append(
        {
            "version": new_version,
            "content": new_content,
            "created_at": now,
            "username": username,
            "step_id": edit_step_id,
            "note": note,
            "diff_stats": stats,
        }
    )

    # Update manifest version
    manifest["version"] = new_version
    manifest["last_modified_at"] = now
    manifest["last_modified_by"] = username

    # Reconstruct the provenance
    return {
        "manifest": manifest,
        "view_model": {
            **view_model,
            "steps": steps,
            "edges": edges,
            "recent_outputs": recent_outputs,
        },
        "versions": versions,
    }


def get_provenance_view_model(
    provenance_data: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Extract the view model from provenance data for frontend rendering.

    Args:
        provenance_data: The full provenance data structure

    Returns:
        The view model suitable for the ProvenanceGraph component
    """
    if not provenance_data:
        return None

    return provenance_data.get("view_model")
