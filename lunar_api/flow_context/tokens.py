# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from lunarflow.context import ServiceToken
from openai.lib.azure import AsyncAzureOpenAI
from lunarflow.llm import LLMClient

from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.persistence.connections import StorageConnection

llm_client_token = ServiceToken(AsyncAzureOpenAI, token="async-azure-openai")
llm_provider_token = ServiceToken(LLMClient, token="azure-openai")
storage_connection_token = ServiceToken(StorageConnection, token="storage_connection")
report_repository_token = ServiceToken(ReportRepository, token="report_repository")
