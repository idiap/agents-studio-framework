# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest
from unittest.mock import MagicMock
from lunar_api.persistence.kv_storage.sqlite_kv_storage import SQLiteKVStorage
from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection
from lunar_api.persistence.kv_storage.keys import Keys

# Register test key templates for the tests
Keys.register("test_resource", "test-resource:{id}")


@pytest.fixture
def sqlite_conn():
    """Create an in-memory SQLite connection for testing."""
    conn = SQLiteConnection(":memory:")
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture
def kv_storage(sqlite_conn):
    """Create a SQLiteKVStorage with the SQLite connection."""
    return SQLiteKVStorage(sqlite_conn)


def test_put_and_get(kv_storage):
    key = Keys.factory("test_resource", id="test2")
    kv_storage.put(key, "value2", ttl=5)
    value = kv_storage.get(key)
    assert value == b"value2"


def test_delete(kv_storage):
    key = Keys.factory("test_resource", id="test3")
    kv_storage.put(key, "value3")
    assert kv_storage.get(key) == b"value3"
    kv_storage.delete(key)
    assert kv_storage.get(key) is None


def test_get_nonexistent_key(kv_storage):
    key = Keys.factory("test_resource", id="nonexistent")
    value = kv_storage.get(key)
    assert value is None


def test_put_overwrite(kv_storage):
    key = Keys.factory("test_resource", id="overwrite")
    kv_storage.put(key, "original")
    kv_storage.put(key, "updated")
    value = kv_storage.get(key)
    assert value == b"updated"
