## MODIFIED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_army_composition, game_time_seconds, and expansion_count

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
