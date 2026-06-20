## ADDED Requirements

### Requirement: Bot launches and connects to StarCraft II
The system SHALL launch a StarCraft II game instance and connect a Protoss bot to it using the python-sc2 `run_game` interface. The launch script SHALL resolve the configured map before starting the game and report a clear project-specific error if the map is unavailable.

#### Scenario: Game starts successfully
- **WHEN** the user runs the bot launch script and the configured map is installed
- **THEN** StarCraft II opens, loads the specified map, and the bot begins receiving `on_step` calls

#### Scenario: Missing map is reported clearly
- **WHEN** the configured map is not found in the Maps directory
- **THEN** the system SHALL report an error message containing the missing map name, the expected Maps directory, and the `scripts/setup_maps.sh` helper path

### Requirement: Bot plays Protoss macro strategy
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression, army production, and a final attack when max supply is reached.

#### Scenario: Constant worker production
- **WHEN** the bot has fewer than 70 probes and available supply
- **THEN** the bot SHALL queue a probe from the Nexus

#### Scenario: Supply management
- **WHEN** available supply drops below 4
- **THEN** the bot SHALL build a Pylon at a valid placement location

#### Scenario: Natural expansion
- **WHEN** the bot reaches approximately 20 supply and has enough minerals
- **THEN** the bot SHALL send a probe to build a Nexus at the natural expansion location

#### Scenario: Tech progression
- **WHEN** the bot has a completed Gateway
- **THEN** the bot SHALL build a Cybernetics Core, then research Warp Gate, and add additional Gateways

#### Scenario: Army production
- **WHEN** the bot has available resources and production capacity
- **THEN** the bot SHALL produce army units (Stalkers, Zealots) from Gateways

#### Scenario: Attack at max supply
- **WHEN** the bot reaches 200 supply
- **THEN** the bot SHALL send all army units to attack the enemy starting location

### Requirement: Bot can play against built-in AI
The system SHALL configure the game to play against Blizzard's built-in Computer opponent at a specified difficulty level.

#### Scenario: Match against Computer opponent
- **WHEN** the game is configured with `Computer(Race.Terran, Difficulty.Medium)` as opponent
- **THEN** the built-in AI SHALL control the opposing player and the match SHALL play to completion

### Requirement: Games run at accelerated speed for testing
The system SHALL support running games in non-realtime mode (`realtime=False`) so matches complete quickly during development.

#### Scenario: Accelerated game execution
- **WHEN** the bot is launched with `realtime=False`
- **THEN** the game SHALL run as fast as the CPU allows without rendering delays
