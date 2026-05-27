# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Optional
from .keys import KVKey


class KVStorage(ABC):
    def __init__(self, connection):
        self.connection = connection

    @abstractmethod
    def get(self, key: KVKey) -> Any:
        pass

    @abstractmethod
    def put(self, key: KVKey, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    def delete(self, key: KVKey):
        pass
