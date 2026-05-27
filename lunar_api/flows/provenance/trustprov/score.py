# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Scoring engine: compute a Trust Index + explanations for a provenance run.

Conceptual model (high level)
-----------------------------
We treat an agentic system execution as a directed acyclic graph (DAG) of steps,
where steps may be:
- deterministic transforms (DET)
- retrieval / evidence acquisition (RET)
- generative model calls (GEN)
- verification / validation (VER)
- human-in-the-loop steps (HUM)

For a given *target output* (a step id), we compute trust over the *ancestor subgraph*
(the steps that contributed to producing the target). Each step receives a per-step
risk `r(step) in [0,1]`. Overall risk aggregates as:

    R = 1 - Π(1 - r_i)

and overall trust is:

    Trust = 1 - R

This aggregation behaves like an "independent failure" approximation:
- many small risks accumulate,
- one high-risk step can dominate,
- adding verification reduces risk for validated generative steps.

Partial provenance / missing metadata
-------------------------------------
A key requirement is that scoring must not require complete logs.

If metadata is missing:
- scoring still runs,
- a separate *Confidence* score is lowered,
- and for a few critical GEN fields (tokens, model id) we add small conservative bumps.

Explainability by construction
------------------------------
We generate:
- `drivers`: the top risky steps, each with a factor breakdown
  (base risk, context amplifier, chain amplifier, mitigation).
- `actions`: short recommendations mapped from weak subscores.

This makes the Trust Index usable for domain experts:
it becomes "what to check next" rather than only a number.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import ipaddress
from urllib.parse import urlparse

from .classify import classify_step
from .graph import ancestors_of, build_adjacency, compute_depths
from .types import ProvenanceRun, Step, TrustReport, Workflow


@dataclass(frozen=True)
class TrustConfig:
    """
    Scoring configuration.

    These parameters are *heuristics* and are intentionally simple. They are meant to:
    - provide sensible ordering across common agentic mechanisms,
    - remain interpretable (no hidden neural calibration),
    - be tunable via a small YAML/JSON config (see `trustprov.config`).

    Notes for calibration:
    - `base_risk_*` set the baseline risk by step kind.
    - `alpha_ctx` controls how strongly context size amplifies generative risk.
    - `gamma_depth` controls how strongly multi-step chains amplify risk.
    - `lambda_mitigation` controls how much verification can reduce risk.
    - `bump_unknown_*` provide explicit conservatism when critical GEN metadata is missing.
    """

    # Base risks (tuned to provide meaningful spread across realistic scenarios)
    base_risk_gen: float = 0.05
    base_risk_ret: float = 0.015
    base_risk_det: float = 0.001
    base_risk_ver: float = 0.0
    base_risk_hum: float = 0.05

    # Context scaling for generative steps.
    # We use the logged LLM input token count as a proxy for "context used".
    ctx_ref: int = 4096
    alpha_ctx: float = 0.55

    # Chain scaling:
    # - deeper steps (further from the target) increase risk slightly
    # - retries (if extracted) can also increase risk; currently retries are optional
    gamma_depth: float = 0.30
    eta_retries: float = 0.15

    # Mitigation strength (verification reduces risk).
    # A mitigation of 1.0 does not remove all risk; it scales by `lambda_mitigation`.
    lambda_mitigation: float = 0.7

    # Conservative bumps for unknown critical fields.
    # These only apply to GEN steps.
    bump_unknown_gen_tokens: float = 0.03
    bump_unknown_model: float = 0.01


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp `x` into [lo, hi]."""
    return max(lo, min(hi, x))


def _base_risk(kind: str, cfg: TrustConfig) -> float:
    """
    Return the baseline risk for a step kind.

    These are intentionally small: the main spread comes from:
    - GEN context amplification
    - chain depth amplification
    - verification mitigation
    """
    return {
        "GEN": cfg.base_risk_gen,
        "RET": cfg.base_risk_ret,
        "DET": cfg.base_risk_det,
        "VER": cfg.base_risk_ver,
        "HUM": cfg.base_risk_hum,
    }.get(kind, cfg.base_risk_det)


def compute_step_missingness(step: Step) -> float:
    """
    Compute step-level missingness (0..1), where 1 means critical metadata missing.

    Missingness is used for:
    - provenance completeness subscore,
    - confidence calculation,
    - and (for GEN steps) small conservative base-risk bumps.

    We weight GEN missingness more heavily around token accounting because your
    trust model treats context window size as a primary risk factor.
    """
    if step.kind == "GEN":
        missing = 0.0
        # Critical: token accounting for context amplification.
        if step.llm.input_tokens is None:
            missing += 0.55
        if step.llm.output_tokens is None:
            missing += 0.25
        # Helpful: model id supports auditability / reproducibility.
        if not step.llm.model:
            missing += 0.10
        # Helpful: lineage hints (depends_on/inputs) support traceability.
        if not step.depends_on and not step.inputs:
            missing += 0.10
        return _clip(missing, 0.0, 1.0)

    # Non-generative: we mainly care about:
    # - component name (so we can classify/interpret it),
    # - lineage hints (traceability),
    # - runtime timestamps (operational observability).
    missing = 0.0
    if not step.component:
        missing += 0.40
    if not step.depends_on and not step.inputs:
        missing += 0.30
    if not step.run.started_at or not step.run.ended_at:
        missing += 0.30
    return _clip(missing, 0.0, 1.0)


def compute_step_risk(
    step: Step, cfg: TrustConfig, mitigation: float = 0.0, retries: int = 0
) -> float:
    """
    Compute per-step risk r(step) in [0,1].

    Components:
    - base risk: depends on step kind (GEN/RET/DET/VER/HUM)
    - context amplification: GEN-only, increases with input token count
    - chain amplification: increases with depth (and optional retries)
    - mitigation: reduces GEN risk when validated by verification steps

    Args:
        step: Step to score. Must have `kind` and `depth` populated.
        cfg: TrustConfig hyperparameters.
        mitigation: 0..1 mitigation strength (e.g., verification passed).
        retries: number of retries for this step (optional; defaults to 0).

    Returns:
        Risk value in [0,1].
    """
    kind = step.kind or "DET"
    r0 = _base_risk(kind, cfg)

    # Conservative bumps for missing critical info on GEN.
    # We keep them small so they don't dominate; their main role is "fail-safe".
    if kind == "GEN":
        if step.llm.input_tokens is None and step.llm.total_tokens is None:
            r0 += cfg.bump_unknown_gen_tokens
        if not step.llm.model:
            r0 += cfg.bump_unknown_model

    # Context amplification (GEN only).
    # We treat logged input tokens as a proxy for "context used".
    amp_ctx = 1.0
    if kind == "GEN":
        ctx = step.llm.input_tokens
        if ctx is None:
            # If missing, fall back to reference scale (neutral) and rely on missingness.
            ctx = cfg.ctx_ref
        amp_ctx = 1.0 + cfg.alpha_ctx * math.log(1.0 + (ctx / float(cfg.ctx_ref)))

    # Chain amplification:
    # Longer causal chains create more opportunities for drift and compounding errors.
    amp_chain = (
        1.0
        + cfg.gamma_depth * math.log(1.0 + float(max(step.depth, 0)))
        + cfg.eta_retries * math.log(1.0 + float(max(retries, 0)))
    )

    # Apply mitigation (0..1). Only meaningful for GEN (we pass 0.0 for others).
    risk = (
        r0
        * amp_ctx
        * amp_chain
        * (1.0 - cfg.lambda_mitigation * _clip(mitigation, 0.0, 1.0))
    )
    return _clip(risk, 0.0, 1.0)


def aggregate_risk(step_risks: List[float]) -> float:
    """
    Aggregate per-step risks into overall risk R in [0,1].

    We use:
        R = 1 - Π(1 - r_i)

    This behaves well for explainability and monotonicity:
    - adding risky steps never decreases risk,
    - adding a verification mitigation reduces r_i and therefore reduces R.
    """
    prod = 1.0
    for r in step_risks:
        prod *= 1.0 - _clip(r)
    return _clip(1.0 - prod)


def choose_target(run: ProvenanceRun, explicit_target: Optional[str] = None) -> str:
    """
    Choose a target step id if the user didn't specify one.

    Heuristic priority:
    1) explicit target (CLI / API), **if it exists in the run**
    2) "final_report" if present
    3) first `recent_outputs` entry if provided in provenance
    4) otherwise any step id (stable iteration order in Python 3.7+ dicts)

    Note:
        If you rely on (4) in production, it's a signal that your provenance should
        record recent outputs or you should pass `--target`.
    """
    if explicit_target:
        # If a user passes a non-existent target, we ignore it and fall back to heuristics.
        if explicit_target in run.steps:
            return explicit_target
        # (No exception here: the library aims to degrade gracefully.)

    if "final_report" in run.steps:
        return "final_report"
    if run.recent_outputs:
        s = run.recent_outputs[0].get("step")
        if s:
            return s
    return next(iter(run.steps.keys()))


def _evidence_step(step: Step) -> bool:
    """
    Heuristic: does this step materialize an evidence artifact usable for grounding?

    "Evidence artifacts" are deterministic outputs a reviewer can inspect:
    - tables
    - charts (data)
    - computed statistics

    This is used for the `evidence_availability` subscore.
    """
    return (step.component or "") in {
        "sparql_to_table",
        "sparql_to_chart_data",
        "sql_to_table",
        "sql_to_chart_data",
        "stats_compute",
        "compute_stats",
        "compute_statistics",
        "chart_data",
        "report_bar_chart",
        "reports-line-chart",
        "plot",
        "table",
    }


def _extract_endpoint(step: Step) -> Optional[str]:
    """
    Best-effort extraction of an endpoint / source identifier from a retrieval step.

    This supports the `external_dependency` indicator. We look for a variety of common
    keys since different provenance formats use different names.

    Returns:
        A string like a URL, DB URI, or endpoint identifier if found; else None.
    """
    comp = step.component or ""
    candidates = []

    # Component-specific keys
    if comp == "rdf_query":
        candidates.append(step.inputs.get("sparql_endpoint"))
    if comp == "sql_query":
        candidates.append(step.inputs.get("db_uri"))
        candidates.append(step.inputs.get("database"))
    if comp in {"web_fetch", "pdf_fetch"}:
        candidates.append(step.inputs.get("url"))
        candidates.append(step.inputs.get("source_url"))
    if comp == "api_query":
        candidates.append(step.inputs.get("api_base"))
        candidates.append(step.inputs.get("endpoint"))

    # Generic fallbacks
    candidates.extend(
        [step.inputs.get("endpoint"), step.inputs.get("source"), step.inputs.get("uri")]
    )

    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def _has_snapshot(step: Step) -> bool:
    """
    True if the provenance suggests retrieved content was snapshotted/version-pinned.

    Snapshotting is a major trust booster because it improves reproducibility:
    - same endpoint + same query + same snapshot hash -> stable evidence.
    """
    for k in ("snapshot_hash", "snapshot_id", "content_hash", "dataset_hash", "etag"):
        v = step.inputs.get(k)
        if isinstance(v, str) and v.strip():
            return True
    return False


def _host_is_private(host: str) -> bool:
    """
    Heuristic: is `host` private/internal?

    We treat internal sources as less risky than public ones, all else equal.
    """
    if not host:
        return False
    host = host.strip().lower()
    if host in {"localhost"}:
        return True

    # IP address literal
    try:
        ip = ipaddress.ip_address(host)
        return bool(ip.is_private or ip.is_loopback or ip.is_link_local)
    except Exception:
        pass

    # Simple internal domain heuristics
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    return False


def _endpoint_is_external(endpoint: str) -> bool:
    """
    Return True if the endpoint looks like a public/external source.

    We parse URLs and DB URIs where possible. Non-URL identifiers default to False.
    """
    if not endpoint:
        return False
    ep = endpoint.strip()

    # Parse HTTP(S) URLs
    if ep.startswith("http://") or ep.startswith("https://"):
        host = urlparse(ep).hostname or ""
        return not _host_is_private(host)

    # Parse other URIs like postgres://user@host:port/db
    if "://" in ep:
        host = urlparse(ep).hostname or ""
        if host:
            return not _host_is_private(host)

    return False


def _verification_passed(step: Step) -> bool:
    """
    Best-effort pass/fail inference for a verification step.

    Supported patterns:
    - output.status in {"pass", "passed", "ok", "success"}
    - output.passed == True
    - inputs.passed == True

    If unknown, we return False (no mitigation). This is conservative.
    """
    out = step.output or {}
    if isinstance(out, dict):
        if out.get("status") in {"pass", "passed", "ok", "success"}:
            return True
        if out.get("passed") is True:
            return True
        if out.get("status") in {"fail", "failed", "error"}:
            return False

    # fallback to inputs
    if step.inputs.get("passed") is True:
        return True
    if step.inputs.get("passed") is False:
        return False

    return False


def _verification_targets(step: Step) -> Set[str]:
    """
    Infer which steps this VER step is meant to validate.

    Preferred keys (in step.inputs):
      - verifies
      - verified_step
      - checked_step
      - checked_steps
      - targets

    Fallback:
      - if none are present, assume it validates its direct dependencies (`depends_on`).

    This linkage enables per-step mitigation for GEN steps.
    """
    targets: Set[str] = set()
    for k in ("verifies", "verified_step", "checked_step", "checked_steps", "targets"):
        v = step.inputs.get(k)
        if isinstance(v, str) and v:
            targets.add(v)
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, str) and it:
                    targets.add(it)

    if not targets:
        for d in step.depends_on or []:
            if isinstance(d, str) and d:
                targets.add(d)
    return targets


def score_run(
    run: ProvenanceRun,
    workflow: Optional[Workflow] = None,
    target: Optional[str] = None,
    cfg: Optional[TrustConfig] = None,
) -> TrustReport:
    """
    Compute a TrustReport for a provenance run.

    Steps:
    1) Choose target step id.
    2) Extract ancestor subgraph (the steps that contributed to the target).
    3) Compute depths within that subgraph.
    4) Classify steps into GEN/RET/DET/VER/HUM.
    5) Compute missingness.
    6) Map verification steps to mitigations for validated GEN steps.
    7) Compute per-step risks and aggregate overall Trust.
    8) Compute subscores and confidence.
    9) Build explanatory drivers and recommended actions.

    Args:
        run: Parsed provenance run.
        workflow: Optional workflow description (improves classification and fills missing components).
        target: Optional target step id.
        cfg: Optional TrustConfig; if None, defaults are used.

    Returns:
        TrustReport with trust/confidence, subscores, drivers and actions.
    """
    cfg = cfg or TrustConfig()
    tgt = choose_target(run, target)

    # Warnings are included in the report details so UIs can surface them to users.
    warnings: List[str] = []
    if target and target not in run.steps:
        warnings.append(
            f"Requested target '{target}' was not found in provenance; using '{tgt}' instead."
        )

    # Build adjacency and ancestor subgraph for the chosen target.
    fwd, rev = build_adjacency(run)
    sub = ancestors_of(tgt, rev)

    # Compute depth values for chain amplification. We set the target as a "root" at depth=0.
    depths = compute_depths(fwd, sub, roots=[tgt])

    # -------------------------------------------------------------------------
    # Classification + missingness
    # -------------------------------------------------------------------------
    for sid in sub:
        st = run.steps.get(sid)
        if not st:
            continue

        st.depth = depths.get(sid, 0)

        # If workflow YAML is provided, we can fill missing component names.
        if (
            workflow
            and (not (st.component or "").strip())
            and st.id in (workflow.steps or {})
        ):
            wf_step = workflow.steps.get(st.id) or {}
            comp = wf_step.get("component")
            if isinstance(comp, str) and comp.strip():
                st.component = comp.strip()

        # Assign kind and compute missingness.
        st.kind = classify_step(st, workflow)
        st.missingness = compute_step_missingness(st)

    # -------------------------------------------------------------------------
    # Verification -> mitigation mapping
    # -------------------------------------------------------------------------
    # Verification steps reduce risk for specific GEN steps they validate.
    ver_steps = [
        run.steps[s] for s in sub if s in run.steps and run.steps[s].kind == "VER"
    ]
    verified: Dict[str, float] = {}  # step_id -> mitigation strength (0..1)

    for ver in ver_steps:
        if not _verification_passed(ver):
            continue
        targets = _verification_targets(ver)
        for t in targets:
            # Apply mitigation only to GEN steps (verification of DET/RET doesn't change our trust model directly).
            st = run.steps.get(t)
            if st and st.kind == "GEN":
                # Multiple verifications can validate the same step; take the strongest.
                verified[t] = max(verified.get(t, 0.0), 0.75)

    # -------------------------------------------------------------------------
    # Per-step risks + overall trust
    # -------------------------------------------------------------------------
    step_risks: List[float] = []
    gen_risks: List[float] = []
    ret_steps: Set[str] = set()
    evidence_steps: Set[str] = set()

    for sid in sub:
        st = run.steps.get(sid)
        if not st:
            continue
        mitigation = verified.get(sid, 0.0) if st.kind == "GEN" else 0.0
        st.risk = compute_step_risk(st, cfg, mitigation=mitigation)
        step_risks.append(st.risk)

        if st.kind == "GEN":
            gen_risks.append(st.risk)
        if st.kind == "RET":
            ret_steps.add(sid)
        if _evidence_step(st):
            evidence_steps.add(sid)

    overall_risk = aggregate_risk(step_risks)
    trust = 1.0 - overall_risk

    gen_ids = [sid for sid in sub if sid in run.steps and run.steps[sid].kind == "GEN"]

    # -------------------------------------------------------------------------
    # Subscores / indicators
    # -------------------------------------------------------------------------
    # Generative exposure (bad-direction): aggregated risk over GEN steps.
    ge = aggregate_risk(gen_risks) if gen_risks else 0.0

    # Verification coverage (good): fraction of GEN steps validated by any VER step.
    if gen_ids:
        vc = sum(1 for sid in gen_ids if verified.get(sid, 0.0) > 0.0) / float(
            len(gen_ids)
        )
    else:
        vc = 1.0

    # Grounding strength (good): fraction of GEN steps with at least one RET ancestor.
    def has_ret_ancestor(sid: str) -> bool:
        from collections import deque

        q = deque([sid])
        seen: Set[str] = set()
        while q:
            cur = q.popleft()
            if cur in seen:
                continue
            seen.add(cur)
            if cur in ret_steps and cur != sid:
                return True
            for p in rev.get(cur, []):
                if p in sub:
                    q.append(p)
        return False

    if gen_ids:
        gs = sum(1 for sid in gen_ids if has_ret_ancestor(sid)) / float(len(gen_ids))
    else:
        gs = 1.0

    # Evidence availability (good): fraction of GEN steps with evidence artifacts upstream.
    def has_evidence_ancestor(sid: str) -> bool:
        from collections import deque

        q = deque([sid])
        seen: Set[str] = set()
        while q:
            cur = q.popleft()
            if cur in seen:
                continue
            seen.add(cur)
            if cur in evidence_steps and cur != sid:
                return True
            for p in rev.get(cur, []):
                if p in sub:
                    q.append(p)
        return False

    if gen_ids:
        ea = sum(1 for sid in gen_ids if has_evidence_ancestor(sid)) / float(
            len(gen_ids)
        )
    else:
        ea = 1.0

    # Provenance completeness (good): 1 - average missingness across steps in subgraph.
    present_steps = [run.steps[s] for s in sub if s in run.steps]
    avg_missing = sum(st.missingness for st in present_steps) / float(
        max(1, len(present_steps))
    )
    pc = _clip(1.0 - avg_missing)

    # Deterministic robustness (good): simple proxy for deterministic reliability.
    # If the run recorded an execution error, heavily penalize. Otherwise:
    # - reward deterministic steps having runtime durations (indicates they actually ran and were logged).
    exec_error = ((run.raw or {}).get("execution_result") or {}).get("error")
    if exec_error:
        dr = 0.2
    else:
        det_ids = [
            sid for sid in sub if sid in run.steps and run.steps[sid].kind == "DET"
        ]
        if det_ids:
            timed = sum(
                1 for sid in det_ids if run.steps[sid].run.duration_s is not None
            )
            dr = timed / float(len(det_ids))
        else:
            dr = 1.0

    # External dependency (bad-direction): non-private endpoints in retrieval steps.
    endpoints: List[str] = []
    external_weights: List[float] = []
    for sid in ret_steps:
        ep = _extract_endpoint(run.steps[sid])
        if ep:
            endpoints.append(ep)
            if _endpoint_is_external(ep):
                # External but snapshotted is less risky than external unsnapshotted.
                external_weights.append(0.25 if _has_snapshot(run.steps[sid]) else 1.0)
            else:
                external_weights.append(0.0)
    ed = max(external_weights) if external_weights else 0.0

    subscores = {
        "generative_exposure": float(ge),
        "verification_coverage": float(vc),
        "grounding_strength": float(gs),
        "evidence_availability": float(ea),
        "provenance_completeness": float(pc),
        "deterministic_robustness": float(dr),
        "external_dependency": float(ed),
    }

    # Confidence (0..1): mostly provenance completeness, with additional weighting for deterministic robustness
    # and specific penalties for missing GEN token info (because it's central to risk scaling).
    gen_missing = 0.0
    if gen_ids:
        gen_missing = sum(run.steps[s].missingness for s in gen_ids) / float(
            len(gen_ids)
        )
    confidence = _clip(0.55 * pc + 0.25 * dr + 0.20 * (1.0 - gen_missing))

    # -------------------------------------------------------------------------
    # Drivers: top risky steps with factor breakdown (explainability)
    # -------------------------------------------------------------------------
    drivers: List[Dict[str, object]] = []
    top = sorted(
        (run.steps[s] for s in sub if s in run.steps),
        key=lambda st: st.risk,
        reverse=True,
    )[:10]

    for st in top:
        reason_bits: List[str] = []
        base = _base_risk(st.kind or "DET", cfg)

        # Apply the same conservative bumps as in compute_step_risk so explanations match the actual score.
        base_eff = base
        if (st.kind or "") == "GEN":
            if st.llm.input_tokens is None and st.llm.total_tokens is None:
                base_eff += cfg.bump_unknown_gen_tokens
            if not st.llm.model:
                base_eff += cfg.bump_unknown_model

        # Context factor (GEN only)
        ctx = st.llm.input_tokens if st.llm.input_tokens is not None else None
        ctx_used = ctx if ctx is not None else cfg.ctx_ref
        ctx_amp = 1.0
        if (st.kind or "") == "GEN":
            ctx_amp = 1.0 + cfg.alpha_ctx * math.log(
                1.0 + (ctx_used / float(cfg.ctx_ref))
            )

        # Chain factor (depth)
        chain_amp = 1.0 + cfg.gamma_depth * math.log(1.0 + float(max(st.depth, 0)))

        # Mitigation is per-step: only verified GEN steps are mitigated.
        mitigation = verified.get(st.id, 0.0) if (st.kind or "") == "GEN" else 0.0

        # Human-readable explanation snippet.
        if st.kind == "GEN":
            reason_bits.append(f"GEN step (input_tokens={ctx_used}, depth={st.depth})")
            if not st.llm.model:
                reason_bits.append("model id missing")
        if st.kind == "RET":
            ep = _extract_endpoint(st)
            if ep:
                snap = " (snapshotted)" if _has_snapshot(st) else ""
                reason_bits.append(f"retrieval source={ep}{snap}")
            else:
                reason_bits.append("retrieval with unknown endpoint")
        if st.missingness > 0.4:
            reason_bits.append(f"missingness={st.missingness:.2f}")

        drivers.append(
            {
                "step_id": st.id,
                "kind": st.kind,
                "component": st.component,
                "risk": round(st.risk, 4),
                "depth": st.depth,
                "missingness": round(st.missingness, 4),
                "llm": (
                    {
                        "model": st.llm.model,
                        "input_tokens": st.llm.input_tokens,
                        "output_tokens": st.llm.output_tokens,
                        "total_tokens": st.llm.total_tokens,
                    }
                    if st.kind == "GEN"
                    else None
                ),
                "risk_factors": {
                    "base_risk": round(base, 6),
                    "base_risk_effective": round(base_eff, 6),
                    "ctx_tokens_used": int(ctx_used) if st.kind == "GEN" else None,
                    "ctx_amplifier": round(ctx_amp, 6),
                    "chain_amplifier": round(chain_amp, 6),
                    "mitigation": round(mitigation, 4),
                },
                "reason": "; ".join(reason_bits) if reason_bits else "baseline risk",
            }
        )

    # -------------------------------------------------------------------------
    # Actions: map weak subscores to recommended mitigations
    # -------------------------------------------------------------------------
    actions: List[str] = []
    if ge >= 0.35:
        actions.append(
            "Reduce generative exposure: chunk inputs, constrain outputs (JSON schema), "
            "and avoid LLM-on-LLM stacking by feeding key raw tables/stats to synthesis steps."
        )
    if vc < 0.5 and gen_ids:
        actions.append(
            "Add verification: implement a deterministic claim-checker (recompute key stats from tables) "
            "and attach pass/fail provenance edges to narrative steps."
        )
    if gs < 0.6 and gen_ids:
        actions.append(
            "Improve grounding: ensure each narrative step has retrieval/evidence ancestors (tables/queries) "
            "and include explicit evidence pointers (table/row/metric IDs) in the report."
        )
    if pc < 0.7:
        actions.append(
            "Improve instrumentation: log model params (temperature/top_p), context window, stable IDs, "
            "and complete dependency edges to raise confidence in the Trust Index."
        )
    if ed >= 0.5:
        actions.append(
            "Harden external dependencies: snapshot/version data sources (endpoint + dataset hash) "
            "and log retrieval parameters (query, time) for reproducibility."
        )
    if not actions:
        actions.append(
            "No urgent actions: perform normal spot-checks on a few key claims against the underlying tables."
        )

    # -------------------------------------------------------------------------
    # Banding + summary
    # -------------------------------------------------------------------------
    trust_index = int(round(100 * trust))
    conf_index = int(round(100 * confidence))
    if trust_index >= 80 and conf_index >= 70:
        band = "green"
    elif trust_index < 50 or conf_index < 40:
        band = "red"
    else:
        band = "amber"

    verified_gen_count = sum(1 for sid in gen_ids if verified.get(sid, 0.0) > 0.0)
    external_unsnap = sum(
        1
        for sid in ret_steps
        if (
            _extract_endpoint(run.steps[sid])
            and _endpoint_is_external(_extract_endpoint(run.steps[sid]))  # type: ignore[arg-type]
            and not _has_snapshot(run.steps[sid])
        )
    )
    summary = (
        f"Trust {trust_index}/100 ({band.upper()}), Confidence {conf_index}/100. "
        f"GEN={len(gen_ids)} (verified {verified_gen_count}), RET={len(ret_steps)} (external-unsnap {external_unsnap}), "
        f"verification_coverage={vc:.2f}."
    )

    # Package the final report.
    return TrustReport(
        target=tgt,
        trust_index=trust_index,
        band=band,
        confidence=conf_index,
        subscores={k: round(v, 4) for k, v in subscores.items()},
        drivers=drivers,
        actions=actions,
        summary=summary,
        details={
            "num_steps": len(sub),
            "num_generative_steps": len(gen_ids),
            "num_retrieval_steps": len(ret_steps),
            "num_verification_steps": len(ver_steps),
            "num_human_steps": sum(
                1 for sid in sub if sid in run.steps and run.steps[sid].kind == "HUM"
            ),
            "num_evidence_steps": len(evidence_steps),
            "num_verified_generative_steps": verified_gen_count,
            "num_external_unsnapshotted_retrieval_steps": external_unsnap,
            "endpoints": endpoints,
            "warnings": warnings,
            # Record the key config values used to compute the score for auditability.
            "config": {
                "base_risk_gen": cfg.base_risk_gen,
                "base_risk_ret": cfg.base_risk_ret,
                "base_risk_det": cfg.base_risk_det,
                "alpha_ctx": cfg.alpha_ctx,
                "ctx_ref": cfg.ctx_ref,
                "gamma_depth": cfg.gamma_depth,
            },
            # Quick reference for domain experts reading the report.
            "subscore_guide": {
                "generative_exposure": "0..1 (higher = more exposure / higher risk). Reduce by limiting context, avoiding LLM-on-LLM stacking, and constraining outputs.",
                "verification_coverage": "0..1 (higher = better). Increase by adding deterministic checkers (schema checks, recompute key stats, pass/fail assertions) linked in provenance.",
                "grounding_strength": "0..1 (higher = better). Increase by ensuring narrative steps depend on retrieval/evidence artifacts and include evidence pointers.",
                "evidence_availability": "0..1 (higher = better). Increase by persisting tables/charts used by narratives and linking them as inputs.",
                "provenance_completeness": "0..1 (higher = better). Increase by logging stable IDs, dependencies, token usage, and run timestamps.",
                "deterministic_robustness": "0..1 (higher = better). Increase by adding validation and error handling around deterministic transforms.",
                "external_dependency": "0..1 (higher = more external dependency / higher risk). Mitigate by snapshotting data sources and logging dataset/version hashes.",
            },
        },
    )
