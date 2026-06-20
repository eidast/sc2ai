## 1. Observation pipeline — extend extract_features()

- [x] 1.1 Add `our_army_composition` to features: iterate `self.units`, count by `type_id.name`, exclude workers and observers
- [x] 1.2 Add `our_structures` to features: iterate `self.structures`, count by `type_id.name`
- [x] 1.3 Add `bases` list to features: for each nexus, compute `position` (tuple), `ideal_workers` (nearby minerals * 2 + nearby gas * 3), `current_workers` (assigned_harvesters), `saturation_ratio`, `enemy_nearby` (enemy units within THREAT_RANGE), `army_nearby` (our combat units within 15)
- [x] 1.4 Update `src/bot/strategy.py` with new constants: `WORKERS_PER_MINERAL = 2`, `WORKERS_PER_GAS = 3`, `MAX_SATURATION_RATIO = 0.9`, `THREAT_RANGE = 15`, `ENGAGE_RANGE = 8`, `BASE_MINERAL_RADIUS = 10`
- [x] 1.5 Verify existing tests still pass with extended features

## 2. Probe management — saturation-aware training

- [x] 2.1 Rewrite `manage_probes()`: compute saturation for each nexus, sort by ratio ascending, train at first nexus with ratio < 0.9
- [x] 2.2 Add `_get_base_saturation(nexus)` helper that returns `(ideal, current, ratio)` using mineral field and gas building counts within BASE_MINERAL_RADIUS
- [x] 2.3 Add `_sort_bases_by_saturation()` helper returning nexuses sorted by ratio ascending
- [x] 2.4 Fallback: if `assigned_harvesters` is not available, count workers by proximity to nexus position

## 3. Expansion management — saturation-driven

- [x] 3.1 Rewrite `manage_expansion()`: remove `townhalls.amount >= 2` and `supply_used < 20` guards
- [x] 3.2 Check that ALL current nexuses have saturation ≥ MAX_SATURATION_RATIO before expanding
- [x] 3.3 Keep existing affordability and pending checks

## 4. Defense system — manage_defense()

- [x] 4.1 Add `manage_defense()` method to MyBot: 3-state logic (PEACEFUL / THREATENED / ENGAGED)
- [x] 4.2 PEACEFUL: compute defensive rally point (midpoint between main and natural, or main ramp if single base), move idle army there
- [x] 4.3 THREATENED: find most threatened base (highest sum of enemy supply_cost within THREAT_RANGE), move idle army toward that base
- [x] 4.4 ENGAGED: when army units are within ENGAGE_RANGE of enemies near a base, attack nearest enemy
- [x] 4.5 Add `manage_defense()` to `on_step()` dispatch BEFORE `manage_attack()`
- [x] 4.6 Add `_compute_defensive_rally()` helper

## 5. Events — new event types

- [x] 5.1 Add `_detect_base_oversaturated()`: emit when a nexus has ratio > 1.0 AND another nexus has ratio < 0.9
- [x] 5.2 Add `_detect_base_under_attack()`: emit when enemy units within THREAT_RANGE have attack orders targeting our structures
- [x] 5.3 Refine `_detect_enemy_push()` to include `near_base` flag in details (whether any new enemy units are within THREAT_RANGE of a base)
- [x] 5.4 Add new event detectors to `detect_events()` call chain

## 6. Report fixes — HTML, opponent race, composition

- [x] 6.1 Fix `bot_info` in `on_end()` to use `self.enemy_race.name` instead of hardcoded `"Terran"`
- [x] 6.2 Fix HTML table column mismatch: change "Our Army" table to have 3 headers matching 3 data cells
- [x] 6.3 Populate "Enemy Army" table with enemy composition data (currently empty)
- [x] 6.4 Add "Our Army Composition" section to report showing unit type breakdown
- [x] 6.5 Include `our_composition` in `_build_army_snapshots()` and report JSON
- [x] 6.6 Add per-base saturation data to report (summary of bases, saturation ratios, threats)

## 7. Tests

- [x] 7.1 Test `extract_features()` includes new fields (`our_army_composition`, `our_structures`, `bases`)
- [x] 7.2 Test saturation math: `ideal_workers` calculation with varying mineral/gas counts
- [x] 7.3 Test `manage_probes()`: trains at least saturated nexus, skips saturated bases
- [x] 7.4 Test `manage_expansion()`: expands when saturated, not when undersaturated
- [x] 7.5 Test `manage_defense()`: threat scoring, rally point calculation, engagement range
- [x] 7.6 Test new events: `base_oversaturated`, `base_under_attack` detection conditions
- [x] 7.7 Test report generation: correct table structure, no hardcoded race, our composition present

## 8. Integration & cleanup

- [x] 8.1 Run `uv run pytest` — all tests pass
- [x] 8.2 Run a test game against built-in AI, verify report HTML renders correctly
- [x] 8.3 Verify `features.jsonl` includes new fields without breaking existing readers
- [x] 8.4 Remove unused constants from `src/bot/strategy.py` (old `EXPAND_SUPPLY`, `GATEWAY_COUNT_*` if no longer referenced)
