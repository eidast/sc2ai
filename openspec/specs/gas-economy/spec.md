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
The system SHALL build at most one assimilator per `on_step` call regardless of how many geysers are available. The system SHALL NOT build a second Assimilator until at least one Gateway or Warpgate structure exists (combined count > 0).

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

### Requirement: Gas construction is limited before Gateway exists
The system SHALL NOT build a second Assimilator until at least one Gateway or Warpgate exists (combined count > 0). This prevents `manage_gas` from consuming workers needed for Gateway construction during early game. The system SHALL also require at least one Pylon before building the first Assimilator, ensuring the correct build order: Pylon → Gateway → Assimilator.

#### Scenario: Gas building stopped at one assimilator without Gateway or Warpgate
- **WHEN** the bot has 1 Assimilator, 0 Gateways, 0 Warpgates, and an unoccupied geyser is available
- **THEN** the bot SHALL NOT build a second Assimilator

#### Scenario: Gas building resumes after Gateway or Warpgate
- **WHEN** the bot has 1 Assimilator, at least 1 Gateway or Warpgate, and an unoccupied geyser is available
- **THEN** the bot SHALL build a second Assimilator normally

#### Scenario: No assimilator built before first Pylon
- **WHEN** the bot has 0 Pylons and an unoccupied geyser is available
- **THEN** `manage_gas` SHALL NOT build an Assimilator

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

### Requirement: Assimilator construction waits for Pylon
`manage_gas()` SHALL check for a Pylon before building any Assimilator. If no Pylon exists, the method SHALL return without building gas or assigning gas workers.

#### Scenario: Gas skipped when no Pylon exists
- **WHEN** the bot has 0 Pylons, 1 Nexus, and an unoccupied geyser
- **THEN** `manage_gas` SHALL return without building an Assimilator

#### Scenario: Gas built after Pylon exists
- **WHEN** the bot has at least 1 Pylon, 0 Assimilators, and an unoccupied geyser
- **THEN** `manage_gas` SHALL proceed to build the first Assimilator normally
