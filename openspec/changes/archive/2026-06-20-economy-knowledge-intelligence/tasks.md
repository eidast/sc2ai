## 1. Economy Foundation (Phase 1)

- [x] 1.1 Fix `manage_gas()` early-exit bug: change `return` to `continue` when can't afford assimilator at a geyser
- [x] 1.2 Add explicit gas worker assignment: `_assign_gas_workers()` method that sends idle workers to undersaturated assimilators
- [x] 1.3 Dynamic production capacity: compute target gateway count from bases + mineral float (4-16), replace hardcoded `target_gateways = 4`
- [x] 1.4 Mineral sink: build Forge when floating minerals > 300, start cycling ground upgrades (Weapons → Armor → Shields)
- [x] 1.5 Economy events: add `gas_starved` detection (high minerals, low vespene, undersaturated gas), lower `resource_float` threshold to 300

## 2. Unit Knowledge Base (Phase 2)

- [x] 2.1 Create `src/data/__init__.py` and `src/data/units.py` with `ALL_UNITS` dict covering all ladder units (Protoss, Zerg, Terran) and `get_unit_info()`, `get_units_by_attribute()`, `get_units_by_race()` functions
- [x] 2.2 Create `src/data/counters.py` with `compute_counters()` (effective DPS ranking of Protoss units vs enemy comp) and `compute_threat_assessment()` (enemy unit danger ranking)
- [x] 2.3 Create `src/data/icons.py` with `get_unit_icon_url()` and `get_unit_race_icon_url()` mapping to Liquipedia CDN, with fallback icon
- [x] 2.4 Enrich observation features: add `enemy_army_analysis`, `enemy_threat_assessment`, `recommended_counters` to `extract_features()` return dict
- [x] 2.5 Embed unit icons in HTML reports: modify `generate_report_html()` to render `<img>` tags alongside unit names in army composition tables

## 3. Intelligence — Scouting (Phase 3)

- [x] 3.1 Create `src/bot/scout.py` with `ScoutState` enum, `get_scout_waypoints()`, `should_retreat_scout()`, `compute_next_scout_move()` functions
- [x] 3.2 Integrate scout into bot loop: add `manage_scout()` method to `MyBot`, call from `on_step()` after `manage_defense()`

## 4. Intelligence — Upgrades (Phase 3)

- [x] 4.1 Create `src/bot/upgrades.py` with `UPGRADE_ORDER` list, `get_next_upgrade()`, `should_build_forge()`, `should_build_twilight()`, `get_twilight_upgrade()` functions
- [x] 4.2 Integrate upgrade engine into bot loop: add `manage_upgrades()` method to `MyBot` (replaces Phase 1's simpler `manage_forge_upgrades()`), call from `on_step()` after `manage_tech()` — includes Forge, Twilight Council, ground upgrades, Charge/Blink

## 5. Intelligence — Adaptive Production (Phase 3)

- [x] 5.1 Adapt unit production to enemy counters: modify `manage_army()` to use `recommended_counters` to choose primary/secondary unit type (Zealot/Stalker), with Immortal fallback to Stalker

## 6. Verification

- [x] 6.1 Run full test suite (`uv run pytest tests/ -v`) — all tests must pass without SC2 instance
- [x] 6.2 Verify existing specs still satisfied: bot-gameplay, observation-pipeline, reactive-defense, army-composition-tracking
- [x] 6.3 Verify new spec scenarios are covered by tests: gas-economy, unit-knowledge-base, scout-behavior, upgrade-strategy
