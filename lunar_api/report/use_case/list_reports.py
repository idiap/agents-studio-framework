# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import List, Optional

from lunar_api.report.repository.report_repository import ReportRepository


class ListReportsUseCase:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def execute(self, limit: Optional[int] = 100, user_id: Optional[str] = None) -> List[dict]:
        """List all reports with optional limit.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of report dictionaries
        """
        reports = self._report_repository.list_reports(limit=limit, user_id=user_id)
        return [report.to_dict() for report in reports]
