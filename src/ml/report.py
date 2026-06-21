import json
import os
from datetime import datetime

from src.data.icons import render_unit_icon_svg


_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")


def _read_d3_js() -> str:
    path = os.path.join(_VENDOR_DIR, "d3.v7.min.js")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _load_jsonl(path: str) -> list[dict]:
    rows = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return rows


def _build_event_ranges(events: list[dict]) -> list[dict]:
    if not events:
        return []

    by_type: dict[str, list[dict]] = {}
    for e in events:
        etype = e.get("type", "unknown")
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(e)

    ranges = []
    for etype, typed_events in by_type.items():
        typed_events.sort(key=lambda e: e.get("time", 0))
        severity = typed_events[0].get("severity", "info")
        run_start = typed_events[0].get("time", 0)
        run_end = run_start
        run_count = 1

        for e in typed_events[1:]:
            etime = e.get("time", 0)
            run_end = etime
            run_count += 1

        ranges.append({
            "type": etype,
            "severity": severity,
            "count": run_count,
            "first": run_start,
            "last": run_end,
            "duration": round(run_end - run_start, 3),
        })

    severity_order = {"high": 0, "medium": 1, "info": 2}
    ranges.sort(key=lambda r: (severity_order.get(r["severity"], 3), -r["count"]))
    return ranges


def _build_timeline_data(event_ranges: list[dict], duration: float) -> dict:
    ranged_events = []
    point_events = []

    for r in event_ranges:
        if r["duration"] > 0:
            ranged_events.append({
                "type": r["type"],
                "severity": r["severity"],
                "start": r["first"],
                "end": r["last"],
                "count": r["count"],
            })
        else:
            point_events.append({
                "type": r["type"],
                "time": r["first"],
                "severity": r["severity"],
                "details": f"count: {r['count']}",
            })

    return {
        "ranges": ranged_events,
        "points": point_events,
        "duration": duration,
    }


def _compute_metrics(features: list[dict], events: list[dict]) -> dict:
    if not features:
        return {}

    total_minerals = sum(f.get("minerals", 0) for f in features)
    total_vespene = sum(f.get("vespene", 0) for f in features)
    n = len(features)

    event_ranges = _build_event_ranges(events)
    supply_block_ranges = [r for r in event_ranges if r["type"] == "supply_block"]
    supply_block_count = sum(r["count"] for r in supply_block_ranges)

    worker_counts = [f.get("worker_count", 0) for f in features]
    peak_workers = max(worker_counts) if worker_counts else 0

    supply_used_vals = [f.get("supply_used", 0) for f in features]
    supply_cap_vals = [f.get("supply_cap", 0) for f in features]
    max_supply = max(supply_used_vals) if supply_used_vals else 0
    max_supply_cap = max(supply_cap_vals) if supply_cap_vals else 0

    army_counts = [f.get("army_count", 0) for f in features]
    max_army_size = max(army_counts) if army_counts else 0

    our_army_values = [f.get("our_army_value", 0) for f in features]
    enemy_army_values = [f.get("enemy_army_value", 0) for f in features]
    our_army_value_peak = max(our_army_values) if our_army_values else 0
    enemy_army_value_peak = max(enemy_army_values) if enemy_army_values else 0

    our_t3_counts = [f.get("our_t3_count", 0) for f in features]
    enemy_t3_counts = [f.get("enemy_t3_count", 0) for f in features]
    our_t3_peak = max(our_t3_counts) if our_t3_counts else 0
    enemy_t3_peak = max(enemy_t3_counts) if enemy_t3_counts else 0

    last_features = features[-1]
    collected_minerals = last_features.get("collected_minerals", 0)
    collected_vespene = last_features.get("collected_vespene", 0)
    avg_unspent_minerals = total_minerals / n
    avg_unspent_vespene = total_vespene / n
    mineral_efficiency = (
        round((collected_minerals - avg_unspent_minerals) / max(collected_minerals, 1) * 100, 1)
    )
    vespene_efficiency = (
        round((collected_vespene - avg_unspent_vespene) / max(collected_vespene, 1) * 100, 1)
    )

    last_bases = features[-1].get("bases", []) if features else []
    saturation_summary = [
        {
            "current": b.get("current_workers", 0),
            "ideal": b.get("ideal_workers", 0),
            "ratio": b.get("saturation_ratio", 0),
            "mineral_patches": b.get("mineral_patches", 0),
            "gas_geysers": b.get("gas_geysers", 0),
            "ideal_mineral_workers": b.get("ideal_mineral_workers", 0),
            "ideal_gas_workers": b.get("ideal_gas_workers", 0),
            "actual_mineral_workers": b.get("actual_mineral_workers", 0),
            "actual_gas_workers": b.get("actual_gas_workers", 0),
            "idle_workers_nearby": b.get("idle_workers_nearby", 0),
            "mineral_saturation": b.get("mineral_saturation", 0),
            "gas_saturation": b.get("gas_saturation", 0),
            "status": b.get("status", "optimal"),
        }
        for b in last_bases
    ]

    return {
        "avg_unspent_minerals": round(avg_unspent_minerals, 1),
        "avg_unspent_vespene": round(avg_unspent_vespene, 1),
        "collected_minerals": collected_minerals,
        "collected_vespene": collected_vespene,
        "mineral_efficiency": mineral_efficiency,
        "vespene_efficiency": vespene_efficiency,
        "supply_block_count": supply_block_count,
        "supply_block_ranges": supply_block_ranges,
        "peak_workers": peak_workers,
        "worker_target": 70,
        "total_steps": n,
        "max_supply": max_supply,
        "max_supply_cap": max_supply_cap,
        "max_army_size": max_army_size,
        "our_army_value_peak": our_army_value_peak,
        "enemy_army_value_peak": enemy_army_value_peak,
        "our_t3_peak": our_t3_peak,
        "enemy_t3_peak": enemy_t3_peak,
        "saturation_summary": saturation_summary,
    }


def _build_timeline(features: list[dict]) -> list[dict]:
    timeline = []
    for f in features:
        timeline.append({
            "step": f.get("iteration", 0),
            "time": f.get("game_time_seconds", 0),
            "supply_used": f.get("supply_used", 0),
            "supply_cap": f.get("supply_cap", 0),
            "workers": f.get("worker_count", 0),
            "army": f.get("army_count", 0),
            "minerals": f.get("minerals", 0),
            "vespene": f.get("vespene", 0),
            "expansion_count": f.get("expansion_count", 0),
        })
    return timeline


def _build_army_snapshots(
    features: list[dict], interval_seconds: float = 60
) -> list[dict]:
    snapshots = []
    last_time = -interval_seconds
    for f in features:
        t = f.get("game_time_seconds", 0)
        if t - last_time >= interval_seconds:
            snapshots.append({
                "time": int(t),
                "our_army_count": f.get("army_count", 0),
                "our_composition": f.get("our_army_composition", {}),
                "enemy_visible": f.get("enemy_visible_units", 0),
                "enemy_composition": f.get("enemy_army_composition", {}),
            })
            last_time = t
    return snapshots


def _build_saturation_snapshots(
    features: list[dict], interval_seconds: float = 60
) -> list[dict]:
    snapshots = []
    last_time = -interval_seconds
    for f in features:
        t = f.get("game_time_seconds", 0)
        if t - last_time >= interval_seconds:
            bases = f.get("bases", [])
            totals = {
                "workers": f.get("worker_count", 0),
                "bases": len(bases),
                "oversaturated_bases": sum(
                    1 for b in bases if b.get("status") == "oversaturated"
                ),
                "undersaturated_bases": sum(
                    1 for b in bases if b.get("status") == "undersaturated"
                ),
                "idle_workers": sum(
                    b.get("idle_workers_nearby", 0) for b in bases
                ),
                "avg_mineral_sat": round(
                    sum(b.get("mineral_saturation", 0) for b in bases) / max(len(bases), 1), 3
                ),
                "avg_gas_sat": round(
                    sum(b.get("gas_saturation", 0) for b in bases) / max(len(bases), 1), 3
                ),
            }
            snapshots.append({
                "time": int(t),
                "bases": [
                    {
                        "base": i,
                        "mineral_workers": b.get("actual_mineral_workers", 0),
                        "gas_workers": b.get("actual_gas_workers", 0),
                        "mineral_saturation": b.get("mineral_saturation", 0),
                        "gas_saturation": b.get("gas_saturation", 0),
                        "status": b.get("status", "optimal"),
                        "idle": b.get("idle_workers_nearby", 0),
                    }
                    for i, b in enumerate(bases)
                ],
                "totals": totals,
            })
            last_time = t
    return snapshots


def generate_report_json(
    match_id: str,
    features: list[dict],
    events: list[dict],
    bot_info: dict | None = None,
) -> dict:
    metrics = _compute_metrics(features, events)
    timeline = _build_timeline(features)
    army_snapshots = _build_army_snapshots(features)
    saturation_timeline = _build_saturation_snapshots(features)

    raw_events = [
        {
            "time": e.get("time", 0),
            "type": e.get("type", "unknown"),
            "severity": e.get("severity", "info"),
        }
        for e in events
    ]
    event_ranges = _build_event_ranges(raw_events)
    duration = features[-1].get("game_time_seconds", 0) if features else 0
    timeline_data = _build_timeline_data(event_ranges, duration)
    policy = _normalize_policy(bot_info.get("policy") if bot_info else None)

    return {
        "match_id": match_id,
        "map": bot_info.get("map", "unknown") if bot_info else "unknown",
        "opponent_race": bot_info.get("opponent_race", "unknown") if bot_info else "unknown",
        "opponent_difficulty": bot_info.get("opponent_difficulty", "unknown") if bot_info else "unknown",
        "our_race": "Protoss",
        "duration_seconds": duration,
        "result": bot_info.get("result", "unknown") if bot_info else "unknown",
        "policy": policy,
        "max_supply_reached": max((f.get("supply_used", 0) for f in features), default=0),
        "timeline": timeline,
        "army_snapshots": army_snapshots,
        "metrics": metrics,
        "key_events": raw_events,
        "event_ranges": event_ranges,
        "timeline_data": timeline_data,
        "saturation_timeline": saturation_timeline,
    }


def _normalize_policy(policy: dict | None) -> dict:
    policy = policy or {}
    return {
        "mode": policy.get("mode", "unknown"),
        "selected_policy": policy.get("selected_policy", "unknown"),
        "heuristic_profile": policy.get("heuristic_profile", "unknown"),
        "model_name": policy.get("model_name"),
        "model_version": policy.get("model_version"),
        "experiment_id": policy.get("experiment_id"),
        "code_version": policy.get("code_version", "unknown"),
    }


def generate_report_md(report: dict) -> str:
    lines = []
    lines.append(f"# Match Report: {report['match_id']}")
    lines.append("")
    lines.append(f"- **Map**: {report['map']}")
    lines.append(f"- **Opponent**: {report['opponent_race']} ({report['opponent_difficulty']})")
    lines.append(f"- **Duration**: {report['duration_seconds']:.0f}s")
    lines.append(f"- **Result**: {report['result']}")
    lines.append(f"- **Max Supply**: {report['max_supply_reached']}")
    lines.append("")

    policy = _normalize_policy(report.get("policy"))
    lines.append("## Policy")
    lines.append(f"- Mode: {policy['mode']}")
    lines.append(f"- Selected policy: {policy['selected_policy']}")
    lines.append(f"- Heuristic profile: {policy['heuristic_profile']}")
    lines.append(f"- Model: {policy['model_name'] or 'unknown'}")
    lines.append(f"- Model version: {policy['model_version'] or 'unknown'}")
    lines.append(f"- Experiment: {policy['experiment_id'] or 'unknown'}")
    lines.append(f"- Code version: {policy['code_version'] or 'unknown'}")
    lines.append("")

    m = report["metrics"]
    lines.append("## Metrics")
    lines.append(f"- Average unspent minerals: {m['avg_unspent_minerals']}")
    lines.append(f"- Average unspent vespene: {m['avg_unspent_vespene']}")
    lines.append(f"- Supply blocks: {m['supply_block_count']}")
    lines.append(f"- Peak workers: {m['peak_workers']}/{m['worker_target']}")
    lines.append("")

    sat_summary = m.get("saturation_summary", [])
    if sat_summary:
        lines.append("## Base Saturation")
        for i, base in enumerate(sat_summary):
            status = base.get("status", "optimal")
            min_act = base.get("actual_mineral_workers", 0)
            min_ideal = base.get("ideal_mineral_workers", 0)
            gas_act = base.get("actual_gas_workers", 0)
            gas_ideal = base.get("ideal_gas_workers", 0)
            idle = base.get("idle_workers_nearby", 0)
            idle_str = f" (Idle: {idle})" if idle > 0 else ""
            lines.append(
                f"- **Base {i + 1}** [{status}]: "
                f"Minerals {min_act}/{min_ideal} "
                f"({int(base.get('mineral_saturation', 0) * 100)}%) | "
                f"Gas {gas_act}/{gas_ideal} "
                f"({int(base.get('gas_saturation', 0) * 100)}%){idle_str}"
            )
        lines.append("")

    events = report.get("key_events", [])
    if events:
        lines.append("## Key Events")
        for e in events:
            lines.append(f"- **{e['time']:.0f}s**: {e['type']} ({e['severity']})")
        lines.append("")

    snaps = report.get("army_snapshots", [])
    if snaps:
        lines.append("## Army Snapshots")
        lines.append("| Time | Our Army | Our Composition | Enemy Visible | Enemy Composition |")
        lines.append("|------|----------|-----------------|---------------|-------------------|")
        for s in snaps:
            our_comp_str = ", ".join(f"{k}: {v}" for k, v in s.get("our_composition", {}).items()) or "none"
            enemy_comp_str = ", ".join(f"{k}: {v}" for k, v in s.get("enemy_composition", {}).items()) or "none"
            lines.append(f"| {s['time']}s | {s['our_army_count']} | {our_comp_str} | {s['enemy_visible']} | {enemy_comp_str} |")

    return "\n".join(lines)


def _sparkline(values: list[float], width: int = 40, max_val: float | None = None) -> str:
    if not values:
        return ""
    if max_val is None:
        max_val = max(values) or 1
    chars = "▁▂▃▄▅▆▇█"
    result = []
    for v in values:
        idx = min(int((v / max_val) * (len(chars) - 1)), len(chars) - 1)
        result.append(chars[idx])
    return "".join(result)


def _render_unit_icon(unit_name: str, size: int = 24) -> str:
    return render_unit_icon_svg(unit_name, size)


def generate_report_html(report: dict) -> str:
    import json as _json

    r = report
    m = r["metrics"]
    snaps = r.get("army_snapshots", [])
    timeline = r.get("timeline", [])

    supply_vals = [t["supply_used"] for t in timeline]
    supply_spark = _sparkline(supply_vals, 50, 200)

    event_ranges = r.get("event_ranges", [])
    timeline_data = r.get("timeline_data", {})
    policy = _normalize_policy(r.get("policy"))

    event_rows = ""
    for er in event_ranges:
        dur_str = f'{er["duration"]:.0f}s' if er["duration"] > 0 else "—"
        icon = "⚠" if er["severity"] == "high" else ("●" if er["severity"] == "medium" else "•")
        event_rows += (
            f'<tr>'
            f'<td>{icon}</td>'
            f'<td class="evt-{er["severity"]}">{er["type"]}</td>'
            f'<td>{er["count"]:,}</td>'
            f'<td>{er["first"]:.0f}s</td>'
            f'<td>{er["last"]:.0f}s</td>'
            f'<td>{dur_str}</td>'
            f'</tr>\n'
        )

    our_rows = ""
    for s in snaps:
        our_comp = s.get("our_composition", {})
        our_parts = []
        for k, v in our_comp.items():
            icon = _render_unit_icon(k, 20)
            our_parts.append(f'{icon} {k}: {v}')
        our_str = " ".join(our_parts) if our_parts else "none"
        our_rows += (
            f'<tr><td>{s["time"]}s</td>'
            f'<td>{s["our_army_count"]}</td>'
            f'<td>{our_str}</td></tr>\n'
        )

    enemy_rows = ""
    for s in snaps:
        enemy_comp = s.get("enemy_composition", {})
        enemy_parts = []
        for k, v in enemy_comp.items():
            icon = _render_unit_icon(k, 20)
            enemy_parts.append(f'{icon} {k}: {v}')
        enemy_str = " ".join(enemy_parts) if enemy_parts else "none"
        enemy_rows += (
            f'<tr><td>{s["time"]}s</td>'
            f'<td>{s["enemy_visible"]}</td>'
            f'<td>{enemy_str}</td></tr>\n'
        )

    sat_rows = ""
    sat_summary = m.get("saturation_summary", [])
    for i, base in enumerate(sat_summary):
        ratio_pct = base["ratio"] * 100
        status = base.get("status", "optimal")
        status_cls = "good" if status == "optimal" else ("bad" if status == "oversaturated" else "warn")
        status_icon = "●" if status == "optimal" else ("▲" if status == "oversaturated" else "▾")
        idle = base.get("idle_workers_nearby", 0)
        idle_str = f' <span class="metric-value warn">Idle: {idle}</span>' if idle > 0 else ""

        min_act = base.get("actual_mineral_workers", 0)
        min_ideal = base.get("ideal_mineral_workers", 0)
        min_sat = base.get("mineral_saturation", 0)
        gas_act = base.get("actual_gas_workers", 0)
        gas_ideal = base.get("ideal_gas_workers", 0)
        gas_sat = base.get("gas_saturation", 0)

        min_bar_w = min(100, int(min(min_sat, 1.0) * 100)) if min_ideal > 0 else 0
        gas_bar_w = min(100, int(min(gas_sat, 1.0) * 100)) if gas_ideal > 0 else 0
        min_over = min_sat > 1.0
        gas_over = gas_sat > 1.0

        sat_rows += (
            f'<div class="metric-card" style="flex:1;min-width:200px;">'
            f'<h3>Base {i + 1} <span class="metric-value {status_cls}">{status_icon} {status}</span>{idle_str}</h3>'
            f'<div style="margin:6px 0;">'
            f'<span class="metric-label">Minerals</span> '
            f'<span class="metric-value {"bad" if min_over else "good"}">{min_act}/{min_ideal}</span>'
            f'<span style="color:#888;font-size:11px;"> ({int(min_sat*100)}%)</span>'
            f'<div style="background:#333;border-radius:3px;height:8px;margin:3px 0;">'
            f'<div style="width:{min_bar_w}%;height:100%;background:{"#e94560" if min_over else "#4ecdc4"};border-radius:3px;"></div>'
            f'</div></div>'
            f'<div style="margin:6px 0;">'
            f'<span class="metric-label">Gas</span> '
            f'<span class="metric-value {"bad" if gas_over else "good"}">{gas_act}/{gas_ideal}</span>'
            f'<span style="color:#888;font-size:11px;"> ({int(gas_sat*100)}%)</span>'
            f'<div style="background:#333;border-radius:3px;height:8px;margin:3px 0;">'
            f'<div style="width:{gas_bar_w}%;height:100%;background:{"#e94560" if gas_over else "#4ecdc4"};border-radius:3px;"></div>'
            f'</div></div>'
            f'</div>\n'
        )

    d3_js = _read_d3_js()
    timeline_json = _json.dumps(timeline_data)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Match Report: {r['match_id']}</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1100px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
h1 {{ color: #e94560; margin-bottom: 4px; }}
h2 {{ color: #f5c542; border-bottom: 1px solid #333; margin-top: 24px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #333; padding: 6px 10px; text-align: left; }}
th {{ background: #16213e; }}
tr:nth-child(even) {{ background: #1f3050; }}
.columns {{ display: flex; gap: 20px; }}
.col {{ flex: 1; }}
.sparkline {{ font-size: 18px; letter-spacing: -1px; }}
.warning {{ color: #f5c542; }}
.subtitle {{ color: #888; font-size: 14px; margin-bottom: 16px; }}
.metric-card {{ background: #16213e; border: 1px solid #333; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px; }}
.metric-card h3 {{ margin: 0 0 10px 0; color: #f5c542; font-size: 14px; }}
.metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 16px; }}
.metric-label {{ color: #888; font-size: 12px; }}
.metric-value {{ font-size: 15px; font-weight: 600; }}
.metric-value.good {{ color: #4ecdc4; }}
.metric-value.bad {{ color: #e94560; }}
.metric-value.warn {{ color: #f5c542; }}
.evt-high {{ color: #e94560; }}
.evt-medium {{ color: #f5c542; }}
.evt-info {{ color: #4a9eff; }}
.timeline-container {{ position: relative; background: #16213e; border: 1px solid #333; border-radius: 6px; overflow: hidden; margin: 10px 0; }}
.timeline-container svg {{ display: block; }}
.tooltip {{ position: absolute; background: #0d0d1a; border: 1px solid #555; border-radius: 4px; padding: 6px 10px; font-size: 12px; pointer-events: none; opacity: 0; transition: opacity 0.15s; z-index: 10; max-width: 280px; }}
</style>
</head>
<body>
	<h1>SC2AI Match Report</h1>
	<p class="subtitle"><strong>Match:</strong> {r['match_id']} | <strong>Map:</strong> {r['map']} | <strong>Result:</strong> {r['result']} | <strong>Duration:</strong> {r['duration_seconds']:.0f}s | <strong>Opponent:</strong> {r['opponent_race']} ({r['opponent_difficulty']})</p>
	<div class="metric-card">
	<h3>Policy</h3>
	<div class="metric-grid">
	<span class="metric-label">Mode</span><span class="metric-value">{policy['mode']}</span>
	<span class="metric-label">Selected policy</span><span class="metric-value">{policy['selected_policy']}</span>
	<span class="metric-label">Heuristic profile</span><span class="metric-value">{policy['heuristic_profile']}</span>
	<span class="metric-label">Model</span><span class="metric-value">{policy['model_name'] or 'unknown'}</span>
	<span class="metric-label">Model version</span><span class="metric-value">{policy['model_version'] or 'unknown'}</span>
	<span class="metric-label">Experiment</span><span class="metric-value">{policy['experiment_id'] or 'unknown'}</span>
	<span class="metric-label">Code version</span><span class="metric-value">{policy['code_version'] or 'unknown'}</span>
	</div>
	</div>
	
<div class="columns">
<div class="col">
<div class="metric-card">
<h3>Economy</h3>
<div class="metric-grid">
<span class="metric-label">Minerals gathered</span><span class="metric-value good">{m['collected_minerals']:,}</span>
<span class="metric-label">Vespene gathered</span><span class="metric-value good">{m['collected_vespene']:,}</span>
<span class="metric-label">Avg unspent minerals</span><span class="metric-value warn">{m['avg_unspent_minerals']:,}</span>
<span class="metric-label">Avg unspent vespene</span><span class="metric-value warn">{m['avg_unspent_vespene']:,}</span>
<span class="metric-label">Mineral efficiency</span><span class="metric-value {'good' if m['mineral_efficiency'] >= 70 else 'bad' if m['mineral_efficiency'] < 40 else 'warn'}">{m['mineral_efficiency']}%</span>
<span class="metric-label">Vespene efficiency</span><span class="metric-value {'good' if m['vespene_efficiency'] >= 70 else 'bad' if m['vespene_efficiency'] < 40 else 'warn'}">{m['vespene_efficiency']}%</span>
<span class="metric-label">Peak workers</span><span class="metric-value">{m['peak_workers']}/{m['worker_target']}</span>
<span class="metric-label">Supply blocks</span><span class="metric-value {'good' if m['supply_block_count'] < 10 else 'bad'}">{m['supply_block_count']:,}</span>
</div>
</div>
</div>
<div class="col">
<div class="metric-card">
<h3>Army</h3>
<div class="metric-grid">
<span class="metric-label">Max supply</span><span class="metric-value">{m['max_supply']}/{m['max_supply_cap']}</span>
<span class="metric-label">Max army size</span><span class="metric-value">{m['max_army_size']}</span>
<span class="metric-label">Army value peak</span><span class="metric-value good">{m['our_army_value_peak']:,}</span>
<span class="metric-label">Enemy army value (visible)</span><span class="metric-value bad">{m['enemy_army_value_peak']:,}</span>
<span class="metric-label">Our T3 units</span><span class="metric-value">{m['our_t3_peak']}</span>
<span class="metric-label">Enemy T3 units</span><span class="metric-value {'good' if m['enemy_t3_peak'] == 0 else 'bad'}">{m['enemy_t3_peak']}</span>
</div>
</div>
</div>
</div>

<h2>Events</h2>
<table>
<tr><th></th><th>Event</th><th>Count</th><th>First</th><th>Last</th><th>Duration</th></tr>
{event_rows if event_rows else '<tr><td colspan="6">No events recorded</td></tr>'}
</table>

<h2>Timeline</h2>
<div class="timeline-container" id="timeline"></div>

<h2>Supply</h2>
<p class="sparkline">Supply (0–200): {supply_spark}</p>
<p>Max supply reached: {r['max_supply_reached']}/{m['max_supply_cap']} | Workers: {m['peak_workers']}/{m['worker_target']}</p>

<div class="columns">
<div class="col">
<h2>Our Army</h2>
<table>
<tr><th>Time</th><th>Units</th><th>Composition</th></tr>
{our_rows}
</table>
</div>
<div class="col">
<h2>Enemy Army</h2>
<table>
<tr><th>Time</th><th>Units</th><th>Composition</th></tr>
{enemy_rows}
</table>
</div>
</div>

<h2>Base Saturation</h2>
<div style="display:flex;gap:16px;flex-wrap:wrap;">
{sat_rows if sat_rows else '<p style="color:#888;">No base data available</p>'}
</div>

<script>{d3_js}</script>
<script>
(function() {{
  var data = {timeline_json};
  if (!data || (!data.ranges.length && !data.points.length)) {{
    document.getElementById("timeline").innerHTML = '<p style="padding:20px;color:#888;">No events recorded</p>';
    return;
  }}

  var SEVERITY_COLORS = {{ high: "#e94560", medium: "#f5c542", info: "#4a9eff" }};
  var MARGIN = {{ top: 10, right: 20, bottom: 30, left: 150 }};
  var container = document.getElementById("timeline");
  var W = container.clientWidth;
  var H = 280;
  var width = W - MARGIN.left - MARGIN.right;
  var height = H - MARGIN.top - MARGIN.bottom;

  var allTypes = [];
  data.ranges.forEach(function(r) {{ if (allTypes.indexOf(r.type) === -1) allTypes.push(r.type); }});
  data.points.forEach(function(p) {{ if (allTypes.indexOf(p.type) === -1) allTypes.push(p.type); }});

  var x = d3.scaleLinear().domain([0, data.duration || 1]).range([0, width]);
  var y = d3.scaleBand().domain(allTypes).range([0, height]).padding(0.3);

  var svg = d3.select("#timeline").append("svg")
    .attr("width", W).attr("height", H)
    .call(d3.zoom().scaleExtent([1, 50]).translateExtent([[0, 0], [W, H]])
      .on("zoom", function(event) {{
        g.attr("transform", event.transform);
      }}));

  var g = svg.append("g").attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")");

  g.append("g").call(d3.axisLeft(y).tickSize(0).tickPadding(6))
    .selectAll("text").attr("fill", "#ccc").style("font-size", "11px");

  g.append("g").attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).ticks(10).tickFormat(function(d) {{ return d + "s"; }}))
    .selectAll("text").attr("fill", "#888").style("font-size", "10px");

  var tooltip = d3.select("#timeline").append("div")
    .attr("class", "tooltip");

  var laneHeight = y.bandwidth();

  data.ranges.forEach(function(r) {{
    var yPos = y(r.type);
    if (yPos === undefined) return;
    g.append("rect")
      .attr("x", x(r.start))
      .attr("y", yPos)
      .attr("width", function() {{ var w = x(r.end) - x(r.start); return Math.max(w, 2); }})
      .attr("height", laneHeight)
      .attr("fill", SEVERITY_COLORS[r.severity] || "#666")
      .attr("rx", 2).attr("ry", 2)
      .attr("opacity", 0.85)
      .on("mouseover", function(event) {{
        tooltip.style("opacity", 1)
          .html("<strong>" + r.type + "</strong><br>"
            + "Count: " + r.count.toLocaleString() + "<br>"
            + "Time: " + r.start.toFixed(1) + "s – " + r.end.toFixed(1) + "s<br>"
            + "Duration: " + (r.end - r.start).toFixed(1) + "s<br>"
            + "Severity: " + r.severity)
          .style("left", (event.offsetX + 12) + "px")
          .style("top", (event.offsetY - 10) + "px");
      }})
      .on("mousemove", function(event) {{
        tooltip.style("left", (event.offsetX + 12) + "px")
          .style("top", (event.offsetY - 10) + "px");
      }})
      .on("mouseout", function() {{ tooltip.style("opacity", 0); }});
  }});

  data.points.forEach(function(p) {{
    var yPos = y(p.type);
    if (yPos === undefined) return;
    g.append("circle")
      .attr("cx", x(p.time))
      .attr("cy", yPos + laneHeight / 2)
      .attr("r", 5)
      .attr("fill", SEVERITY_COLORS[p.severity] || "#4a9eff")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .on("mouseover", function(event) {{
        tooltip.style("opacity", 1)
          .html("<strong>" + p.type + "</strong><br>"
            + "Time: " + p.time.toFixed(1) + "s<br>"
            + "Severity: " + p.severity)
          .style("left", (event.offsetX + 12) + "px")
          .style("top", (event.offsetY - 10) + "px");
      }})
      .on("mousemove", function(event) {{
        tooltip.style("left", (event.offsetX + 12) + "px")
          .style("top", (event.offsetY - 10) + "px");
      }})
      .on("mouseout", function() {{ tooltip.style("opacity", 0); }});
  }});
}})();
</script>
</body>
</html>"""


def generate_report(
    match_dir: str,
    match_id: str,
    features: list[dict],
    events: list[dict],
    bot_info: dict | None = None,
) -> None:
    report = generate_report_json(match_id, features, events, bot_info)

    json_path = os.path.join(match_dir, "report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    md_path = os.path.join(match_dir, "report.md")
    with open(md_path, "w") as f:
        f.write(generate_report_md(report))

    html_path = os.path.join(match_dir, "report.html")
    with open(html_path, "w") as f:
        f.write(generate_report_html(report))


def generate_index(project_root: str) -> None:
    reports_dir = os.path.join(project_root, "reports")
    if not os.path.isdir(reports_dir):
        return

    rows = ""
    for entry in sorted(os.listdir(reports_dir), reverse=True):
        match_dir = os.path.join(reports_dir, entry)
        if not os.path.isdir(match_dir):
            continue
        report_path = os.path.join(match_dir, "report.json")
        if not os.path.isfile(report_path):
            continue
        try:
            with open(report_path) as f:
                r = json.load(f)
            policy = _normalize_policy(r.get("policy"))
            rows += (
                f'<tr>'
                f'<td><a href="{entry}/report.html">{entry}</a></td>'
                f'<td>{r.get("map", "?")}</td>'
                f'<td>{r.get("result", "?")}</td>'
                f'<td>{r.get("duration_seconds", 0):.0f}s</td>'
                f'<td>{r.get("max_supply_reached", 0)}</td>'
                f'<td>{policy["mode"]}</td>'
                f'<td>{policy["selected_policy"]}</td>'
                f'<td>{policy["heuristic_profile"]}</td>'
                f'<td>{policy["model_name"] or "unknown"}</td>'
                f'<td>{policy["model_version"] or "unknown"}</td>'
                f'<td>{policy["experiment_id"] or "unknown"}</td>'
                f'</tr>\n'
            )
        except (json.JSONDecodeError, KeyError):
            continue

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>SC2AI — Match Reports</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
h1 {{ color: #e94560; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #333; padding: 8px 12px; text-align: left; }}
th {{ background: #16213e; }}
tr:nth-child(even) {{ background: #1f3050; }}
a {{ color: #f5c542; }}
</style>
</head>
<body>
<h1>SC2AI — Match Reports</h1>
<table>
	<tr><th>Date</th><th>Map</th><th>Result</th><th>Duration</th><th>Max Supply</th><th>Policy</th><th>Selected</th><th>Profile</th><th>Model</th><th>Model Version</th><th>Experiment</th></tr>
{rows}
</table>
<p>{len(rows.splitlines())} matches recorded.</p>
</body>
</html>"""

    index_path = os.path.join(reports_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(html)
