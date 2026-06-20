from sc2.game_state import GameState
from sc2.bot_ai import BotAI


def extract_features(bot: BotAI) -> dict:
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
        "game_time_seconds": bot.time,
        "expansion_count": bot.townhalls.amount,
        "iteration": bot.state.game_loop if hasattr(bot, "state") else 0,
    }
