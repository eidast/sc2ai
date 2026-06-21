## MODIFIED Requirements

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

## ADDED Requirements

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
