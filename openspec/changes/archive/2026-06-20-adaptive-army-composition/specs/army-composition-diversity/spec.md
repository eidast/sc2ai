## ADDED Requirements

### Requirement: Army production uses top-3 counter mix
`manage_army()` SHALL select units from the top-3 recommended counters. Gateway structures SHALL produce the highest-scoring Gateway-compatible counter. Robotics structures SHALL produce the highest-scoring Robo-compatible counter. Stargate structures SHALL produce the highest-scoring Stargate-compatible counter. Warpgates SHALL match the Gateway unit selection. All three production loops SHALL run independently each step.

#### Scenario: Mixed production from top-3 counters
- **WHEN** top counters are IMMORTAL (score 813), DARKTEMPLAR (score 787), STALKER (score 485), and all three production structures exist
- **THEN** Gateway SHALL produce Zealot or Stalker, Robo SHALL produce Immortal, and Stargate SHALL produce its best unit if a Stargate exists

#### Scenario: No Robo counter degrades to Immortal
- **WHEN** top counters are all Gateway units, but a Robo structure exists
- **THEN** Robo SHALL default to producing Immortal

#### Scenario: No Stargate means no Stargate production
- **WHEN** top counter is Phoenix but no Stargate exists
- **THEN** no Stargate unit production SHALL be attempted

### Requirement: Upgrades use combined resource threshold
`manage_upgrades()` SHALL use the combined minerals + vespene threshold instead of minerals-only. If `minerals + vespene >= UPGRADE_RESOURCE_THRESHOLD`, upgrade research SHALL proceed. The threshold SHALL be 500 combined resources.

#### Scenario: Upgrade proceeds with high gas, low minerals
- **WHEN** minerals = 100, vespene = 450, combined = 550 >= 500
- **THEN** the bot SHALL attempt upgrade research

#### Scenario: No upgrade when combined resources insufficient
- **WHEN** minerals = 150, vespene = 200, combined = 350 < 500
- **THEN** the bot SHALL NOT attempt upgrade research

### Requirement: Counter-driven tech tree construction
`manage_tech()` SHALL examine top-3 counters after Gateway and CyberCore prerequisites. If any top counter requires Stargate or Twilight Council and the structure does not exist, the bot SHALL build it. One tech structure per step. Stargate SHALL take priority over Twilight Council.

#### Scenario: Stargate built when Phoenix is top counter
- **WHEN** top-3 counters include PHOENIX or VOIDRAY or ORACLE, no Stargate exists
- **THEN** the bot SHALL build a Stargate

#### Scenario: Twilight built when Archon is top counter
- **WHEN** top-3 counters include ARCHON or DARKTEMPLAR, no Twilight Council exists, and either no Stargate is needed or Stargate already exists
- **THEN** the bot SHALL build a Twilight Council

#### Scenario: Forge built when upgrades are available
- **WHEN** no Forge exists and combined minerals+vespene >= 500
- **THEN** the bot SHALL build a Forge to enable upgrades

### Requirement: Hoard prevention attack trigger
`evaluate_decision()` SHALL transition from DEFEND to ATTACK when the bot has been in DEFEND state for 60+ seconds, has 8+ army units, and `army_value_ratio > 0.8`.

#### Scenario: Attack after 60s hoarding
- **WHEN** state is DEFEND for 65s, army_count = 12, army_value_ratio = 0.9
- **THEN** the decision engine SHALL transition to ATTACK

#### Scenario: No attack when severely outmatched
- **WHEN** state is DEFEND for 65s, army_count = 10, army_value_ratio = 0.3
- **THEN** the decision engine SHALL remain in DEFEND
