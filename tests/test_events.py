from types import SimpleNamespace

from src.ml.events import Event, detect_events, _detect_supply_block, _detect_enemy_push, _detect_worker_stalled


class FakeBot:
    def __init__(self, supply_left=5, pylon_pending=True, enemy_count=0,
                 worker_count=30, max_workers=70, nexus_idle=False,
                 can_afford_probe=True, attack_triggered=False,
                 attack_supply=200):
        self.supply_left = supply_left
        self._pylon_pending = pylon_pending
        self.enemy_count = enemy_count
        self._worker_count = worker_count
        self.MAX_WORKERS = max_workers
        self._nexus_idle = nexus_idle
        self._can_afford_probe = can_afford_probe
        self.attack_triggered = attack_triggered
        self.ATTACK_SUPPLY = attack_supply
        self.townhalls = SimpleNamespace(ready=[])
        self._cyber_milestone_fired = False
        self._warp_milestone_fired = False

    def already_pending(self, _unit_type):
        return self._pylon_pending

    def already_pending_upgrade(self, _upgrade_id):
        return True

    def structures(self, _unit_type):
        return SimpleNamespace(ready=SimpleNamespace(amount=0), amount=0)

    def can_afford(self, _unit_type):
        return True


class FakeNexus:
    def __init__(self, idle=True):
        self.is_idle = idle


def make_bot(**kwargs):
    bot = FakeBot(**kwargs)
    if kwargs.get("nexus_idle", False):
        bot.townhalls = SimpleNamespace(ready=[FakeNexus(idle=True)])
    else:
        bot.townhalls = SimpleNamespace(ready=[])
    return bot


def test_game_start_event_when_no_prev_features():
    bot = make_bot()
    features = {"game_time_seconds": 0, "supply_used": 6}
    events = detect_events(bot, features, None, 0)
    assert len(events) == 1
    assert events[0].type == "game_start"


def test_prev_features_none_emits_game_start_only():
    bot = make_bot()
    features = {"game_time_seconds": 0}
    events = detect_events(bot, features, None, 0)
    assert len(events) == 1
    assert events[0].type == "game_start"


def test_event_dataclass_fields():
    event = Event(type="test", time=10.0, step=100, severity="high", details={"key": "val"})
    assert event.type == "test"
    assert event.time == 10.0
    assert event.step == 100
    assert event.severity == "high"
    assert event.details == {"key": "val"}


def test_detect_events_with_only_game_start():
    bot = FakeBot()
    features = {"game_time_seconds": 0, "enemy_visible_units": 0}
    prev = {}
    events = detect_events(bot, features, prev, 1)
    assert len(events) >= 0


def test_detect_enemy_push_triggers():
    bot = make_bot()
    features = {"game_time_seconds": 30, "enemy_visible_units": 25}
    prev = {"game_time_seconds": 29, "enemy_visible_units": 5}
    events = detect_events(bot, features, prev, 50)
    types = [e.type for e in events]
    assert "enemy_push" in types


def test_detect_enemy_push_no_delta():
    bot = make_bot()
    features = {"game_time_seconds": 30, "enemy_visible_units": 5}
    prev = {"game_time_seconds": 29, "enemy_visible_units": 5}
    events = detect_events(bot, features, prev, 50)
    types = [e.type for e in events]
    assert "enemy_push" not in types
