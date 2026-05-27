# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import redis
from typing import Optional

from .storage_connection import StorageConnection


class RedisConnection(StorageConnection):
    def __init__(self, redis_url: str):
        super().__init__()
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            self.connect()
        if not self._client:
            raise RuntimeError("Redis connection not initialized")
        return self._client

    def connect(self) -> "RedisConnection":
        self._client = redis.Redis.from_url(self.redis_url)
        return self

    def disconnect(self):
        if self._client:
            self._client.close()
            self._client = None
