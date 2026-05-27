# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional
from uuid import UUID

from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.report.use_case.report_provenance_service import (
    create_initial_provenance,
    get_provenance_view_model,
)


class GetReportProvenanceUseCase:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def execute(
        self,
        report_id: UUID,
        user_id: Optional[str] = None,
        username: str = "system",
    ) -> Optional[dict]:
        """Get the provenance data for a report.

        Returns the provenance view model suitable for rendering.
        Creates initial provenance if none exists.

        Args:
            report_id: The report UUID
            username: Username for initial provenance creation

        Returns:
            Dictionary with provenance data or None if report not found
        """
        report = self._report_repository.get_report(report_id=report_id, user_id=user_id)
        if not report:
            return None

        # If no provenance data exists, create initial provenance
        if not report.provenance_data:
            initial_provenance = create_initial_provenance(
                report_id=report_id,
                content=report.content,
                username=username,
            )
            report = self._report_repository.update_provenance_data(
                report_id=report_id,
                provenance_data=initial_provenance,
                user_id=user_id,
            )
            if not report:
                return None

        view_model = get_provenance_view_model(report.provenance_data)

        return {
            "report_id": str(report_id),
            "manifest": (
                report.provenance_data.get("manifest", {})
                if report.provenance_data
                else {}
            ),
            "view_model": view_model,
            "versions": (
                report.provenance_data.get("versions", [])
                if report.provenance_data
                else []
            ),
        }
