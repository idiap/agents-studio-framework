# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from lunarflow.llm import LLMClient, LLMConfig, LLMProviderRegistry
from openai.lib.azure import AsyncAzureOpenAI

from . import tokens
from .config import AppConfig
from .tokens import EmbeddingsLLMClient
from ..ioc import DependencyContainer
from ..persistence.connections.sqlite_connection import SQLiteConnection
from ..persistence.kv_storage.sqlite_kv_storage import SQLiteKVStorage
from ..persistence.migrations import run_migrations
from ..report.repository.report_repository import ReportRepository
from ..auth.repository.user_repository import UserRepository


def register_dependencies(container: DependencyContainer) -> None:

    container.register_instance(
        tokens.APP_CONFIG, AppConfig.from_env(), name="app_config"
    )

    def create_sqlite_connection(config: AppConfig) -> SQLiteConnection:
        conn = SQLiteConnection(config.database_path)
        conn.connect()
        run_migrations(conn)
        return conn

    container.register_factory(
        tokens.DB_CONNECTION,
        create_sqlite_connection,
        name="db_connection",
        config=tokens.APP_CONFIG,
    )

    container.register(
        tokens.KV_STORAGE,
        SQLiteKVStorage,
        name="kv_storage",
        connection=tokens.DB_CONNECTION,
    )

    container.register(
        tokens.LLM_PROVIDER,
        LLMClient,
        registry=LLMProviderRegistry.with_defaults(),
        base_config=LLMConfig(provider="openai"),
        name="llm_provider",
    )

    container.register_factory(
        tokens.LLM_EMBEDDINGS_PROVIDER,
        lambda config: EmbeddingsLLMClient(
            registry=LLMProviderRegistry.with_defaults(),
            base_config=LLMConfig(
                provider="openai",
                azure_deployment=config.azure_openai_embedding_deployment,
            ),
        ),
        name="llm_embeddings_provider",
        config=tokens.APP_CONFIG,
    )

    container.register(
        tokens.REPORT_REPOSITORY,
        ReportRepository,
        name="report_repository",
        sql_database_connection=tokens.DB_CONNECTION,
    )

    container.register(
        tokens.USER_REPOSITORY,
        UserRepository,
        name="user_repository",
        sql_database_connection=tokens.DB_CONNECTION,
    )

    container.register_factory(
        tokens.ASYNC_AZURE_OPENAI,
        lambda config: AsyncAzureOpenAI(
            api_key=config.llm_azure_api_key,
            api_version=config.llm_azure_api_version,
            azure_endpoint=config.llm_azure_base_url,
        ),
        name="async_azure_openai",
        config=tokens.APP_CONFIG,
    )
