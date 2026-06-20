import pytest
from src.bot.decision import (
    evaluate_decision, DecisionState, Decision,
    _get_game_phase, _get_race_multiplier, _compute_supply_min,
    SURRENDER_SUSTAIN_SECONDS,
)


def _features(**overrides):
    base = {
        "game_time_seconds": 0.0,
        "supply_used": 12,
        "army_count": 0,
        "army_value_ratio": 0.0,
        "our_t3_count": 0,
        "enemy_t3_count": 0,
        "worker_count": 12,
    }
    base.update(overrides)
    return base


def _eval(state, features=None, **kwargs):
    params = {
        "current_state": state,
        "enemy_race_name": "Terran",
        "fog_enabled": False,
        "surrender_enabled": False,
        "time_in_state": 0.0,
        "surrender_sustained": 0.0,
        "enemy_gone_sustained": 0.0,
        "enemy_push_active": False,
    }
    params.update(kwargs)
    if features:
        return evaluate_decision(features, **params)
    return evaluate_decision(_features(), **params)


class TestGamePhase:
    def test_early_phase(self):
        assert _get_game_phase(30)["name"] == "early"

    def test_mid_phase(self):
        assert _get_game_phase(300)["name"] == "mid"

    def test_late_phase(self):
        assert _get_game_phase(700)["name"] == "late"

    def test_desperate_phase(self):
        assert _get_game_phase(1000)["name"] == "desperate"


class TestRaceMultipliers:
    def test_zerg_is_lower(self):
        assert _get_race_multiplier("Zerg") == 0.85

    def test_terran_is_baseline(self):
        assert _get_race_multiplier("Terran") == 1.0

    def test_protoss_is_higher(self):
        assert _get_race_multiplier("Protoss") == 1.1

    def test_unknown_race_defaults(self):
        assert _get_race_multiplier(None) == 1.0


class TestFogMultipliers:
    def test_fog_increases_supply_min(self):
        phase = _get_game_phase(300)
        base = phase["min_supply"] * 1.0
        fog = _compute_supply_min(phase, 1.0, fog_enabled=True)
        assert fog > base
        assert fog == base * 1.3


class TestDecisionFSM:
    def test_default_state_is_defend(self):
        result = _eval(DecisionState.DEFEND)
        assert result.state == DecisionState.DEFEND

    def test_supply_cap_triggers_attack(self):
        result = _eval(DecisionState.DEFEND, _features(supply_used=200))
        assert result.state == DecisionState.ATTACK
        assert "supply cap" in result.reason.lower()

    def test_early_game_no_attack_without_advantage(self):
        result = _eval(DecisionState.DEFEND, _features(game_time_seconds=100, supply_used=50, army_value_ratio=1.0))
        assert result.state == DecisionState.DEFEND

    def test_early_game_attack_on_advantage(self):
        result = _eval(DecisionState.DEFEND, _features(game_time_seconds=100, supply_used=40, army_value_ratio=1.6, army_count=15))
        assert result.state == DecisionState.ATTACK

    def test_mid_game_attack_on_advantage(self):
        result = _eval(DecisionState.DEFEND, _features(game_time_seconds=300, supply_used=85, army_value_ratio=1.3, army_count=20))
        assert result.state == DecisionState.ATTACK

    def test_t3_window_triggers_attack(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=400, supply_used=50, army_count=15,
            enemy_t3_count=2, our_t3_count=0,
        ))
        assert result.state == DecisionState.ATTACK
        assert "t3" in result.reason.lower()

    def test_enemy_push_triggers_attack(self):
        result = _eval(DecisionState.DEFEND, _features(game_time_seconds=200, supply_used=25),
                       enemy_push_active=True)
        assert result.state == DecisionState.ATTACK

    def test_army_destroyed_triggers_recover(self):
        result = _eval(DecisionState.ATTACK, _features(army_count=2), time_in_state=10.0)
        assert result.state == DecisionState.RECOVER

    def test_attack_timeout_triggers_recover(self):
        result = _eval(DecisionState.ATTACK, _features(army_count=10), time_in_state=130.0)
        assert result.state == DecisionState.RECOVER

    def test_recover_to_defend_on_rebuild(self):
        result = _eval(DecisionState.RECOVER, _features(army_value_ratio=0.7, worker_count=25), time_in_state=30.0)
        assert result.state == DecisionState.DEFEND

    def test_recover_stays_when_not_ready(self):
        result = _eval(DecisionState.RECOVER, _features(army_value_ratio=0.3, worker_count=15), time_in_state=30.0)
        assert result.state == DecisionState.RECOVER

    def test_surrender_not_triggered_when_disabled(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=False, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state != DecisionState.SURRENDER

    def test_surrender_not_triggered_in_early_game(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=200, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state != DecisionState.SURRENDER

    def test_surrender_not_triggered_during_attack(self):
        result = _eval(DecisionState.ATTACK, _features(
            game_time_seconds=500, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state != DecisionState.SURRENDER

    def test_surrender_triggers_from_defend(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state == DecisionState.SURRENDER

    def test_surrender_triggers_from_recover(self):
        result = _eval(DecisionState.RECOVER, _features(
            game_time_seconds=500, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, time_in_state=30.0,
            surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state == DecisionState.SURRENDER

    def test_surrender_requires_sustained(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, surrender_sustained=50.0)
        assert result.state == DecisionState.DEFEND

    def test_surrender_conditions_not_met_reverts(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_value_ratio=0.5, worker_count=25,
        ), surrender_enabled=True, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state == DecisionState.DEFEND

    def test_race_zerg_lower_threshold(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=300, supply_used=70, army_value_ratio=1.3, army_count=20,
        ), enemy_race_name="Zerg")
        assert result.state == DecisionState.ATTACK

    def test_fog_increases_attack_threshold(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=300, supply_used=85, army_value_ratio=1.3, army_count=20,
        ), fog_enabled=True)
        assert result.state == DecisionState.DEFEND

    def test_hysteresis_no_oscillation(self):
        result = _eval(DecisionState.ATTACK, _features(game_time_seconds=300, supply_used=90, army_count=15),
                       time_in_state=5.0)
        assert result.state == DecisionState.ATTACK

    def test_desperate_phase_always_attacks(self):
        result = _eval(DecisionState.DEFEND, _features(game_time_seconds=1000, supply_used=70, army_count=15))
        assert result.state == DecisionState.ATTACK

    def test_already_surrendered_stays_surrendered(self):
        result = _eval(DecisionState.SURRENDER, surrender_enabled=True)
        assert result.state == DecisionState.SURRENDER

    def test_fog_surrender_uses_lower_threshold(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_value_ratio=0.08, worker_count=3,
        ), surrender_enabled=True, fog_enabled=True,
            surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1)
        assert result.state == DecisionState.SURRENDER

    def test_victory_detected_when_enemy_gone_long_enough(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=300, army_count=10,
        ), enemy_gone_sustained=70.0)
        assert result.state == DecisionState.WON

    def test_victory_not_detected_too_early(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=30, army_count=10,
        ), enemy_gone_sustained=70.0)
        assert result.state != DecisionState.WON

    def test_victory_not_detected_without_army(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=300, army_count=2,
        ), enemy_gone_sustained=70.0)
        assert result.state != DecisionState.WON

    def test_victory_not_detected_insufficient_sustained(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=300, army_count=10,
        ), enemy_gone_sustained=30.0)
        assert result.state != DecisionState.WON

    def test_victory_has_priority_over_surrender(self):
        result = _eval(DecisionState.DEFEND, _features(
            game_time_seconds=500, army_count=10, army_value_ratio=0.05, worker_count=3,
        ), surrender_enabled=True, surrender_sustained=SURRENDER_SUSTAIN_SECONDS + 1,
            enemy_gone_sustained=70.0)
        assert result.state == DecisionState.WON

    def test_already_won_stays_won(self):
        result = _eval(DecisionState.WON)
        assert result.state == DecisionState.WON
