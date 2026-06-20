from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bot.core import MyBot


MAP_NAME = "AcropolisLE"
MAPS_DIR = "/Applications/StarCraft II/Maps/"


def resolve_map(map_registry=maps):
    selected_map = map_registry.get(MAP_NAME)
    if selected_map is None:
        raise RuntimeError(
            f"Missing StarCraft II map: {MAP_NAME}. "
            f"Install ladder maps under {MAPS_DIR} or run scripts/setup_maps.sh."
        )
    return selected_map


def main():
    run_game(
        resolve_map(),
        [
            Bot(Race.Protoss, MyBot(), fullscreen=True),
            Computer(Race.Terran, Difficulty.Medium),
        ],
        realtime=False,
        disable_fog=True,
    )


if __name__ == "__main__":
    main()
