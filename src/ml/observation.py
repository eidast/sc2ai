from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId


_NON_COMBAT_TYPES = {UnitTypeId.PROBE, UnitTypeId.OBSERVER, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER}


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
        "enemy_army_composition": enemy_composition,
        "our_army_composition": our_army_composition,
        "our_structures": our_structures,
        "bases": bases,
        "game_time_seconds": bot.time,
        "expansion_count": bot.townhalls.amount,
        "iteration": bot.state.game_loop if hasattr(bot, "state") else 0,
    }


def _extract_base_features(bot: BotAI) -> list[dict]:
    from src.bot.strategy import THREAT_RANGE, BASE_MINERAL_RADIUS

    bases = []
    for nexus in bot.townhalls:
        minerals_nearby = bot.mineral_field.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        gas_nearby = bot.gas_buildings.closer_than(BASE_MINERAL_RADIUS, nexus.position).amount
        ideal_workers = minerals_nearby * 2 + gas_nearby * 3
        current_workers = getattr(nexus, "assigned_harvesters", 0)
        saturation_ratio = current_workers / ideal_workers if ideal_workers > 0 else 1.0

        army_units = bot.units.exclude_type(_NON_COMBAT_TYPES)
        army_nearby = army_units.closer_than(THREAT_RANGE, nexus.position).amount
        enemy_nearby = bot.enemy_units.closer_than(THREAT_RANGE, nexus.position).amount

        bases.append({
            "position": (nexus.position.x, nexus.position.y),
            "ideal_workers": ideal_workers,
            "current_workers": current_workers,
            "saturation_ratio": round(saturation_ratio, 3),
            "army_nearby": army_nearby,
            "enemy_nearby": enemy_nearby,
        })

    return bases
