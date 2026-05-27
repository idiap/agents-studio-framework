# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
trustprov
========

`trustprov` computes an *output-centric* Trust Index for agentic workflows by combining:

1) a **workflow description** (YAML) describing the intended steps/components, and
2) a **provenance log** (JSON) describing what actually ran (steps, dependencies, token usage, etc.).

Design goals
------------
- **Works with partial provenance.** Missing metadata should *not* crash scoring.
  Instead, it reduces a separate *Confidence* score and may add conservative bumps.
- **Explainable by construction.** The final report includes top risk drivers and
  recommended actions that map directly to the causal subgraph for the chosen target.
- **Portable ingestion.** The current parser targets a "view_model" JSON shape
  (as produced by the synthetic fixtures), but the internal types are generic enough
  to support adapters for PROV-O / custom logs.

The public API surface is intentionally small:
- :func:`trustprov.io.load_inputs` to load workflow + provenance
- :func:`trustprov.score.score_run` to compute the TrustReport
- `trustprov` CLI entrypoint for convenience

See:
- `docs/USAGE.md` for hands-on usage
- `docs/CONCEPT.md` for model rationale and interpretation
"""

__all__ = ["__version__"]
__version__ = "0.1.2"
