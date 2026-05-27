# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from .parsers import load_workflow, load_execution_log
from .mapping import build_prov_dataset
from .hashing import graph_sha256_nt, stable_json_bytes
from .signing import load_private_key, sign_bytes
from .prov_io import load_dataset, save_dataset, infer_base_and_run_id
from .manual_edits import add_manual_edits_bundle, ManualEdit


def export_prov(
    workflow_path: str,
    log_path: str,
    out_path: str,
    base_uri: str = "http://lunarbase.ai/prov",
    fmt: str = "trig",
    embed_values: bool = True,
    max_embed_bytes: int | None = 500_000,
    emit_redacted: bool = False,
    html_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    sign_private_key: Optional[str] = None,
    sign_password: Optional[str] = None,
) -> Dict[str, Any]:
    workflow = load_workflow(workflow_path)
    log = load_execution_log(log_path)

    ds, manifest = build_prov_dataset(
        workflow=workflow,
        log=log,
        base_uri=base_uri,
        embed_values=embed_values,
        max_embed_bytes=max_embed_bytes,
        emit_redacted=emit_redacted,
    )

    # Write dataset
    ds.serialize(destination=out_path, format=fmt)

    # Optional: write an interactive HTML/JS rendering for drill-down exploration.
    if html_path:
        from .render import build_view_model, render_html

        vm = build_view_model(
            workflow=workflow, log=log, base_uri=base_uri, embed_values=embed_values
        )
        html = render_html(vm)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    # Compute per-bundle hashes
    bundles_info = {}
    for ctx in ds.contexts():
        iri = str(ctx.identifier)
        h = graph_sha256_nt(ctx)
        bundles_info[iri] = {
            "sha256_nt_sorted": h,
            "triple_count": len(ctx),
        }

    manifest_full = {
        **manifest,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_hashes": bundles_info,
    }

    if html_path:
        manifest_full["html_view"] = html_path

    # Sign manifest if requested
    if sign_private_key:
        key = load_private_key(sign_private_key, password=sign_password)
        msg = stable_json_bytes(manifest_full)
        sig = sign_bytes(key, msg)
        manifest_full["signature"] = sig

    if manifest_path:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_full, f, ensure_ascii=False, indent=2, sort_keys=True)

    return manifest_full


def append_manual_edits(
    prov_in: str,
    out_path: str,
    report_id: str,
    edits: List[ManualEdit],
    attach_to_entity_iri: Optional[str] = None,
    base_uri: Optional[str] = None,
    fmt: str = "trig",
    embed_values: bool = True,
    max_embed_bytes: int | None = 500_000,
    emit_redacted: bool = False,
    html_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    sign_private_key: Optional[str] = None,
    sign_password: Optional[str] = None,
) -> Dict[str, Any]:
    """Append manual Markdown edit provenance to an existing PROV dataset.

    This enables the *human-in-the-loop* extension of a workflow's provenance
    record after experts edited a generated report.
    """
    # Parse input using its own extension unless the caller forces a format.
    # (Output format is controlled separately by `fmt`.)
    ds = load_dataset(prov_in, fmt=None)

    inferred_base, run_id = infer_base_and_run_id(ds)
    base_uri = base_uri or inferred_base

    info = add_manual_edits_bundle(
        ds=ds,
        base_uri=base_uri,
        run_id=run_id,
        report_id=report_id,
        edits=edits,
        attach_to_entity_iri=attach_to_entity_iri,
        embed_values=embed_values,
        max_embed_bytes=max_embed_bytes,
        emit_redacted=emit_redacted,
    )

    save_dataset(ds, out_path, fmt=fmt)

    # Optional HTML rendering directly from the Dataset
    if html_path:
        from .render import render_html_from_dataset

        html = render_html_from_dataset(
            ds, base_uri=base_uri, embed_values=embed_values
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    # Bundle hashes + manifest
    bundles_info = {}
    for ctx in ds.contexts():
        iri = str(ctx.identifier)
        bundles_info[iri] = {
            "sha256_nt_sorted": graph_sha256_nt(ctx),
            "triple_count": len(ctx),
        }

    manifest_full = {
        "base_uri": base_uri,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_hashes": bundles_info,
        "manual_edits": info,
    }

    if html_path:
        manifest_full["html_view"] = html_path

    if sign_private_key:
        key = load_private_key(sign_private_key, password=sign_password)
        msg = stable_json_bytes(manifest_full)
        sig = sign_bytes(key, msg)
        manifest_full["signature"] = sig

    if manifest_path:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_full, f, ensure_ascii=False, indent=2, sort_keys=True)

    return manifest_full
