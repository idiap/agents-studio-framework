# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Pytest configuration for lunar_api tests.

Sets up the app context with SQLite before any tests run.
"""

import pytest
import os

# Set environment variable for SQLite database path before any imports
os.environ.setdefault("SQLITE_DATABASE_PATH", ":memory:")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment with proper configuration."""
    # Ensure we use in-memory SQLite for tests
    os.environ["SQLITE_DATABASE_PATH"] = ":memory:"
    yield
