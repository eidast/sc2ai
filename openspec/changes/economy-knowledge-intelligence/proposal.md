## Why

The bot currently runs a fixed Protoss macro script — it produces stalkers, waits for 200 supply, and attacks. It can't adapt to what the enemy is doing, can't scout, can't choose upgrades, and has a concrete gas economy bug that causes severe mineral floating. These three layers — economy, knowledge, and intelligence — are the prerequisites for an actual AI bot that can make decisions instead of following a script.

## What Changes

- **Fix gas economy bug**: `manage_gas()` exits early when it can't afford an assimilator, skipping all other geysers. Add explicit gas worker assignment and dynamic gateway count scaling to spend excess minerals.
- **Add mineral sinks**: Build Forge + start ground upgrades when floating minerals, giving the bot something useful to spend excess on.
- **Build unit knowledge base**: Static database of all ladder unit properties (HP, shields, armor, attributes, attacks) for Protoss, Zerg, and Terran. Counter calculation engine based on effective damage.
- **Add scouting behavior**: Send a probe to explore enemy starting locations, detect enemy structures, and retreat when threatened. Provides the intel needed for adaptive decisions.
- **Add upgrade decision engine**: Prioritize ground weapons/armor/shields cycling, build Twilight Council, research Charge or Blink based on scouted enemy.
- **Enrich observation features**: Add enemy army analysis (armor type counts, DPS, threat assessment) and recommended counters to the feature vector.
- **Embed unit icons in reports**: Add faction and unit icons from Liquipedia CDN to HTML match reports.
- **Adapt unit production**: Use counter recommendations to choose between Zealots, Stalkers, or Immortals based on scouted enemy composition.

## Capabilities

### New Capabilities
- `unit-knowledge-base`: Static database of SC2 unit properties, counter calculation engine, and icon URL mappings for all three races
- `scout-behavior`: Probe-based map exploration with waypoints, enemy structure detection, and retreat logic
- `upgrade-strategy`: Forge construction, ground upgrade priority cycling, Twilight Council, and Charge/Blink research based on enemy context
- `gas-economy`: Fixed gas management loop, explicit gas worker assignment, dynamic production capacity scaling with mineral float

### Modified Capabilities
- `bot-gameplay`: Bot loop extended with scout management, upgrade management, adaptive unit production, and economy fixes. Existing macro behaviors (probes, pylons, expansion, army, defense, attack) remain intact.
- `observation-pipeline`: Feature extraction returns new enriched enemy analysis fields (armor type breakdown, DPS estimates, threat ranking, counter recommendations)

## Impact

- **New files**: `src/data/__init__.py`, `src/data/units.py`, `src/data/counters.py`, `src/data/icons.py`, `src/bot/scout.py`, `src/bot/upgrades.py`
- **Modified files**: `src/bot/core.py`, `src/bot/strategy.py`, `src/ml/observation.py`, `src/ml/events.py`, `src/ml/report.py`
- **New test files**: `tests/test_economy.py`, `tests/test_unit_data.py`, `tests/test_scout.py`, `tests/test_upgrades.py` (partially: data tests appended to `tests/test_unit_data.py`)
- **Modified test files**: `tests/test_events.py`, `tests/test_observation.py`, `tests/test_report.py`
- **No new dependencies**: All work uses existing python-sc2 API and standard library
- **No breaking changes**: All existing bot behaviors preserved, new behaviors are additive
