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
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression, army production, and a final attack when max supply is reached. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context.

#### Scenario: Constant worker production
- **WHEN** the bot has fewer than 70 probes and available supply
- **THEN** the bot SHALL prioritize probe training at the nexus with the lowest saturation ratio. A nexus SHALL be skipped if its saturation ratio is ≥ 0.9.

#### Scenario: Supply management
- **WHEN** available supply drops below 4
- **THEN** the bot SHALL build a Pylon at a valid placement location

#### Scenario: Supply block reactivity
- **WHEN** a `supply_block` event is detected (supply_left < 3 and no pylon pending)
- **THEN** the bot SHALL prioritize pylon construction above other build actions

#### Scenario: Natural expansion
- **WHEN** ALL current nexuses have saturation ratio ≥ 0.9 AND the bot can afford a Nexus AND no Nexus is already pending
- **THEN** the bot SHALL send a probe to build a Nexus at the next expansion location. There SHALL be no hard limit on the number of expansions.

#### Scenario: Tech progression
- **WHEN** the bot has a completed Gateway
- **THEN** the bot SHALL build a Cybernetics Core, then research Warp Gate, and add additional Gateways

#### Scenario: Army production
- **WHEN** the bot has available resources and production capacity
- **THEN** the bot SHALL produce army units (Stalkers, Zealots) from Gateways

#### Scenario: Attack at max supply
- **WHEN** the bot reaches 200 supply
- **THEN** the bot SHALL send all army units to attack the enemy starting location. Attack commands SHALL take priority over defensive repositioning.

#### Scenario: Tactical camera in early game
- **WHEN** the bot is in `EARLY_GAME` phase
- **THEN** the camera SHALL follow the scout probe if one exists, otherwise center on the main base

#### Scenario: Tactical camera during engagement
- **WHEN** `attack_triggered` is True and army units exist
- **THEN** the camera SHALL follow the attacking army

#### Scenario: Tactical camera during defense
- **WHEN** an `enemy_push` event is detected
- **THEN** the camera SHALL focus on the location of enemy units

### Requirement: Bot can play against built-in AI
The system SHALL configure the game to play against Blizzard's built-in Computer opponent at a specified difficulty level.

#### Scenario: Match against Computer opponent
- **WHEN** the game is configured with `Computer(Race.Terran, Difficulty.Medium)` as opponent
- **THEN** the built-in AI SHALL control the opposing player and the match SHALL play to completion

### Requirement: Bot aggressively cleans up remaining enemy structures
The system SHALL make `manage_attack()` actively search for and destroy remaining enemy structures while the decision engine is in `ATTACK`.

#### Scenario: Visible enemy structure is prioritized
- **WHEN** the decision state is `ATTACK`, army units exist, and at least one enemy structure is visible
- **THEN** idle army units SHALL attack the closest visible enemy structure instead of a generic map waypoint

#### Scenario: Cleanup sweeps known map locations
- **WHEN** the decision state is `ATTACK`, army units exist, and no enemy structures are visible
- **THEN** idle army units SHALL attack a cleanup waypoint selected from the enemy starting location and known expansion locations

#### Scenario: Cleanup advances after reaching waypoint
- **WHEN** the attacking army is close to the current cleanup waypoint
- **THEN** the bot SHALL advance to the next cleanup waypoint for subsequent attack orders

#### Scenario: Macro continues during cleanup
- **WHEN** cleanup attack orders are being issued in `ATTACK`
- **THEN** the bot SHALL continue running the existing macro managers before `manage_attack()` in `on_step()`

#### Scenario: Cleanup does not alter victory result semantics
- **WHEN** cleanup attack behavior is active
- **THEN** the bot SHALL still accept victory only from SC2 `player_result` or the existing sustained no-enemy-visible heuristic

### Requirement: Games run at accelerated speed for testing
The system SHALL support running games in non-realtime mode (`realtime=False`) so matches complete quickly during development. The system SHALL also support running games in realtime mode (`realtime=True`) via the `--realtime` CLI flag.

#### Scenario: Accelerated game execution
- **WHEN** the bot is launched with `realtime=False` (default)
- **THEN** the game SHALL run as fast as the CPU allows without rendering delays

#### Scenario: Realtime game execution
- **WHEN** the bot is launched with the `--realtime` flag
- **THEN** the game SHALL run at normal speed with rendering enabled

### Requirement: Bot detects gameplay events during on_step
The system SHALL detect key gameplay events on every `on_step` call by comparing current features against the previous step. Events SHALL include at minimum: `supply_block`, `enemy_push`, `worker_stalled`, `resource_float`, `tech_milestone`, `attack_ready`, `expansion_started`, `base_under_attack`, and `base_oversaturated`.

#### Scenario: Events detected each step
- **WHEN** `on_step` is called
- **THEN** the bot SHALL run event detection and make detected events available to managers

#### Scenario: Base oversaturation event
- **WHEN** a nexus has saturation > 1.0 and another nexus has saturation < 0.9
- **THEN** a `base_oversaturated` event SHALL be emitted

#### Scenario: Base under attack event
- **WHEN** enemy units are within THREAT_RANGE of a nexus and have attack orders
- **THEN** a `base_under_attack` event SHALL be emitted

#### Scenario: No events on first step
- **WHEN** `on_step` is called at iteration 0
- **THEN** no events other than `game_start` SHALL be emitted

### Requirement: Bot generates match reports on game end
The system SHALL generate per-match reports when `on_end` is called, using the persisted `features.jsonl` and `events.jsonl` data. The reports SHALL include JSON, HTML, and Markdown formats. The HTML report SHALL display our army composition and enemy army composition in separate, correctly-aligned tables. The opponent race SHALL be taken from actual game data (`self.enemy_race`) rather than hardcoded.

#### Scenario: Reports generated on game end
- **WHEN** `on_end` is called with a game result
- **THEN** `report.json`, `report.html`, and `report.md` SHALL be written to `reports/{match_id}/`

#### Scenario: HTML report has correct table columns
- **WHEN** an HTML report is generated
- **THEN** the "Our Army" table SHALL have matching header and data column counts, and the "Enemy Army" table SHALL be populated with enemy composition data

#### Scenario: Opponent race from game data
- **WHEN** a report is generated after a match against a Terran opponent
- **THEN** the `opponent_race` field SHALL reflect the actual race (`Terran`, `Protoss`, or `Zerg`) from `self.enemy_race.name`

#### Scenario: Index updated on game end
- **WHEN** a new match report is generated
- **THEN** `reports/index.html` SHALL be regenerated to include the new match

### Requirement: Bot executes defensive behavior during on_step
The system SHALL execute `manage_defense()` on every `on_step` before `manage_attack()`. Defense SHALL evaluate threats per base, reposition idle army units toward threatened bases, and engage enemy units within range.

#### Scenario: Defense runs before attack
- **WHEN** `on_step` is called
- **THEN** `manage_defense()` SHALL execute before `manage_attack()` in the dispatch order

#### Scenario: Army repositions when threatened
- **WHEN** enemy units are detected near a base and our army is idle elsewhere
- **THEN** idle army units SHALL be ordered to move toward the threatened base

#### Scenario: Army engages when in range
- **WHEN** army units are within 8 range of enemy units near a threatened base
- **THEN** idle army units SHALL attack the closest enemy unit
