# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import os
from dotenv import load_dotenv
from lunarflow.context import Context
from report.report import report
from lunar_api.auth.model import SYSTEM_USER_ID
from lunar_api.app_context.tokens import REPORT_REPOSITORY
from lunar_api.flow_context.tokens import report_repository_token

load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = "2025-03-01-preview"


def dependency_registration(context: Context, user_id: str | None = None):
    from lunar_api.app_context import get_app_context
    app_context = get_app_context()
    report_repository = app_context.container.get(REPORT_REPOSITORY).for_user(
        user_id=user_id or str(SYSTEM_USER_ID)
    )
    context.components.set(report)
    context.register_instance(
        report_repository_token,
        report_repository,
        registered_by="api",
    )
