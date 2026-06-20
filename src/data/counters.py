from src.data.units import get_unit_info, get_units_by_race


def _effective_damage(our_unit_name: str, enemy_unit_name: str) -> float:
    our_info = get_unit_info(our_unit_name)
    enemy_info = get_unit_info(enemy_unit_name)
    if not our_info or not enemy_info:
        return 0.0

    total = 0.0
    enemy_attrs = set(enemy_info.get("attributes", []))

    for attack in our_info.get("attacks", []):
        base = attack["damage"]
        bonus = 0.0
        for attr, bonus_dmg in attack.get("bonus", {}).items():
            if attr in enemy_attrs:
                bonus += bonus_dmg
        speed = max(attack.get("speed", 1.0), 0.1)
        dps = (base + bonus) / speed
        total += dps

    return total


def compute_counters(enemy_comp: dict[str, int], race: str = "Protoss") -> dict[str, float]:
    if not enemy_comp:
        return {}

    our_units = get_units_by_race(race)
    our_combat_units = [
        name for name in our_units
        if (info := get_unit_info(name)) and info.get("attacks")
        and name not in ("PROBE", "DRONE", "SCV")
    ]

    scores: dict[str, float] = {}
    for our_unit in our_combat_units:
        score = 0.0
        for enemy_name, count in enemy_comp.items():
            dmg = _effective_damage(our_unit, enemy_name)
            score += dmg * count
        if score > 0:
            scores[our_unit] = round(score, 1)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def compute_threat_assessment(enemy_comp: dict[str, int]) -> dict[str, float]:
    if not enemy_comp:
        return {}

    threat: dict[str, float] = {}
    for enemy_name, count in enemy_comp.items():
        info = get_unit_info(enemy_name)
        if not info:
            continue
        hp = info["hp"] + info["shields"]
        dps = 0.0
        for attack in info.get("attacks", []):
            speed = max(attack.get("speed", 1.0), 0.1)
            dps += attack["damage"] / speed
        threat[enemy_name] = round(hp * count + dps * count * 10, 1)

    return dict(sorted(threat.items(), key=lambda x: x[1], reverse=True))
