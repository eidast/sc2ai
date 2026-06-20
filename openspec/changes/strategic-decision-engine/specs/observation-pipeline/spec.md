## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_worker_count, enemy_army_composition, enemy_army_analysis, enemy_threat_assessment, recommended_counters, our_army_composition, our_structures, our_army_value, enemy_army_value, army_value_ratio, enemy_t3_count, our_t3_count, bases, game_time_seconds, and expansion_count

#### Scenario: Our army composition is tracked
- **WHEN** the bot has combat units (Stalkers, Zealots, etc.)
- **THEN** `our_army_composition` SHALL contain a mapping of unit type name to count, excluding workers and observers

#### Scenario: Our army composition is empty when no combat units
- **WHEN** the bot has only probes
- **THEN** `our_army_composition` SHALL be an empty dict `{}`

#### Scenario: Per-base saturation data is included
- **WHEN** `extract_features()` is called
- **THEN** `bases` SHALL be a list of dicts, each containing: `position` (tuple of floats), `ideal_workers` (int), `current_workers` (int), `saturation_ratio` (float), `enemy_nearby` (int), `army_nearby` (int)

#### Scenario: Enemy army composition is available when enemies are visible
- **WHEN** enemy units are visible on the map
- **THEN** `enemy_army_composition` SHALL contain a mapping of unit type name to count (e.g., `{"Marine": 8, "SiegeTank": 2}`)

#### Scenario: Enemy army composition is empty when no enemies visible
- **WHEN** no enemy units are visible
- **THEN** `enemy_army_composition` SHALL be an empty dict `{}`

#### Scenario: Feature extraction does not crash on empty state
- **WHEN** the game has just started and no enemy units are visible
- **THEN** `extract_features()` SHALL return zeros or empty defaults for all fields without raising exceptions
