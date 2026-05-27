# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from lunarflow.flows import Flow
from .parsers import ExecutionLog, flow_start_event, index_events
from .prov_dataset import PROV
from rdflib import Dataset, RDFS, URIRef

from .prov_io import infer_base_and_run_id
from .utils import find_flow_input_refs, find_step_refs, safe_id


def _iso(dt: Any) -> str:
    """Return a stable ISO string (pass-through if already a string)."""
    if dt is None:
        return ""
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _summarize_value(v: Any, limit: int = 180) -> str:
    """Human-friendly compact summary of a potentially large JSON value."""
    if v is None:
        return "(null)"
    if isinstance(v, (int, float, bool)):
        return str(v)
    if isinstance(v, str):
        s = v.replace("\n", " ").strip()
        return (s[:limit] + "…") if len(s) > limit else s
    if isinstance(v, dict):
        keys = list(v.keys())
        head = ", ".join(keys[:6])
        more = "…" if len(keys) > 6 else ""
        return f"dict({len(keys)} keys: {head}{more})"
    if isinstance(v, list):
        return f"list({len(v)})"
    s = str(v)
    return (s[:limit] + "…") if len(s) > limit else s


def _extract_path(obj: Any, path: Optional[str]) -> Any:
    """Best-effort extraction of a dotted path from a dict/list structure."""
    if not path:
        return obj
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                idx = int(part)
                cur = cur[idx]
            except Exception:
                return None
        else:
            return None
    return cur


def build_view_model(
    workflow: Flow,
    log: ExecutionLog,
    base_uri: str,
    embed_values: bool = True,
) -> Dict[str, Any]:
    """Build a lightweight JSON model for an interactive HTML drill-down view.

    The model is derived from the same YAML+log inputs used for PROV-O export,
    but is optimized for human navigation (steps, dependencies, inputs/outputs).
    """
    base = base_uri.rstrip("/")
    flow_id = workflow.get_id()
    run_id = safe_id(f"{flow_id}-{log.started_at}")

    ev_flow = flow_start_event(log.event_log) or {}
    flow_inputs = (
        ((ev_flow.get("payload") or {}).get("inputs") or {})
        if isinstance(ev_flow, dict)
        else {}
    )
    step_events = index_events(log.event_log)

    # Convert workflow nodes to steps dict
    flow_dict = json.loads(workflow.to_json())
    workflow_steps = {}
    for node in flow_dict.get("nodes", []):
        node_id = node.get("id", "")
        workflow_steps[node_id] = node

    # Step outputs (retrospective values)
    step_outputs: Dict[str, Any] = {}

    # First, try to extract from log.result_value (contains all step results)
    if log.result_value and isinstance(log.result_value, dict):
        for step_id, step_result in log.result_value.items():
            if step_id in workflow_steps:
                # Handle both direct values and wrapped {"value": ...} format
                if isinstance(step_result, dict) and "value" in step_result:
                    step_outputs[step_id] = step_result.get("value")
                else:
                    step_outputs[step_id] = step_result

    # Then, supplement/override with step:result events if present
    for step_id, evs in step_events.items():
        res = evs.get("step:result")
        if res:
            payload = res.get("payload") or {}
            if isinstance(payload, dict) and "value" in payload:
                step_outputs[step_id] = payload.get("value")

    # Dependencies from $step refs + which input introduces the dependency
    edges: List[Dict[str, Any]] = []
    depends: Dict[str, List[str]] = {sid: [] for sid in workflow_steps.keys()}
    for step_id, spec in workflow_steps.items():
        inputs = (spec.get("inputs") or {}) if isinstance(spec, dict) else {}
        if not isinstance(inputs, dict):
            continue
        for in_key, in_val in inputs.items():
            for ref_step, field in find_step_refs(in_val):
                if ref_step in workflow_steps:
                    edges.append(
                        {
                            "type": "dependsOn",
                            "from_step": ref_step,
                            "to_step": step_id,
                            "via": in_key,
                            "field": field or "",
                        }
                    )
                    depends.setdefault(step_id, []).append(ref_step)

    # Flow-input references per step (for provenance “data sources”)
    flow_refs_per_step: Dict[str, List[str]] = {
        sid: [] for sid in workflow_steps.keys()
    }
    for step_id, spec in workflow_steps.items():
        inputs = (spec.get("inputs") or {}) if isinstance(spec, dict) else {}
        if not isinstance(inputs, dict):
            continue
        refs: List[str] = []
        for _, in_val in inputs.items():
            refs.extend(list(find_flow_input_refs(in_val)))
        flow_refs_per_step[step_id] = sorted(set([r for r in refs if r]))

    # Step run times + status
    def _ts(e: Optional[Dict[str, Any]]) -> str:
        return _iso(e.get("timestamp")) if e else ""

    steps: List[Dict[str, Any]] = []
    for step_id, spec in workflow_steps.items():
        evs = step_events.get(step_id, {})
        st = _ts(evs.get("step:started"))
        en = _ts(evs.get("step:finished"))
        duration_s: Optional[float] = None
        if st and en:
            try:
                # datetime.fromisoformat handles offsets too.
                ds = datetime.fromisoformat(st.replace("Z", "+00:00"))
                de = datetime.fromisoformat(en.replace("Z", "+00:00"))
                duration_s = (de - ds).total_seconds()
            except Exception:
                duration_s = None

        out_val = step_outputs.get(step_id)
        out_summary = _summarize_value(out_val)

        # Check if this is an LLM step and extract metadata
        is_llm_step = isinstance(spec, dict) and spec.get("kind") == "llm"
        llm_metadata: Optional[Dict[str, Any]] = None

        if is_llm_step:
            # Try to extract LLM metadata from step:finished event
            finished_evt = evs.get("step:finished")
            if finished_evt:
                payload = finished_evt.get("payload") or {}
                if isinstance(payload, dict):
                    result_data = payload.get("result") or {}
                    if isinstance(result_data, dict):
                        value_data = result_data.get("value") or {}
                        if isinstance(value_data, dict):
                            model = value_data.get("model")
                            usage = value_data.get("usage") or {}
                            if isinstance(usage, dict) or model:
                                llm_metadata = {
                                    "model": model,
                                    "input_tokens": (
                                        usage.get("input")
                                        if isinstance(usage, dict)
                                        else None
                                    ),
                                    "output_tokens": (
                                        usage.get("output")
                                        if isinstance(usage, dict)
                                        else None
                                    ),
                                    "total_tokens": (
                                        usage.get("total")
                                        if isinstance(usage, dict)
                                        else None
                                    ),
                                }

        # Resolve each input into a small “binding” object for drill-down.
        bindings: List[Dict[str, Any]] = []
        inputs = (spec.get("inputs") or {}) if isinstance(spec, dict) else {}
        if isinstance(inputs, dict):
            for in_key, in_val in inputs.items():
                b: Dict[str, Any] = {"name": in_key, "raw": in_val}
                if isinstance(in_val, str):
                    # Step output reference: $step.field
                    for ref_step, field in find_step_refs(in_val):
                        if ref_step in workflow_steps:
                            b.update(
                                {
                                    "kind": "step_output",
                                    "ref": ref_step,
                                    "field": field or "",
                                }
                            )
                            if embed_values:
                                ref_val = step_outputs.get(ref_step)
                                b["value"] = _extract_path(ref_val, field)
                                b["value_summary"] = _summarize_value(b.get("value"))
                            break
                    # Flow input reference: &var
                    for var in find_flow_input_refs(in_val):
                        if var:
                            b.update({"kind": "flow_input", "ref": var})
                            if embed_values:
                                b["value"] = flow_inputs.get(var)
                                b["value_summary"] = _summarize_value(b.get("value"))
                            break
                # Literal or non-recognized
                b.setdefault("kind", "literal")
                if embed_values and b["kind"] == "literal":
                    b["value"] = in_val
                    b["value_summary"] = _summarize_value(in_val)
                bindings.append(b)

        steps.append(
            {
                "id": step_id,
                "component": (spec.get("component") if isinstance(spec, dict) else "")
                or "",
                "plan": spec if isinstance(spec, dict) else {},
                "depends_on": sorted(set(depends.get(step_id, []))),
                "flow_inputs_used": flow_refs_per_step.get(step_id, []),
                "run": {
                    "started_at": st,
                    "ended_at": en,
                    "duration_s": duration_s,
                },
                "inputs": bindings,
                "output": {
                    "value": out_val if embed_values else None,
                    "summary": out_summary,
                },
                "generative": is_llm_step,
                "llm_metadata": llm_metadata,
                "uri": f"{base}/run/{run_id}/activity/step/{safe_id(step_id)}",
            }
        )

    # Recent outputs (most recent finished steps)
    def _ended_at(s: Dict[str, Any]) -> str:
        return (s.get("run") or {}).get("ended_at") or ""

    def _ended_dt(s: Dict[str, Any]) -> float:
        t = _ended_at(s)
        if not t:
            return -1.0
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        except Exception:
            return -1.0

    steps_sorted = sorted(steps, key=_ended_dt, reverse=True)
    recent_outputs = [
        {
            "step": s["id"],
            "ended_at": _ended_at(s),
            "summary": (s.get("output") or {}).get("summary", ""),
        }
        for s in steps_sorted
        if _ended_at(s)
    ]

    # Original data sources (flow inputs), keep order stable.
    data_sources = []
    if isinstance(flow_inputs, dict):
        for k in sorted(flow_inputs.keys()):
            v = flow_inputs.get(k)
            is_external = isinstance(v, str) and (
                v.startswith("http://")
                or v.startswith("https://")
                or v.startswith("file:")
                or v.startswith("/")
                or "/" in v
            )
            data_sources.append(
                {
                    "id": k,
                    "uri": f"{base}/run/{run_id}/entity/input/{safe_id(k)}",
                    "value": v if embed_values else None,
                    "summary": _summarize_value(v),
                    "is_external": bool(is_external),
                }
            )

    model = {
        "base_uri": base_uri,
        "run_id": run_id,
        "workflow": {
            "id": workflow.get_id(),
            "name": workflow.get_name(),
            "description": workflow.get_description(),
            "status": log.status,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "uri": f"{base}/plan/workflow/{safe_id(workflow.get_id())}",
        },
        "data_sources": data_sources,
        "steps": steps,
        "edges": edges,
        "recent_outputs": recent_outputs,
    }
    return model


def build_view_model_from_dataset(
    ds: Dataset, base_uri: Optional[str] = None, embed_values: bool = True
) -> Dict[str, Any]:
    """Build the same HTML view model directly from a PROV Dataset.

    This is used when you *append manual edits* to an existing provenance file
    (TriG/JSON-LD) and you want to regenerate the HTML explorer without having
    the original Lunar YAML+log handy.

    The output schema matches build_view_model(...), but some fields (e.g. exact
    per-input binding reconstruction) are best-effort.
    """
    from rdflib import RDF

    inferred_base, inferred_run = infer_base_and_run_id(ds)
    base_uri = (base_uri or inferred_base).rstrip("/")
    run_id = inferred_run

    # Locate main bundles (best-effort)
    g_pro = None
    g_ret = None
    for ctx in ds.contexts():
        iri = str(ctx.identifier)
        if iri.endswith("/bundle/prospective"):
            g_pro = ctx
        if "/bundle/retrospective/" in iri:
            g_ret = ctx
    if g_ret is None:
        g_ret = ds.default_context

    def _label(g, node) -> str:
        for _, _, o in g.triples((node, RDFS.label, None)):
            return str(o)
        return str(node)

    def _time(node, prop) -> str:
        for _, _, o in g_ret.triples((node, prop, None)):
            return str(o)
        return ""

    # Workflow metadata from prospective bundle
    flow_id = ""
    wf_name = ""
    wf_desc = ""
    if g_pro is not None:
        for s, _, _ in g_pro.triples((None, RDF.type, PROV.Plan)):
            if "/plan/workflow/" in str(s):
                wf_name = _label(g_pro, s)
                flow_id = wf_name
                for _, _, c in g_pro.triples((s, URIRef(str(RDFS) + "comment"), None)):
                    wf_desc = str(c)
                break

    # Activities in retrospective graph
    activities = sorted(
        set([s for s, _, _ in g_ret.triples((None, RDF.type, PROV.Activity))]),
        key=str,  # type: ignore[arg-type]
    )

    # Identify flow activity
    flow_act = None
    for a in activities:
        lab = _label(g_ret, a)
        if lab.startswith("flow:") or str(a).endswith("/activity/flow"):
            flow_act = a
            break

    # Data sources = entities used by flow activity
    data_sources: List[Dict[str, Any]] = []
    if flow_act is not None:
        for _, _, ent in g_ret.triples((flow_act, PROV.used, None)):
            lab = _label(g_ret, ent)
            if not lab.startswith("input:"):
                continue
            key = lab.split("input:", 1)[1]
            val: Any = None
            if embed_values:
                for _, _, vv in g_ret.triples((ent, PROV.value, None)):
                    val = str(vv)
                    break
            is_external = isinstance(val, str) and (
                val.startswith("http://")
                or val.startswith("https://")
                or val.startswith("file:")
                or val.startswith("/")
                or "/" in val
            )
            data_sources.append(
                {
                    "id": key,
                    "uri": str(ent),
                    "value": val if embed_values else None,
                    "summary": _summarize_value(val),
                    "is_external": bool(is_external),
                }
            )

    # Map activity -> generated entities
    gen_by: Dict[str, List[URIRef]] = {}
    for ent, _, act in g_ret.triples((None, PROV.wasGeneratedBy, None)):
        gen_by.setdefault(str(act), []).append(ent)  # type: ignore[arg-type]

    # Dependencies: infer from prospective plan dependsOn links
    edges: List[Dict[str, Any]] = []
    if g_pro is not None:
        dependsOn = URIRef(str(base_uri.rstrip("/") + "/") + "dependsOn")
        for sp, _, dep in g_pro.triples((None, dependsOn, None)):
            sid = _label(g_pro, sp)
            did = _label(g_pro, dep)
            edges.append(
                {
                    "type": "dependsOn",
                    "from": did,
                    "to": sid,
                    "via": "plan:dependsOn",
                    "field": "",
                }
            )

    def _activity_id(a: URIRef) -> str:
        lab = _label(g_ret, a)
        if lab.startswith("step:"):
            return lab.split("step:", 1)[1]
        if lab.startswith("manual_edit:"):
            return lab  # keep unique ids
        return lab

    # Plan JSON lookups
    plan_by_stepid: Dict[str, Any] = {}
    if g_pro is not None:
        import json as _json

        for sp, _, val in g_pro.triples((None, PROV.value, None)):
            if "/plan/step/" not in str(sp):
                continue
            sid = _label(g_pro, sp)
            try:
                plan_by_stepid[sid] = _json.loads(str(val))
            except Exception:
                continue

    # Steps list (including manual edits)
    steps: List[Dict[str, Any]] = []
    extra_edges: List[Dict[str, Any]] = []
    for a in activities:
        if flow_act is not None and str(a) == str(flow_act):
            continue
        sid = _activity_id(a)  # type: ignore[arg-type]
        started = _time(a, PROV.startedAtTime)
        ended = _time(a, PROV.endedAtTime)

        bindings: List[Dict[str, Any]] = []
        for _, _, ent in g_ret.triples((a, PROV.used, None)):
            elab = _label(g_ret, ent)
            b: Dict[str, Any] = {"name": elab, "raw": str(ent)}
            if elab.startswith("input:"):
                b.update({"kind": "flow_input", "ref": elab.split("input:", 1)[1]})
            elif elab.startswith("output:"):
                b.update(
                    {
                        "kind": "step_output",
                        "ref": elab.split("output:", 1)[1],
                        "field": "",
                    }
                )
            elif elab.startswith("report:"):
                b.update({"kind": "report_version", "ref": elab})
            elif elab.startswith("diff:"):
                b.update({"kind": "diff", "ref": elab})
            else:
                b.update({"kind": "entity", "ref": elab})
            if embed_values:
                for _, _, vv in g_ret.triples((ent, PROV.value, None)):
                    b["value"] = str(vv)
                    b["value_summary"] = _summarize_value(b.get("value"))
                    break
            bindings.append(b)

            # If this is a manual edit activity, infer a step-level dependency
            # from the activity that originally generated the used entity.
            if str(sid).startswith("manual_edit:"):
                for _, _, gen_act in g_ret.triples((ent, PROV.wasGeneratedBy, None)):
                    extra_edges.append(
                        {
                            "type": "dependsOn",
                            "from": _activity_id(gen_act),  # type: ignore[arg-type]
                            "to": sid,
                            "via": "used<-wasGeneratedBy",
                            "field": "",
                        }
                    )

        # Output: choose best candidate among generated entities
        out_val: Any = None
        out_sum = ""
        outs = gen_by.get(str(a), [])
        if outs:

            def _score(ent: URIRef) -> int:
                label = _label(g_ret, ent)
                if label.startswith("output:"):
                    return 4
                if label.startswith("report:"):
                    return 3
                if label.startswith("diff:"):
                    return 1
                return 0

            primary = sorted(outs, key=_score, reverse=True)[0]
            if embed_values:
                for _, _, vv in g_ret.triples((primary, PROV.value, None)):
                    out_val = str(vv)
                    break
            out_sum = _summarize_value(out_val)

        steps.append(
            {
                "id": sid,
                "component": (
                    "manual_edit" if str(sid).startswith("manual_edit:") else ""
                ),
                "plan": plan_by_stepid.get(sid, {}),
                "depends_on": [],
                "flow_inputs_used": [],
                "run": {"started_at": started, "ended_at": ended, "duration_s": None},
                "inputs": bindings,
                "output": {
                    "value": out_val if embed_values else None,
                    "summary": out_sum,
                },
                "uri": str(a),
            }
        )

    # Recent outputs by ended time
    def _ended_dt(s: Dict[str, Any]) -> float:
        t = (s.get("run") or {}).get("ended_at") or ""
        if not t:
            return -1.0
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        except Exception:
            return -1.0

    steps_sorted = sorted(steps, key=_ended_dt, reverse=True)
    recent_outputs = [
        {
            "step": s["id"],
            "ended_at": (s.get("run") or {}).get("ended_at") or "",
            "summary": (s.get("output") or {}).get("summary") or "",
        }
        for s in steps_sorted
        if (s.get("run") or {}).get("ended_at")
    ]

    # Merge extra edges (dedupe)
    seen = set()
    for e in extra_edges:
        key = (e["type"], e["from"], e["to"], e.get("via", ""))
        if key in seen:
            continue
        seen.add(key)
        edges.append(e)

    return {
        "base_uri": base_uri,
        "run_id": run_id,
        "workflow": {
            "id": flow_id or wf_name or "",
            "name": wf_name or flow_id or "",
            "description": wf_desc,
            "status": "",
            "started_at": "",
            "completed_at": "",
            "uri": f"{base_uri}/plan/workflow/{safe_id(flow_id or wf_name or 'workflow')}",
        },
        "data_sources": data_sources,
        "steps": steps,
        "edges": edges,
        "recent_outputs": recent_outputs,
    }


def render_html_from_dataset(
    ds: Dataset, base_uri: Optional[str] = None, embed_values: bool = True
) -> str:
    vm = build_view_model_from_dataset(ds, base_uri=base_uri, embed_values=embed_values)
    return render_html(vm)


def render_html(model: Dict[str, Any]) -> str:
    """Render a single-file HTML+JS drill-down provenance explorer.

    The explorer supports two visual modes:
      - Steps: a DAG of workflow steps (activities), inferred from $step references.
      - Entities: a PROV-style bipartite graph (Entity ↔ Activity) with prov:used and prov:wasGeneratedBy-like edges.
    """
    payload = json.dumps(model, ensure_ascii=False)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Lunar Provenance Explorer</title>
  <style>
    :root {{
      --bg: #0b0d12;
      --panel: #121624;
      --panel2: #0f1320;
      --text: #e7e9ee;
      --muted: #aab1c3;
      --line: #2a3146;
      --accent: #7aa2ff;
      --good: #3ddc97;
      --warn: #ffcc66;
    }}
    html, body {{ height: 100%; margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; background: var(--bg); color: var(--text); }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{ padding: 14px 18px; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; align-items: baseline; }}
    header h1 {{ font-size: 16px; margin: 0; letter-spacing: 0.4px; }}
    header .meta {{ font-size: 12px; color: var(--muted); }}
    .layout {{ height: calc(100% - 52px); display: grid; grid-template-columns: 340px 1fr 420px; }}
    .panel {{ border-right: 1px solid var(--line); overflow: auto; background: var(--panel); }}
    .panel.right {{ border-right: none; border-left: 1px solid var(--line); background: var(--panel2); }}
    .center {{ overflow: hidden; position: relative; }}
    .section {{ padding: 14px 14px 6px 14px; }}
    .section h2 {{ font-size: 12px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }}
    .card {{ border: 1px solid var(--line); border-radius: 14px; padding: 10px; background: rgba(255,255,255,0.02); }}
    .small {{ font-size: 12px; color: var(--muted); line-height: 1.35; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{ padding: 8px 10px; border: 1px solid var(--line); border-radius: 12px; margin: 8px 0; background: rgba(255,255,255,0.02); cursor: pointer; }}
    li:hover {{ border-color: rgba(122,162,255,0.6); }}
    li.active {{ border-color: var(--accent); box-shadow: 0 0 0 1px rgba(122,162,255,0.25) inset; }}
    .pill {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); margin-left: 6px; }}
    .pill.good {{ border-color: rgba(61,220,151,0.5); color: var(--good); }}
    .pill.warn {{ border-color: rgba(255,204,102,0.5); color: var(--warn); }}
    .search {{ width: 100%; box-sizing: border-box; background: transparent; color: var(--text); border: 1px solid var(--line); border-radius: 12px; padding: 8px 10px; outline: none; }}
    .search:focus {{ border-color: rgba(122,162,255,0.7); }}
    .kvs {{ display: grid; grid-template-columns: 120px 1fr; gap: 6px 10px; }}
    .kvs .k {{ font-size: 12px; color: var(--muted); }}
    .kvs .v {{ font-size: 12px; color: var(--text); word-break: break-word; }}
    .details pre {{ white-space: pre-wrap; word-break: break-word; font-size: 12px; line-height: 1.35; margin: 8px 0 0 0; color: var(--text); }}
    details {{ border: 1px solid var(--line); border-radius: 12px; padding: 8px 10px; margin-top: 8px; }}
    summary {{ cursor: pointer; font-size: 12px; color: var(--muted); }}
    .kvtable {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    .kvtable th, .kvtable td {{ border-bottom: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }}
    .kvtable th {{ color: var(--muted); font-weight: 600; }}
    .vlist {{ margin: 6px 0 0 0; padding: 0 0 0 16px; }}
    .vlist li {{ border: none; margin: 0; padding: 2px 0; background: none; cursor: default; }}
    .badge {{ display: inline-block; font-size: 11px; padding: 2px 6px; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); margin-left: 6px; }}
    #graphWrap {{ position: absolute; inset: 0; }}
    #graph {{ width: 100%; height: 100%; cursor: grab; }}
    #graph.dragging {{ cursor: grabbing; }}
    .legend {{ position: absolute; right: 12px; top: 12px; background: rgba(0,0,0,0.35); border: 1px solid var(--line); border-radius: 14px; padding: 10px 12px; font-size: 12px; color: var(--muted); max-width: 520px; }}
    .legend b {{ color: var(--text); }}
    .btnrow {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    button {{ background: rgba(255,255,255,0.03); color: var(--text); border: 1px solid var(--line); border-radius: 12px; padding: 7px 10px; cursor: pointer; font-size: 12px; }}
    button:hover {{ border-color: rgba(122,162,255,0.7); }}
    button.active {{ border-color: rgba(122,162,255,0.95); box-shadow: 0 0 0 1px rgba(122,162,255,0.25) inset; }}
    .muted {{ color: var(--muted); }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\"; }}
  </style>
</head>
<body>
  <header>
    <h1 id=\"title\">Lunar Provenance Explorer</h1>
    <div class=\"meta\" id=\"meta\"></div>
  </header>

  <div class=\"layout\">
    <aside class=\"panel\" id=\"left\"></aside>
    <main class=\"center\">
      <div id=\"graphWrap\">
        <svg id=\"graph\" viewBox=\"0 0 1200 800\" preserveAspectRatio=\"xMinYMin meet\"></svg>
        <div class=\"legend\">
          <div class=\"btnrow\" style=\"justify-content:space-between\">
            <div><b>Click</b> a node to drill down.</div>
            <div class=\"btnrow\">
              <button id=\"mode-steps\" class=\"active\">Steps</button>
              <button id=\"mode-entities\">Entities</button>
              <button id=\"toggle-trace\" class=\"active\">Trace only</button>
            </div>
          </div>
          <div class=\"muted\" style=\"margin-top:6px\">
            Default view traces from the most recent output back to original sources.
          </div>
        </div>
      </div>
    </main>
    <aside class=\"panel right\" id=\"right\"></aside>
  </div>

  <script id=\"prov-data\" type=\"application/json\">{payload}</script>
  <script>
  (function() {{
    const data = JSON.parse(document.getElementById('prov-data').textContent);
    const wf = data.workflow;
    const steps = data.steps || [];
    const edges = data.edges || [];

    const base = String(data.base_uri || 'http://lunarbase.ai/prov').replace(/\\/+$/,'');
    const runId = data.run_id || 'run';

    document.getElementById('title').textContent = wf && wf.name ? `Lunar Provenance Explorer · ${{wf.name}}` : 'Lunar Provenance Explorer';
    document.getElementById('meta').textContent = `flow: ${{wf.id || ''}} · run: ${{runId}} · base: ${{base}}`;

    // ---- Utilities ----
    function escapeHTML(s) {{
      return String(s)
        .replaceAll('&','&amp;')
        .replaceAll('<','&lt;')
        .replaceAll('>','&gt;')
        .replaceAll('"','&quot;')
        .replaceAll("'",'&#39;');
    }}
    function cssEscape(s) {{
      return String(s).replaceAll('\\\\','\\\\\\\\').replaceAll('"','\\\\\"');
    }}
    function safeId(text) {{
      let t = String(text || '').trim();
      t = t.replace(/\\s+/g, '_');
      t = t.replace(/[^A-Za-z0-9._~-]/g, '-');
      return t || 'id';
    }}
    const measureTextWidth = (() => {{
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const font = 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
      return (text, size) => {{
        ctx.font = `${{size}}px ${{font}}`;
        return ctx.measureText(String(text || '')).width;
      }};
    }})();
    const view = {{
      baseW: null,
      baseH: null,
      x: 0,
      y: 0,
      w: 0,
      h: 0
    }};
    function setBaseViewBox(width, height) {{
      const svg = document.getElementById('graph');
      if (!view.baseW || view.baseW !== width || view.baseH !== height) {{
        view.baseW = width;
        view.baseH = height;
        view.x = 0;
        view.y = 0;
        view.w = width;
        view.h = height;
      }}
      svg.setAttribute('viewBox', `${{view.x}} ${{view.y}} ${{view.w}} ${{view.h}}`);
    }}
    function applyViewBox() {{
      const svg = document.getElementById('graph');
      svg.setAttribute('viewBox', `${{view.x}} ${{view.y}} ${{view.w}} ${{view.h}}`);
    }}
    function offsetFor(kind, id) {{
      const map = kind === 'steps' ? state.dragOffsetsSteps : state.dragOffsetsEntities;
      const o = map[id];
      return o ? {{x: o.x, y: o.y}} : {{x: 0, y: 0}};
    }}
    function setOffset(kind, id, x, y) {{
      const map = kind === 'steps' ? state.dragOffsetsSteps : state.dragOffsetsEntities;
      map[id] = {{x, y}};
    }}
    let nodeDrag = null;
    function startNodeDrag(kind, id, clientX, clientY) {{
      const off = offsetFor(kind, id);
      nodeDrag = {{
        kind,
        id,
        startX: clientX,
        startY: clientY,
        startOffX: off.x,
        startOffY: off.y,
        moved: false
      }};
    }}
    function outputUri(stepId) {{
      return `${{base}}/run/${{runId}}/entity/output/${{safeId(stepId)}}`;
    }}
    function literalUri(stepId, name) {{
      return `${{base}}/run/${{runId}}/entity/literal/${{safeId(stepId)}}.${{safeId(name)}}`;
    }}

    // ---- Index helpers ----
    const stepById = Object.fromEntries(steps.map(s => [s.id, s]));
    const depsTo = {{}};
    const outsFrom = {{}};
    steps.forEach(s => {{ depsTo[s.id] = (s.depends_on || []).slice(); outsFrom[s.id] = []; }});
    edges.filter(e => e.type === 'dependsOn').forEach(e => {{
      if (outsFrom[e.from]) outsFrom[e.from].push(e.to);
    }});

    // Most recent output step (by ended_at)
    const recent = (data.recent_outputs || []).slice();
    const defaultOutput = recent.length ? recent[0].step : (steps.length ? steps[steps.length-1].id : null);

    function ancestorsOf(stepId) {{
      const seen = new Set();
      const stack = [stepId];
      while (stack.length) {{
        const cur = stack.pop();
        if (!cur || seen.has(cur)) continue;
        seen.add(cur);
        (depsTo[cur] || []).forEach(d => stack.push(d));
      }}
      return seen;
    }}

    // ---- Left panel ----
    function renderLeft(selectedStep, selectedOutput) {{
      const left = document.getElementById('left');
      left.innerHTML = '';

      const sec1 = document.createElement('div');
      sec1.className = 'section';
      sec1.innerHTML = `
        <h2>Workflow</h2>
        <div class="card">
          <div style="font-size:14px"><b>${{escapeHTML(wf.name || wf.id || '')}}</b></div>
          <div class="small" style="margin-top:6px">${{escapeHTML(wf.description || '')}}</div>
          <div class="small" style="margin-top:8px"><span class="pill">${{escapeHTML(wf.status || '')}}</span></div>
        </div>
      `;
      left.appendChild(sec1);

      // Data sources first (as requested)
      const secSources = document.createElement('div');
      secSources.className = 'section';
      secSources.innerHTML = `<h2>Original data sources</h2>`;
      const srcList = document.createElement('ul');
      (data.data_sources || []).forEach(src => {{
        const li = document.createElement('li');
        li.setAttribute('data-src-li', src.id);
        li.innerHTML = `<div><b>&amp;${{escapeHTML(src.id)}}</b> ${{src.is_external ? '<span class="pill warn">external-like</span>' : '<span class="pill">input</span>'}}</div>
                        <div class="small">${{escapeHTML(src.summary || '')}}</div>`;
        li.onclick = () => selectSource(src.id);
        srcList.appendChild(li);
      }});
      if (!(data.data_sources || []).length) {{
        const empty = document.createElement('div');
        empty.className = 'small muted';
        empty.textContent = '(none found in flow start inputs)';
        secSources.appendChild(empty);
      }} else {{
        secSources.appendChild(srcList);
      }}
      left.appendChild(secSources);

      // Recent outputs
      const sec2 = document.createElement('div');
      sec2.className = 'section';
      sec2.innerHTML = `<h2>Most recent outputs</h2>`;
      const ul2 = document.createElement('ul');
      (data.recent_outputs || []).slice(0, 12).forEach(o => {{
        const li = document.createElement('li');
        li.setAttribute('data-out-li', o.step);
        if (o.step === selectedOutput) li.classList.add('active');
        li.innerHTML = `<div><b>${{escapeHTML(o.step)}}</b><span class="pill good">output</span></div>
                        <div class="small">${{escapeHTML(o.summary || '')}}</div>`;
        li.onclick = () => selectOutput(o.step);
        ul2.appendChild(li);
      }});
      if (!(data.recent_outputs || []).length) {{
        const empty = document.createElement('div');
        empty.className = 'small muted';
        empty.textContent = '(no finished steps recorded)';
        sec2.appendChild(empty);
      }} else {{
        sec2.appendChild(ul2);
      }}
      left.appendChild(sec2);

      // Step search + list
      const sec3 = document.createElement('div');
      sec3.className = 'section';
      sec3.innerHTML = `
        <h2>Steps</h2>
        <input class="search" id="stepSearch" placeholder="Search steps…" />
        <div class="small muted" style="margin-top:8px">Click a step to inspect plan, runtime, inputs, and outputs.</div>
      `;
      const ul3 = document.createElement('ul');
      steps.forEach(s => {{
        const li = document.createElement('li');
        li.setAttribute('data-step-li', s.id);
        if (s.id === selectedStep) li.classList.add('active');
        const done = s.run && s.run.ended_at;
        li.innerHTML = `<div><b>${{escapeHTML(s.id)}}</b>${{done ? '<span class="pill good">done</span>' : '<span class="pill">planned</span>'}}</div>
                        <div class="small">${{escapeHTML(s.component || '')}}</div>`;
        li.onclick = () => selectStep(s.id);
        ul3.appendChild(li);
      }});
      sec3.appendChild(ul3);
      left.appendChild(sec3);

      const search = sec3.querySelector('#stepSearch');
      search.addEventListener('input', () => {{
        const q = search.value.trim().toLowerCase();
        steps.forEach(s => {{
          const el = ul3.querySelector(`[data-step-li="${{cssEscape(s.id)}}"]`);
          if (!el) return;
          const hay = `${{s.id}} ${{s.component||''}}`.toLowerCase();
          el.style.display = (!q || hay.includes(q)) ? '' : 'none';
        }});
      }});
    }}

    // ---- Right panel helpers ----
    function isPlainObject(v) {{
      return v && typeof v === 'object' && !Array.isArray(v);
    }}
    function renderValueHTML(value, depth) {{
      if (value === null || value === undefined) {{
        return '<div class="small muted">(null)</div>';
      }}
      const t = typeof value;
      if (t === 'string') {{
        const s = String(value);
        if (s.includes('\\n')) {{
          return `<pre class="mono">${{escapeHTML(s)}}</pre>`;
        }}
        return `<div class="mono">"${{escapeHTML(s)}}"</div>`;
      }}
      if (t === 'number' || t === 'boolean') {{
        return `<div class="mono">${{escapeHTML(String(value))}}</div>`;
      }}
      if (Array.isArray(value)) {{
        if (!value.length) return '<div class="small muted">(empty list)</div>';
        if (depth > 2) return `<pre class="mono">${{escapeHTML(JSON.stringify(value, null, 2))}}</pre>`;
        const isObjectArray = value.every(v => isPlainObject(v));
        if (isObjectArray) {{
          const keys = Array.from(new Set(value.flatMap(v => Object.keys(v)))).slice(0, 8);
          const rows = value.slice(0, 50).map(v => {{
            const cols = keys.map(k => `<td>${{renderValueHTML(v[k], depth + 1)}}</td>`).join('');
            return `<tr>${{cols}}</tr>`;
          }}).join('');
          const header = keys.map(k => `<th>${{escapeHTML(k)}}</th>`).join('');
          const more = value.length > 50 ? `<div class="small muted">…and ${{value.length - 50}} more</div>` : '';
          return `<div class="small"><span class="badge">${{value.length}} items</span></div>
                  <table class="kvtable"><thead><tr>${{header}}</tr></thead><tbody>${{rows}}</tbody></table>${{more}}`;
        }}
        const items = value.slice(0, 50).map(v => `<li>${{renderValueHTML(v, depth + 1)}}</li>`).join('');
        const more = value.length > 50 ? `<div class="small muted">…and ${{value.length - 50}} more</div>` : '';
        return `<div class="small"><span class="badge">${{value.length}} items</span></div><ul class="vlist">${{items}}</ul>${{more}}`;
      }}
      if (isPlainObject(value)) {{
        const keys = Object.keys(value);
        if (!keys.length) return '<div class="small muted">(empty object)</div>';
        if (depth > 2) return `<pre class="mono">${{escapeHTML(JSON.stringify(value, null, 2))}}</pre>`;
        const rows = keys.slice(0, 50).map(k => {{
          return `<tr><th>${{escapeHTML(k)}}</th><td>${{renderValueHTML(value[k], depth + 1)}}</td></tr>`;
        }}).join('');
        const more = keys.length > 50 ? `<div class="small muted">…and ${{keys.length - 50}} more</div>` : '';
        return `<table class="kvtable"><tbody>${{rows}}</tbody></table>${{more}}`;
      }}
      return `<pre class="mono">${{escapeHTML(JSON.stringify(value, null, 2))}}</pre>`;
    }}
    function renderBindingsHTML(bindings) {{
      if (!bindings || !bindings.length) return '<div class="small muted">(none)</div>';
      return bindings.map(b => {{
        const raw = escapeHTML(String(b.raw));
        const kind = b.kind || 'literal';
        const ref = b.ref ? escapeHTML(String(b.ref)) : '';
        const field = b.field ? escapeHTML(String(b.field)) : '';
        const summary = b.value_summary ? escapeHTML(String(b.value_summary)) : '';
        const hasValue = b.value !== undefined && b.value !== null;
        return `
          <div style="margin-top:10px; padding-top:10px; border-top:1px solid var(--line)">
            <div class="small"><b>${{escapeHTML(String(b.name))}}</b> <span class="pill">${{escapeHTML(kind)}}</span></div>
            <div class="small muted mono">raw: ${{raw}}</div>
            ${{ref ? `<div class="small">ref: <span class="mono">${{ref}}</span>${{field ? ` · field: <span class="mono">${{field}}</span>` : ''}}</div>` : ''}}
            ${{summary ? `<div class="small">value: ${{summary}}</div>` : ''}}
            ${{hasValue ? `<details><summary>Value</summary>${{renderValueHTML(b.value, 0)}}</details>` : ''}}
            ${{hasValue ? `<details><summary>Raw JSON</summary><pre class="mono">${{escapeHTML(JSON.stringify(b.value, null, 2))}}</pre></details>` : ''}}
          </div>
        `;
      }}).join('');
    }}

    function renderRightStep(stepId, isOutput) {{
      const s = stepById[stepId];
      const right = document.getElementById('right');
      if (!s) {{ right.innerHTML = ''; return; }}

      const dur = (s.run && s.run.duration_s != null) ? `${{Math.round(s.run.duration_s*100)/100}}s` : '';
      const outSum = (s.output && s.output.summary) ? s.output.summary : '';

      right.innerHTML = `
        <div class="section">
          <h2>Details</h2>
          <div class="card details">
            <div style="font-size:14px"><b>Step: ${{escapeHTML(stepId)}}</b>
              ${{isOutput ? '<span class="pill good">selected output</span>' : ''}}
            </div>
            <div class="small" style="margin-top:6px">
              <span class="pill">${{escapeHTML(s.component || '')}}</span>
              ${{s.run && s.run.ended_at ? '<span class="pill good">finished</span>' : '<span class="pill">planned</span>'}}
            </div>
            <div style="margin-top:10px" class="kvs">
              <div class="k">Started</div><div class="v mono">${{escapeHTML((s.run && s.run.started_at) || '')}}</div>
              <div class="k">Ended</div><div class="v mono">${{escapeHTML((s.run && s.run.ended_at) || '')}}</div>
              <div class="k">Duration</div><div class="v mono">${{escapeHTML(dur)}}</div>
              <div class="k">URI</div><div class="v mono">${{escapeHTML(s.uri || '')}}</div>
            </div>

            <div class="btnrow" style="margin-top:12px">
              <button id="btn-trace">Trace from this output</button>
              <button id="btn-show-entity">Show output entity</button>
            </div>

            <div style="margin-top:12px" class="small"><b>Output summary</b></div>
            <div class="small">${{escapeHTML(outSum)}}</div>

            <details style="margin-top:10px">
              <summary>Inputs (on demand)</summary>
              ${{renderBindingsHTML(s.inputs || [])}}
            </details>

            <details>
              <summary>Output (on demand)</summary>
              ${{(s.output && s.output.value != null) ? renderValueHTML(s.output.value, 0) : '<div class="small muted">(payload omitted)</div>'}}
            </details>

            <details>
              <summary>Plan spec (YAML subtree)</summary>
              <pre class="mono">${{escapeHTML(JSON.stringify(s.plan || {{}}, null, 2))}}</pre>
            </details>
          </div>
        </div>
      `;

      const btnTrace = document.getElementById('btn-trace');
      if (btnTrace) btnTrace.onclick = () => selectOutput(stepId);

      const btnEnt = document.getElementById('btn-show-entity');
      if (btnEnt) btnEnt.onclick = () => {{
        state.mode = 'entities';
        state.selectedEntity = outEntityId(stepId);
        state.subsetEntities = traceUpFromEntity(state.selectedEntity);
        updateModeButtons();
        renderLeft(state.selectedStep, state.selectedOutput);
        renderGraph();
        renderRightEntity(state.selectedEntity);
      }};
    }}

    function renderRightSource(sourceId) {{
      const src = (data.data_sources || []).find(s => s.id === sourceId);
      const right = document.getElementById('right');
      if (!src) {{ right.innerHTML = ''; return; }}

      right.innerHTML = `
        <div class="section">
          <h2>Details</h2>
          <div class="card details">
            <div style="font-size:14px"><b>Flow input: &amp;${{escapeHTML(src.id)}}</b></div>
            <div class="small">${{src.is_external ? '<span class="pill warn">external-like</span>' : '<span class="pill">input</span>'}}</div>
            <div style="margin-top:10px" class="small">Summary: ${{escapeHTML(src.summary || '')}}</div>
            <div class="btnrow" style="margin-top:12px">
              <button id="btn-src-down">Show downstream trace</button>
            </div>
            <details open>
              <summary>Value</summary>
              ${{src.value != null ? renderValueHTML(src.value, 0) : '<div class="small muted">(payload omitted)</div>'}}
            </details>
            <details>
              <summary>URI</summary>
              <div class="small mono">${{escapeHTML(src.uri || '')}}</div>
            </details>
          </div>
        </div>
      `;

      const btn = document.getElementById('btn-src-down');
      if (btn) btn.onclick = () => {{
        state.mode = 'entities';
        state.selectedEntity = inEntityId(sourceId);
        state.subsetEntities = traceDownFromEntity(state.selectedEntity);
        updateModeButtons();
        renderLeft(state.selectedStep, state.selectedOutput);
        renderGraph();
        renderRightEntity(state.selectedEntity);
      }};
    }}

    // ---- Entities graph build ----
    const entityNodes = {{}};
    const entityEdges = [];
    function inEntityId(name) {{ return `E:in:${{name}}`; }}
    function outEntityId(stepId) {{ return `E:out:${{stepId}}`; }}
    function litEntityId(stepId, name) {{ return `E:lit:${{stepId}}:${{name}}`; }}
    function actId(stepId) {{ return `A:${{stepId}}`; }}

    function buildEntityGraph() {{
      (data.data_sources || []).forEach(src => {{
        entityNodes[inEntityId(src.id)] = {{
          id: inEntityId(src.id),
          type: 'entity',
          kind: 'flow_input',
          label: `&${{src.id}}`,
          summary: src.summary || '',
          value: src.value,
          uri: src.uri || `${{base}}/run/${{runId}}/entity/input/${{safeId(src.id)}}`,
          source_id: src.id
        }};
      }});

      steps.forEach(s => {{
        const aid = actId(s.id);
        entityNodes[aid] = {{
          id: aid,
          type: 'activity',
          kind: 'step',
          label: s.id,
          component: s.component || '',
          step_id: s.id,
          uri: s.uri || ''
        }};

        const oid = outEntityId(s.id);
        entityNodes[oid] = {{
          id: oid,
          type: 'entity',
          kind: 'step_output',
          label: `${{s.id}} output`,
          summary: (s.output && s.output.summary) ? s.output.summary : '',
          value: (s.output && s.output.value !== undefined) ? s.output.value : null,
          uri: outputUri(s.id),
          produced_by: s.id
        }};
        entityEdges.push({{type:'generated', from: aid, to: oid, label:'generated'}});

        (s.inputs || []).forEach(b => {{
          const nm = b.name || '';
          if (b.kind === 'flow_input' && b.ref) {{
            const eid = inEntityId(b.ref);
            if (!entityNodes[eid]) {{
              entityNodes[eid] = {{
                id: eid, type:'entity', kind:'flow_input', label:`&${{b.ref}}`,
                summary: b.value_summary || '', value: b.value,
                uri: `${{base}}/run/${{runId}}/entity/input/${{safeId(b.ref)}}`, source_id: b.ref
              }};
            }}
            entityEdges.push({{type:'used', from: eid, to: aid, label: nm}});
          }} else if (b.kind === 'step_output' && b.ref) {{
            const sid = outEntityId(b.ref);
            if (!entityNodes[sid]) {{
              entityNodes[sid] = {{
                id: sid, type:'entity', kind:'step_output', label:`${{b.ref}} output`,
                summary: '', value: null, uri: outputUri(b.ref), produced_by: b.ref
              }};
            }}
            const lbl = b.field ? `${{nm}} ← $${{b.ref}}.${{b.field}}` : `${{nm}} ← $${{b.ref}}`;
            entityEdges.push({{type:'used', from: sid, to: aid, label: lbl}});
          }} else {{
            const lid = litEntityId(s.id, nm);
            if (!entityNodes[lid]) {{
              entityNodes[lid] = {{
                id: lid, type:'entity', kind:'literal', label:`${{s.id}}.${{nm}}`,
                summary: b.value_summary || '', value: (b.value !== undefined) ? b.value : null,
                uri: literalUri(s.id, nm)
              }};
            }}
            entityEdges.push({{type:'used', from: lid, to: aid, label: nm}});
          }}
        }});
      }});
    }}
    buildEntityGraph();

    const outAdj = {{}};
    const inAdj = {{}};
    entityEdges.forEach(e => {{
      (outAdj[e.from] = outAdj[e.from] || []).push(e);
      (inAdj[e.to] = inAdj[e.to] || []).push(e);
    }});

    function traceUpFromEntity(startId) {{
      const seen = new Set();
      const stack = [startId];
      while (stack.length) {{
        const cur = stack.pop();
        if (!cur || seen.has(cur)) continue;
        seen.add(cur);
        const node = entityNodes[cur];
        if (!node) continue;
        if (node.type === 'entity') {{
          (inAdj[cur] || []).filter(e => e.type === 'generated').forEach(e => stack.push(e.from));
        }} else {{
          (inAdj[cur] || []).filter(e => e.type === 'used').forEach(e => stack.push(e.from));
        }}
      }}
      return seen;
    }}

    function traceDownFromEntity(startId) {{
      const seen = new Set();
      const stack = [startId];
      while (stack.length) {{
        const cur = stack.pop();
        if (!cur || seen.has(cur)) continue;
        seen.add(cur);
        const node = entityNodes[cur];
        if (!node) continue;
        if (node.type === 'entity') {{
          (outAdj[cur] || []).filter(e => e.type === 'used').forEach(e => stack.push(e.to));
        }} else {{
          (outAdj[cur] || []).filter(e => e.type === 'generated').forEach(e => stack.push(e.to));
        }}
      }}
      return seen;
    }}

    function renderRightEntity(nodeId) {{
      const right = document.getElementById('right');
      const node = entityNodes[nodeId];
      if (!node) {{ right.innerHTML = ''; return; }}

      if (node.kind === 'flow_input' && node.source_id) {{
        renderRightSource(node.source_id);
        return;
      }}
      if (node.type === 'activity' && node.step_id) {{
        renderRightStep(node.step_id, node.step_id === state.selectedOutput);
        return;
      }}

      const kind = node.kind || 'entity';
      const uri = node.uri || '';
      const produced = node.produced_by ? escapeHTML(node.produced_by) : '';
      const summary = escapeHTML(node.summary || '');
      const val = node.value;

      right.innerHTML = `
        <div class="section">
          <h2>Details</h2>
          <div class="card details">
            <div style="font-size:14px"><b>${{escapeHTML(node.label || node.id)}}</b> <span class="pill">${{escapeHTML(kind)}}</span></div>
            ${{produced ? `<div class="small" style="margin-top:6px">Produced by step: <span class="mono">${{produced}}</span></div>` : ''}}
            <div class="small" style="margin-top:10px">Summary: ${{summary}}</div>

            <div class="btnrow" style="margin-top:12px">
              <button id="btn-up">Trace upstream</button>
              <button id="btn-down">Trace downstream</button>
              ${{node.produced_by ? '<button id="btn-jump">Jump to producing step</button>' : ''}}
            </div>

            <details style="margin-top:10px">
              <summary>Value (on demand)</summary>
              ${{val != null ? `<pre class="mono">${{escapeHTML(JSON.stringify(val, null, 2))}}</pre>` : '<div class="small muted">(payload omitted)</div>'}}
            </details>

            <details>
              <summary>URI</summary>
              <div class="small mono">${{escapeHTML(uri)}}</div>
            </details>
          </div>
        </div>
      `;

      const up = document.getElementById('btn-up');
      if (up) up.onclick = () => {{
        state.subsetEntities = traceUpFromEntity(nodeId);
        state.traceOnly = true;
        updateTraceButton();
        renderGraph();
      }};
      const down = document.getElementById('btn-down');
      if (down) down.onclick = () => {{
        state.subsetEntities = traceDownFromEntity(nodeId);
        state.traceOnly = true;
        updateTraceButton();
        renderGraph();
      }};
      const jump = document.getElementById('btn-jump');
      if (jump && node.produced_by) jump.onclick = () => selectStep(node.produced_by);
    }}

    // ---- Graph renderers ----
    function computeLayers(subset) {{
      const nodes = steps.map(s => s.id).filter(id => !subset || subset.has(id));
      const inDeg = {{}};
      nodes.forEach(n => inDeg[n] = 0);
      const adj = {{}};
      nodes.forEach(n => adj[n] = []);
      edges.filter(e => e.type==='dependsOn').forEach(e => {{
        if (!inDeg.hasOwnProperty(e.from) || !inDeg.hasOwnProperty(e.to)) return;
        adj[e.from].push(e.to);
        inDeg[e.to] += 1;
      }});
      const q = [];
      nodes.forEach(n => {{ if (inDeg[n]===0) q.push(n); }});
      const topo = [];
      while (q.length) {{
        const n = q.shift();
        topo.push(n);
        adj[n].forEach(m => {{
          inDeg[m] -= 1;
          if (inDeg[m]===0) q.push(m);
        }});
      }}
      const layer = {{}};
      topo.forEach(n => layer[n] = 0);
      topo.forEach(n => {{
        adj[n].forEach(m => {{
          layer[m] = Math.max(layer[m]||0, (layer[n]||0)+1);
        }});
      }});
      const groups = {{}};
      nodes.forEach(n => {{ const L = layer[n]||0; (groups[L] = groups[L]||[]).push(n); }});
      Object.keys(groups).forEach(k => groups[k].sort());
      return {{layer, groups}};
    }}

    function clearSvg(svg) {{ while (svg.firstChild) svg.removeChild(svg.firstChild); }}
    function ensureDefs(svg) {{
      const defs = document.createElementNS('http://www.w3.org/2000/svg','defs');
      const marker = document.createElementNS('http://www.w3.org/2000/svg','marker');
      marker.setAttribute('id','arrow');
      marker.setAttribute('viewBox','0 0 10 10');
      marker.setAttribute('refX','9');
      marker.setAttribute('refY','5');
      marker.setAttribute('markerWidth','8');
      marker.setAttribute('markerHeight','8');
      marker.setAttribute('orient','auto-start-reverse');
      const ap = document.createElementNS('http://www.w3.org/2000/svg','path');
      ap.setAttribute('d','M 0 0 L 10 5 L 0 10 z');
      ap.setAttribute('fill','rgba(170,177,195,0.9)');
      marker.appendChild(ap);
      defs.appendChild(marker);
      svg.appendChild(defs);
    }}

    function renderGraphSteps(selectedStep, selectedOutput, subset) {{
      const svg = document.getElementById('graph');
      clearSvg(svg);

      const {{groups}} = computeLayers(subset);
      const layers = Object.keys(groups).map(x => parseInt(x,10)).sort((a,b)=>a-b);
      const xGap = 60, yGap = 96, padX = 70, padY = 60, minW = 160, nodeH = 46;
      const sizes = {{}};
      steps.forEach(s => {{
        const w1 = measureTextWidth(s.id, 12);
        const w2 = measureTextWidth(s.component || '', 11);
        const w = Math.max(minW, w1, w2) + 24;
        sizes[s.id] = {{w, h: nodeH}};
      }});
      const layerWidths = {{}};
      layers.forEach(L => {{
        let maxW = minW;
        (groups[L] || []).forEach(id => {{
          const w = (sizes[id] || {{w: minW}}).w;
          if (w > maxW) maxW = w;
        }});
        layerWidths[L] = maxW;
      }});
      const layerX = {{}};
      let curX = padX;
      layers.forEach(L => {{
        layerX[L] = curX;
        curX += (layerWidths[L] || minW) + xGap;
      }});

      const pos = {{}};
      let maxX = 0;
      let maxY = 0;
      layers.forEach(L => {{
        (groups[L] || []).forEach((id, idx) => {{
          const x = layerX[L] || padX;
          const y = padY + idx * yGap;
          const off = offsetFor('steps', id);
          pos[id] = {{x: x + off.x, y: y + off.y}};
          const size = sizes[id] || {{w: minW, h: nodeH}};
          maxX = Math.max(maxX, pos[id].x + size.w);
          maxY = Math.max(maxY, pos[id].y + size.h);
        }});
      }});
      const width = Math.max(600, maxX + padX);
      const height = Math.max(600, maxY + padY + 120);
      setBaseViewBox(width, height);

      ensureDefs(svg);

      edges.filter(e => e.type==='dependsOn').forEach(e => {{
        if (!pos[e.from] || !pos[e.to]) return;
        const p1 = pos[e.from], p2 = pos[e.to];
        const s1 = sizes[e.from] || {{w: minW, h: nodeH}};
        const s2 = sizes[e.to] || {{w: minW, h: nodeH}};
        const x1 = p1.x + s1.w, y1 = p1.y + s1.h/2, x2 = p2.x, y2 = p2.y + s2.h/2;
        const mid = (x1 + x2) / 2;
        const path = document.createElementNS('http://www.w3.org/2000/svg','path');
        path.setAttribute('d', `M ${{x1}} ${{y1}} C ${{mid}} ${{y1}}, ${{mid}} ${{y2}}, ${{x2}} ${{y2}}`);
        path.setAttribute('fill','none');
        path.setAttribute('stroke','rgba(42,49,70,0.95)');
        path.setAttribute('stroke-width','2');
        path.setAttribute('marker-end','url(#arrow)');
        if (subset && subset.has(e.from) && subset.has(e.to)) path.setAttribute('stroke','rgba(122,162,255,0.65)');
        svg.appendChild(path);
      }});

      steps.forEach(s => {{
        if (subset && !subset.has(s.id)) return;
        const p = pos[s.id];
        if (!p) return;
        const size = sizes[s.id] || {{w: minW, h: nodeH}};
        const g = document.createElementNS('http://www.w3.org/2000/svg','g');
        g.classList.add('graph-node');
        g.style.cursor = 'pointer';

        const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
        rect.setAttribute('x', p.x); rect.setAttribute('y', p.y);
        rect.setAttribute('rx', '14'); rect.setAttribute('ry', '14');
        rect.setAttribute('width', size.w); rect.setAttribute('height', size.h);
        rect.setAttribute('fill', 'rgba(255,255,255,0.03)');
        rect.setAttribute('stroke', 'rgba(42,49,70,1)');
        rect.setAttribute('stroke-width', '2');
        const isDone = s.run && s.run.ended_at;
        if (isDone) rect.setAttribute('stroke','rgba(61,220,151,0.5)');
        if (s.id === selectedStep) rect.setAttribute('stroke','rgba(122,162,255,0.95)');
        if (s.id === selectedOutput) rect.setAttribute('fill','rgba(122,162,255,0.10)');

        const t1 = document.createElementNS('http://www.w3.org/2000/svg','text');
        t1.setAttribute('x', p.x + 12); t1.setAttribute('y', p.y + 20);
        t1.setAttribute('fill', 'rgba(231,233,238,0.95)');
        t1.setAttribute('font-size', '12'); t1.textContent = s.id;

        const t2 = document.createElementNS('http://www.w3.org/2000/svg','text');
        t2.setAttribute('x', p.x + 12); t2.setAttribute('y', p.y + 38);
        t2.setAttribute('fill', 'rgba(170,177,195,0.9)');
        t2.setAttribute('font-size', '11'); t2.textContent = s.component || '';

        g.appendChild(rect); g.appendChild(t1); g.appendChild(t2);
        g.addEventListener('mousedown', (e) => {{
          if (e.button !== 0) return;
          e.stopPropagation();
          startNodeDrag('steps', s.id, e.clientX, e.clientY);
        }});
        g.addEventListener('click', () => selectStep(s.id));
        svg.appendChild(g);
      }});
    }}

    const stepLayers = computeLayers(null).layer || {{}};

    function renderGraphEntities(selectedNode, subsetNodes) {{
      const svg = document.getElementById('graph');
      clearSvg(svg);

      const xGap = 60, yGap = 78, padX = 55, padY = 55, minW = 180, nodeH = 42;

      const nodes = Object.keys(entityNodes).filter(id => !subsetNodes || subsetNodes.has(id));
      const sizes = {{}};
      nodes.forEach(id => {{
        const n = entityNodes[id];
        if (!n) return;
        const label = n.label || id;
        const sub = n.type === 'activity' ? (n.component || 'activity') : (n.kind || 'entity');
        const w1 = measureTextWidth(label, 12);
        const w2 = measureTextWidth(sub, 11);
        const w = Math.max(minW, w1, w2) + 24;
        sizes[id] = {{w, h: nodeH}};
      }});

      function colFor(id) {{
        const n = entityNodes[id];
        if (!n) return 0;
        if (n.type === 'activity') {{
          const L = stepLayers[n.step_id] || 0;
          return 2*L + 1;
        }}
        if (n.kind === 'flow_input') return 0;
        if (n.kind === 'step_output' && n.produced_by) {{
          const L = stepLayers[n.produced_by] || 0;
          return 2*L + 2;
        }}
        if (n.kind === 'literal') {{
          const m = /E:lit:([^:]+):/.exec(id);
          const stepId = m ? m[1] : '';
          const L = stepLayers[stepId] || 0;
          return 2*L;
        }}
        return 0;
      }}

      const groups = {{}};
      nodes.forEach(id => {{
        const c = colFor(id);
        (groups[c] = groups[c] || []).push(id);
      }});
      const cols = Object.keys(groups).map(x => parseInt(x,10)).sort((a,b)=>a-b);
      cols.forEach(c => groups[c].sort());
      const colWidths = {{}};
      cols.forEach(c => {{
        let maxW = minW;
        (groups[c] || []).forEach(id => {{
          const w = (sizes[id] || {{w: minW}}).w;
          if (w > maxW) maxW = w;
        }});
        colWidths[c] = maxW;
      }});
      const colX = {{}};
      let curX = padX;
      cols.forEach(c => {{
        colX[c] = curX;
        curX += (colWidths[c] || minW) + xGap;
      }});

      const pos = {{}};
      let maxX = 0;
      let maxY = 0;
      cols.forEach(c => {{
        (groups[c] || []).forEach((id, idx) => {{
          const x = colX[c] || padX;
          const y = padY + idx * yGap;
          const off = offsetFor('entities', id);
          pos[id] = {{x: x + off.x, y: y + off.y}};
          const size = sizes[id] || {{w: minW, h: nodeH}};
          maxX = Math.max(maxX, pos[id].x + size.w);
          maxY = Math.max(maxY, pos[id].y + size.h);
        }});
      }});
      const width = Math.max(650, maxX + padX + 40);
      const height = Math.max(650, maxY + padY + 140);
      setBaseViewBox(width, height);

      ensureDefs(svg);

      entityEdges.forEach(e => {{
        if (subsetNodes && (!subsetNodes.has(e.from) || !subsetNodes.has(e.to))) return;
        const p1 = pos[e.from], p2 = pos[e.to];
        if (!p1 || !p2) return;
        const s1 = sizes[e.from] || {{w: minW, h: nodeH}};
        const s2 = sizes[e.to] || {{w: minW, h: nodeH}};
        const x1 = p1.x + s1.w, y1 = p1.y + s1.h/2, x2 = p2.x, y2 = p2.y + s2.h/2;
        const mid = (x1 + x2) / 2;

        const path = document.createElementNS('http://www.w3.org/2000/svg','path');
        path.setAttribute('d', `M ${{x1}} ${{y1}} C ${{mid}} ${{y1}}, ${{mid}} ${{y2}}, ${{x2}} ${{y2}}`);
        path.setAttribute('fill','none');
        path.setAttribute('stroke-width','2');
        path.setAttribute('marker-end','url(#arrow)');
        path.setAttribute('stroke', e.type === 'generated' ? 'rgba(122,162,255,0.70)' : 'rgba(42,49,70,0.95)');
        svg.appendChild(path);

        if (e.label && e.type === 'used') {{
          const tx = document.createElementNS('http://www.w3.org/2000/svg','text');
          tx.setAttribute('x', mid - 30);
          tx.setAttribute('y', y2 - 6);
          tx.setAttribute('fill', 'rgba(170,177,195,0.8)');
          tx.setAttribute('font-size', '10');
          tx.textContent = e.label;
          svg.appendChild(tx);
        }}
      }});

      nodes.forEach(id => {{
        const n = entityNodes[id];
        const p = pos[id];
        if (!n || !p) return;
        const size = sizes[id] || {{w: minW, h: nodeH}};

        const g = document.createElementNS('http://www.w3.org/2000/svg','g');
        g.classList.add('graph-node');
        g.style.cursor = 'pointer';

        const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
        rect.setAttribute('x', p.x); rect.setAttribute('y', p.y);
        rect.setAttribute('rx', '14'); rect.setAttribute('ry', '14');
        rect.setAttribute('width', size.w); rect.setAttribute('height', size.h);

        if (n.type === 'activity') {{
          rect.setAttribute('fill', 'rgba(255,255,255,0.03)');
          rect.setAttribute('stroke', 'rgba(61,220,151,0.5)');
        }} else {{
          rect.setAttribute('fill', 'rgba(255,255,255,0.02)');
          rect.setAttribute('stroke', n.kind === 'flow_input' ? 'rgba(255,204,102,0.55)' : 'rgba(42,49,70,1)');
        }}
        rect.setAttribute('stroke-width','2');
        if (id === selectedNode) rect.setAttribute('stroke','rgba(122,162,255,0.95)');

        const t1 = document.createElementNS('http://www.w3.org/2000/svg','text');
        t1.setAttribute('x', p.x + 12); t1.setAttribute('y', p.y + 20);
        t1.setAttribute('fill', 'rgba(231,233,238,0.95)');
        t1.setAttribute('font-size', '12');
        t1.textContent = n.label || id;

        const t2 = document.createElementNS('http://www.w3.org/2000/svg','text');
        t2.setAttribute('x', p.x + 12); t2.setAttribute('y', p.y + 36);
        t2.setAttribute('fill', 'rgba(170,177,195,0.9)');
        t2.setAttribute('font-size', '11');
        t2.textContent = n.type === 'activity' ? (n.component || 'activity') : (n.kind || 'entity');

        g.appendChild(rect); g.appendChild(t1); g.appendChild(t2);
        g.addEventListener('mousedown', (e) => {{
          if (e.button !== 0) return;
          e.stopPropagation();
          startNodeDrag('entities', id, e.clientX, e.clientY);
        }});
        g.addEventListener('click', () => {{
          if (n.type === 'activity' && n.step_id) selectStep(n.step_id);
          else selectEntity(id);
        }});
        svg.appendChild(g);
      }});
    }}

    function renderGraph() {{
      if (state.mode === 'steps') {{
        renderGraphSteps(state.selectedStep, state.selectedOutput, state.traceOnly ? state.subsetSteps : null);
      }} else {{
        renderGraphEntities(state.selectedEntity, state.traceOnly ? state.subsetEntities : null);
      }}
    }}

    let panZoomReady = false;
    function setupPanZoom() {{
      if (panZoomReady) return;
      panZoomReady = true;
      const svg = document.getElementById('graph');
      let isPanning = false;
      let startX = 0, startY = 0, startViewX = 0, startViewY = 0;

      svg.addEventListener('wheel', (e) => {{
        if (!view.baseW) return;
        e.preventDefault();
        const rect = svg.getBoundingClientRect();
        const mx = (e.clientX - rect.left) / rect.width * view.w + view.x;
        const my = (e.clientY - rect.top) / rect.height * view.h + view.y;
        const zoom = Math.exp(-e.deltaY * 0.001);
        const newW = view.w / zoom;
        const newH = view.h / zoom;
        const minW = view.baseW * 0.2;
        const maxW = view.baseW * 6;
        if (newW < minW || newW > maxW) return;
        view.x = mx - (mx - view.x) / zoom;
        view.y = my - (my - view.y) / zoom;
        view.w = newW;
        view.h = newH;
        applyViewBox();
      }}, {{ passive: false }});

      svg.addEventListener('mousedown', (e) => {{
        if (e.button !== 0) return;
        if (e.target.closest('.graph-node')) return;
        isPanning = true;
        svg.classList.add('dragging');
        startX = e.clientX;
        startY = e.clientY;
        startViewX = view.x;
        startViewY = view.y;
      }});
      window.addEventListener('mousemove', (e) => {{
        if (nodeDrag) {{
          const rect = svg.getBoundingClientRect();
          const dx = (e.clientX - nodeDrag.startX) / rect.width * view.w;
          const dy = (e.clientY - nodeDrag.startY) / rect.height * view.h;
          if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) nodeDrag.moved = true;
          setOffset(nodeDrag.kind, nodeDrag.id, nodeDrag.startOffX + dx, nodeDrag.startOffY + dy);
          renderGraph();
          return;
        }}
        if (!isPanning) return;
        const rect = svg.getBoundingClientRect();
        const dx = (e.clientX - startX) / rect.width * view.w;
        const dy = (e.clientY - startY) / rect.height * view.h;
        view.x = startViewX - dx;
        view.y = startViewY - dy;
        applyViewBox();
      }});
      window.addEventListener('mouseup', () => {{
        if (nodeDrag) {{
          nodeDrag = null;
          return;
        }}
        if (!isPanning) return;
        isPanning = false;
        svg.classList.remove('dragging');
      }});
    }}

    // ---- State & actions ----
    let state = {{
      mode: 'steps',
      traceOnly: true,
      selectedStep: defaultOutput,
      selectedOutput: defaultOutput,
      subsetSteps: ancestorsOf(defaultOutput),
      selectedEntity: defaultOutput ? outEntityId(defaultOutput) : null,
      subsetEntities: defaultOutput ? traceUpFromEntity(outEntityId(defaultOutput)) : new Set(),
      dragOffsetsSteps: {{}},
      dragOffsetsEntities: {{}}
    }};

    function updateModeButtons() {{
      const b1 = document.getElementById('mode-steps');
      const b2 = document.getElementById('mode-entities');
      if (b1 && b2) {{
        b1.classList.toggle('active', state.mode === 'steps');
        b2.classList.toggle('active', state.mode === 'entities');
      }}
      updateTraceButton();
    }}
    function updateTraceButton() {{
      const t = document.getElementById('toggle-trace');
      if (t) {{
        t.classList.toggle('active', !!state.traceOnly);
        t.textContent = state.traceOnly ? 'Trace only' : 'Full graph';
      }}
    }}

    function selectStep(stepId) {{
      state.selectedStep = stepId;
      renderLeft(state.selectedStep, state.selectedOutput);
      if (state.mode === 'steps') {{
        renderGraph();
        renderRightStep(stepId, stepId === state.selectedOutput);
      }} else {{
        state.selectedEntity = actId(stepId);
        renderGraph();
        renderRightStep(stepId, stepId === state.selectedOutput);
      }}
    }}

    function selectOutput(stepId) {{
      state.selectedOutput = stepId;
      state.selectedStep = stepId;
      state.subsetSteps = ancestorsOf(stepId);
      state.selectedEntity = outEntityId(stepId);
      state.subsetEntities = traceUpFromEntity(state.selectedEntity);

      renderLeft(state.selectedStep, state.selectedOutput);
      renderGraph();
      if (state.mode === 'steps') renderRightStep(stepId, true);
      else renderRightEntity(state.selectedEntity);
    }}

    function selectSource(sourceId) {{
      state.selectedEntity = inEntityId(sourceId);
      renderLeft(state.selectedStep, state.selectedOutput);
      if (state.mode === 'entities') {{
        if (state.traceOnly) state.subsetEntities = traceDownFromEntity(state.selectedEntity);
        renderGraph();
        renderRightEntity(state.selectedEntity);
      }} else {{
        renderGraph();
        renderRightSource(sourceId);
      }}
    }}

    function selectEntity(entityId) {{
      state.mode = 'entities';
      state.selectedEntity = entityId;
      if (state.traceOnly) state.subsetEntities = traceUpFromEntity(entityId);
      updateModeButtons();
      renderLeft(state.selectedStep, state.selectedOutput);
      renderGraph();
      renderRightEntity(entityId);
    }}

    // ---- Wire buttons ----
    document.getElementById('mode-steps').onclick = () => {{
      state.mode = 'steps';
      updateModeButtons();
      renderLeft(state.selectedStep, state.selectedOutput);
      renderGraph();
      renderRightStep(state.selectedStep, state.selectedStep === state.selectedOutput);
    }};
    document.getElementById('mode-entities').onclick = () => {{
      state.mode = 'entities';
      updateModeButtons();
      renderLeft(state.selectedStep, state.selectedOutput);
      renderGraph();
      renderRightEntity(state.selectedEntity || outEntityId(state.selectedOutput));
    }};
    document.getElementById('toggle-trace').onclick = () => {{
      state.traceOnly = !state.traceOnly;
      updateTraceButton();
      renderGraph();
    }};

    // ---- Initial render ----
    updateModeButtons();
    renderLeft(state.selectedStep, state.selectedOutput);
    setupPanZoom();
    renderGraph();
    renderRightStep(state.selectedStep, true);

  }})();
  </script>
</body>
</html>
"""
