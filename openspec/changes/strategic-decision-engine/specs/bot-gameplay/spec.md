## ADDED Requirements

### Requirement: MyBot accepts surrender and fog configuration
The system SHALL allow the caller to pass `surrender_enabled` and `fog_enabled` flags when constructing a `MyBot` instance.

#### Scenario: Flags passed to bot
- **WHEN** `MyBot(surrender_enabled=True, fog_enabled=True)` is constructed
- **THEN** the bot SHALL store these values for use by the decision engine

#### Scenario: Default values preserve current behavior
- **WHEN** `MyBot()` is constructed with no arguments
- **THEN** `surrender_enabled` SHALL be False and `fog_enabled` SHALL be False

### Requirement: MyBot uses decision engine state for attack decisions
The system SHALL replace the `attack_triggered` boolean with a decision engine state (`DEFEND`, `ATTACK`, `RECOVER`, `SURRENDER`) used by `manage_attack()`.

#### Scenario: Attack managed when FSM in ATTACK
- **WHEN** the decision state is ATTACK and army units exist
- **THEN** `manage_attack()` SHALL send idle army units to attack the enemy start location

#### Scenario: Attack not managed when FSM in DEFEND
- **WHEN** the decision state is DEFEND
- **THEN** `manage_attack()` SHALL NOT issue attack orders

#### Scenario: Defense skipped when FSM in ATTACK
- **WHEN** the decision state is ATTACK
- **THEN** `manage_defense()` SHALL return early without repositioning

### Requirement: MyBot executes surrender on SURRENDER state
The system SHALL implement `manage_surrender()` which triggers when the decision state is SURRENDER.

#### Scenario: Surrender sends gg and stops actions
- **WHEN** the decision state transitions to SURRENDER
- **THEN** the bot SHALL call `chat_send("gg")` and the `manage_surrender()` method SHALL be called in `on_step()`

#### Scenario: Surrender event logged
- **WHEN** surrender is triggered
- **THEN** a `surrender` event SHALL be written to the events file with details including game_time and army_value_ratio

#### Scenario: Other managers skip when surrendered
- **WHEN** the decision state is SURRENDER
- **THEN** all other `manage_*()` methods SHALL be skipped in `on_step()`

### Requirement: Decision engine runs in on_step before managers
The system SHALL evaluate the decision engine at the beginning of `on_step()`, after feature extraction, so all managers consume the current decision state.

#### Scenario: Evaluate decision each step
- **WHEN** `on_step()` is called after iteration 0
- **THEN** `evaluate_decision()` SHALL be called and the result stored before any `manage_*()` calls

#### Scenario: Decision state persists across steps
- **WHEN** the decision state is RECOVER
- **THEN** it SHALL remain RECOVER on subsequent steps until a transition condition is met

### Requirement: CLI exposes surrender and fog flags
The system SHALL add `--surrender` and `--fog` flags to `scripts/run.py`.

#### Scenario: Surrender flag enables surrender
- **WHEN** `python scripts/run.py --surrender` is executed
- **THEN** the bot SHALL be initialized with `surrender_enabled=True`

#### Scenario: Fog flag enables fog-of-war
- **WHEN** `python scripts/run.py --fog` is executed
- **THEN** the game SHALL be started with `disable_fog=False` and the bot SHALL be initialized with `fog_enabled=True`

#### Scenario: No flags preserves current behavior
- **WHEN** `python scripts/run.py` is executed with no new flags
- **THEN** the bot SHALL start with `surrender_enabled=False, fog_enabled=False` and `disable_fog=True`

## MODIFIED Requirements

### Requirement: Bot plays Protoss macro strategy
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression (including Forge, Twilight Council, and ground upgrades), army production (adaptive based on scouted enemy counters), and attack decisions driven by the strategic decision engine instead of a fixed supply threshold. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context. The bot SHALL send a scout probe to explore enemy starting locations. The bot SHALL fix gas economy by continuing to the next geyser when an assimilator is unaffordable and assigning workers to undersaturated assimilators. The bot SHALL optionally surrender when the decision engine determines victory is impossible.

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
- **THEN** the bot SHALL build a Cybernetics Core, then research Warp Gate, dynamically scale Gateway count based on bases and mineral float (4-16), build Forge when floating minerals, build Twilight Council after Cyber Core, and start ground upgrades cycling through Weapons/Armor/Shields

#### Scenario: Army production adapts to enemy
- **WHEN** the bot has available resources and production capacity AND enemy composition data is available
- **THEN** the bot SHALL use counter recommendations to prioritize army units (Zealot if recommended vs light, Stalker if recommended vs armored, Stalker as fallback if recommended unit is not gateway-trainable)

#### Scenario: Army production default
- **WHEN** the bot has available resources and production capacity AND no enemy data is available (scout dead or no enemies seen)
- **THEN** the bot SHALL produce Stalkers primarily and Zealots secondarily from Gateways

#### Scenario: Attack driven by decision engine
- **WHEN** the decision engine transitions to ATTACK state
- **THEN** the bot SHALL send idle army units to attack the enemy starting location. Attack commands SHALL take priority over defensive repositioning.

#### Scenario: Surrender when decision engine triggers
- **WHEN** the decision engine transitions to SURRENDER state AND surrender is enabled
- **THEN** the bot SHALL send `chat_send("gg")`, skip all remaining managers, and log a surrender event

#### Scenario: Scout explores enemy start locations
- **WHEN** game time is less than 30 seconds
- **THEN** the bot SHALL dispatch a probe to explore enemy starting locations in sequence

#### Scenario: Upgrades researched when floating
- **WHEN** minerals exceed 300 and a Forge is ready
- **THEN** the bot SHALL research the next ground upgrade in priority order

#### Scenario: Twilight upgrade adapts to enemy
- **WHEN** a Twilight Council is ready and enemy army analysis is available
- **THEN** the bot SHALL research Blink if enemy has > 3 air units, otherwise Charge

#### Scenario: Gas economy continues past unaffordable geysers
- **WHEN** the first geyser is not affordable
- **THEN** the bot SHALL continue checking remaining geysers and nexuses for assimilator construction

#### Scenario: Tactical camera in early game
- **WHEN** the bot is in `EARLY_GAME` phase
- **THEN** the camera SHALL follow the scout probe if one exists, otherwise center on the main base

#### Scenario: Tactical camera during engagement
- **WHEN** decision state is ATTACK and army units exist
- **THEN** the camera SHALL follow the attacking army

#### Scenario: Tactical camera during defense
- **WHEN** an `enemy_push` event is detected
- **THEN** the camera SHALL focus on the location of enemy units
