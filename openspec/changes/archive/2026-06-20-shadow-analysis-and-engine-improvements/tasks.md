## 1. StrategyProfile schema: extended formula entries

- [x] 1.1 Update `StrategyProfile` dataclass in `src/strategies/types.py` to represent formula entries as `FormulaEntry` (dataclass with `formula: str`, `requires: list[str]`, `max_count: Optional[str]`)
- [x] 1.2 Update `StrategyLoader._parse()` in `src/strategies/loader.py` to parse both string (legacy) and dict (new) formula entries
- [x] 1.3 Update `PriorityEngine.__init__()` to accept the new formula structure from `StrategyProfile`
- [x] 1.4 Update `test_loader.py` with tests for both legacy and new formula entry formats

## 2. Tech tree awareness: _is_reachable with requires

- [x] 2.1 Update `PriorityEngine._is_reachable()` to accept `structures: dict[str, int]` and check formula `requires` against it
- [x] 2.2 Update `PriorityEngine._get_formula_actions()` to include `requires` in candidate tuples
- [x] 2.3 Update `PriorityEngine.evaluate()` to pass structures to `_is_reachable()`
- [x] 2.4 Add `requires` fields to relevant formulas in all 4 YAML profiles:
  - `standard_macro.yaml`: COLOSSUS→ROBOTICSBAY, WARPGATERESEARCH→CYBERNETICSCORE, etc.
  - `stargate_open.yaml`: CARRIER→FLEETBEACON, appropriate prereqs
  - `robo_open.yaml`: COLOSSUS→ROBOTICSBAY, DISRUPTOR→ROBOTICSBAY
  - `fast_expand.yaml`: appropriate prereqs
- [x] 2.5 Add tests to `test_priority_engine.py` for tech tree filtering
- [x] 2.6 Add test for backward compatibility (string-only formulas still work)

## 3. Action momentum: continuity bonus

- [x] 3.1 Add `prev_action: Action | None = None` parameter to `PriorityEngine.evaluate()`
- [x] 3.2 Apply `* 1.15` multiplier when candidate matches `prev_action` in type and target
- [x] 3.3 Skip momentum when `prev_action` is None or NOOP
- [x] 3.4 Update `src/bot/core.py` to pass `self._last_action` as `prev_action` to both heuristic and shadow `evaluate()` calls
- [x] 3.5 Add tests to `test_priority_engine.py` for momentum behavior

## 4. Shadow analysis script

- [x] 4.1 Create `scripts/analyze_shadows.py` with argparse CLI: positional `match_id`, optional `--format json|text` (default text)
- [x] 4.2 Implement `_load_jsonl(path)` helper to read JSONL files
- [x] 4.3 Implement overview metrics: total steps, game time, result, strategic state distribution, override rate
- [x] 4.4 Implement agreement matrix: N×N matrix of target-match percentages across profiles
- [x] 4.5 Implement action distribution: top-3 actions per profile with avg score and std dev
- [x] 4.6 Implement bias evolution: initial/final/delta per bias key from heuristic utility
- [x] 4.7 Implement timeline: state transitions, first divergence between profiles, override periods
- [x] 4.8 Implement `--format json` output mode
- [x] 4.9 Add tests in `tests/test_analyze_shadows.py` with mock JSONL data

## 5. Core integration

- [x] 5.1 Update `MyBot.on_step()` to pass `prev_action=self._last_action` to `PriorityEngine.evaluate()`
- [x] 5.2 Ensure shadow engines also receive `prev_action` (their own last action, not the heuristic's)
- [x] 5.3 Track per-shadow last actions in `self._shadow_last_actions: list[Action | None]`

## 6. YAML profile updates

- [x] 6.1 Add `requires` to standard_macro.yaml formulas (COLOSSUS, WARPGATERESEARCH, upgrades)
- [x] 6.2 Add `requires` to stargate_open.yaml formulas (CARRIER, appropriate tech)
- [x] 6.3 Add `requires` to robo_open.yaml formulas (COLOSSUS, DISRUPTOR, OBSERVER)
- [x] 6.4 Add `requires` to fast_expand.yaml formulas

## 7. Spec files

- [x] 7.1 Copy delta specs to `openspec/specs/`: shadow-analysis-tool, tech-tree-awareness, action-momentum
- [x] 7.2 Apply shadow-profile-engine delta to `openspec/specs/shadow-profile-engine/spec.md`

## 8. Verification

- [x] 8.1 Run `uv run pytest` — all tests pass
- [x] 8.2 Run `uv run python scripts/analyze_shadows.py --help` — verify CLI works
