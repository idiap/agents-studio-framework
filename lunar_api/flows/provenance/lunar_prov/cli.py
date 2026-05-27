# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import argparse

from .export import export_prov, append_manual_edits
from .edits_spec import load_edits_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lunar-prov", description="Export Lunar workflow+log to PROV-O bundles"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    exp = sub.add_parser("export", help="Export provenance")
    exp.add_argument("--workflow", required=True, help="Path to Lunar workflow YAML")
    exp.add_argument("--log", required=True, help="Path to Lunar execution log JSON")
    exp.add_argument("--out", required=True, help="Output path (.trig or .jsonld)")
    exp.add_argument(
        "--format",
        default="trig",
        choices=["trig", "json-ld"],
        help="RDF serialization format",
    )
    exp.add_argument(
        "--base-uri",
        default="http://lunarbase.ai/prov",
        help="Base URI for minted resources",
    )
    exp.add_argument(
        "--no-embed-values",
        action="store_true",
        help="Do not embed prov:value payloads",
    )
    exp.add_argument(
        "--max-embed-bytes",
        type=int,
        default=500_000,
        help="Max bytes to embed in prov:value before truncating (default: 500000). Use 0 to disable embedding.",
    )
    exp.add_argument(
        "--emit-redacted",
        action="store_true",
        help="Emit a redacted bundle and link alternates",
    )
    exp.add_argument(
        "--html",
        default=None,
        help="Optional: write an interactive HTML provenance explorer",
    )
    exp.add_argument(
        "--manifest", default=None, help="Write a JSON manifest with per-bundle hashes"
    )
    exp.add_argument(
        "--sign-private-key",
        default=None,
        help="PEM private key to sign the manifest (Ed25519 or RSA)",
    )
    exp.add_argument(
        "--sign-password",
        default=None,
        help="Password for the private key (if encrypted)",
    )

    ap = sub.add_parser(
        "append-edits", help="Append manual Markdown edits to an existing PROV file"
    )
    ap.add_argument(
        "--prov-in", required=True, help="Existing provenance file (TriG or JSON-LD)"
    )
    ap.add_argument("--out", required=True, help="Output provenance file")
    ap.add_argument(
        "--format",
        default="trig",
        choices=["trig", "json-ld"],
        help="RDF serialization format",
    )
    ap.add_argument(
        "--base-uri",
        default=None,
        help="Override base URI (default: inferred from prov-in)",
    )
    ap.add_argument(
        "--edits-json",
        required=True,
        help="JSON spec describing one or more edit sessions",
    )
    ap.add_argument(
        "--report-id", default=None, help="Override report_id from edits-json"
    )
    ap.add_argument(
        "--attach-entity",
        default=None,
        help="IRI of the entity being edited (e.g., a workflow output entity)",
    )
    ap.add_argument(
        "--no-embed-values",
        action="store_true",
        help="Do not embed prov:value payloads",
    )
    ap.add_argument(
        "--max-embed-bytes",
        type=int,
        default=500_000,
        help="Max bytes to embed in prov:value before truncating (default: 500000). Use 0 to disable embedding.",
    )
    ap.add_argument(
        "--emit-redacted",
        action="store_true",
        help="Emit a redacted edits bundle and link alternates",
    )
    ap.add_argument(
        "--html",
        default=None,
        help="Optional: write an interactive HTML explorer for the resulting dataset",
    )
    ap.add_argument(
        "--manifest", default=None, help="Write a JSON manifest with per-bundle hashes"
    )
    ap.add_argument(
        "--sign-private-key",
        default=None,
        help="PEM private key to sign the manifest (Ed25519 or RSA)",
    )
    ap.add_argument(
        "--sign-password",
        default=None,
        help="Password for the private key (if encrypted)",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "export":
        export_prov(
            workflow_path=args.workflow,
            log_path=args.log,
            out_path=args.out,
            base_uri=args.base_uri,
            fmt=args.format,
            embed_values=(not args.no_embed_values) and (args.max_embed_bytes != 0),
            max_embed_bytes=None if args.max_embed_bytes == 0 else args.max_embed_bytes,
            emit_redacted=args.emit_redacted,
            html_path=args.html,
            manifest_path=args.manifest,
            sign_private_key=args.sign_private_key,
            sign_password=args.sign_password,
        )
        return 0
    if args.cmd == "append-edits":
        report_id, attach_in_spec, edits = load_edits_json(args.edits_json)
        append_manual_edits(
            prov_in=args.prov_in,
            out_path=args.out,
            report_id=args.report_id or report_id,
            edits=edits,
            attach_to_entity_iri=args.attach_entity or attach_in_spec,
            base_uri=args.base_uri,
            fmt=args.format,
            embed_values=(not args.no_embed_values) and (args.max_embed_bytes != 0),
            max_embed_bytes=None if args.max_embed_bytes == 0 else args.max_embed_bytes,
            emit_redacted=args.emit_redacted,
            html_path=args.html,
            manifest_path=args.manifest,
            sign_private_key=args.sign_private_key,
            sign_password=args.sign_password,
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
