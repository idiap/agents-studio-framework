# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from lunarflow.components import ComponentRegistry
from lunarflow.context import InMemoryContext
from lunarflow.runner import PythonRunner

from lunar_api.app_context import get_app_context, tokens
from lunar_api.auth.dependencies import get_current_user
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.flow_context.flow_context_registration import dependency_registration
from lunar_api.report.model import ReportUpdate
from lunar_api.report.use_case.list_reports import ListReportsUseCase
from lunar_api.report.use_case.get_report_by_id import GetReportByIdUseCase
from lunar_api.report.use_case.update_report import UpdateReportUseCase
from lunar_api.report.use_case.get_report_provenance import GetReportProvenanceUseCase
from lunar_api.report.use_case.delete_report import DeleteReportUseCase

MODEL = "gpt-4.1"

app_context = get_app_context()

components = ComponentRegistry()
context = InMemoryContext(components)
dependency_registration(context)

runner = PythonRunner(context=context)

router = APIRouter(prefix="/report", tags=["report"])

# TODO: Refactor Comparative Report Use Case as a lunarflow agent
# @router.post("/comparative")
# async def build_comparative_report():
#     knowledge_base_repository = app_context.container.get(
#         tokens.KNOWLEDGE_BASE_REPOSITORY
#     )
#     build_report_use_case = BuildComparativeReportUseCase(
#         knowledge_base_repository=knowledge_base_repository,
#         runner=runner,
#         context=context,
#         model=MODEL,
#     )
#     return await build_report_use_case.execute()


@router.get("/", response_model=list)
async def list_reports(
    limit: Optional[int] = 100,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    report_repository = app_context.container.get(tokens.REPORT_REPOSITORY)
    use_case = ListReportsUseCase(report_repository=report_repository)
    return use_case.execute(limit=limit, user_id=str(current_user.id))


@router.get("/{report_id}", response_model=dict)
async def get_report_by_id(
    report_id: UUID,
    version: Optional[int] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    report_repository = app_context.container.get(tokens.REPORT_REPOSITORY)
    use_case = GetReportByIdUseCase(report_repository=report_repository)
    result = use_case.execute(
        report_id=report_id,
        version=version,
        user_id=str(current_user.id),
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Report{f' or version {version}' if version is not None else ''} not found",
        )

    return result


@router.put("/{report_id}", response_model=dict)
async def update_report(
    report_id: UUID,
    report_update: ReportUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    report_repository = app_context.container.get(tokens.REPORT_REPOSITORY)
    use_case = UpdateReportUseCase(report_repository=report_repository)
    result = use_case.execute(
        report_id=report_id,
        report_update=report_update,
        user_id=str(current_user.id),
        username=current_user.login,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    return result


@router.get("/{report_id}/provenance", response_model=dict)
async def get_report_provenance(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the provenance data for a report.

    Returns the provenance view model suitable for rendering in the ProvenanceGraph component.
    """
    report_repository = app_context.container.get(tokens.REPORT_REPOSITORY)
    use_case = GetReportProvenanceUseCase(report_repository=report_repository)
    result = use_case.execute(
        report_id=report_id,
        user_id=str(current_user.id),
        username=current_user.login,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    return result


@router.delete("/{report_id}", response_model=dict)
async def delete_report(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    report_repository = app_context.container.get(tokens.REPORT_REPOSITORY)
    use_case = DeleteReportUseCase(report_repository=report_repository)
    success = use_case.execute(report_id=report_id, user_id=str(current_user.id))
    return {"success": success, "message": "Report deleted successfully"}
