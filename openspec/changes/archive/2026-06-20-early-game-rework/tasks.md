## 1. Foundation — `_build_if_able` helper

- [x] 1.1 Create `_build_if_able(self, unit_type_id) -> bool` helper method in `src/bot/core.py` that wraps `can_afford` → `find_placement` → `build` with logging of success/failure and reason
- [x] 1.2 Log diagnostic on each call: affordability, placement result, worker tag (on success) or failure reason (no worker, placement failed, cant afford)

## 2. Early game build order — `manage_early_game`

- [x] 2.1 Create `manage_early_game(self)` async method in `MyBot` that executes the fixed build order: Pylon → Gateway → Cybernetics Core → Warp Gate research
- [x] 2.2 Implement phase progression with checks: each phase issues one build order and returns, retrying next step if it fails
- [x] 2.3 Implement 15-second timeout per phase that skips to next phase on persistent failure with a warning log
- [x] 2.4 `manage_early_game` SHALL return early without doing anything when game_time >= 90s (cede control to strategy engine)
- [x] 2.5 Call `manage_early_game()` in `on_step` BEFORE `manage_tech()` and all other managers

## 3. Rework `manage_tech` — Gateway-first guarantee

- [x] 3.1 Move Gateway check (amount == 0 → build) to TOP of `manage_tech`, BEFORE the action-based early return block
- [x] 3.2 Move Cybernetics Core check (amount == 0 → build) right after Gateway check, BEFORE the action-based early return
- [x] 3.3 Add emergency fallback: if game_time >= 120s and no Gateway exists, log warning and force-build Gateway via `_build_if_able` regardless of action
- [x] 3.4 Replace inline `can_afford`/`find_placement`/`build` calls in `manage_tech` with `_build_if_able`

## 4. Limit `manage_gas` before Gateway

- [x] 4.1 In `manage_gas`, add check: if `self.structures(GATEWAY).amount == 0 and self.gas_buildings.amount >= 1`, return without building another assimilator

## 5. Improve `manage_expansion` with mineral banking

- [x] 5.1 In `manage_expansion`, before the saturation check, add: if `minerals > 400 and not already_pending(NEXUS)`, call `expand_now()` and return
- [x] 5.2 Ensure the mineral banking trigger does not spam multiple expansion attempts (use `already_pending` guard)

## 6. Update strategy YAML formulas with prerequisites

- [x] 6.1 In `standard_macro.yaml`, multiply FORGE formula by `has_structure('GATEWAY')` so score is zero without a Gateway
- [x] 6.2 In `standard_macro.yaml`, multiply ROBOTICSFACILITY formula by `has_structure('CYBERNETICSCORE')` so score is zero without a Cybernetics Core
- [x] 6.3 In `standard_macro.yaml`, multiply STARGATE formula by `has_structure('CYBERNETICSCORE')`
- [x] 6.4 In `standard_macro.yaml`, multiply TWILIGHTCOUNCIL formula by `has_structure('CYBERNETICSCORE')`
- [x] 6.5 Apply the same prerequisite changes to `robo_open.yaml`

## 7. Tests

- [x] 7.1 `test_early_game.py`: test `manage_early_game` builds Pylon → Gateway → Cybernetics Core in correct order
- [x] 7.2 `test_early_game.py`: test phase timeout skips to next phase after 15s of failures
- [x] 7.3 `test_early_game.py`: test `manage_early_game` returns without action after all phases complete
- [x] 7.4 `test_manage_tech.py`: test Gateway is built before Forge even when strategy engine recommends Forge
- [x] 7.5 `test_manage_tech.py`: test emergency fallback at t=120s builds Gateway even after early game window
- [x] 7.6 `test_gas_economy.py`: test second assimilator is not built when no Gateway exists
- [x] 7.7 `test_expansion.py`: test mineral banking trigger expands when minerals > 400
- [x] 7.8 `test_formulas.py`: test that Forge/Robo/Stargate formulas return zero without required prerequisites

## 8. Integration & verification

- [x] 8.1 Run `uv run pytest` to ensure all tests pass
- [x] 8.2 Run `uv run python scripts/run.py --difficulty VeryEasy --opponent-race Terran` to verify bot builds Gateway within first 30s
- [x] 8.3 Run 3 games against Hard Terran matching original scenario and verify Gateway is built every time
