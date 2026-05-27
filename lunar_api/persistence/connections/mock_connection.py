# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from lunar_api.persistence.connections.storage_connection import StorageConnection


class MockConnection(StorageConnection):
    def connect(self):
        return self

    def disconnect(self):
        return
