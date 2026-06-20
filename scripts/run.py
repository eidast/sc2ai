import platform
import sys

from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bot.core import MyBot


MAP_NAME = "AcropolisLE"

_system = platform.system()
if _system == "Darwin":
    SC2_DIR = "/Applications/StarCraft II"
    MAPS_DIR = SC2_DIR + "/Maps/"
    _SETUP_SCRIPT = "scripts/setup_maps.sh"
elif _system == "Windows":
    SC2_DIR = r"C:\Program Files (x86)\StarCraft II"
    MAPS_DIR = SC2_DIR + r"\Maps\\"
    _SETUP_SCRIPT = r"scripts\setup_maps.bat"
else:
    raise RuntimeError(
        f"Unsupported operating system: {_system}. "
        f"This project supports macOS (Darwin) and Windows only."
    )


def resolve_map(map_registry=maps):
    selected_map = map_registry.get(MAP_NAME)
    if selected_map is None:
        raise RuntimeError(
            f"Missing StarCraft II map: {MAP_NAME}. "
            f"Install ladder maps under {MAPS_DIR} or run {_SETUP_SCRIPT}."
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
