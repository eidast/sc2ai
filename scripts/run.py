import argparse
import platform
import random
import sys

from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bot.core import MyBot


DEFAULT_MAP = "AcropolisLE"

DIFFICULTY_CHOICES = [
    "VeryEasy", "Easy", "Medium", "MediumHard",
    "Hard", "Harder", "VeryHard",
]
RACE_CHOICES = ["Terran", "Zerg", "Protoss", "Random"]

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


def resolve_map(map_name: str, map_registry=maps):
    try:
        available = list(map_registry.keys())
    except AttributeError:
        try:
            available = list(map_registry.maps.keys())
        except AttributeError:
            available = []

    if map_name == "random":
        if not available:
            raise RuntimeError(
                f"No maps found in {MAPS_DIR}. "
                f"Install ladder maps or run {_SETUP_SCRIPT}."
            )
        map_name = random.choice(available)

    selected_map = map_registry.get(map_name)
    if selected_map is None:
        avail_list = ", ".join(sorted(available)) if available else "(none found)"
        raise RuntimeError(
            f"Map '{map_name}' not found. Available maps: {avail_list}. "
            f"Install ladder maps under {MAPS_DIR} or run {_SETUP_SCRIPT}."
        )
    return selected_map


def _list_maps(map_registry=maps):
    try:
        return sorted(map_registry.keys())
    except AttributeError:
        try:
            return sorted(map_registry.maps.keys())
        except AttributeError:
            return []


def main():
    available = _list_maps()
    epilog = f"Available maps: {', '.join(available)}" if available else ""
    parser = argparse.ArgumentParser(
        description="SC2AI — Protoss macro bot launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--realtime", action="store_true",
        help="Run at normal speed with rendering (default: accelerated)",
    )
    parser.add_argument(
        "--map", default=DEFAULT_MAP,
        help=f"Map name or 'random' (default: {DEFAULT_MAP})",
    )
    parser.add_argument(
        "--surrender", action="store_true",
        help="Enable strategic surrender when victory is mathematically impossible",
    )
    parser.add_argument(
        "--fog", action="store_true",
        help="Enable fog of war (default: disabled for full visibility)",
    )
    parser.add_argument(
        "--difficulty", default="Medium",
        choices=DIFFICULTY_CHOICES,
        help=f"AI opponent difficulty (default: Medium). Choices: {', '.join(DIFFICULTY_CHOICES)}",
    )
    parser.add_argument(
        "--opponent-race", default="Terran",
        choices=RACE_CHOICES,
        help=f"Opponent race (default: Terran). Choices: {', '.join(RACE_CHOICES)}",
    )
    parser.add_argument(
        "--opponents", type=int, default=1,
        choices=range(1, 5),
        metavar="N",
        help="Number of AI opponents, 1-4 (default: 1)",
    )

    args = parser.parse_args()

    run_game(
        resolve_map(args.map),
        [
            Bot(Race.Protoss, MyBot(
                surrender_enabled=args.surrender,
                fog_enabled=args.fog,
                opponent_difficulty=args.difficulty,
                opponent_race=args.opponent_race,
                opponent_count=args.opponents,
            ), fullscreen=True),
        ] + [
            Computer(Race[args.opponent_race], Difficulty[args.difficulty])
            for _ in range(args.opponents)
        ],
        realtime=args.realtime,
        disable_fog=not args.fog,
    )


if __name__ == "__main__":
    main()
