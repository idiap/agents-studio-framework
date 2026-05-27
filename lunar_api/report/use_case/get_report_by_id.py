# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional
from uuid import UUID

from lunar_api.report.repository.report_repository import ReportRepository


class GetReportByIdUseCase:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def execute(
        self,
        report_id: UUID,
        version: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Get a report by ID, optionally specifying a version.

        Args:
            report_id: The report UUID
            version: Optional version number to retrieve

        Returns:
            Report dictionary or None if not found
        """
        if version is not None:
            report = self._report_repository.get_report_version(
                report_id=report_id,
                version=version,
                user_id=user_id,
            )
        else:
            report = self._report_repository.get_report(
                report_id=report_id,
                user_id=user_id,
            )

        if not report:
            return None

        return report.to_dict()
