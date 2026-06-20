## MODIFIED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_army_composition, our_army_composition, our_structures, bases, game_time_seconds, and expansion_count

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

## ADDED Requirements

### Requirement: Our structure composition is included in features
The system SHALL include `our_structures` in extracted features, mapping structure type names to counts of all owned structures (ready and pending).

#### Scenario: Structure tracking
- **WHEN** the bot has 2 Gateways, 1 Cybernetics Core, and 1 Pylon
- **THEN** `our_structures` SHALL be `{"GATEWAY": 2, "CYBERNETICSCORE": 1, "PYLON": 1, "NEXUS": 1, "ASSIMILATOR": 0}` (all zero-value types present for schema consistency)
