# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Generic, Type, TypeVar

T = TypeVar("T")


class ServiceToken(Generic[T]):
    def __init__(self, service_type: Type[T]):
        self.service_type = service_type
