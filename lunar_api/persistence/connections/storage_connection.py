# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from abc import ABC, abstractmethod


class StorageConnection(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def connect(self) -> "StorageConnection":
        pass

    @abstractmethod
    def disconnect(self):
        pass
