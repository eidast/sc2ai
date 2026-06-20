## ADDED Requirements

### Requirement: Gas construction is limited before Gateway exists
The system SHALL NOT build a second Assimilator until at least one Gateway exists. This prevents `manage_gas` from consuming workers needed for Gateway construction during early game.

#### Scenario: Gas building stopped at one assimilator without Gateway
- **WHEN** the bot has 1 Assimilator, 0 Gateways, and an unoccupied geyser is available
- **THEN** the bot SHALL NOT build a second Assimilator

#### Scenario: Gas building resumes after Gateway
- **WHEN** the bot has 1 Assimilator, at least 1 Gateway, and an unoccupied geyser is available
- **THEN** the bot SHALL build a second Assimilator normally

## MODIFIED Requirements

### Requirement: Only one assimilator is built per step
The system SHALL build at most one assimilator per `on_step` call regardless of how many geysers are available. The system SHALL NOT build a second Assimilator until at least one Gateway structure exists.

#### Scenario: One assimilator per step
- **WHEN** multiple geysers are affordable and unoccupied
- **THEN** the bot SHALL build exactly one assimilator and return
