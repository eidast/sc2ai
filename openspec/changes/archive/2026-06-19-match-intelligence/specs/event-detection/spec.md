## ADDED Requirements

### Requirement: Runtime event detection during on_step
The system SHALL detect gameplay events on every `on_step` call by comparing current `extract_features()` output against the previous step's features. Each detected event SHALL be logged to `events.jsonl` and made available to bot managers.

#### Scenario: Supply block detected
- **WHEN** `supply_left < 3` AND no Pylon is pending or in production
- **THEN** the system SHALL emit a `supply_block` event

#### Scenario: Enemy push detected
- **WHEN** `enemy_visible_units` increases by more than 10 units compared to the previous step
- **THEN** the system SHALL emit an `enemy_push` event

#### Scenario: Worker production stalled
- **WHEN** any Nexus is idle AND `worker_count < MAX_WORKERS` AND the bot can afford a Probe
- **THEN** the system SHALL emit a `worker_stalled` event

#### Scenario: Resource float detected
- **WHEN** `minerals > 500` AND all Gateways are idle AND no unit is in production
- **THEN** the system SHALL emit a `resource_float` event

#### Scenario: Attack ready
- **WHEN** `supply_used >= ATTACK_SUPPLY` (200)
- **THEN** the system SHALL emit an `attack_ready` event

#### Scenario: Tech milestone reached
- **WHEN** Cybernetics Core completes OR Warp Gate research finishes
- **THEN** the system SHALL emit a `tech_milestone` event

#### Scenario: No false events on game start
- **WHEN** the game has just started and `prev_features` is empty or all-zero
- **THEN** no events SHALL be emitted other than `game_start`

### Requirement: Tactical camera driven by game phase and events
The system SHALL select camera behavior based on `BuildPhase` and recently detected events instead of a static priority list. The camera SHALL move at most once per `on_step`.

#### Scenario: Camera follows scout probe in early game
- **WHEN** `BuildPhase` is `EARLY_GAME` AND the bot has a unit away from base (scout probe)
- **THEN** the camera SHALL follow that unit

#### Scenario: Camera locks on engagement during attack
- **WHEN** `attack_triggered` is True AND army units exist
- **THEN** the camera SHALL follow the attacking army

#### Scenario: Camera focuses on threat during defense
- **WHEN** an `enemy_push` event was detected AND enemy units are near a base
- **THEN** the camera SHALL center on the threatened base or enemy units

#### Scenario: Camera defaults to army in mid game
- **WHEN** no attack is active, no enemy threat exists, and army units exist
- **THEN** the camera SHALL follow the army

#### Scenario: Camera falls back to base
- **WHEN** no army units exist and no enemy threat exists
- **THEN** the camera SHALL center on the main townhall
