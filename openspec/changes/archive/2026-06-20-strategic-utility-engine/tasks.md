## 1. Infrastructure — Module setup, YAML loader, JSON Schema

- [x] 1.1 Create `src/strategies/` package with `__init__.py`, `bias_calculator.py`, `priority_engine.py`, `loader.py`, `formula.py`, `types.py`
- [x] 1.2 Create `src/data/strategies/protoss/` directory for YAML profiles
- [x] 1.3 Define `Action` dataclass (`type`, `target`, `score`, `params`) in `src/strategies/types.py`
- [x] 1.4 Define `StrategyProfile` dataclass (`name`, `race`, `initial_biases`, `scouting_adjustments`, `priority_formulas`, `meta`) in `src/strategies/types.py`
- [x] 1.5 Create JSON Schema for YAML profile validation in `src/strategies/schema.py`
- [x] 1.6 Implement `loader.py` with `load(path) -> StrategyProfile` and `load_all(race) -> list[StrategyProfile]`
- [x] 1.7 Add YAML/JSON Schema validation in `loader.py` (raise `ValidationError` on invalid profile)

## 2. Formula Evaluator — DSL for priority formulas and scouting conditions

- [x] 2.1 Implement `evaluate_formula(formula: str, bias_vector: dict, builtins: dict) -> float` in `formula.py`
- [x] 2.2 Implement built-in functions: `own_ratio(unit, category)`, `has_structure(name)`, `has_upgrade(name)`, `minerals`, `vespene`, `supply_left`, `supply_used`, `workers`, `game_time`
- [x] 2.3 Implement `evaluate_condition(condition: str, features: dict) -> bool` for scouting adjustment rules
- [x] 2.4 Handle errors gracefully: invalid formula → log warning + return 0.0; unknown condition field → log warning + return False
- [x] 2.5 Add tests for formula evaluator with various expressions and edge cases

## 3. Bias Calculator — Continuous bias system with scouting decay

- [x] 3.1 Implement `BiasCalculator` class with `update(features, scout_metadata) -> bias_vector` method
- [x] 3.2 Initialize biases from `StrategyProfile.initial_biases` on first call
- [x] 3.3 Evaluate `scouting_adjustments` rules against features + scout_metadata confidence
- [x] 3.4 Apply `bias_speed` multiplier and EMA smoothing to bias changes
- [x] 3.5 Clamp all biases to [0.0, 1.0] after each update
- [x] 3.6 Apply exponential decay to scouting confidence: `confidence *= exp(-decay_rate * delta_time)`
- [x] 3.7 Expose `bias_vector` as read-only property
- [x] 3.8 Add tests for BiasCalculator: initialization, single adjustment, multi-adjustment, decay, clamping, speed

## 4. Priority Engine — Action scoring and selection

- [x] 4.1 Implement `PriorityEngine` class with `evaluate(bias_vector, features, game_state) -> Action` method
- [x] 4.2 Iterate over all actions defined in `priority_formulas` from the active profile
- [x] 4.3 Filter reachable actions: check prerequisites (tech tree), resources, supply
- [x] 4.4 Evaluate priority formula for each reachable action using formula evaluator
- [x] 4.5 Select highest-scoring action; break ties deterministically
- [x] 4.6 Return `Action(type=NOOP)` when no actions are reachable
- [x] 4.7 Add tests for PriorityEngine: all actions reachable, some blocked, tie-breaking, no actions

## 5. Strategy YAML Profiles — Perfiles para Protoss

- [x] 5.1 Create `standard_macro.yaml` — perfil default que replique comportamiento actual del bot
- [x] 5.2 Create `stargate_open.yaml` — apertura con Stargate, transición a air-heavy
- [x] 5.3 Create `robo_open.yaml` — apertura con Robo, transición a ground-heavy
- [x] 5.4 Create `fast_expand.yaml` — apertura económica con nexus temprano
- [x] 5.5 Add YAML validation tests: valid profile loads, invalid profile raises error, all profiles in dir are valid
- [x] 5.6 Configure `standard_macro` as default profile in loader

## 6. Scout Metadata — Tracking per-unit-type with confidence decay

- [x] 6.1 Extend `ScoutState` or add `ScoutMetadata` tracker with `{unit_type_name: {last_seen, confidence}}` dict
- [x] 6.2 Update metadata whenever enemy units are visible during scouting (`on_step` observations)
- [x] 6.3 Apply confidence decay on each step based on `scout_decay_rate` from active profile
- [x] 6.4 Expose `scout_metadata` to observation pipeline for feature extraction
- [x] 6.5 Add tests: record observation, decay behavior, re-observation resets confidence, DEAD scout stops updates

## 7. Observation Pipeline Extensions — New features for utility engine

- [x] 7.1 Add `scout_age` feature to `extract_features()` — map of unit type → `{last_seen, confidence}`
- [x] 7.2 Add `building_inference` feature — enemy building types/counts from visible structures
- [x] 7.3 Add `eco_inference` feature — estimated enemy economy (bases_count, gas_count, estimated_workers)
- [x] 7.4 Update tests in `test_observation.py` for new features
- [x] 7.5 Verify existing feature fields are unchanged (backward compatibility)

## 8. Strategy Delegation — Refactor manage_* to accept PriorityEngine actions

- [x] 8.1 Modify `manage_tech()` to accept optional `Action` parameter; execute `BUILD_STRUCTURE` action when provided
- [x] 8.2 Modify `manage_upgrades()` to accept optional `Action` parameter; execute `RESEARCH_UPGRADE` action when provided
- [x] 8.3 Modify `manage_army()` to accept optional `Action` parameter; train `BUILD_UNIT` action target when provided
- [x] 8.4 Add fallback to existing autonomous logic in each manage_* when no action or `NOOP`
- [x] 8.5 Preserve existing behavior of `manage_probes`, `manage_pylons`, `manage_gas`, `manage_expansion`, `manage_defense`, `manage_attack`, `manage_scout` (no-op for action passthrough)
- [x] 8.6 Add tests: manage_* follows engine action, manage_* falls back without action, manage_* ignores unachievable action

## 9. Core Integration — Connect engine to game loop

- [x] 9.1 Modify `MyBot.__init__()` to instantiate `StrategyLoader`, `BiasCalculator`, `PriorityEngine`
- [x] 9.2 Select active profile at match start based on race (default: `standard_macro`)
- [x] 9.3 Modify `on_step()`: run `BiasCalculator.update()` and `PriorityEngine.evaluate()` after `extract_features()` and before `manage_*` block
- [x] 9.4 Pass resulting `Action` to corresponding manage_* functions
- [x] 9.5 Preserve FSM evaluation after PriorityEngine as safety override; restrict engine during SURRENDER/WON
- [x] 9.6 Log selected action and bias vector at log_interval for debugging
- [x] 9.7 Add constructor parameter `strategy_profile: str | None` to select non-default strategy
- [x] 9.8 Add tests: engine produces action before manage_*, FSM overrides in critical states, log output includes action info

## 10. Calibration & Regression Testing

- [x] 10.1 Write regression test harness: compare old bot decisions vs new engine decisions on historical feature snapshots
- [x] 10.2 Tune `standard_macro.yaml` biases and formulas until engine decisions match current bot behavior >= 90%
- [x] 10.3 Run full test suite (`uv run pytest`) and fix any failures
- [x] 10.4 Verify cross-platform compatibility (macOS + Windows via mock tests)

## 11. Documentation

- [x] 11.1 Add `docs/bitacora/` entry (ES) describing the utility-based strategic engine architecture
- [x] 11.2 Document YAML profile format with examples in code comments or `AGENTS.md`
- [x] 11.3 Add tecnicas y referencias mencionadas durante el diseño: Utility AI, exponential scout decay, bias speed smoothing, Multi-Armed Bandit context
