## MODIFIED Requirements

### Requirement: Bot launches and connects to StarCraft II
The system SHALL launch a StarCraft II game instance and connect a Protoss bot to it using the python-sc2 `run_game` interface. The launch script SHALL resolve the configured map before starting the game and report a clear project-specific error if the map is unavailable.

#### Scenario: Game starts successfully
- **WHEN** the user runs the bot launch script and the configured map is installed
- **THEN** StarCraft II opens, loads the specified map, and the bot begins receiving `on_step` calls

#### Scenario: Missing map is reported clearly
- **WHEN** the configured map is not found in the Maps directory
- **THEN** the system SHALL report an error message containing the missing map name, the expected Maps directory, and the `scripts/setup_maps.sh` helper path
