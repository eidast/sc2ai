"""Analyze shadow decision records from a match.

Usage: uv run python scripts/analyze_shadows.py <match_id> [--format json|text]
"""

import argparse
import json
import sys
from pathlib import Path


def _load_jsonl(path: str) -> list[dict]:
    records = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _compute_overview(decisions: list[dict], features_count: int) -> dict:
    total = len(decisions)
    if total == 0:
        return {"total_steps": 0, "game_time": 0, "result": "unknown"}

    game_time = decisions[-1].get("time", 0)

    states = {}
    for d in decisions:
        s = d.get("strategic_state", "unknown")
        states[s] = states.get(s, 0) + 1
    state_pcts = {k: round(v / total * 100, 1) for k, v in states.items()}

    overrides = sum(1 for d in decisions if d.get("override_source", "none") != "none")
    override_rate = round(overrides / total * 100, 1) if total else 0

    return {
        "total_steps": total,
        "game_time": round(game_time, 1),
        "strategic_states": state_pcts,
        "override_rate": override_rate,
        "features_count": features_count,
    }


def _compute_agreement(decisions: list[dict]) -> dict:
    profiles = set()
    for d in decisions:
        for sp in d.get("shadow_predictions", []):
            profiles.add(sp.get("profile", "unknown"))
        rec = d.get("utility", {}).get("recommended_action")
        if rec and rec.get("target"):
            profiles.add(d.get("heuristic_profile", "heuristic"))

    profiles = sorted(profiles)
    if len(profiles) <= 1:
        return {"profiles": profiles, "matrix": {}}

    heuristic_name = None
    for d in decisions:
        hn = d.get("heuristic_profile", None)
        if hn:
            heuristic_name = hn
            break

    pair_counts = {}
    pair_agreements = {}
    for p1 in profiles:
        for p2 in profiles:
            key = f"{p1}|{p2}"
            pair_counts[key] = 0
            pair_agreements[key] = 0

    for d in decisions:
        targets = {}
        utility_rec = d.get("utility", {}).get("recommended_action")
        if utility_rec and utility_rec.get("target"):
            targets[heuristic_name or "heuristic"] = utility_rec["target"]
        for sp in d.get("shadow_predictions", []):
            rec = sp.get("recommended_action")
            if rec and rec.get("target"):
                targets[sp.get("profile", "unknown")] = rec["target"]

        for p1 in profiles:
            for p2 in profiles:
                key = f"{p1}|{p2}"
                t1 = targets.get(p1)
                t2 = targets.get(p2)
                if t1 and t2:
                    pair_counts[key] += 1
                    if t1 == t2:
                        pair_agreements[key] += 1

    matrix = {}
    for p1 in profiles:
        row = {}
        for p2 in profiles:
            key = f"{p1}|{p2}"
            if pair_counts[key] > 0:
                row[p2] = round(pair_agreements[key] / pair_counts[key] * 100, 1)
            else:
                row[p2] = None
        matrix[p1] = row

    return {"profiles": profiles, "matrix": matrix}


def _compute_action_distribution(decisions: list[dict]) -> dict:
    profile_actions = {}

    for d in decisions:
        utility_rec = d.get("utility", {}).get("recommended_action")
        hn = d.get("heuristic_profile", "heuristic")
        if utility_rec and utility_rec.get("target"):
            profile_actions.setdefault(hn, []).append(utility_rec)
        for sp in d.get("shadow_predictions", []):
            rec = sp.get("recommended_action")
            if rec and rec.get("target"):
                profile_actions.setdefault(sp.get("profile", "unknown"), []).append(rec)

    results = {}
    for profile, actions in profile_actions.items():
        counts = {}
        scores = {}
        for a in actions:
            t = a["target"]
            counts[t] = counts.get(t, 0) + 1
            scores.setdefault(t, []).append(a["score"])
        top = sorted(counts.items(), key=lambda x: -x[1])[:3]
        top_actions = []
        for target, count in top:
            s = scores[target]
            avg = sum(s) / len(s)
            variance = sum((x - avg) ** 2 for x in s) / len(s)
            top_actions.append({
                "target": target,
                "count": count,
                "pct": round(count / len(actions) * 100, 1),
                "avg_score": round(avg, 3),
                "std_score": round(variance ** 0.5, 3),
            })
        results[profile] = top_actions

    return results


def _compute_bias_evolution(decisions: list[dict]) -> dict:
    first_bias = None
    last_bias = None
    for d in decisions:
        bv = d.get("utility", {}).get("bias_vector")
        if bv and first_bias is None:
            first_bias = bv
        if bv:
            last_bias = bv

    if not first_bias or not last_bias:
        return {}

    results = {}
    for key in first_bias:
        initial = first_bias.get(key, 0)
        final = last_bias.get(key, 0)
        results[key] = {
            "initial": round(initial, 4),
            "final": round(final, 4),
            "delta": round(final - initial, 4),
        }
    return results


def _compute_timeline(decisions: list[dict]) -> list[dict]:
    events = []
    prev_state = None
    prev_override = None
    first_divergence = None

    for d in decisions:
        state = d.get("strategic_state")
        if state and state != prev_state:
            events.append({
                "time": d.get("time", 0),
                "step": d.get("step", 0),
                "event": f"State transition: {prev_state or 'start'} → {state}",
            })
            prev_state = state

        override = d.get("override_source", "none")
        if override != "none" and prev_override == "none":
            events.append({
                "time": d.get("time", 0),
                "step": d.get("step", 0),
                "event": f"Override active: {override}",
            })
        elif override == "none" and prev_override and prev_override != "none":
            events.append({
                "time": d.get("time", 0),
                "step": d.get("step", 0),
                "event": f"Override released: was {prev_override}",
            })
        prev_override = override

        if first_divergence is None:
            sps = d.get("shadow_predictions", [])
            targets = set()
            for sp in sps:
                rec = sp.get("recommended_action")
                if rec and rec.get("target"):
                    targets.add(rec["target"])
            utility_rec = d.get("utility", {}).get("recommended_action")
            if utility_rec and utility_rec.get("target"):
                targets.add(utility_rec["target"])
            if len(targets) > 1:
                first_divergence = {"time": d.get("time", 0), "step": d.get("step", 0)}
                events.append({
                    "time": d.get("time", 0),
                    "step": d.get("step", 0),
                    "event": f"First divergence between profiles (targets: {', '.join(targets)})",
                })

    return events


def _format_text(results: dict) -> str:
    lines = []
    overview = results["overview"]
    lines.append("SHADOW ANALYSIS")
    lines.append(f"  Total steps: {overview['total_steps']}  "
                  f"Game time: {overview['game_time']}s  "
                  f"Override rate: {overview['override_rate']}%")
    states = overview.get("strategic_states", {})
    if states:
        states_str = ", ".join(f"{k}={v}%" for k, v in sorted(states.items()))
        lines.append(f"  Strategic states: {states_str}")

    ag = results["agreement"]
    lines.append("")
    lines.append("AGREEMENT MATRIX (% same target)")
    profiles = ag["profiles"]
    if len(profiles) <= 1:
        lines.append("  Not enough profiles for matrix")
    else:
        header = "           " + "".join(f"{p[:10]:>12}" for p in profiles)
        lines.append(header)
        matrix = ag["matrix"]
        for p1 in profiles:
            row_vals = []
            for p2 in profiles:
                v = matrix.get(p1, {}).get(p2)
                if v is None:
                    row_vals.append("          —")
                else:
                    row_vals.append(f"{v:>10.1f}%")
            lines.append(f"  {p1[:10]:<10}" + "".join(row_vals))

    dist = results["action_distribution"]
    lines.append("")
    lines.append("ACTION DISTRIBUTION (top 3 per profile)")
    for profile, actions in dist.items():
        lines.append(f"  {profile}:")
        for a in actions:
            lines.append(f"    {a['target']:<20} {a['pct']:>5.1f}%  "
                         f"score={a['avg_score']:.3f} ±{a['std_score']:.3f}")

    bias = results.get("bias_evolution", {})
    if bias:
        lines.append("")
        lines.append("BIAS EVOLUTION")
        for key, vals in sorted(bias.items()):
            lines.append(f"  {key:<25} {vals['initial']:.4f} → {vals['final']:.4f}  "
                         f"(Δ{vals['delta']:+.4f})")

    timeline = results.get("timeline", [])
    if timeline:
        lines.append("")
        lines.append("TIMELINE")
        for e in timeline:
            lines.append(f"  t={e['time']:>6.1f}s  step={e['step']:>4d}  {e['event']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze shadow decision records from a match",
    )
    parser.add_argument("match_id", help="Match ID (reports/<match_id>/)")
    parser.add_argument(
        "--format", default="text", choices=["text", "json"],
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--reports-dir", default=None,
        help="Reports directory (default: <project_root>/reports)",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir) if args.reports_dir else (
        Path(__file__).resolve().parent.parent / "reports"
    )
    match_dir = reports_dir / args.match_id

    if not match_dir.is_dir():
        print(f"Error: match directory not found: {match_dir}", file=sys.stderr)
        sys.exit(1)

    decisions_path = match_dir / "decisions.jsonl"
    features_path = match_dir / "features.jsonl"

    try:
        decisions = _load_jsonl(str(decisions_path))
    except FileNotFoundError:
        print(f"Error: decisions.jsonl not found in {match_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        features = _load_jsonl(str(features_path))
    except FileNotFoundError:
        features = []

    results = {
        "overview": _compute_overview(decisions, len(features)),
        "agreement": _compute_agreement(decisions),
        "action_distribution": _compute_action_distribution(decisions),
        "bias_evolution": _compute_bias_evolution(decisions),
        "timeline": _compute_timeline(decisions),
    }

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(_format_text(results))


if __name__ == "__main__":
    main()
