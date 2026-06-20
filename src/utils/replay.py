import os
from datetime import datetime


async def save_replay(bot, result_name: str = "unknown") -> str | None:
    replays_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "replays"
    )
    os.makedirs(replays_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{result_name}.SC2Replay"
    filepath = os.path.join(replays_dir, filename)

    try:
        await bot.client.save_replay(filepath)
        return filepath
    except Exception:
        return None
