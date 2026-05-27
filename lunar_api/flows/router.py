# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from lunar_api.reasoner_flow import reasoner_flow_argumentation, reasoner_flow_enrich_thesis, reasoner_flow_class_support
from lunar_api.app_context import tokens
from lunar_api.app_context.app_context import get_app_context
from lunar_api.auth.dependencies import get_current_user
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.flows.task_status import TaskStatusManager, TaskInfo
from lunar_api.flows.flow_registry import flow_registry
from lunar_api.flows.use_case.list_flows import ListFlowsUseCase
from lunar_api.flows.use_case.get_agent_status import GetAgentStatusUseCase
from lunar_api.flows.use_case.get_flow import GetFlowUseCase
from lunar_api.flows.use_case.run_agent import RunAgentUseCase
from lunar_api.flows.use_case.cancel_agent import CancelAgentUseCase
from lunar_api.flows.use_case.get_agent_provenance import GetAgentProvenanceUseCase
from lunar_api.flows.use_case.get_agent_provenance_trig import GetAgentProvenanceTriGUseCase

from lunar_api.flows.models import AgentInputConfig


TASK_TIMEOUT = 3 * 60 * 60

router = APIRouter(prefix="/flow", tags=["flow"])
logger = logging.getLogger(__name__)
context = get_app_context()
kv_storage = context.container.get(tokens.KV_STORAGE)
task_manager = TaskStatusManager(kv_storage)


def register_agents():
    """Register all available agents in the system."""
    flow_registry.register(reasoner_flow_argumentation)
    flow_registry.register(reasoner_flow_enrich_thesis)
    flow_registry.register(reasoner_flow_class_support,
                           inputs=[
            AgentInputConfig(
                id="input_global_objective",
                label="Objectif global ou question à traiter",
                type="string",
                required=True,
            ), AgentInputConfig(
                id="input_learning_objectives",
                label="Objectifs d'apprentissage spécifiques ou sous-questions (optionnel)",
                type="string",
                required=False,
            ),
            AgentInputConfig(
                id="input_harmos_year",
                label="Année Harmos (e.g., 5H–11H)",
                type="string",
                required=True,
            ),
            AgentInputConfig(
                id="input_constraints",
                label="Contraintes spécifiques à respecter (optionnel)",
                type="string",
                required=False,
            ),
        ])

register_agents()


@router.get("/list")
async def list_flows():
    """List all registered agents with their configurations."""
    use_case = ListFlowsUseCase(flow_registry=flow_registry)
    return use_case.execute()


@router.get("/{flow_id}/status", response_model=TaskInfo)
async def get_agent_status(
    flow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the status of a specific agent by ID."""
    use_case = GetAgentStatusUseCase(
        flow_registry=flow_registry,
        task_manager=task_manager,
    )
    result = await use_case.execute(flow_id=flow_id, user_id=str(current_user.id))

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    return result


@router.get("/{flow_id}")
async def get_flow(flow_id: str, definition: bool = False):
    """Get flow by ID."""
    use_case = GetFlowUseCase(flow_registry=flow_registry)
    result = use_case.execute(flow_id=flow_id, definition=definition)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    return result


@router.post("/{flow_id}")
async def run_agent(
    flow_id: str,
    inputs: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Generic endpoint to run any registered agent by ID."""
    use_case = RunAgentUseCase(
        flow_registry=flow_registry,
        task_manager=task_manager,
    )
    result = await use_case.execute(
        flow_id=flow_id,
        inputs=inputs,
        background_tasks=background_tasks,
        user_id=str(current_user.id),
    )

    print(f">>>Run agent result: {result}")

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    if result.get("error") == "already_running":
        raise HTTPException(
            status_code=409,
            detail=f"{result['flow_name']} task is already running. Please wait for it to complete.",
        )

    return result


@router.post("/{flow_id}/cancel")
async def cancel_agent(
    flow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Cancel a running agent by ID."""
    use_case = CancelAgentUseCase(
        flow_registry=flow_registry,
        task_manager=task_manager,
    )
    result = await use_case.execute(flow_id=flow_id, user_id=str(current_user.id))

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    if result.get("error") == "not_running":
        raise HTTPException(
            status_code=409,
            detail=f"Flow '{flow_id}' is not running. Current status: {result.get('current_status')}",
        )

    if result.get("error") == "cancel_failed":
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel flow '{flow_id}'.",
        )

    return result


@router.get("/{flow_id}/provenance")
async def get_agent_provenance(
    flow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get the provenance data for a completed agent execution.

    Returns the PROV-O provenance data including:
    - manifest: Bundle information and hashes
    - view_model: Data for HTML visualization

    Returns 404 if the flow doesn't exist or hasn't been run.
    Returns 409 if the flow is still running.
    """
    use_case = GetAgentProvenanceUseCase(
        flow_registry=flow_registry,
        task_manager=task_manager,
    )
    result = await use_case.execute(flow_id=flow_id, user_id=str(current_user.id))

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    if result.get("error") == "still_running":
        raise HTTPException(
            status_code=409,
            detail=f"Flow '{flow_id}' is still running. Please wait for completion.",
        )

    if result.get("error") == "not_executed":
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow_id}' has not been executed yet.",
        )

    if result.get("error") == "execution_failed":
        raise HTTPException(
            status_code=400,
            detail=f"Flow '{flow_id}' execution failed: {result.get('message')}",
        )

    if result.get("error") == "no_result":
        raise HTTPException(
            status_code=404,
            detail=f"No result found for flow '{flow_id}'.",
        )

    if result.get("error") == "no_provenance":
        raise HTTPException(
            status_code=404,
            detail=f"No provenance data found for flow '{flow_id}'.",
        )

    if result.get("error") == "provenance_generation_failed":
        raise HTTPException(
            status_code=500,
            detail=f"Provenance generation failed: {result.get('message')}",
        )

    return result


@router.get("/{flow_id}/provenance/trig")
async def get_agent_provenance_trig(
    flow_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get the full TriG RDF provenance data for a completed agent execution.

    Returns the serialized PROV-O data in TriG format suitable for
    import into triple stores or further processing.
    """
    use_case = GetAgentProvenanceTriGUseCase(
        flow_registry=flow_registry,
        task_manager=task_manager,
    )
    result = await use_case.execute(flow_id=flow_id, user_id=str(current_user.id))

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Flow with id '{flow_id}' not found"
        )

    if result.get("error") == "not_completed":
        raise HTTPException(
            status_code=400,
            detail=f"Flow '{flow_id}' is not completed. Status: {result.get('status')}",
        )

    if result.get("error") == "no_result":
        raise HTTPException(
            status_code=404,
            detail=f"No result found for flow '{flow_id}'.",
        )

    if result.get("error") == "no_trig_data":
        raise HTTPException(
            status_code=404,
            detail=f"No TriG data found for flow '{flow_id}'.",
        )

    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        content=result["trig_data"],
        media_type="application/trig",
        headers={
            "Content-Disposition": f"attachment; filename={flow_id}_provenance.trig"
        },
    )
