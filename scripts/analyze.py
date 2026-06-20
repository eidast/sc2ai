import json
import os
import sys


REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

_NON_COMBAT_ENEMY_NAMES = {
    "SCV", "DRONE", "PROBE", "LARVA", "EGG", "MULE",
    "OVERLORD", "OVERSEER", "OBSERVER",
    "CHANGELING", "CHANGELINGMARINE", "CHANGELINGMARINESHIELD",
    "CHANGELINGZEALOT", "CHANGELINGZERGLING", "CHANGELINGZERGLINGWINGS",
}

T3_UNITS = {
    "Protoss": {"COLOSSUS", "CARRIER", "TEMPEST", "MOTHERSHIP", "VOIDRAY", "IMMORTAL"},
    "Terran": {"BATTLECRUISER", "THOR", "SIEGETANK", "SIEGETANKSIEGED",
               "LIBERATOR", "LIBERATORAG", "BANSHEE", "GHOST", "RAVEN"},
    "Zerg": {"BROODLORD", "ULTRALISK", "CORRUPTOR", "MUTALISK",
             "LURKER", "VIPER", "SWARMHOSTMP", "INFESTOR"},
}

_system_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, _system_src)
from data.units import get_unit_info  # noqa: E402


def _army_value(comp: dict[str, int]) -> int:
    total = 0
    for name, count in comp.items():
        if name in _NON_COMBAT_ENEMY_NAMES:
            continue
        info = get_unit_info(name)
        if not info:
            continue
        total += (info["mineral_cost"] + info["vespene_cost"]) * count
    return total


def _t3_count(comp: dict[str, int], race: str) -> int:
    t3_set = T3_UNITS.get(race.title(), set())
    return sum(c for n, c in comp.items() if n in t3_set and n not in _NON_COMBAT_ENEMY_NAMES)


def analyze():
    if not os.path.isdir(REPORTS_DIR):
        print("No reports directory found.")
        return

    matches = []
    for entry in sorted(os.listdir(REPORTS_DIR)):
        match_dir = os.path.join(REPORTS_DIR, entry)
        if not os.path.isdir(match_dir):
            continue
        features_path = os.path.join(match_dir, "features.jsonl")
        report_path = os.path.join(match_dir, "report.json")
        if not os.path.isfile(features_path):
            continue

        features = []
        try:
            with open(features_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        features.append(json.loads(line))
        except (json.JSONDecodeError, IOError):
            continue

        if not features:
            continue

        report = {}
        if os.path.isfile(report_path):
            try:
                with open(report_path) as f:
                    report = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        times = []
        ratios = []
        t3_times = []
        death_spiral_time = None

        for feat in features:
            t = feat.get("game_time_seconds", 0)
            comp = feat.get("enemy_army_composition", {})

            our_av_raw = feat.get("our_army_value")
            enemy_av_raw = feat.get("enemy_army_value")

            if our_av_raw is not None and enemy_av_raw is not None:
                av_ratio = feat.get("army_value_ratio", 0)
            else:
                our_av = _army_value(feat.get("our_army_composition", {}))
                enemy_av = _army_value(comp)
                av_ratio = our_av / max(enemy_av, 1)

            times.append(t)
            ratios.append(av_ratio)

            race = report.get("opponent_race", "Terran")
            enemy_t3 = feat.get("enemy_t3_count")
            if enemy_t3 is None:
                enemy_t3 = _t3_count(comp, race)
            if enemy_t3 > 0 and not t3_times:
                t3_times.append(t)

            if death_spiral_time is None and t > 180 and av_ratio < 0.3:
                death_spiral_time = t

        result = report.get("result", "unknown")
        duration = report.get("duration_seconds", times[-1] if times else 0)
        max_supply = report.get("max_supply_reached", 0)

        min_ratio = min(ratios) if ratios else 0
        start_ratio = ratios[0] if ratios else 0
        end_ratio = ratios[-1] if ratios else 0

        matches.append({
            "id": entry,
            "result": result,
            "duration": duration,
            "max_supply": max_supply,
            "min_ratio": min_ratio,
            "start_ratio": start_ratio,
            "end_ratio": end_ratio,
            "death_spiral": death_spiral_time,
            "t3_detected": t3_times[0] if t3_times else None,
        })

    print(f"{'Match ID':<20} {'Result':<10} {'Dur(s)':<8} {'MaxSup':<8} {'MinAVR':<10} {'Death@':<10} {'T3@':<10}")
    print("-" * 86)
    for m in matches:
        ds = f"{m['death_spiral']:.0f}s" if m['death_spiral'] else "-"
        t3 = f"{m['t3_detected']:.0f}s" if m['t3_detected'] else "-"
        print(f"{m['id']:<20} {m['result']:<10} {m['duration']:<8.0f} {m['max_supply']:<8} {m['min_ratio']:<10.3f} {ds:<10} {t3:<10}")

    print(f"\n{len(matches)} matches analyzed.\n")

    if matches:
        defeats = [m for m in matches if m["result"] == "defeat"]
        if defeats:
            avg_death = sum(m["death_spiral"] or m["duration"] for m in defeats) / len(defeats)
            print(f"Recommendations:")
            print(f"  Average death spiral start: {avg_death:.0f}s")
            print(f"  Suggested SURRENDER_MIN_TIME: {max(300, avg_death * 0.5):.0f}s")
            print(f"  Suggested attack windows: before death spiral starts")

            t3_matches = [m for m in defeats if m["t3_detected"]]
            if t3_matches:
                avg_t3 = sum(m["t3_detected"] for m in t3_matches) / len(t3_matches)
                print(f"  Average T3 detection: {avg_t3:.0f}s — attack BEFORE this time")


if __name__ == "__main__":
    analyze()
