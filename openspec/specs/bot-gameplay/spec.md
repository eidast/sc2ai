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
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression (including Forge, Twilight Council, and ground upgrades), army production (adaptive based on scouted enemy counters), and attack decisions driven by the strategic decision engine instead of a fixed supply threshold. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context. The bot SHALL send a scout probe to explore enemy starting locations. The bot SHALL fix gas economy by continuing to the next geyser when an assimilator is unaffordable and assigning workers to undersaturated assimilators. The bot SHALL optionally surrender when the decision engine determines victory is impossible. During the first ~90 seconds of game time, the bot SHALL follow a deterministic build order via `manage_early_game()` to guarantee production infrastructure (Pylon → Gateway → Cybernetics Core → Warp Gate) before yielding control to the strategy engine.

### Requirement: Constant worker production
The system SHALL train probes at the least saturated nexus when `undersaturated_bases > 0`, worker count is below the dynamic max (min(70, sum of ideal_workers × 1.1) when game_time > 900, else 70), and supply and minerals are available. A nexus SHALL be skipped if its status is not "undersaturated". The system SHALL NOT train probes when all bases are "optimal" or "oversaturated", regardless of total worker count.

#### Scenario: Probe trained at undersaturated base
- **WHEN** base 1 is "optimal" (mineral_sat 0.95) and base 2 is "undersaturated" (mineral_sat 0.4), and all conditions met
- **THEN** a probe SHALL be trained at base 2

#### Scenario: No probe trained when all bases saturated
- **WHEN** the bot has 40 workers, 2 bases, both with status "optimal", and supply and minerals are available
- **THEN** no probe SHALL be trained

#### Scenario: Probe trained respects dynamic max in late game
- **WHEN** game_time > 900, dynamic_max is 41, and current workers is 40
- **THEN** the effective max worker limit SHALL be 41 and probe training SHALL respect it

#### Scenario: Supply management
- **WHEN** available supply drops below 4
- **THEN** the bot SHALL build a Pylon at a valid placement location

#### Scenario: Supply block reactivity
- **WHEN** a `supply_block` event is detected (supply_left < 3 and no pylon pending)
- **THEN** the bot SHALL prioritize pylon construction above other build actions

### Requirement: Natural expansion
The system SHALL expand when ALL current nexuses have a saturation ratio at or above the pressure-adaptive threshold (NONE: 0.65, LOW: 0.75, MEDIUM: 0.85, HIGH: no expansion), AND the bot can afford a Nexus, AND no Nexus is already pending. The system SHALL also expand when minerals exceed the pressure-adaptive banking threshold (NONE: 350, LOW: 400, MEDIUM: 500, HIGH: no expansion), regardless of saturation. There SHALL be no hard limit on the number of expansions.

#### Scenario: Natural expansion at pressure NONE
- **WHEN** pressure is NONE, all current nexuses have saturation ratio ≥ 0.65, AND the bot can afford a Nexus AND no Nexus is already pending
- **THEN** the bot SHALL send a probe to build a Nexus at the next expansion location

#### Scenario: Natural expansion at pressure LOW
- **WHEN** pressure is LOW, all current nexuses have saturation ratio ≥ 0.75, AND the bot can afford a Nexus AND no Nexus is already pending
- **THEN** the bot SHALL send a probe to build a Nexus

#### Scenario: No expansion at pressure MEDIUM below threshold
- **WHEN** pressure is MEDIUM, saturation ratio is 0.80, and can afford Nexus
- **THEN** the bot SHALL NOT expand (0.80 < 0.85 threshold)

#### Scenario: No expansion at pressure HIGH
- **WHEN** pressure is HIGH, saturation ratio is 1.0, minerals > 600
- **THEN** the bot SHALL NOT expand

#### Scenario: Tech progression
- **WHEN** the bot has a completed Gateway
- **THEN** the bot SHALL build a Cybernetics Core, then research Warp Gate, and add additional Gateways. The bot SHALL NOT build Forge, Twilight Council, Robotics Facility, or Stargate before a Gateway exists.

#### Scenario: Formula-driven tech requires production prerequisites
- **WHEN** the strategy engine evaluates priority formulas for structures
- **THEN** the formulas for Forge, Twilight Council, Robotics Facility, and Stargate SHALL include `has_structure('GATEWAY')` or `has_structure('CYBERNETICSCORE')` as a multiplication factor so their score is zero when the prerequisite structure is missing

### Requirement: Army production
The system SHALL produce a proportional mix of army units from the top-3 recommended counters, distributing production across all available production structures (Gateway, Warpgate, Robotics Facility, Stargate) each step. Gateway-bound counters SHALL be produced from Gateway/Warpgate, Robo-bound from Robotics Facility, Stargate-bound from Stargate. When a structure type has no matching counter in the top-3, it SHALL default to a standard unit (Stalker/Zealot for Gateway, Immortal for Robo, Void Ray for Stargate).

#### Scenario: Army production from all structures
- **WHEN** the bot has Gateways, Robos, and Stargates, and most-enemy units are ROACH
- **THEN** Gateway SHALL produce Zealot/Stalker, Robo SHALL produce Immortal, and Stargate SHALL produce its unit

#### Scenario: Production scales with available resources
- **WHEN** the bot has available minerals and vespene and idle production structures
- **THEN** all idle structures SHALL attempt to produce simultaneously in a single step

### Requirement: Attack driven by decision engine
The system SHALL transition from DEFEND to ATTACK when the decision engine detects army value advantage, supply cap, enemy push counter-attack, T3 window, or 60-second hoard timeout. The hoard timeout SHALL require army_count >= 8, army_value_ratio > 0.8, and DEFEND state sustained for 60 seconds.

#### Scenario: Hoard timeout triggers attack
- **WHEN** the bot has been in DEFEND for 65 seconds, has 10 army units, and army_value_ratio is 0.85
- **THEN** the decision engine SHALL transition to ATTACK with reason "hoard timeout"

#### Scenario: Severely outmatched bot does not attack on timeout
- **WHEN** the bot has been in DEFEND for 65 seconds, has 10 army units, but army_value_ratio is 0.3
- **THEN** the decision engine SHALL remain in DEFEND

#### Scenario: Surrender when decision engine triggers
- **WHEN** the decision engine transitions to SURRENDER state AND surrender is enabled
- **THEN** the bot SHALL send `chat_send("gg")`, skip all remaining managers, and log a surrender event

#### Scenario: Tactical camera in early game
- **WHEN** the bot is in `EARLY_GAME` phase
- **THEN** the camera SHALL follow the scout probe if one exists, otherwise center on the main base

#### Scenario: Tactical camera during engagement
- **WHEN** decision state is ATTACK and army units exist
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

### Requirement: Gateway production capacity scales with economy
The system SHALL dynamically compute the target gateway count based on the number of bases, current mineral float, and the current pressure level. The target SHALL be capped at 16 gateways.

#### Scenario: One base baseline
- **WHEN** the bot has 1 base, pressure is NONE, and minerals < 500
- **THEN** the target gateway count SHALL be 4

#### Scenario: Extra gateways under pressure
- **WHEN** the bot has 1 base, pressure is MEDIUM, and minerals < 500
- **THEN** the target gateway count SHALL be 6 (baseline 4 + pressure 2)

#### Scenario: Scales with bases
- **WHEN** the bot has 2 bases, pressure is NONE, and minerals < 500
- **THEN** the target gateway count SHALL be 7 (4 + 1*3)

#### Scenario: Extra gateways when floating under pressure
- **WHEN** the bot has 2 bases, pressure is LOW, and minerals > 500
- **THEN** the target gateway count SHALL increase by 3 (pressure-based float extra)

#### Scenario: Respects maximum cap
- **WHEN** the computed target exceeds 16
- **THEN** the target SHALL be capped at 16

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

### Requirement: MyBot accepts surrender and fog configuration
The system SHALL allow the caller to pass `surrender_enabled` and `fog_enabled` flags when constructing a `MyBot` instance.

#### Scenario: Flags passed to bot
- **WHEN** `MyBot(surrender_enabled=True, fog_enabled=True)` is constructed
- **THEN** the bot SHALL store these values for use by the decision engine

#### Scenario: Default values preserve current behavior
- **WHEN** `MyBot()` is constructed with no arguments
- **THEN** `surrender_enabled` SHALL be False and `fog_enabled` SHALL be False

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

### Requirement: Worker transfer manager runs autonomously
The system SHALL execute `manage_worker_transfer()` on every `on_step` as part of the `manage_probes()` flow. The manager SHALL: (1) reassign idle or excess mineral workers to undersaturated gas geysers, (2) transfer workers from oversaturated bases to undersaturated bases, and (3) in late game (game_time > 900, all bases oversaturated), suppress further probe production by setting the effective max workers to the dynamic cap.

#### Scenario: manage_worker_transfer runs after probe training
- **WHEN** `on_step` is called
- **THEN** `manage_worker_transfer()` SHALL execute within `manage_probes()`, after the probe training logic but before the method returns

#### Scenario: Worker transfer does not interfere with other managers
- **WHEN** `manage_worker_transfer()` issues a gather order to a worker
- **THEN** the worker transfer SHALL NOT prevent `manage_tech()`, `manage_upgrades()`, `manage_army()`, or `manage_attack()` from executing normally in the same step

### Requirement: Bot executes pressure assessment during on_step
The system SHALL call `assess_pressure()` on every `on_step` after feature extraction and before any manager methods. The resulting `PressureLevel` SHALL be stored as `self._pressure_level` and made available to all `manage_*` methods.

#### Scenario: Pressure assessed before managers
- **WHEN** `on_step` is called
- **THEN** `assess_pressure()` SHALL run after feature extraction and before `manage_expansion()`, `manage_tech()`, and `manage_army()`

### Requirement: Counter-driven tech tree
`manage_tech()` SHALL build tech structures (Stargate, Twilight Council) when the top-3 recommended counters require them. The system SHALL check after Gateway and CyberCore prerequisites are met. One tech structure SHALL be built per step. Stargate SHALL take priority over Twilight Council.

#### Scenario: Stargate for Phoenix counter
- **WHEN** PHOENIX is in top-3 counters and no Stargate exists
- **THEN** `manage_tech` SHALL build a Stargate

#### Scenario: Twilight for Archon counter
- **WHEN** ARCHON is in top-3 counters, no Twilight Council exists, and Stargate is not needed
- **THEN** `manage_tech` SHALL build a Twilight Council

### Requirement: Combined resource upgrade threshold
The system SHALL use `minerals + vespene >= 500` as the resource gate for upgrade research in `manage_upgrades()`, replacing the minerals-only threshold. This SHALL apply to Forge, Twilight Council, and CyberCore upgrades.

#### Scenario: Upgrade with gas-heavy economy
- **WHEN** minerals = 120, vespene = 420, combined = 540
- **THEN** the bot SHALL proceed with upgrade research
