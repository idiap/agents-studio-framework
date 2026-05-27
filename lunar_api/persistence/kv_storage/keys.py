# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Callable, TypeAlias

KVKey: TypeAlias = str


class Keys:
    _registry: dict[str, Callable[..., KVKey]] = {}

    @classmethod
    def register(cls, name: str, template: str):
        """
        Register a new key template.
        Example: Keys.register('invoice', 'resource:invoice:{id}')
        """

        def key_func(**kwargs):
            return template.format(**kwargs)

        cls._registry[name] = key_func

    @classmethod
    def factory(cls, *names: str, **kwargs) -> KVKey:
        """
        Factory a key from registered templates.
        Example: Keys.factory('invoice', id=123)
        """
        if not names:
            raise ValueError("At least one key name must be provided")
        key_func = cls._registry.get(names[0])
        if not key_func:
            raise KeyError(f"Key template '{names[0]}' not registered")
        key = key_func(**kwargs)
        for name in names[1:]:
            key_func = cls._registry.get(name)
            if not key_func:
                raise KeyError(f"Key template '{name}' not registered")
            key = f"{key}:{key_func(**kwargs)}"
        return key


Keys.register("azure_doc_intelligence", "azure_doc_intelligence:{hash}")
Keys.register(
    "azure_document_intelligence_figure", "azure_doc_intelligence:figure:{figure_id}"
)
