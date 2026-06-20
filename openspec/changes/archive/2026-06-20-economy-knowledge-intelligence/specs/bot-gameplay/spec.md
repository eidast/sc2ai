## ADDED Requirements

### Requirement: HTML reports include unit icons
The system SHALL embed unit icons from the Liquipedia CDN in HTML match reports. Our army composition and enemy army composition tables SHALL render icons alongside unit names.

#### Scenario: Unit icons appear in army tables
- **WHEN** an HTML report is generated with army composition data
- **THEN** each unit entry SHALL include an `<img>` tag with a valid `src` attribute pointing to a unit icon URL

#### Scenario: Fallback icon for unknown units
- **WHEN** a unit name has no specific icon mapping
- **THEN** a fallback icon URL SHALL be used instead

## MODIFIED Requirements

### Requirement: Bot plays Protoss macro strategy
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression (including Forge, Twilight Council, and ground upgrades), army production (adaptive based on scouted enemy counters), and a final attack when max supply is reached. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context. The bot SHALL send a scout probe to explore enemy starting locations. The bot SHALL fix gas economy by continuing to the next geyser when an assimilator is unaffordable and assigning workers to undersaturated assimilators.

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

#### Scenario: Attack at max supply
- **WHEN** the bot reaches 200 supply
- **THEN** the bot SHALL send all army units to attack the enemy starting location. Attack commands SHALL take priority over defensive repositioning.

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
- **WHEN** `attack_triggered` is True and army units exist
- **THEN** the camera SHALL follow the attacking army

#### Scenario: Tactical camera during defense
- **WHEN** an `enemy_push` event is detected
- **THEN** the camera SHALL focus on the location of enemy units

### Requirement: Bot detects gameplay events during on_step
The system SHALL detect key gameplay events on every `on_step` call by comparing current features against the previous step. Events SHALL include at minimum: `supply_block`, `enemy_push`, `worker_stalled`, `resource_float`, `gas_starved`, `tech_milestone`, `attack_ready`, `expansion_started`, `base_under_attack`, and `base_oversaturated`.

#### Scenario: Events detected each step
- **WHEN** `on_step` is called
- **THEN** the bot SHALL run event detection and make detected events available to managers

#### Scenario: Gas starved event
- **WHEN** minerals ≥ 300, vespene < 100, and either no assimilators exist or mineral/vespene ratio > 3
- **THEN** a `gas_starved` event SHALL be emitted with severity "high"

#### Scenario: Base oversaturation event
- **WHEN** a nexus has saturation > 1.0 and another nexus has saturation < 0.9
- **THEN** a `base_oversaturated` event SHALL be emitted

#### Scenario: Base under attack event
- **WHEN** enemy units are within THREAT_RANGE of a nexus and have attack orders
- **THEN** a `base_under_attack` event SHALL be emitted

#### Scenario: No events on first step
- **WHEN** `on_step` is called at iteration 0
- **THEN** no events other than `game_start` SHALL be emitted
