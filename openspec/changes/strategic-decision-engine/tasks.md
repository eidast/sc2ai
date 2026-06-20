## 1. Army Value Metrics (Phase 1)

- [x] 1.1 Add `_NON_COMBAT_ENEMY` set to `src/ml/observation.py` (SCV, DRONE, LARVA, EGG, MULE, OVERLORD, OVERSEER, CHANGELING variants, OBSERVER)
- [x] 1.2 Add `_compute_army_value(composition)` helper to `src/ml/observation.py`
- [x] 1.3 Add `our_army_value` and `enemy_army_value` to `extract_features()` return dict
- [x] 1.4 Add `army_value_ratio` to `extract_features()` return dict
- [x] 1.5 Add `enemy_worker_count` to `extract_features()` return dict

## 2. T3 Detection (Phase 1)

- [x] 2.1 Define `T3_UNITS` dict by race in `src/bot/strategy.py` (Protoss, Terran, Zerg)
- [x] 2.2 Add `enemy_t3_count` and `our_t3_count` to `extract_features()` using `T3_UNITS` mapping and `self.enemy_race`

## 3. Decision Engine (Phase 2)

- [x] 3.1 Create `src/bot/decision.py` with `DecisionState` enum (DEFEND, ATTACK, RECOVER, SURRENDER)
- [x] 3.2 Implement `_get_game_phase(game_time)` helper returning EARLY/MID/LATE/DESPERATE
- [x] 3.3 Implement attack threshold table with phase-dependent supply minimums and army_value_ratio conditions
- [x] 3.4 Implement race-specific multiplier adjustments (Zerg ×0.85, Terran ×1.0, Protoss ×1.1)
- [x] 3.5 Implement fog-aware multiplier adjustment (×1.3 when fog enabled)
- [x] 3.6 Implement `evaluate_decision()` function with FSM transitions
- [x] 3.7 Implement DEFEND → ATTACK transition (4 rules: supply cap, advantage ratio, T3 window, enemy push)
- [x] 3.8 Implement ATTACK → RECOVER transition (army destroyed or timeout without damage)
- [x] 3.9 Implement RECOVER → DEFEND transition (army_value_ratio ≥ 0.6 and workers ≥ 20)
- [x] 3.10 Implement RECOVER → SURRENDER transition (ratio < 0.15, workers < 10, sustained 120s, game_time > 300s)
- [x] 3.11 Implement hysteresis: track `time_in_state` and `_state_start_game_time` to prevent oscillation

## 4. Bot Integration (Phase 3)

- [x] 4.1 Add `surrender_enabled` and `fog_enabled` params to `MyBot.__init__()` with defaults False
- [x] 4.2 Replace `self.attack_triggered` bool with `self._decision_state: DecisionState` and `self._state_start_time: float`
- [x] 4.3 Call `evaluate_decision()` at start of `on_step()` after feature extraction
- [x] 4.4 Modify `manage_attack()` to check `self._decision_state == DecisionState.ATTACK` instead of `self.attack_triggered`
- [x] 4.5 Modify `manage_defense()` to skip when `self._decision_state == DecisionState.ATTACK`
- [x] 4.6 Add `manage_surrender()` method: calls `chat_send("gg")`, sets surrendered flag
- [x] 4.7 Add surrender early-return in `on_step()`: skip all managers when surrendered
- [x] 4.8 Write `surrender` event to events file with details (game_time, army_value_ratio, reason)
- [x] 4.9 Update `manage_camera()` to use decision state instead of `attack_triggered`

## 5. CLI Integration (Phase 3)

- [x] 5.1 Add `--surrender` flag to `scripts/run.py` argparse
- [x] 5.2 Add `--fog` flag to `scripts/run.py` argparse
- [x] 5.3 Pass `surrender_enabled` and `fog_enabled` to `MyBot()` constructor
- [x] 5.4 Use `disable_fog=not args.fog` when `--fog` is passed

## 6. Analysis Script (Phase 4)

- [x] 6.1 Create `scripts/analyze.py`: reads all `reports/*/report.json`
- [x] 6.2 For each match, compute army_value timeline from `features.jsonl`
- [x] 6.3 Compute army_value_ratio timeline (our / enemy, excluding workers)
- [x] 6.4 Identify death spiral points: first step where ratio drops below 0.3 and never recovers
- [x] 6.5 Output summary table: match_id, result, duration, max_supply, min_army_value_ratio, death_spiral_time
- [x] 6.6 Output recommended thresholds based on death spiral analysis

## 7. Tests (Phase 5)

- [x] 7.1 Create `tests/test_decision.py` with mock features dicts
- [x] 7.2 Test default state is DEFEND
- [x] 7.3 Test DEFEND → ATTACK on supply cap (200)
- [x] 7.4 Test DEFEND → ATTACK on early game advantage (army_value_ratio > 1.5)
- [x] 7.5 Test DEFEND → ATTACK on mid game advantage (army_value_ratio > 1.2)
- [x] 7.6 Test DEFEND → ATTACK on T3 window (enemy T3, no our T3)
- [x] 7.7 Test ATTACK → RECOVER on army destroyed (army_count < 3)
- [x] 7.8 Test RECOVER → DEFEND on recovery
- [x] 7.9 Test RECOVER → SURRENDER on no comeback (ratio < 0.15, sustained 120s)
- [x] 7.10 Test surrender NOT triggered when surrender_enabled=False
- [x] 7.11 Test surrender NOT triggered in early game (< 300s)
- [x] 7.12 Test surrender NOT triggered during ATTACK state
- [x] 7.13 Test race-specific thresholds (Zerg lower, Protoss higher)
- [x] 7.14 Test fog-aware thresholds (higher supply requirements)
- [x] 7.15 Test hysteresis (no state oscillation)
- [x] 7.16 Update `tests/test_observation.py` for new fields (army_value, t3_count, worker_count)
- [x] 7.17 Run full test suite (`uv run pytest tests/ -v`) — all tests pass

## 8. Verification

- [x] 8.1 Verify existing specs still satisfied: bot-gameplay, observation-pipeline, reactive-defense, army-composition-tracking
- [x] 8.2 Run existing tests pass without SC2 instance
- [x] 8.3 Verify no regression: without --surrender, behavior matches current (attack at 200 supply via supply cap rule)
