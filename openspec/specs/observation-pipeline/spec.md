## ADDED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, collected_minerals, collected_vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_army_composition, our_army_composition, our_structures, bases, game_time_seconds, and expansion_count

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
