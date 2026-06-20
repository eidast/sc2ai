## ADDED Requirements

### Requirement: Priority formulas include structure prerequisites
All structure-building priority formulas in strategy profiles (YAML) SHALL include production chain prerequisites as multiplication factors. Specifically:
- `GATEWAY` formula SHALL NOT depend on any prerequisite (always buildable for gateway units)
- `CYBERNETICSCORE` formula SHALL require `has_structure('GATEWAY')` as a factor
- `FORGE`, `TWILIGHTCOUNCIL`, `ROBOTICSFACILITY`, `STARGATE` formulas SHALL require `has_structure('CYBERNETICSCORE')` as a factor, ensuring score is zero when the Cybernetics Core is missing

#### Scenario: Forge score is zero without Core
- **WHEN** the bot has no Cybernetics Core and the strategy engine evaluates the Forge formula
- **THEN** the Forge score SHALL be zero because `has_structure('CYBERNETICSCORE')` evaluates to 0

#### Scenario: Robo score is zero without Core
- **WHEN** the bot has no Cybernetics Core and the strategy engine evaluates the Robotics Facility formula
- **THEN** the Robotics Facility score SHALL be zero because `has_structure('CYBERNETICSCORE')` evaluates to 0

#### Scenario: Formula prerequisite chain respects production requirements
- **WHEN** the bot has a Gateway but no Cybernetics Core
- **THEN** the Cybernetics Core formula MAY have a positive score (requires Gateway), but Forge, Robo, Stargate, and Twilight Council formulas SHALL have zero score (require Cybernetics Core)
