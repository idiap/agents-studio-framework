# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection
from lunar_api.persistence.kv_storage.sqlite_kv_storage import SQLiteKVStorage
from lunarflow.llm import LLMClient
from openai.lib.azure import AsyncAzureOpenAI

from lunar_api.app_context.config import AppConfig
from lunar_api.ioc import ServiceToken
from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.auth.repository.user_repository import UserRepository

APP_CONFIG = ServiceToken(AppConfig)
DB_CONNECTION = ServiceToken(SQLiteConnection)
LLM_PROVIDER = ServiceToken(LLMClient)


class EmbeddingsLLMClient(LLMClient):
    pass


LLM_EMBEDDINGS_PROVIDER = ServiceToken(EmbeddingsLLMClient)
ASYNC_AZURE_OPENAI = ServiceToken(AsyncAzureOpenAI)

REPORT_REPOSITORY = ServiceToken(ReportRepository)
USER_REPOSITORY = ServiceToken(UserRepository)

KV_STORAGE = ServiceToken(SQLiteKVStorage)
