# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import BackgroundTasks
from lunarflow.llm.models import LLMResponse
from lunarflow.runner.python_runner import PythonRunner
from lunarflow.events import EventType
from lunarflow.context import InMemoryContext
from lunarflow.exceptions import LunarException

from lunar_api.app_context import tokens
from lunar_api.app_context.app_context import get_app_context
from lunar_api.flows.task_status import TaskStatusManager
from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.provenance.provenance_service import generate_provenance
from lunar_api.flows.provenance.provenance_models import ProvenanceData
from lunar_api.flow_context.flow_context_registration import dependency_registration
from lunar_api.report.model import Report
from lunar_api.report.repository.report_repository import ReportRepository

TASK_TIMEOUT = 3 * 60 * 60
logger = logging.getLogger(__name__)


def _extract_step_value(step_result: Any) -> Any:
    if isinstance(step_result, dict):
        return step_result.get("value")
    return getattr(step_result, "value", None)


def extract_reports_from_result(result_value: Dict[str, Any]) -> List[Report]:
    """Extract all Report objects from a flow execution result.

    Args:
        result_value: The result.value dict from flow execution, keyed by step ID.

    Returns:
        List of Report objects found in the result.
    """
    reports: List[Report] = []
    if not isinstance(result_value, dict):
        return reports

    for step_id, result in result_value.items():
        # Handle both dict and object access patterns (results may be serialized/deserialized)
        value = _extract_step_value(result)

        if value is None:
            continue

        # Check for direct Report instances
        if step_id == "final_report":
            logger.info(">>> Final Report found")
        if isinstance(value, Report):
            logger.debug(f"Found Report object in step '{step_id}': id={value.id}")
            reports.append(value)
        elif isinstance(value, dict):
            # Check if it looks like a serialized Report
            if all(k in value for k in ("id", "name", "content", "created_at")):
                try:
                    report = Report(
                        id=(
                            UUID(str(value["id"]))
                            if isinstance(value["id"], str)
                            else value["id"]
                        ),
                        name=value["name"],
                        content=value["content"],
                        created_at=(
                            value["created_at"]
                            if isinstance(value["created_at"], datetime)
                            else datetime.fromisoformat(str(value["created_at"]))
                        ),
                        provenance_data=value.get("provenance_data"),
                    )
                    reports.append(report)
                except (ValueError, KeyError, TypeError):
                    # Not a valid Report structure, skip
                    pass

    return reports


def update_reports_with_provenance(
    reports: List[Report],
    provenance_data: ProvenanceData,
    report_repository: ReportRepository,
    user_id: Optional[str] = None,
    result_value: Optional[Dict[str, Any]] = None,
) -> List[UUID]:
    """Update reports with provenance data and apply trust annotations.

    Args:
        reports: List of Report objects to update.
        provenance_data: The provenance data to attach to each report.
        report_repository: Repository to use for database updates.
        result_value: The flow result value dict (keyed by step ID) for extracting component outputs.

    Returns:
        List of report IDs that were successfully updated.
    """
    updated_ids: List[UUID] = []
    provenance_dict = provenance_data.model_dump(mode="json")

    # Extract trust scores from provenance view_model
    trust_scores: Dict[str, Dict[str, Any]] = {}
    if provenance_data.view_model and provenance_data.view_model.steps:
        for step in provenance_data.view_model.steps:
            if step.trust:
                trust_scores[step.id] = step.trust.model_dump()
                logger.debug(
                    f"Trust score for step '{step.id}': {trust_scores[step.id]}"
                )

    # Extract component outputs from result_value
    component_outputs: Dict[str, str] = {}
    if result_value and isinstance(result_value, dict):
        for step_id, step_result in result_value.items():
            # Handle both dict and object access patterns (results may be serialized/deserialized)
            value = _extract_step_value(step_result)

            if value is not None:
                # Handle string outputs (tables, etc.)
                if isinstance(value, str):
                    component_outputs[step_id] = value
                # Handle dict outputs with 'tag' key (charts)
                elif isinstance(value, dict) and "tag" in value:
                    component_outputs[step_id] = value["tag"]
                # Handle LLM responses with 'content' key (nested in value dict)
                elif isinstance(value, LLMResponse):
                    component_outputs[step_id] = value.content

    logger.info(f"Extracted {len(component_outputs)} component outputs for annotation")
    logger.info(f"Extracted {len(trust_scores)} trust scores for annotation")

    for report in reports:
        try:
            # Apply trust annotations to report content if we have trust scores
            annotated_content = report.content
            if trust_scores and component_outputs:
                try:
                    annotated_content = _apply_trust_annotations_to_content(
                        report_content=report.content,
                        component_outputs=component_outputs,
                        trust_scores=trust_scores,
                    )
                    if annotated_content != report.content:
                        logger.info(f"Applied trust annotations to report {report.id}")
                except Exception as ann_error:
                    logger.warning(
                        f"Failed to apply trust annotations to report {report.id}: {ann_error}",
                        exc_info=True,
                    )
                    annotated_content = report.content

            # Update report with provenance and annotated content
            updated = report_repository.update_report_with_provenance_and_content(
                report_id=report.id,
                content=annotated_content,
                provenance_data=provenance_dict,
                user_id=user_id,
            )
            if updated:
                updated_ids.append(report.id)
        except Exception as e:
            logger.warning(
                f"Failed to update provenance for report {report.id}: {e}",
                exc_info=True,
            )

    return updated_ids


def _apply_trust_annotations_to_content(
    report_content: str,
    component_outputs: Dict[str, str],
    trust_scores: Dict[str, Dict[str, Any]],
) -> str:
    """Apply trust annotations to component outputs in the report.

    Finds component outputs in the report and wraps them with trust annotations.
    Only annotates outputs that have trust scores available.

    Args:
        report_content: The assembled report content
        component_outputs: Dictionary of component ID to output content
        trust_scores: Dictionary of component ID to trust data

    Returns:
        Report content with trust annotations applied
    """
    from lunar_api.report.utils.trust_annotation import annotate_component_output

    annotated_content = report_content

    for component_id, output in component_outputs.items():
        if output and output in annotated_content:
            trust_data = trust_scores.get(component_id)
            # Only annotate if trust data is available
            if trust_data:
                annotated_output = annotate_component_output(
                    component_id=component_id,
                    content=output,
                    trust_data=trust_data,
                )
                annotated_content = annotated_content.replace(
                    output, annotated_output, 1
                )
                logger.debug(f"Annotated output for component '{component_id}'")

    return annotated_content


class RunAgentUseCase:
    def __init__(
        self,
        flow_registry: FlowRegistry,
        task_manager: TaskStatusManager,
    ):
        self._flow_registry = flow_registry
        self._task_manager = task_manager

    async def execute(
        self,
        flow_id: str,
        inputs: Dict[str, Any],
        background_tasks: BackgroundTasks,
        user_id: Optional[str] = None,
        generate_prov: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Execute an agent flow asynchronously.

        Args:
            flow_id: The flow ID to execute
            inputs: Input parameters for the flow
            background_tasks: FastAPI background tasks
            generate_prov: Whether to generate provenance data

        Returns:
            Response dictionary with status and agent_id, or None if flow not found
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        if await self._task_manager.is_running(flow.get_id(), user_id=user_id):
            return {"error": "already_running", "flow_name": flow.get_name()}

        async def run_agent_flow():
            started_at: Optional[str] = None
            try:
                await self._task_manager.start_task(
                    flow.get_id(),
                    metadata={
                        "id": flow.get_id(),
                        "name": flow.get_name(),
                        "description": flow.get_description(),
                    },
                    user_id=user_id,
                )

                async def inner_execute_flow():
                    nonlocal started_at
                    await self._task_manager.update_progress(
                        flow.get_id(),
                        "Initializing context and runner",
                        user_id=user_id,
                    )
                    context = InMemoryContext()
                    dependency_registration(context, user_id=user_id)
                    runner = PythonRunner(context=context)
                    watched_events = [
                        EventType.FLOW_STARTED,
                        EventType.FLOW_FINISHED,
                        EventType.FLOW_ERROR,
                        EventType.STEP_STARTED,
                        EventType.STEP_FINISHED,
                        EventType.STEP_ERROR,
                        # EventType.AGENT_STREAM,
                    ]

                    for event_type in watched_events:
                        runner.subscribe(event_type, lambda *args: None)

                    await self._task_manager.update_progress(
                        flow.get_id(),
                        f"Running {flow.get_name()}",
                        user_id=user_id,
                    )

                    # Record start time for provenance
                    started_at = datetime.now(timezone.utc).isoformat()
                    try:
                        result = await runner.run(flow=flow, inputs=inputs)
                    finally:
                        for event_type in watched_events:
                            runner.unsubscribe(event_type, lambda *args: None)

                    # Record completion time for provenance
                    completed_at = datetime.now(timezone.utc).isoformat()

                    for key, value in result.value.items():
                        if isinstance(value, LunarException):
                            logger.info(f">>> Result key: {key}")

                    # Generate provenance data
                    provenance_data: Optional[ProvenanceData] = None
                    if generate_prov:
                        try:
                            await self._task_manager.update_progress(
                                flow.get_id(),
                                "Generating provenance data",
                                user_id=user_id,
                            )
                            provenance_data = generate_provenance(
                                flow=flow,
                                result=result,
                                inputs=inputs,
                                started_at=started_at,
                                completed_at=completed_at,
                                status="completed",
                                embed_values=True,
                                max_embed_bytes=100_000,
                                emit_redacted=False,
                            )
                            logger.info(
                                f"Generated provenance for {flow.get_id()}: "
                                f"{len(provenance_data.manifest.bundles)} bundles"
                            )
                        except Exception as prov_error:
                            logger.warning(
                                f"Failed to generate provenance for {flow.get_id()}: {prov_error}",
                                exc_info=True,
                            )
                            provenance_data = None

                    # Update any reports created during flow execution
                    if provenance_data is not None:
                        try:
                            reports = extract_reports_from_result(result.value)
                            if reports:
                                await self._task_manager.update_progress(
                                    flow.get_id(),
                                    f"Attaching provenance and trust annotations to {len(reports)} report(s)",
                                    user_id=user_id,
                                )
                                app_context = get_app_context()
                                report_repository: ReportRepository = (
                                    app_context.container.get(tokens.REPORT_REPOSITORY)
                                )
                                updated_ids = update_reports_with_provenance(
                                    reports=reports,
                                    provenance_data=provenance_data,
                                    report_repository=report_repository,
                                    user_id=user_id,
                                    result_value=result.value,
                                )
                                logger.info(
                                    f"Updated {len(updated_ids)} report(s) with provenance and trust annotations for flow {flow.get_id()}"
                                )
                        except Exception as report_prov_error:
                            logger.warning(
                                f"Failed to attach provenance to reports for {flow.get_id()}: {report_prov_error}",
                                exc_info=True,
                            )

                    # Complete task with result and provenance
                    await self._task_manager.complete_task(
                        flow.get_id(),
                        result={
                            "execution_result": result,
                            "provenance": (
                                provenance_data.model_dump(mode="json")
                                if provenance_data
                                else None
                            ),
                        },
                        user_id=user_id,
                    )

                await asyncio.wait_for(inner_execute_flow(), timeout=TASK_TIMEOUT)
            except asyncio.TimeoutError:
                error_msg = (
                    f"{flow.get_name()} timed out after {TASK_TIMEOUT / 3600} hours"
                )
                logger.error(error_msg)
                await self._task_manager.fail_task(
                    flow.get_id(),
                    error_msg,
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(f"{flow.get_name()} failed: {str(e)}", exc_info=True)
                await self._task_manager.fail_task(
                    flow.get_id(),
                    str(e),
                    user_id=user_id,
                )

        def sync_wrapper():
            asyncio.run(run_agent_flow())

        background_tasks.add_task(sync_wrapper)

        return {
            "status": "accepted",
            "message": f"{flow.get_name()} started",
            "agent_id": flow.get_id(),
        }
