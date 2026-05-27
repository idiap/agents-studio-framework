# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from .sqlite_connection import SQLiteConnection
from .storage_connection import StorageConnection
from .mock_connection import MockConnection

# Alias for backwards compatibility
PostgresConnection = SQLiteConnection

__all__ = ["SQLiteConnection", "PostgresConnection", "StorageConnection", "MockConnection"]
