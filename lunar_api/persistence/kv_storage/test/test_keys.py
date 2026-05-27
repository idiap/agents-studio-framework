# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest
from lunar_api.persistence.kv_storage.keys import Keys


def test_register_and_generate_key():
    Keys.register("simple", "simple:{id}")
    key = Keys.factory("simple", id=42)
    assert key == "simple:42"


def test_overwrite_template():
    Keys.register("overwrite", "first:{id}")
    key1 = Keys.factory("overwrite", id=1)
    assert key1 == "first:1"
    Keys.register("overwrite", "second:{id}")
    key2 = Keys.factory("overwrite", id=2)
    assert key2 == "second:2"


def test_missing_template_raises():
    with pytest.raises(KeyError):
        Keys.factory("not_registered", id=1)


def test_missing_param_raises():
    Keys.register("needs_param", "foo:{bar}")
    with pytest.raises(KeyError):
        Keys.factory("needs_param", baz=1)


def test_multiple_templates_composition():
    Keys.register("a", "A:{x}")
    Keys.register("b", "B:{y}")
    key = Keys.factory("a", "b", x=1, y=2)
    assert key == "A:1:B:2"
