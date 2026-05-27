# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Any, Optional
from .base import KVStorage
from ..connections.redis_connection import RedisConnection
from .keys import KVKey


class RedisKVStorage(KVStorage):
    def __init__(self, connection: RedisConnection):
        super().__init__(connection)

    def get(self, key: KVKey) -> Any:
        return self.connection.client.get(key)

    def put(self, key: KVKey, value: Any, ttl: Optional[int] = None):
        return self.connection.client.set(key, value, ex=ttl)

    def delete(self, key: KVKey):
        return self.connection.client.delete(key)
