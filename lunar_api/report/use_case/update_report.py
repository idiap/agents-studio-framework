# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional
from uuid import UUID

from lunar_api.report.model import ReportUpdate
from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.report.use_case.report_provenance_service import add_edit_to_provenance


class UpdateReportUseCase:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def execute(
        self,
        report_id: UUID,
        report_update: ReportUpdate,
        user_id: Optional[str] = None,
        username: str = "anonymous",
    ) -> Optional[dict]:
        """Update a report's name and/or content.

        Args:
            report_id: The report UUID
            report_update: The update data (name and/or content)
            username: Username making the update (for provenance)

        Returns:
            Updated report dictionary or None if not found
        """
        # Get the current report to compare content
        current_report = self._report_repository.get_report(
            report_id=report_id,
            user_id=user_id,
        )
        if not current_report:
            return None

        # Check if content is changing
        content_changed = (
            report_update.content is not None
            and report_update.content != current_report.content
        )

        # Update the report (increment version if content changed)
        report = self._report_repository.update_report(
            report_id=report_id,
            name=report_update.name,
            content=report_update.content,
            increment_version=content_changed,
            user_id=user_id,
        )
        if not report:
            return None

        # If content changed, update provenance
        if content_changed:
            updated_provenance = add_edit_to_provenance(
                existing_provenance=current_report.provenance_data,
                report_id=report_id,
                old_content=current_report.content,
                new_content=report_update.content or "",
                username=username,
                note="",
            )
            report = self._report_repository.update_provenance_data(
                report_id=report_id,
                provenance_data=updated_provenance,
                user_id=user_id,
            )

        if not report:
            return None

        return report.to_dict()
