# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional

from . import tokens
from .config import AppConfig
from ..ioc import DependencyContainer
from .dependency_registration import register_dependencies


class AppContext:
    _instance: Optional["AppContext"] = None
    _container: Optional[DependencyContainer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True

    @property
    def config(self) -> AppConfig:
        return self.container.get(tokens.APP_CONFIG)

    @property
    def container(self) -> DependencyContainer:
        if self._container is None:
            self._container = DependencyContainer()
            register_dependencies(self._container)
        return self._container

    def start(self) -> None:
        self.container.db_connection.connect()

    def stop(self) -> None:
        self.container.db_connection.disconnect()

    def reset(self) -> None:
        self.stop()
        if self._container is not None:
            self._container.reset()
            self._container = None


_app_context_instance: Optional[AppContext] = None


def get_app_context() -> AppContext:
    """Get the singleton app context instance"""
    global _app_context_instance
    if _app_context_instance is None:
        _app_context_instance = AppContext()
    return _app_context_instance
