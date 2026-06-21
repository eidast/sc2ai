## 1. Fix scout decay duplication

- [x] 1.1 Remove `_apply_scout_decay` method from `BiasCalculator` in `src/strategies/bias_calculator.py`
- [x] 1.2 Remove the `if scout_metadata: self._apply_scout_decay(scout_metadata)` call from `BiasCalculator.update()`
- [x] 1.3 Update `test_bias_calculator.py` if any test asserts on the removed method behavior

## 2. Bot: shadow profile acceptance and engine initialization

- [x] 2.1 Add `shadow_profiles: list[str] | None` parameter to `MyBot.__init__` (default `None`)
- [x] 2.2 Validate in `__init__`: if `policy_mode == \"ml_shadow\"` and `shadow_profiles` is None or empty, raise `ValueError` listing available profiles
- [x] 2.3 In `__init__`, load each shadow profile via `self._strategy_loader` and store in `self._shadow_profiles: list[tuple[str, StrategyProfile]]`
- [x] 2.4 In `__init__`, create `BiasCalculator` and `PriorityEngine` for each shadow profile, storing in `self._shadow_bias_calculators: list[BiasCalculator]` and `self._shadow_priority_engines: list[PriorityEngine]`
- [x] 2.5 Replace `self._last_shadow_prediction: dict | None` with `self._last_shadow_predictions: list[dict]` (initialized as empty list)

## 3. Bot: shadow evaluation in on_step

- [x] 3.1 After the heuristic `BiasCalculator.update()` and `PriorityEngine.evaluate()` block (around lines 249-261), add shadow evaluation loop
- [x] 3.2 For each shadow engine: call `shadow_bias_calc.update(features, scout_metadata_dict)`, then `shadow_priority_engine.evaluate(bias_vector, features, ...)`, serialize using `_serialize_action()`, and append `{"profile": name, "recommended_action": serialized}` to `self._last_shadow_predictions`
- [x] 3.3 Clear `self._last_shadow_predictions = []` at the start of each `on_step` iteration

## 4. Decision record: shadow_predictions array

- [x] 4.1 In `_build_decision_record`, replace `"shadow_prediction": self._last_shadow_prediction` with `"shadow_predictions": self._last_shadow_predictions`
- [x] 4.2 In `_build_policy_metadata`, add `"shadow_profiles": [name for name, _ in self._shadow_profiles]` when in `ml_shadow` mode with shadows configured

## 5. CLI: --shadow-profile flag

- [x] 5.1 Add `--shadow-profile` to `scripts/run.py` using `action="append"`, `default=None`, with help listing available profiles
- [x] 5.2 In `main()`, validate: if `args.policy_mode == \"ml_shadow\"` and `args.shadow_profile` is None/empty, print error listing available profiles from `src/data/strategies/protoss/` and exit
- [x] 5.3 Pass `shadow_profiles=args.shadow_profile` to `MyBot(...)` in the `run_game` call

## 6. Tests

- [x] 6.1 Update `test_early_game.py`: replace `_last_shadow_prediction` with `_last_shadow_predictions` in all test methods that mock or assert on shadow predictions
- [x] 6.2 Update `test_decision_record_includes_available_shadow_prediction` to use array format
- [x] 6.3 Update `test_write_decision_record_persists_shadow_prediction` to use array format and `shadow_predictions` key
- [x] 6.4 Update `test_decision_record_handles_missing_optional_context` to assert `shadow_predictions == []`
- [x] 6.5 Add `test_bot_rejects_ml_shadow_without_shadow_profiles` to `test_bot_logging.py`
- [x] 6.6 Add `test_bot_accepts_ml_shadow_with_shadow_profiles` to `test_bot_logging.py`
- [x] 6.7 Add `test_shadow_profiles_validated_in_cli` to `test_run_script.py`
- [x] 6.8 Add `test_multiple_shadow_profiles_accepted_in_cli` to `test_run_script.py`
- [x] 6.9 Add `test_shadow_engines_produce_predictions` to `test_early_game.py`
- [x] 6.10 Add `test_bias_calculator_does_not_mutate_scout_metadata` to `test_bias_calculator.py`

## 7. Spec files

- [x] 7.1 Apply changes from `specs/policy-shadow-telemetry/spec.md` delta to `openspec/specs/policy-shadow-telemetry/spec.md`
- [x] 7.2 Copy `specs/shadow-profile-engine/spec.md` to `openspec/specs/shadow-profile-engine/spec.md`

## 8. Verification

- [x] 8.1 Run `uv run pytest` — all tests must pass
- [x] 8.2 Run `uv run python scripts/run.py --help` — verify `--shadow-profile` appears with correct help text
- [x] 8.3 Run `uv run python scripts/run.py --policy-mode ml_shadow` — verify it exits with error listing available profiles
