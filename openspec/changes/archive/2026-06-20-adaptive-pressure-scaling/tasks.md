## 1. Create pressure module

- [x] 1.1 Create `src/bot/pressure.py` with `PressureLevel` enum (NONE, LOW, MEDIUM, HIGH)
- [x] 1.2 Implement `assess_pressure(features, prev_level, prev_level_start, game_time)` with signal weighting and 5s hysteresis
- [x] 1.3 Add `_pressure_level` and `_pressure_level_start` attributes to `MyBot.__init__()`

## 2. Wire pressure into on_step

- [x] 2.1 Import and call `assess_pressure()` in `on_step()` after feature extraction, store result on `self`
- [x] 2.2 Add `pressure_level` field to decision records in `_build_decision_record()`

## 3. Adapt manage_expansion() to pressure

- [x] 3.1 Replace hardcoded `MAX_SATURATION_RATIO` with pressure-adaptive lookup (0.65/0.75/0.85/no-expand)
- [x] 3.2 Replace hardcoded mineral bank threshold (400) with pressure-adaptive lookup (350/400/500/no-expand)
- [x] 3.3 At HIGH pressure, return early without expanding

## 4. Add fast expand to manage_early_game()

- [x] 4.1 Insert phase 2.5 (Nexus) between CyberCore (phase 2) and Warpgate Research (phase 3)
- [x] 4.2 Guard with `pressure_level <= LOW and expansion_count < 2`
- [x] 4.3 Increment subsequent phase numbers (old phase 3 → 4, old phase 4 → 5)

## 5. Adapt manage_tech() gateway target to pressure

- [x] 5.1 Add pressure-based bonus (+0/+1/+2/+3) to gateway target count
- [x] 5.2 Make `GATEWAY_MINERAL_FLOAT_EXTRA` pressure-adaptive (+2/+3/+4/+5)

## 6. Adapt manage_army() production to pressure

- [x] 6.1 At HIGH pressure, attempt production from Robo and Stargate even when strategy engine recommends gateway units
- [x] 6.2 At NONE/LOW/MEDIUM, preserve existing production behavior

## 7. Create pressure tests

- [x] 7.1 Create `tests/test_pressure.py` with tests for all 5 pressure signals
- [x] 7.2 Test hysteresis: no change before 5s, change after sustained
- [x] 7.3 Test all 4 pressure level mappings (NONE, LOW, MEDIUM, HIGH)
- [x] 7.4 Test edge cases: ratio=0, no features, all signals maximum

## 8. Update existing tests

- [x] 8.1 Update `_make_bot` in `tests/test_early_game.py` to include `_pressure_level` and `_pressure_level_start`
- [x] 8.2 Update `test_early_game.py` expansion tests for pressure-adaptive thresholds
- [x] 8.3 Add test for fast expand phase 2.5

## 9. Verify with tests and simulations

- [x] 9.1 Run `uv run pytest` to confirm all tests pass
- [ ] 9.2 Run 3 simulations vs Zerg Hard
- [ ] 9.3 Run 3 simulations vs Terran Hard
- [ ] 9.4 Run 3 simulations vs Protoss Hard
- [ ] 9.5 Verify 2/3+ win rate on Hard
