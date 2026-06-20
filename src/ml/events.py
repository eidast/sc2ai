from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    type: str
    time: float
    step: int
    severity: str = "info"
    details: dict[str, Any] = field(default_factory=dict)


def detect_events(
    bot: Any,
    features: dict,
    prev_features: dict | None,
    iteration: int,
) -> list[Event]:
    if prev_features is None:
        return [Event(
            type="game_start",
            time=features.get("game_time_seconds", 0),
            step=iteration,
        )]

    events: list[Event] = []
    now = features.get("game_time_seconds", 0)

    if _detect_supply_block(features, bot):
        events.append(Event(
            type="supply_block", time=now, step=iteration,
            severity="high",
            details={"supply_left": features["supply_left"]},
        ))

    push_details = _detect_enemy_push(features, prev_features, bot)
    if push_details:
        events.append(Event(
            type="enemy_push", time=now, step=iteration,
            severity="high",
            details=push_details,
        ))

    if _detect_worker_stalled(features, bot):
        events.append(Event(
            type="worker_stalled", time=now, step=iteration,
            severity="medium",
            details={"worker_count": features["worker_count"]},
        ))

    if _detect_resource_float(features, bot):
        events.append(Event(
            type="resource_float", time=now, step=iteration,
            severity="medium",
            details={"minerals": features["minerals"], "vespene": features["vespene"]},
        ))

    if _detect_tech_milestone(features, bot):
        events.append(Event(
            type="tech_milestone", time=now, step=iteration,
        ))

    if _detect_attack_ready(features, bot):
        events.append(Event(
            type="attack_ready", time=now, step=iteration,
            severity="info",
        ))

    if _detect_expansion_started(features, prev_features):
        events.append(Event(
            type="expansion_started", time=now, step=iteration,
            details={"expansion_count": features["expansion_count"]},
        ))

    if _detect_base_oversaturated(features):
        events.append(Event(
            type="base_oversaturated", time=now, step=iteration,
            severity="medium",
            details={"bases": features.get("bases", [])},
        ))

    if _detect_base_under_attack(features, bot):
        events.append(Event(
            type="base_under_attack", time=now, step=iteration,
            severity="high",
        ))

    return events


def _detect_supply_block(features: dict, bot: Any) -> bool:
    if features.get("supply_left", 0) >= 3:
        return False
    from sc2.ids.unit_typeid import UnitTypeId
    return not bool(bot.already_pending(UnitTypeId.PYLON))


def _detect_enemy_push(features: dict, prev_features: dict, bot: Any) -> dict | None:
    current = features.get("enemy_visible_units", 0)
    previous = prev_features.get("enemy_visible_units", 0)
    delta = current - previous
    if delta <= 10:
        return None

    from src.bot.strategy import THREAT_RANGE
    near_base = False
    for base in features.get("bases", []):
        if base.get("enemy_nearby", 0) > 0:
            near_base = True
            break

    return {
        "enemy_visible": current,
        "delta": delta,
        "near_base": near_base,
    }


def _detect_base_oversaturated(features: dict) -> bool:
    bases = features.get("bases", [])
    if len(bases) < 2:
        return False
    has_oversaturated = any(b.get("saturation_ratio", 0) > 1.0 for b in bases)
    has_undersaturated = any(b.get("saturation_ratio", 1.0) < 0.9 for b in bases)
    return has_oversaturated and has_undersaturated


def _detect_base_under_attack(features: dict, bot: Any) -> bool:
    from src.bot.strategy import THREAT_RANGE
    townhalls = getattr(bot, "townhalls", None)
    if townhalls is None:
        return False
    nexus_list = getattr(townhalls, "ready", townhalls)
    try:
        for nexus in nexus_list:
            nearby_enemy = bot.enemy_units.closer_than(THREAT_RANGE, nexus.position)
            for enemy in nearby_enemy:
                if hasattr(enemy, "order_target") and enemy.order_target is not None:
                    return True
    except (TypeError, AttributeError):
        pass
    return False


def _detect_worker_stalled(features: dict, bot: Any) -> bool:
    if features.get("worker_count", 0) >= getattr(bot, "MAX_WORKERS", 70):
        return False
    if not bot.townhalls.ready:
        return False
    idle_nexus = any(n.is_idle for n in bot.townhalls.ready)
    if not idle_nexus:
        return False
    from sc2.ids.unit_typeid import UnitTypeId
    return bot.can_afford(UnitTypeId.PROBE)


def _detect_resource_float(features: dict, bot: Any) -> bool:
    if features.get("minerals", 0) <= 500:
        return False
    from sc2.ids.unit_typeid import UnitTypeId
    gateways = bot.structures(UnitTypeId.GATEWAY)
    warp_gates = bot.structures(UnitTypeId.WARPGATE)
    all_gates = gateways + warp_gates
    return all_gates.amount == 0 or all(
        g.is_idle for g in all_gates
    )


def _detect_tech_milestone(features: dict, bot: Any) -> bool:
    from sc2.ids.unit_typeid import UnitTypeId

    if not getattr(bot, "_cyber_milestone_fired", False):
        if bot.structures(UnitTypeId.CYBERNETICSCORE).ready.amount > 0:
            bot._cyber_milestone_fired = True
            return True

    if not getattr(bot, "_warp_milestone_fired", False):
        from sc2.ids.upgrade_id import UpgradeId
        if not bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH):
            bot._warp_milestone_fired = True
            return True

    return False


def _detect_attack_ready(features: dict, bot: Any) -> bool:
    attack_supply = getattr(bot, "ATTACK_SUPPLY", 200)
    return (
        features.get("supply_used", 0) >= attack_supply
        and not getattr(bot, "attack_triggered", False)
    )


def _detect_expansion_started(features: dict, prev_features: dict) -> bool:
    current = features.get("expansion_count", 0)
    previous = prev_features.get("expansion_count", 0)
    return current > previous
