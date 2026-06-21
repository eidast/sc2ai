## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Bot executes pressure assessment during on_step
The system SHALL call `assess_pressure()` on every `on_step` after feature extraction and before any manager methods. The resulting `PressureLevel` SHALL be stored as `self._pressure_level` and made available to all `manage_*` methods.

#### Scenario: Pressure assessed before managers
- **WHEN** `on_step` is called
- **THEN** `assess_pressure()` SHALL run after feature extraction and before `manage_expansion()`, `manage_tech()`, and `manage_army()`
