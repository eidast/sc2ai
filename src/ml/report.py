import json
import os
from datetime import datetime


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


def _compute_metrics(features: list[dict], events: list[dict]) -> dict:
    if not features:
        return {}

    total_minerals = sum(f.get("minerals", 0) for f in features)
    total_vespene = sum(f.get("vespene", 0) for f in features)
    n = len(features)

    supply_blocks = [
        {"time": e["time"], "duration_steps": 1}
        for e in events if e.get("type") == "supply_block"
    ]

    worker_counts = [f.get("worker_count", 0) for f in features]
    peak_workers = max(worker_counts) if worker_counts else 0

    last_bases = features[-1].get("bases", []) if features else []
    saturation_summary = [
        {
            "current": b.get("current_workers", 0),
            "ideal": b.get("ideal_workers", 0),
            "ratio": b.get("saturation_ratio", 0),
        }
        for b in last_bases
    ]

    return {
        "avg_unspent_minerals": round(total_minerals / n, 1),
        "avg_unspent_vespene": round(total_vespene / n, 1),
        "supply_blocks": supply_blocks,
        "supply_block_count": len(supply_blocks),
        "peak_workers": peak_workers,
        "worker_target": 70,
        "total_steps": n,
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


def generate_report_json(
    match_id: str,
    features: list[dict],
    events: list[dict],
    bot_info: dict | None = None,
) -> dict:
    metrics = _compute_metrics(features, events)
    timeline = _build_timeline(features)
    army_snapshots = _build_army_snapshots(features)

    return {
        "match_id": match_id,
        "map": bot_info.get("map", "unknown") if bot_info else "unknown",
        "opponent_race": bot_info.get("opponent_race", "unknown") if bot_info else "unknown",
        "opponent_difficulty": bot_info.get("opponent_difficulty", "unknown") if bot_info else "unknown",
        "our_race": "Protoss",
        "duration_seconds": features[-1].get("game_time_seconds", 0) if features else 0,
        "result": bot_info.get("result", "unknown") if bot_info else "unknown",
        "max_supply_reached": max((f.get("supply_used", 0) for f in features), default=0),
        "timeline": timeline,
        "army_snapshots": army_snapshots,
        "metrics": metrics,
        "key_events": [
            {
                "time": e.get("time", 0),
                "type": e.get("type", "unknown"),
                "severity": e.get("severity", "info"),
            }
            for e in events
        ],
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

    m = report["metrics"]
    lines.append("## Metrics")
    lines.append(f"- Average unspent minerals: {m['avg_unspent_minerals']}")
    lines.append(f"- Average unspent vespene: {m['avg_unspent_vespene']}")
    lines.append(f"- Supply blocks: {m['supply_block_count']}")
    lines.append(f"- Peak workers: {m['peak_workers']}/{m['worker_target']}")
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


def generate_report_html(report: dict) -> str:
    r = report
    m = r["metrics"]
    events = r.get("key_events", [])
    snaps = r.get("army_snapshots", [])
    timeline = r.get("timeline", [])

    supply_vals = [t["supply_used"] for t in timeline]
    supply_spark = _sparkline(supply_vals, 50, 200)

    event_html = ""
    for e in events:
        icon = "⚠" if e["severity"] == "high" else "•"
        event_html += (
            f'<tr><td>{icon}</td>'
            f'<td>{e["time"]:.0f}s</td>'
            f'<td>{e["type"]}</td>'
            f'<td>{e["severity"]}</td></tr>\n'
        )

    our_rows = ""
    for s in snaps:
        our_comp = s.get("our_composition", {})
        our_str = ", ".join(f"{k}: {v}" for k, v in our_comp.items()) if our_comp else "none"
        our_rows += (
            f'<tr><td>{s["time"]}s</td>'
            f'<td>{s["our_army_count"]}</td>'
            f'<td>{our_str}</td></tr>\n'
        )

    enemy_rows = ""
    for s in snaps:
        enemy_comp = s.get("enemy_composition", {})
        enemy_str = ", ".join(f"{k}: {v}" for k, v in enemy_comp.items()) if enemy_comp else "none"
        enemy_rows += (
            f'<tr><td>{s["time"]}s</td>'
            f'<td>{s["enemy_visible"]}</td>'
            f'<td>{enemy_str}</td></tr>\n'
        )

    sat_rows = ""
    sat_summary = m.get("saturation_summary", [])
    for i, base in enumerate(sat_summary):
        ratio_pct = base["ratio"] * 100
        sat_rows += (
            f'<tr><td>Base {i + 1}</td>'
            f'<td>{base["current"]}/{base["ideal"]}</td>'
            f'<td>{ratio_pct:.0f}%</td></tr>\n'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Match Report: {r['match_id']}</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
h1 {{ color: #e94560; }}
h2 {{ color: #f5c542; border-bottom: 1px solid #333; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #333; padding: 6px 10px; text-align: left; }}
th {{ background: #16213e; }}
tr:nth-child(even) {{ background: #1f3050; }}
.columns {{ display: flex; gap: 20px; }}
.col {{ flex: 1; }}
.sparkline {{ font-size: 18px; letter-spacing: -1px; }}
.warning {{ color: #f5c542; }}
</style>
</head>
<body>
<h1>SC2AI Match Report</h1>
<p><strong>Match:</strong> {r['match_id']} | <strong>Map:</strong> {r['map']} | <strong>Result:</strong> {r['result']} | <strong>Duration:</strong> {r['duration_seconds']:.0f}s</p>

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
<table>
<tr><th>Base</th><th>Workers</th><th>Saturation</th></tr>
{sat_rows if sat_rows else '<tr><td colspan="3">No base data available</td></tr>'}
</table>

<h2>Supply</h2>
<p class="sparkline">Supply (0–200): {supply_spark}</p>
<p>Max supply reached: {r['max_supply_reached']}/200 | Workers: {m['peak_workers']}/{m['worker_target']}</p>

<h2>Events</h2>
<table>
<tr><th></th><th>Time</th><th>Event</th><th>Severity</th></tr>
{event_html}
</table>

<h2>Metrics</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Average unspent minerals</td><td>{m['avg_unspent_minerals']}</td></tr>
<tr><td>Average unspent vespene</td><td>{m['avg_unspent_vespene']}</td></tr>
<tr><td>Supply blocks</td><td class="warning">{m['supply_block_count']}</td></tr>
<tr><td>Peak workers</td><td>{m['peak_workers']}/{m['worker_target']}</td></tr>
</table>
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
            rows += (
                f'<tr>'
                f'<td><a href="{entry}/report.html">{entry}</a></td>'
                f'<td>{r.get("map", "?")}</td>'
                f'<td>{r.get("result", "?")}</td>'
                f'<td>{r.get("duration_seconds", 0):.0f}s</td>'
                f'<td>{r.get("max_supply_reached", 0)}</td>'
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
<tr><th>Date</th><th>Map</th><th>Result</th><th>Duration</th><th>Max Supply</th></tr>
{rows}
</table>
<p>{len(rows.splitlines())} matches recorded.</p>
</body>
</html>"""

    index_path = os.path.join(reports_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(html)
