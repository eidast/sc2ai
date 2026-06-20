## MODIFIED Requirements

### Requirement: Bot plays Protoss macro strategy
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression, army production, and a final attack when max supply is reached. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context.

#### Scenario: Constant worker production
- **WHEN** the bot has fewer than 70 probes and available supply
- **THEN** the bot SHALL queue a probe from the Nexus

#### Scenario: Supply management
- **WHEN** available supply drops below 4
- **THEN** the bot SHALL build a Pylon at a valid placement location

#### Scenario: Supply block reactivity
- **WHEN** a `supply_block` event is detected (supply_left < 3 and no pylon pending)
- **THEN** the bot SHALL prioritize pylon construction above other build actions

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

#### Scenario: Tactical camera in early game
- **WHEN** the bot is in `EARLY_GAME` phase
- **THEN** the camera SHALL follow the scout probe if one exists, otherwise center on the main base

#### Scenario: Tactical camera during engagement
- **WHEN** `attack_triggered` is True and army units exist
- **THEN** the camera SHALL follow the attacking army

#### Scenario: Tactical camera during defense
- **WHEN** an `enemy_push` event is detected
- **THEN** the camera SHALL focus on the location of enemy units

### Requirement: Bot detects gameplay events during on_step
The system SHALL detect key gameplay events on every `on_step` call by comparing current features against the previous step. Events SHALL include at minimum: `supply_block`, `enemy_push`, `worker_stalled`, `resource_float`, `tech_milestone`, and `attack_ready`.

#### Scenario: Events detected each step
- **WHEN** `on_step` is called
- **THEN** the bot SHALL run event detection and make detected events available to managers

#### Scenario: No events on first step
- **WHEN** `on_step` is called at iteration 0
- **THEN** no events other than `game_start` SHALL be emitted

### Requirement: Games run at accelerated speed for testing
The system SHALL support running games in non-realtime mode (`realtime=False`) so matches complete quickly during development. The system SHALL also support running games in realtime mode (`realtime=True`) via the `--realtime` CLI flag.

#### Scenario: Accelerated game execution
- **WHEN** the bot is launched with `realtime=False` (default)
- **THEN** the game SHALL run as fast as the CPU allows without rendering delays

#### Scenario: Realtime game execution
- **WHEN** the bot is launched with the `--realtime` flag
- **THEN** the game SHALL run at normal speed with rendering enabled

## ADDED Requirements

### Requirement: Bot generates match reports on game end
The system SHALL generate per-match reports when `on_end` is called, using the persisted `features.jsonl` and `events.jsonl` data. The reports SHALL include JSON, HTML, and Markdown formats.

#### Scenario: Reports generated on game end
- **WHEN** `on_end` is called with a game result
- **THEN** `report.json`, `report.html`, and `report.md` SHALL be written to `reports/{match_id}/`

#### Scenario: Index updated on game end
- **WHEN** a new match report is generated
- **THEN** `reports/index.html` SHALL be regenerated to include the new match
