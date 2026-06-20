from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

from src.data.units import get_unit_info
from src.data.counters import compute_threat_assessment, compute_counters


_NON_COMBAT_TYPES = {UnitTypeId.PROBE, UnitTypeId.OBSERVER, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER}

_NON_COMBAT_ENEMY_NAMES = {
    "SCV", "DRONE", "PROBE", "LARVA", "EGG", "MULE",
    "OVERLORD", "OVERSEER", "OBSERVER",
    "CHANGELING", "CHANGELINGMARINE", "CHANGELINGMARINESHIELD",
    "CHANGELINGZEALOT", "CHANGELINGZERGLING", "CHANGELINGZERGLINGWINGS",
}

_WORKER_NAMES = {"SCV", "DRONE", "PROBE"}


def _compute_army_value(composition: dict[str, int]) -> int:
    total = 0
    for name, count in composition.items():
        if name in _NON_COMBAT_ENEMY_NAMES:
            continue
        info = get_unit_info(name)
        if not info:
            continue
        total += (info["mineral_cost"] + info["vespene_cost"]) * count
    return total


def _enrich_enemy_army(enemy_comp: dict[str, int]) -> dict:
    if not enemy_comp:
        return {
            "total_hp": 0,
            "total_shields": 0,
            "armored_count": 0,
            "light_count": 0,
            "biological_count": 0,
            "mechanical_count": 0,
            "massive_count": 0,
            "air_count": 0,
            "ground_dps": 0.0,
            "air_dps": 0.0,
        }

    total_hp = 0
    total_shields = 0
    armored_count = 0
    light_count = 0
    biological_count = 0
    mechanical_count = 0
    massive_count = 0
    air_count = 0
    ground_dps = 0.0
    air_dps = 0.0

    for name, count in enemy_comp.items():
        info = get_unit_info(name)
        if not info:
            continue
        total_hp += info["hp"] * count
        total_shields += info["shields"] * count
        attrs = info.get("attributes", [])
        if "Armored" in attrs:
            armored_count += count
        if "Light" in attrs:
            light_count += count
        if "Biological" in attrs:
            biological_count += count
        if "Mechanical" in attrs:
            mechanical_count += count
        if "Massive" in attrs:
            massive_count += count
        for attack in info.get("attacks", []):
            dps = attack["damage"] / max(attack.get("speed", 1.0), 0.1)
            if attack.get("targets") == "ground":
                ground_dps += dps * count
            elif attack.get("targets") == "air":
                air_dps += dps * count
        if any(a.get("targets") == "air" for a in info.get("attacks", [])):
            air_count += count

    return {
        "total_hp": total_hp,
        "total_shields": total_shields,
        "armored_count": armored_count,
        "light_count": light_count,
        "biological_count": biological_count,
        "mechanical_count": mechanical_count,
        "massive_count": massive_count,
        "air_count": air_count,
        "ground_dps": round(ground_dps, 1),
        "air_dps": round(air_dps, 1),
    }


def extract_features(bot: BotAI) -> dict:
    enemy_composition = {}
    for unit in bot.enemy_units:
        name = unit.type_id.name
        enemy_composition[name] = enemy_composition.get(name, 0) + 1

    our_army_composition = {}
    for unit in bot.units:
        if unit.type_id not in _NON_COMBAT_TYPES:
            name = unit.type_id.name
            our_army_composition[name] = our_army_composition.get(name, 0) + 1

    our_structures = {}
    for structure in bot.structures:
        name = structure.type_id.name
        our_structures[name] = our_structures.get(name, 0) + 1

    bases = _extract_base_features(bot)

    our_army_value = _compute_army_value(our_army_composition)
    enemy_army_value = _compute_army_value(enemy_composition)
    army_value_ratio = our_army_value / max(enemy_army_value, 1)

    from src.bot.strategy import T3_UNITS
    enemy_race_name = bot.enemy_race.name.title() if hasattr(bot, "enemy_race") else None
    enemy_t3_set = T3_UNITS.get(enemy_race_name, set()) if enemy_race_name else set()
    our_t3_set = T3_UNITS.get("Protoss", set())

    enemy_t3_count = sum(
        count for name, count in enemy_composition.items()
        if name in enemy_t3_set and name not in _NON_COMBAT_ENEMY_NAMES
    )
    our_t3_count = sum(
        count for name, count in our_army_composition.items()
        if name in our_t3_set
    )

    enemy_worker_count = sum(
        count for name, count in enemy_composition.items()
        if name in _WORKER_NAMES
    )

    collected_minerals = 0
    collected_vespene = 0
    if hasattr(bot, "state") and bot.state and hasattr(bot.state, "score"):
        collected_minerals = getattr(bot.state.score, "collected_minerals", 0)
        collected_vespene = getattr(bot.state.score, "collected_vespene", 0)

    return {
        "minerals": bot.minerals,
        "vespene": bot.vespene,
        "supply_used": bot.supply_used,
        "supply_cap": bot.supply_cap,
        "supply_left": bot.supply_left,
        "worker_count": bot.workers.amount,
        "army_count": bot.units.exclude_type(
            [
                bot.workers.first.type_id if bot.workers else None,
            ]
        ).amount
        if bot.workers
        else 0,
        "enemy_visible_units": len(bot.enemy_units),
        "enemy_visible_structures": len(bot.enemy_structures),
        "enemy_worker_count": enemy_worker_count,
        "enemy_army_composition": enemy_composition,
        "enemy_army_analysis": _enrich_enemy_army(enemy_composition),
        "enemy_threat_assessment": compute_threat_assessment(enemy_composition),
        "recommended_counters": compute_counters(enemy_composition, race="Protoss"),
        "our_army_composition": our_army_composition,
        "our_structures": our_structures,
        "our_army_value": our_army_value,
        "enemy_army_value": enemy_army_value,
        "army_value_ratio": round(army_value_ratio, 3),
        "enemy_t3_count": enemy_t3_count,
        "our_t3_count": our_t3_count,
        "bases": bases,
        "collected_minerals": collected_minerals,
        "collected_vespene": collected_vespene,
        "game_time_seconds": bot.time,
        "expansion_count": bot.townhalls.amount,
        "iteration": bot.state.game_loop if hasattr(bot, "state") else 0,
    }


def _extract_base_features(bot: BotAI) -> list[dict]:
    from src.bot.strategy import THREAT_RANGE, BASE_MINERAL_RADIUS

    idle_workers = bot.workers.idle
    ready_gas = bot.gas_buildings.ready

    def _nearest_nexus(unit):
        best_dist = float("inf")
        best = None
        for nexus in bot.townhalls:
            d = unit.position.distance_to(nexus.position)
            if d < best_dist:
                best_dist = d
                best = nexus
        return best, best_dist

    idle_by_base: dict[int, int] = {}
    for w in idle_workers:
        nearest, _ = _nearest_nexus(w)
        if nearest:
            idle_by_base[nearest.tag] = idle_by_base.get(nearest.tag, 0) + 1

    bases = []
    for nexus in bot.townhalls:
        minerals_nearby = bot.mineral_field.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        gas_buildings_nearby = ready_gas.closer_than(BASE_MINERAL_RADIUS, nexus.position)
        gas_geysers = gas_buildings_nearby.amount

        ideal_mineral_workers = min(minerals_nearby * 2, 16)
        ideal_gas_workers = gas_geysers * 3
        ideal_workers = ideal_mineral_workers + ideal_gas_workers

        current_workers = getattr(nexus, "assigned_harvesters", 0)

        actual_gas_workers = sum(
            getattr(g, "assigned_harvesters", 0) for g in gas_buildings_nearby
        )
        actual_mineral_workers = max(0, current_workers - actual_gas_workers)

        idle_nearby = idle_by_base.get(nexus.tag, 0)

        mineral_saturation = actual_mineral_workers / ideal_mineral_workers if ideal_mineral_workers > 0 else 1.0
        gas_saturation = actual_gas_workers / ideal_gas_workers if ideal_gas_workers > 0 else 1.0
        total_saturation = current_workers / ideal_workers if ideal_workers > 0 else 1.0

        if mineral_saturation > 1.1 or (gas_saturation > 1.0 and gas_geysers > 0):
            status = "oversaturated"
        elif mineral_saturation < 0.7 or (gas_saturation < 0.5 and gas_geysers > 0):
            status = "undersaturated"
        else:
            status = "optimal"

        army_units = bot.units.exclude_type(_NON_COMBAT_TYPES)
        army_nearby = army_units.closer_than(THREAT_RANGE, nexus.position).amount
        enemy_nearby = bot.enemy_units.closer_than(THREAT_RANGE, nexus.position).amount

        bases.append({
            "position": (nexus.position.x, nexus.position.y),
            "ideal_workers": ideal_workers,
            "current_workers": current_workers,
            "saturation_ratio": round(total_saturation, 3),
            "army_nearby": army_nearby,
            "enemy_nearby": enemy_nearby,
            "mineral_patches": minerals_nearby,
            "gas_geysers": gas_geysers,
            "ideal_mineral_workers": ideal_mineral_workers,
            "ideal_gas_workers": ideal_gas_workers,
            "actual_mineral_workers": actual_mineral_workers,
            "actual_gas_workers": actual_gas_workers,
            "idle_workers_nearby": idle_nearby,
            "mineral_saturation": round(mineral_saturation, 3),
            "gas_saturation": round(gas_saturation, 3),
            "total_saturation": round(total_saturation, 3),
            "status": status,
        })

    return bases


def extract_building_inference(bot) -> dict[str, int]:
    result = {}
    for structure in bot.enemy_structures:
        name = structure.type_id.name
        result[name] = result.get(name, 0) + 1
    return result


def extract_eco_inference(features: dict) -> dict:
    game_time = features.get("game_time_seconds", 0)
    bases_count = features.get("expansion_count", 1)
    enemy_workers = features.get("enemy_worker_count", 0)

    if enemy_workers == 0 and bases_count > 0 and game_time > 60:
        estimated = min(int(game_time * 0.45 * bases_count), 90)
    else:
        estimated = enemy_workers

    gas_count = 0
    building_inference = features.get("building_inference", {})
    for name, count in building_inference.items():
        if "ASSIMILATOR" in name.upper() or "EXTRACTOR" in name.upper() or "REFINERY" in name.upper():
            gas_count += count

    return {
        "bases_count": building_inference.get("TOWNHALL", 0)
        or building_inference.get("HATCHERY", 0)
        or building_inference.get("COMMANDCENTER", 0)
        or 1,
        "gas_count": gas_count,
        "estimated_workers": estimated,
    }
