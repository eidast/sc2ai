import asyncio
from types import SimpleNamespace

from sc2.position import Point2

from src.bot.core import MyBot
from src.bot.decision import DecisionState


class FakeUnit:
    def __init__(self, x, y):
        self.position = Point2((x, y))
        self.attack_target = None

    def attack(self, target):
        self.attack_target = target


class FakeUnits:
    def __init__(self, units):
        self._units = units
        self.idle = self
        self.amount = len(units)

    def __iter__(self):
        return iter(self._units)

    def __len__(self):
        return len(self._units)

    def closest_to(self, target):
        return min(self._units, key=lambda unit: unit.position.distance_to(target))


def _bot_with_army(army):
    bot = MyBot()
    bot._decision_state = DecisionState.ATTACK
    bot._get_army_units = lambda: FakeUnits(army)
    bot.game_info = SimpleNamespace(start_locations=[Point2((100, 100))])
    bot._expansion_positions_list = [Point2((20, 20))]
    bot.enemy_structures = FakeUnits([])
    return bot


def test_attack_prioritizes_visible_enemy_structure():
    army_unit = FakeUnit(0, 0)
    visible_structure = FakeUnit(30, 30)
    bot = _bot_with_army([army_unit])
    bot.enemy_structures = FakeUnits([visible_structure])

    asyncio.run(bot.manage_attack())

    assert army_unit.attack_target == visible_structure.position


def test_attack_uses_cleanup_waypoint_when_no_structure_visible():
    army_unit = FakeUnit(0, 0)
    bot = _bot_with_army([army_unit])
    bot._cleanup_target_index = 1

    asyncio.run(bot.manage_attack())

    assert army_unit.attack_target == Point2((20, 20))


def test_cleanup_waypoint_advances_after_army_reaches_target():
    army_unit = FakeUnit(101, 100)
    bot = _bot_with_army([army_unit])
    bot._cleanup_target_index = 0

    asyncio.run(bot.manage_attack())

    assert bot._cleanup_target_index == 1
    assert army_unit.attack_target == Point2((20, 20))
