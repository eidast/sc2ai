## ADDED Requirements

### Requirement: Gas management skips unaffordable geysers without exiting
The system SHALL iterate through all geysers across all nexuses when attempting to build assimilators. If an assimilator cannot be afforded at one geyser, the system SHALL continue checking remaining geysers rather than returning from the function.

#### Scenario: Skip unaffordable, build on affordable
- **WHEN** the first geyser is not affordable but the second geyser is
- **THEN** the bot SHALL skip the first geyser and build an assimilator on the second

#### Scenario: Continue to next nexus after skip
- **WHEN** a geyser at the first nexus is not affordable
- **THEN** the bot SHALL continue checking geysers at remaining nexuses

### Requirement: Only one assimilator is built per step
The system SHALL build at most one assimilator per `on_step` call regardless of how many geysers are available.

#### Scenario: One assimilator per step
- **WHEN** multiple geysers are affordable and unoccupied
- **THEN** the bot SHALL build exactly one assimilator and return

### Requirement: Workers are assigned to undersaturated assimilators
The system SHALL assign idle or mineral-gathering workers to assimilators that have fewer than 3 assigned harvesters. Assignment SHALL happen after checking all geysers for new assimilator construction.

#### Scenario: Workers assigned to undersaturated assimilator
- **WHEN** an assimilator has 1 assigned harvester and idle workers exist
- **THEN** 2 additional workers SHALL be ordered to gather from that assimilator

#### Scenario: Fully saturated assimilator skipped
- **WHEN** all assimilators have 3 assigned harvesters
- **THEN** no worker reassignment SHALL occur

### Requirement: Gateway production capacity scales with economy
The system SHALL dynamically compute the target gateway count based on the number of bases and current mineral float. The target SHALL be capped at 16 gateways.

#### Scenario: One base baseline
- **WHEN** the bot has 1 base and minerals < 500
- **THEN** the target gateway count SHALL be 4

#### Scenario: Scales with bases
- **WHEN** the bot has 2 bases and minerals < 500
- **THEN** the target gateway count SHALL be 7

#### Scenario: Extra gateways when floating
- **WHEN** the bot has 2 bases and minerals > 500
- **THEN** the target gateway count SHALL increase by 2

#### Scenario: Respects maximum cap
- **WHEN** the computed target exceeds 16
- **THEN** the target SHALL be capped at 16

### Requirement: Gas starvation is detected as an event
The system SHALL detect when the bot has high minerals (≥ 300), low vespene (< 100), and the mineral-to-vespene ratio exceeds 3:1. The event SHALL also trigger when no assimilators exist despite having affordable minerals.

#### Scenario: Gas starved with no assimilators
- **WHEN** minerals ≥ 300, vespene < 100, and zero assimilators exist
- **THEN** a `gas_starved` event SHALL be emitted with severity "high"

#### Scenario: Gas starved with undersaturated assimilators
- **WHEN** minerals ≥ 300, vespene < 100, mineral/vespene ratio > 3, and total workers on gas < assimilator_count × 3
- **THEN** a `gas_starved` event SHALL be emitted

#### Scenario: No gas starved when gas is adequate
- **WHEN** vespene ≥ 100
- **THEN** no `gas_starved` event SHALL be emitted
