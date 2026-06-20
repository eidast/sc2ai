## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_army_composition, enemy_army_analysis, enemy_threat_assessment, recommended_counters, our_army_composition, our_structures, bases, game_time_seconds, and expansion_count

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
