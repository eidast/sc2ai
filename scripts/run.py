from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bot.core import MyBot


def main():
    run_game(
        maps.get("AcropolisLE"),
        [
            Bot(Race.Protoss, MyBot(), fullscreen=True),
            Computer(Race.Terran, Difficulty.Medium),
        ],
        realtime=False,
        disable_fog=True,
    )


if __name__ == "__main__":
    main()
