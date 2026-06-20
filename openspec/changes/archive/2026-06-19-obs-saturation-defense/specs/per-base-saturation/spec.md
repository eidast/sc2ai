## ADDED Requirements

### Requirement: Per-base worker saturation is calculated
The system SHALL calculate saturation metrics for each owned townhall (Nexus) on every `on_step`, using the formula `ideal_workers = nearby_mineral_patches * 2 + nearby_gas_buildings * 3` and `current_workers = nexus.assigned_harvesters`. Saturation ratio SHALL be `current / ideal`.

#### Scenario: Main base saturation at game start
- **WHEN** the game starts with 1 nexus, 8 mineral patches, and 0 gas buildings
- **THEN** ideal_workers SHALL equal 16, current_workers SHALL equal 12, and saturation ratio SHALL be 0.75

#### Scenario: Saturated base with gas
- **WHEN** a nexus has 8 mineral patches, 2 gas buildings, and 22 assigned harvesters
- **THEN** ideal_workers SHALL equal 22 and saturation ratio SHALL be 1.0

#### Scenario: Oversaturated base detected
- **WHEN** a nexus has ideal_workers = 16 and assigned_harvesters = 24
- **THEN** saturation ratio SHALL be > 1.0

### Requirement: Probes are trained at the least saturated nexus
The system SHALL prioritize probe training at the nexus with the lowest saturation ratio. A nexus with saturation ratio ≥ 0.9 SHALL be skipped for training. Only one probe SHALL be queued per `on_step`.

#### Scenario: Train at least saturated base
- **WHEN** main base has ratio 1.1 and natural has ratio 0.3, and probe training conditions are met
- **THEN** the probe SHALL be trained at the natural nexus, not the main

#### Scenario: Skip saturated bases
- **WHEN** all nexuses have saturation ratio ≥ 0.9 and workers are below MAX_WORKERS
- **THEN** no probe SHALL be trained at any nexus

#### Scenario: Single base skips when saturated
- **WHEN** there is only one nexus and its saturation ratio is ≥ 0.9
- **THEN** no probe SHALL be trained

### Requirement: Expansion is triggered by saturation, not supply
The system SHALL initiate a new expansion when ALL current nexuses have saturation ratio ≥ 0.9 AND the bot can afford a Nexus AND no Nexus is already pending. There SHALL be no hard limit on the number of expansions.

#### Scenario: Expand when all bases saturated
- **WHEN** the bot has 2 nexuses, both with saturation ≥ 0.9, and 400+ minerals
- **THEN** the bot SHALL start building a 3rd Nexus

#### Scenario: Do not expand when any base is undersaturated
- **WHEN** the bot has 2 nexuses, one with saturation 1.1 and one with saturation 0.5
- **THEN** the bot SHALL NOT start a new expansion

#### Scenario: Do not expand when cannot afford
- **WHEN** all nexuses are saturated but minerals are below Nexus cost
- **THEN** the bot SHALL NOT start a new expansion

### Requirement: Base oversaturation event is detected
The system SHALL emit a `base_oversaturated` event when any nexus has saturation ratio > 1.0 and there exists at least one other nexus with saturation ratio < 0.9. The event details SHALL include the oversaturated nexus position and ratio.

#### Scenario: Oversaturation event with undersaturated alternative
- **WHEN** main base has ratio 1.2 and natural has ratio 0.4
- **THEN** a `base_oversaturated` event SHALL be emitted with the main base position and ratio in details

#### Scenario: No event when only one base is oversaturated
- **WHEN** the only nexus is oversaturated with no other bases to compare
- **THEN** no `base_oversaturated` event SHALL be emitted
