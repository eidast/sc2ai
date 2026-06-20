## 1. Observation — Enriched base saturation data

- [x] 1.1 Enrich `_extract_base_features()` in `src/ml/observation.py`: add `mineral_patches`, `gas_geysers`, `ideal_mineral_workers`, `ideal_gas_workers`, `actual_mineral_workers`, `actual_gas_workers`, `idle_workers_nearby`, `mineral_saturation`, `gas_saturation`, `total_saturation`, and `status` fields per base
- [x] 1.2 Iterate `bot.workers` to count actual workers by resource type (mineral vs gas vs idle) and assign to nearest base
- [x] 1.3 Retain legacy fields (`ideal_workers`, `current_workers`, `saturation_ratio`) mapping to new fields for backward compatibility
- [x] 1.4 Verify `extract_features()` passes through all new base fields unchanged

## 2. Reports — Saturation summary, timeline, and HTML dashboard

- [x] 2.1 Update `_compute_metrics()` in `src/ml/report.py` to build enriched `saturation_summary` from the last features frame
- [x] 2.2 Create `_build_saturation_snapshots()` function producing timeline snapshots at 60s intervals with per-base breakdown and aggregate totals
- [x] 2.3 Include `saturation_timeline` in `generate_report_json()` output
- [x] 2.4 Add per-base saturation cards to `generate_report_html()` with mineral/gas bars, status labels, and idle worker warnings
- [x] 2.5 Update `generate_report_md()` with saturation section showing per-base breakdown and status

## 3. Core Bot — Worker transfer and dynamic probe production

- [x] 3.1 Rename `_get_base_saturation()` to `_get_rich_saturation()` and consolidate saturation logic (remove duplication with observation layer where safe)
- [x] 3.2 Implement `manage_worker_transfer()` in `src/bot/core.py`: oversaturated → undersaturated transfer, idle → gas reassignment, at most one action per step
- [x] 3.3 Implement late-game dynamic `MAX_WORKERS`: compute `dynamic_max = sum(ideal_workers) * 1.1` when `game_time > 900`
- [x] 3.4 Update `manage_probes()` to call `manage_worker_transfer()` after training logic, and respect dynamic max + undersaturated_bases check for probe training
- [x] 3.5 Add `idle_workers` and `undersaturated_bases`/`oversaturated_bases` aggregate detection to the observation or core layer for use by managers and events

## 4. Scouting — Worker scout secondary thread

- [x] 4.1 Add `_worker_scout_tag`, `_worker_scout_waypoint_index`, `_worker_scout_active` state to `MyBot.__init__()`
- [x] 4.2 Implement worker scout activation logic in `manage_scout()`: activate when idle > 1 or oversaturated base exists, game_time > 180, and scout confidence < 0.4
- [x] 4.3 Implement worker scout movement using existing `compute_next_scout_move()` with shared waypoints
- [x] 4.4 Implement worker scout deactivation: return to mining after completing waypoints, reset state on death

## 5. Strategy Engine — Builtins and YAML formulas

- [x] 5.1 Add `undersaturated_bases`, `oversaturated_bases`, `idle_workers`, `avg_mineral_sat`, `avg_gas_sat` to `prepare_builtins()` in `src/strategies/formula.py`
- [x] 5.2 Update PROBE formula in all 4 YAML profiles (`standard_macro`, `fast_expand`, `robo_open`, `stargate_open`) to use `undersaturated_bases > 0` condition
- [x] 5.3 Update NEXUS formula in all 4 YAML profiles to boost score when `oversaturated_bases > 0`
- [x] 5.4 Update ASSIMILATOR formula in all 4 YAML profiles to factor `avg_mineral_sat > 0.8`

## 6. Auto-Tuner — Saturation-aware adjustments

- [x] 6.1 Extend `load_match_results()` in `scripts/tune_strategies.py` to parse `saturation_timeline` from `report.json` when available
- [x] 6.2 Add temporal metrics to `analyze()`: `avg_oversat_duration`, `t_first_gas_saturated`, `idle_worker_minutes`, and `saturation_stability`
- [x] 6.3 Extend `compute_adjustments()` to adjust `fast_expand`, `gas_heavy`, and `max_workers` based on saturation metrics comparing wins vs losses
- [x] 6.4 Auto-tuner preserves existing behavior when `saturation_timeline` is not available (older reports)

## 7. Tests

- [x] 7.1 Add tests for enriched `_extract_base_features()` output in `tests/test_observation.py` (verify all new fields, status classification, idle detection)
- [x] 7.2 Add tests for `_build_saturation_snapshots()` in `tests/test_report.py`
- [x] 7.3 Add tests for `manage_worker_transfer()` scenarios in `tests/test_bot_logging.py` (mock-based, no SC2 required)
- [x] 7.4 Add tests for worker scout activation/deactivation in scout tests
- [x] 7.5 Add tests for new builtins in `tests/test_formula.py`
- [x] 7.6 Run full test suite: `uv run pytest` — all existing tests must still pass
