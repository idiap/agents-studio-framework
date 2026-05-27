# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    llm_model: str
    llm_azure_api_version: str
    llm_azure_api_key: str
    llm_azure_deployment: str
    llm_azure_base_url: str
    llm_azure_embeddings_deployment: str
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_embedding_deployment: str
    azure_openai_api_version: str
    database_path: str
    elasticsearch_host: str
    elasticsearch_api_key: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        database_path = os.getenv("SQLITE_DATABASE_PATH", "lunar_api.db")

        return cls(
            llm_model=os.getenv("LLM_MODEL", "lunar-gpt-4.1"),
            llm_azure_api_version=os.getenv("AZURE_API_VERSION", "2024-12-01-preview"),
            llm_azure_api_key=os.getenv("AZURE_API_KEY", ""),
            llm_azure_deployment=os.getenv("AZURE_DEPLOYMENT", "lunar-gpt-4.1"),
            llm_azure_base_url=os.getenv("AZURE_API_BASE", ""),
            llm_azure_embeddings_deployment=os.getenv(
                "LLM_AZURE_EMBEDDING_DEPLOYMENT", ""
            ),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_openai_embedding_deployment=os.getenv(
                "LLM_AZURE_EMBEDDING_DEPLOYMENT", "lunar-text-embedding-3-small"
            ),
            azure_openai_api_version=os.getenv(
                "AZURE_OPENAI_API_VERSION", "2024-02-01"
            ),
            database_path=database_path,
            elasticsearch_host=os.getenv(
                "ELASTICSEARCH_HOST", "http://elasticsearch:9200"
            ),
            elasticsearch_api_key=os.getenv("ELASTICSEARCH_API_KEY", "9200"),
        )
