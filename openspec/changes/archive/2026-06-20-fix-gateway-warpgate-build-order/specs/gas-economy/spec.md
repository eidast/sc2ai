## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Assimilator construction waits for Pylon
`manage_gas()` SHALL check for a Pylon before building any Assimilator. If no Pylon exists, the method SHALL return without building gas or assigning gas workers.

#### Scenario: Gas skipped when no Pylon exists
- **WHEN** the bot has 0 Pylons, 1 Nexus, and an unoccupied geyser
- **THEN** `manage_gas` SHALL return without building an Assimilator

#### Scenario: Gas built after Pylon exists
- **WHEN** the bot has at least 1 Pylon, 0 Assimilators, and an unoccupied geyser
- **THEN** `manage_gas` SHALL proceed to build the first Assimilator normally
