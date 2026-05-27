# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
from lunarflow.components import component
from lunarflow.context import Context

from lunar_api.report.model import Report, ReportInput
from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.flow_context.tokens import report_repository_token

logger = logging.getLogger(__name__)


@component(
    name="Report",
    description="Generates a report by replacing variables in a markdown template",
    token="report",
)
def report(context: Context, title: str, template: str, **kwargs) -> Report:
    try:
        report_content = template.format(**kwargs)
        logger.info("Report generated successfully")
        report_repository: ReportRepository = context.get(report_repository_token.token)
        report_input = ReportInput(name=title, content=report_content)
        created_report = report_repository.create_report(report_input)
        return created_report
    except KeyError as e:
        error_msg = f"Missing variable in template: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        logger.error(error_msg)
        raise