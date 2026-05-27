# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Pytest configuration.

This repository is frequently used in 'editable' mode (pip install -e .),
but unit tests should also run directly from the source tree.

We ensure the project root is on sys.path so `import lunar_prov` works
reliably in minimal environments.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
