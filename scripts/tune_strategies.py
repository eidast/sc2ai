"""Auto-tuner: analyzes historical match data and adjusts YAML strategy biases."""

import json
import math
import sys
from pathlib import Path

import yaml


def load_match_results(reports_dir: Path) -> list[dict]:
    matches = []
    for match_dir in sorted(reports_dir.iterdir()):
        if not match_dir.is_dir():
            continue
        report_json = match_dir / "report.json"
        features_jsonl = match_dir / "features.jsonl"
        if not report_json.exists() or not features_jsonl.exists():
            continue
        with open(report_json) as f:
            report = json.load(f)
        result = report.get("result", "unknown")
        opponent = report.get("opponent_race", "unknown")
        duration = report.get("duration_seconds", 0)

        features = []
        with open(features_jsonl) as f:
            for line in f:
                features.append(json.loads(line))

        if not features:
            continue

        max_workers = max(f.get("worker_count", 0) for f in features)
        max_army = max(f.get("army_count", 0) for f in features)
        max_supply = max(f.get("supply_used", 0) for f in features)
        avg_unspent_mins = sum(f.get("minerals", 0) for f in features) / len(features)
        avg_unspent_gas = sum(f.get("vespene", 0) for f in features) / len(features)

        peak_gates = 0
        peak_robo = 0
        peak_sg = 0
        for f in features:
            s = f.get("our_structures", {})
            peak_gates = max(peak_gates, s.get("GATEWAY", 0) + s.get("WARPGATE", 0))
            peak_robo = max(peak_robo, s.get("ROBOTICSFACILITY", 0))
            peak_sg = max(peak_sg, s.get("STARGATE", 0))

        army_at_5m = 0
        army_at_10m = 0
        for f in features:
            t = f.get("game_time_seconds", 0)
            if abs(t - 300) < 15:
                army_at_5m = max(army_at_5m, f.get("army_count", 0))
            if abs(t - 600) < 15:
                army_at_10m = max(army_at_10m, f.get("army_count", 0))

        matches.append({
            "match_id": match_dir.name,
            "result": result,
            "opponent": opponent,
            "duration": duration,
            "max_workers": max_workers,
            "max_army": max_army,
            "max_supply": max_supply,
            "avg_unspent_mins": avg_unspent_mins,
            "avg_unspent_gas": avg_unspent_gas,
            "peak_gates": peak_gates,
            "peak_robo": peak_robo,
            "peak_stargate": peak_sg,
            "army_at_5m": army_at_5m,
            "army_at_10m": army_at_10m,
        })
    return matches


def analyze(matches: list[dict]) -> dict:
    wins = [m for m in matches if m["result"] == "victory"]
    losses = [m for m in matches if m["result"] == "defeat"]

    def avg(lst, key):
        vals = [m[key] for m in lst]
        return sum(vals) / len(vals) if vals else 0

    analysis = {
        "total_games": len(matches),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(matches) if matches else 0,
    }

    for race in sorted({m["opponent"] for m in matches}):
        rw = [m for m in wins if m["opponent"] == race]
        rl = [m for m in losses if m["opponent"] == race]
        analysis[f"vs_{race}"] = {
            "wins": len(rw),
            "losses": len(rl),
            "win_avg_army_5m": avg(rw, "army_at_5m"),
            "loss_avg_army_5m": avg(rl, "army_at_5m"),
            "win_avg_workers": avg(rw, "max_workers"),
            "loss_avg_workers": avg(rl, "max_workers"),
            "win_avg_gates": avg(rw, "peak_gates"),
            "loss_avg_gates": avg(rl, "peak_gates"),
            "win_avg_robo": avg(rw, "peak_robo"),
            "loss_avg_robo": avg(rl, "peak_robo"),
            "win_avg_supply": avg(rw, "max_supply"),
            "loss_avg_supply": avg(rl, "max_supply"),
        }

    return analysis


def compute_adjustments(matches: list[dict]) -> dict:
    wins = [m for m in matches if m["result"] == "victory"]
    losses = [m for m in matches if m["result"] == "defeat"]

    if not wins or not losses:
        return {"gateway_units": 0.0, "robo_units": 0.0, "stargate_units": 0.0}

    win_army_5m = sum(m["army_at_5m"] for m in wins) / len(wins)
    loss_army_5m = sum(m["army_at_5m"] for m in losses) / len(losses)

    win_gates = sum(m["peak_gates"] for m in wins) / len(wins)
    loss_gates = sum(m["peak_gates"] for m in losses) / len(losses)
    win_robo = sum(m["peak_robo"] for m in wins) / len(wins)
    loss_robo = sum(m["peak_robo"] for m in losses) / len(losses)

    adj = {}

    if loss_army_5m < 5 and win_army_5m > 5:
        adj["gateway_units"] = +0.10
    if loss_gates < win_gates * 0.5:
        adj["gateway_units"] = adj.get("gateway_units", 0) + 0.05

    if loss_robo > win_robo * 1.5:
        adj["robo_units"] = -0.10

    if win_robo > 2 and loss_robo < 2:
        adj["robo_units"] = adj.get("robo_units", 0) + 0.05

    return adj


def tune_profile(profile_path: Path, matches: list[dict]) -> dict:
    with open(profile_path) as f:
        profile = yaml.safe_load(f)

    adj = compute_adjustments(matches)
    if not adj:
        return profile

    biases = profile.get("initial_biases", {})
    for key, delta in adj.items():
        old = biases.get(key, 0.5)
        new = max(0.0, min(1.0, old + delta))
        biases[key] = round(new, 2)
        print(f"  {key}: {old:.2f} → {new:.2f} ({delta:+.2f})")

    profile["initial_biases"] = biases
    return profile


def run(reports_dir: Path, yaml_dir: Path, profile_name: str = "standard_macro"):
    print(f"Analyzing {reports_dir}...")
    matches = load_match_results(reports_dir)
    print(f"  Found {len(matches)} matches")

    analysis = analyze(matches)
    print(f"  Win rate: {analysis['win_rate']:.0%} ({analysis['wins']}W/{analysis['losses']}L)")

    for key, val in analysis.items():
        if key.startswith("vs_"):
            print(f"  {key}: W={val['wins']} L={val['losses']} "
                  f"army_5m(W)={val['win_avg_army_5m']:.0f} army_5m(L)={val['loss_avg_army_5m']:.0f} "
                  f"gates(W)={val['win_avg_gates']:.0f} gates(L)={val['loss_avg_gates']:.0f} "
                  f"robo(W)={val['win_avg_robo']:.0f} robo(L)={val['loss_avg_robo']:.0f}")

    profile_path = yaml_dir / "protoss" / f"{profile_name}.yaml"
    if not profile_path.exists():
        print(f"  Profile not found: {profile_path}")
        return

    print(f"\nTuning {profile_path}...")
    tuned = tune_profile(profile_path, matches)

    backup = profile_path.with_suffix(".yaml.bak")
    with open(backup, "w") as f:
        yaml.dump(yaml.safe_load(open(profile_path)), f, default_flow_style=False)

    with open(profile_path, "w") as f:
        yaml.dump(tuned, f, default_flow_style=False, sort_keys=False)
    print(f"  Saved to {profile_path} (backup: {backup})")


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    yaml_dir = project_root / "src" / "data" / "strategies"
    run(reports_dir, yaml_dir)
