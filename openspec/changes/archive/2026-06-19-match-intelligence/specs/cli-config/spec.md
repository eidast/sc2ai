## ADDED Requirements

### Requirement: Launch script accepts --realtime flag
The system SHALL accept a `--realtime` flag in `scripts/run.py` that, when present, sets `realtime=True` in the `run_game()` call instead of the default `realtime=False`.

#### Scenario: Realtime mode enabled
- **WHEN** `uv run python scripts/run.py --realtime` is executed
- **THEN** the game SHALL run at normal speed with rendering enabled

#### Scenario: Default is accelerated
- **WHEN** `uv run python scripts/run.py` is executed without `--realtime`
- **THEN** the game SHALL run in accelerated mode (`realtime=False`)

### Requirement: Launch script accepts --map argument
The system SHALL accept a `--map` argument in `scripts/run.py` that specifies the map to play on. The value SHALL be validated against available maps.

#### Scenario: Specific map selected
- **WHEN** `uv run python scripts/run.py --map ThunderbirdLE` is executed
- **THEN** the game SHALL launch on the ThunderbirdLE map

#### Scenario: Random map selected
- **WHEN** `uv run python scripts/run.py --map random` is executed
- **THEN** a random map from the available maps SHALL be selected and the game SHALL launch on it

#### Scenario: Invalid map produces error
- **WHEN** `uv run python scripts/run.py --map NonExistentMap` is executed
- **THEN** the script SHALL report an error with the invalid map name and list available maps

#### Scenario: Default map is AcropolisLE
- **WHEN** `uv run python scripts/run.py` is executed without `--map`
- **THEN** the game SHALL launch on AcropolisLE

### Requirement: Existing OS detection behavior is preserved
The system SHALL preserve all existing OS auto-detection behavior (macOS Darwin paths, Windows paths, unsupported OS error) when CLI arguments are added.

#### Scenario: macOS detection still works
- **WHEN** the script runs on macOS with any CLI arguments
- **THEN** `SC2_DIR` SHALL be `/Applications/StarCraft II` and the game SHALL launch

#### Scenario: Windows detection still works
- **WHEN** the script runs on Windows with any CLI arguments
- **THEN** `SC2_DIR` SHALL be `C:\Program Files (x86)\StarCraft II` and the game SHALL launch
