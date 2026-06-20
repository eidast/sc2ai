## ADDED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, collected_minerals, collected_vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_worker_count, enemy_army_composition, enemy_army_analysis, enemy_threat_assessment, recommended_counters, our_army_composition, our_structures, our_army_value, enemy_army_value, army_value_ratio, enemy_t3_count, our_t3_count, bases, game_time_seconds, and expansion_count

#### Scenario: Collected resources are available when score exists
- **WHEN** `bot.state.score.collected_minerals` and `bot.state.score.collected_vespene` are accessible
- **THEN** `collected_minerals` and `collected_vespene` SHALL reflect the cumulative totals from game score

#### Scenario: Collected resources default to zero when score unavailable
- **WHEN** `bot.state` or `bot.state.score` is not accessible (testing, early init)
- **THEN** `collected_minerals` and `collected_vespene` SHALL both be 0

#### Scenario: Our army composition is tracked
- **WHEN** the bot has combat units (Stalkers, Zealots, etc.)
- **THEN** `our_army_composition` SHALL contain a mapping of unit type name to count, excluding workers and observers

#### Scenario: Our army composition is empty when no combat units
- **WHEN** the bot has only probes
- **THEN** `our_army_composition` SHALL be an empty dict `{}`

### Requirement: Per-base saturation data is included
- **WHEN** `extract_features()` is called
- **THEN** `bases` SHALL be a list of dicts, each containing: `position` (tuple of floats), `ideal_workers` (int, retained for backward compatibility), `current_workers` (int), `saturation_ratio` (float, retained as alias for total_saturation), `enemy_nearby` (int), `army_nearby` (int), plus the new fields: `mineral_patches` (int), `gas_geysers` (int), `ideal_mineral_workers` (int), `ideal_gas_workers` (int), `actual_mineral_workers` (int), `actual_gas_workers` (int), `idle_workers_nearby` (int), `mineral_saturation` (float), `gas_saturation` (float), `total_saturation` (float), and `status` (str).

#### Scenario: Enriched base dict includes mineral/gas split
- **WHEN** extract_features is called on a bot with a base that has 8 mineral patches, 2 gas geysers, 14 mineral workers, and 4 gas workers
- **THEN** the base dict SHALL contain `mineral_patches: 8`, `gas_geysers: 2`, `actual_mineral_workers: 14`, `actual_gas_workers: 4`, `mineral_saturation: 0.875`, `gas_saturation: 0.667`, `total_saturation: 0.818`, and `status: "undersaturated"`

#### Scenario: Legacy fields preserved for backward compatibility
- **WHEN** extract_features is called
- **THEN** each base dict SHALL still contain `ideal_workers`, `current_workers`, and `saturation_ratio` with values matching the total mineral+gas workers and saturation

#### Scenario: Enemy army composition is available when enemies are visible
- **WHEN** enemy units are visible on the map
- **THEN** `enemy_army_composition` SHALL contain a mapping of unit type name to count (e.g., `{"Marine": 8, "SiegeTank": 2}`)

#### Scenario: Enemy army composition is empty when no enemies visible
- **WHEN** no enemy units are visible
- **THEN** `enemy_army_composition` SHALL be an empty dict `{}`

#### Scenario: Feature extraction does not crash on empty state
- **WHEN** the game has just started and no enemy units are visible
- **THEN** `extract_features()` SHALL return zeros or empty defaults for all fields without raising exceptions

### Requirement: Our structure composition is included in features
The system SHALL include `our_structures` in extracted features, mapping structure type names to counts of all owned structures (ready and pending).

#### Scenario: Structure tracking
- **WHEN** the bot has 2 Gateways, 1 Cybernetics Core, and 1 Pylon
- **THEN** `our_structures` SHALL be `{"GATEWAY": 2, "CYBERNETICSCORE": 1, "PYLON": 1, "NEXUS": 1, "ASSIMILATOR": 0}` (all zero-value types present for schema consistency)

### Requirement: Features are logged every N steps
The system SHALL log extracted features at a configurable interval (default every 22 steps, approximately 1 second) using Python's `logging` module. The bot SHALL allow callers to override this interval during initialization.

#### Scenario: Features appear in log output
- **WHEN** the bot runs with logging enabled at INFO level
- **THEN** the extracted feature dictionary SHALL appear in the console/log output at the configured interval

#### Scenario: Logging interval is configurable
- **WHEN** the bot is initialized with `log_interval=44`
- **THEN** features SHALL be logged every 44 steps instead of the default 22

### Requirement: Replays are saved after each match
The system SHALL save a StarCraft II replay file after each completed match to the `replays/` directory with a timestamped filename.

#### Scenario: Replay file exists after match
- **WHEN** a match ends (win or loss)
- **THEN** a `.SC2Replay` file SHALL exist in `replays/` with a filename containing the date and result

#### Scenario: Replay directory is created if missing
- **WHEN** the `replays/` directory does not exist at match start
- **THEN** the system SHALL create it before saving the replay

### Requirement: Features are persisted to file during gameplay
The system SHALL append each step's extracted features to a `features.jsonl` file in the match report directory, so match data survives even if the game crashes before `on_end`.

#### Scenario: Features appended each step
- **WHEN** `on_step` is called and features are extracted
- **THEN** the feature dictionary SHALL be written as one JSON line to `reports/{match_id}/features.jsonl`

#### Scenario: Match directory created on first step
- **WHEN** `on_step` is called for the first time (iteration 0)
- **THEN** the `reports/{match_id}/` directory SHALL be created if it does not exist

### Requirement: Events are persisted to file during gameplay
The system SHALL append each detected event to an `events.jsonl` file in the match report directory.

#### Scenario: Event appended when detected
- **WHEN** an event is detected by the event detection system
- **THEN** the event SHALL be written as one JSON line to `reports/{match_id}/events.jsonl`

### Requirement: Configurable logging interval preserves existing behavior
The system SHALL continue to log extracted features at a configurable interval (default every 22 steps) using Python's `logging` module, unchanged from the original implementation.

#### Scenario: Features appear in log output
- **WHEN** the bot runs with logging enabled at INFO level
- **THEN** the extracted feature dictionary SHALL appear in the console/log output at the configured interval

#### Scenario: Logging interval is configurable
- **WHEN** the bot is initialized with `log_interval=44`
- **THEN** features SHALL be logged every 44 steps instead of the default 22

### Requirement: Enemy army analysis is included in features
The system SHALL include enriched enemy army analysis in extracted features. The analysis SHALL break down enemy composition by armor type (armored, light, biological, mechanical, massive, air), compute total HP and shields, and estimate ground and air DPS. The system SHALL also include a threat assessment ranking enemy unit types by danger and recommended counter units for Protoss.

#### Scenario: Enemy analysis with visible units
- **WHEN** enemy units are visible with known unit types
- **THEN** `enemy_army_analysis` SHALL contain `armored_count`, `light_count`, `biological_count`, `mechanical_count`, `massive_count`, `air_count`, `total_hp`, `total_shields`, `ground_dps`, and `air_dps`

#### Scenario: Enemy analysis with no visible units
- **WHEN** no enemy units are visible
- **THEN** `enemy_army_analysis` SHALL contain all fields with zero or 0.0 values

#### Scenario: Threat assessment ranks enemies
- **WHEN** enemy units are visible
- **THEN** `enemy_threat_assessment` SHALL be a dict mapping enemy unit type names to threat scores, sorted from highest to lowest

#### Scenario: Counter recommendations provided
- **WHEN** enemy units are visible
- **THEN** `recommended_counters` SHALL be a dict mapping Protoss unit type names to counter scores, sorted from highest to lowest

#### Scenario: Counter recommendations empty when no enemy visible
- **WHEN** no enemy units are visible
- **THEN** `recommended_counters` SHALL be an empty dict

### Requirement: Army value metrics are included in features
The system SHALL include `our_army_value`, `enemy_army_value`, and `army_value_ratio` in the extracted features dictionary.

#### Scenario: Army value fields present
- **WHEN** `extract_features()` is called
- **THEN** the returned dict SHALL contain `our_army_value` (int), `enemy_army_value` (int), and `army_value_ratio` (float)

### Requirement: T3 unit counts are included in features
The system SHALL include `enemy_t3_count` and `our_t3_count` in extracted features, counting only combat units classified as tier-3 for each race.

#### Scenario: T3 counts present
- **WHEN** `extract_features()` is called
- **THEN** `enemy_t3_count` SHALL be the number of visible enemy T3 combat units and `our_t3_count` SHALL be the number of our T3 combat units

#### Scenario: T3 counts zero when no T3 units
- **WHEN** neither player has T3 units
- **THEN** `enemy_t3_count` and `our_t3_count` SHALL both be 0

### Requirement: Enemy worker count is included in features
The system SHALL include `enemy_worker_count` in extracted features.

#### Scenario: Worker count present
- **WHEN** `extract_features()` is called
- **THEN** `enemy_worker_count` SHALL be the count of visible enemy worker units (SCV, Drone, Probe)
