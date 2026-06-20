## ADDED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, game_time_seconds, and expansion_count

#### Scenario: Feature extraction does not crash on empty state
- **WHEN** the game has just started and no enemy units are visible
- **THEN** `extract_features()` SHALL return zeros or empty defaults for all fields without raising exceptions

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
