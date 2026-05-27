# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Command-line interface for `trustprov`.

We expose a single subcommand today:

    trustprov score --provenance run.json [--workflow workflow.yaml] [--target step_id] [--out report.json]

The CLI is intentionally thin:
- parsing is done in `trustprov.io`
- scoring is done in `trustprov.score`
- serialization is done in `trustprov.report`

This keeps the CLI easy to maintain and test.
"""

from __future__ import annotations
import argparse
import sys
from .config import load_config
from .io import load_inputs
from .report import save_json, to_json
from .score import TrustConfig, score_run


def build_parser() -> argparse.ArgumentParser:
    """
    Build the CLI argument parser.

    Returns:
        argparse.ArgumentParser configured with subcommands.
    """
    p = argparse.ArgumentParser(
        prog="trustprov",
        description="Compute an output-centric Trust Index from workflow + provenance logs.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser(
        "score",
        help="Compute trust score for a target output step (default: final_report if present).",
    )
    s.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Path to workflow YAML (optional; helps classification).",
    )
    s.add_argument(
        "--provenance",
        type=str,
        required=True,
        help="Path to provenance JSON (view_model format).",
    )
    s.add_argument(
        "--target", type=str, default=None, help="Target step id (optional)."
    )
    s.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional YAML/JSON scoring config overriding TrustConfig defaults.",
    )
    s.add_argument(
        "--out",
        type=str,
        default=None,
        help="Write JSON report to this path (optional).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint.

    Returns:
        0 on success, non-zero on error.
    """
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "score":
        # Load optional workflow + required provenance run.
        wf, run = load_inputs(args.workflow, args.provenance)

        # Load config overrides if provided; otherwise use defaults.
        cfg = load_config(args.config) if args.config else TrustConfig()

        # Compute report.
        report = score_run(run, workflow=wf, target=args.target, cfg=cfg)

        # Output either to file or stdout.
        if args.out:
            save_json(report, args.out)
        else:
            print(to_json(report, indent=2))
        return 0

    parser.error("Unknown command")
    return 2
