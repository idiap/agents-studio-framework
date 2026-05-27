# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from uuid import UUID

from lunar_api.report.repository.report_repository import ReportRepository


class DeleteReportUseCase:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def execute(self, report_id: UUID, user_id: str | None = None) -> bool:
        """Delete a report by ID.

        Args:
            report_id: The report UUID

        Returns:
            True if deleted successfully, False otherwise
        """
        return self._report_repository.delete_report(report_id=report_id, user_id=user_id)
