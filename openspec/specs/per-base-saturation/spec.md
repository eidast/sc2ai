## ADDED Requirements

### Requirement: Per-base worker saturation is calculated
The system SHALL calculate saturation metrics for each owned townhall (Nexus) on every `on_step`. The metrics SHALL include a mineral/gas breakdown: `mineral_patches` (nearby mineral fields), `gas_geysers` (nearby gas buildings), `ideal_mineral_workers` (mineral_patches × 2, capped at 16), `ideal_gas_workers` (gas_geysers × 3), `actual_mineral_workers` (workers currently gathering minerals near the base), `actual_gas_workers` (workers currently gathering gas near the base), and `idle_workers_nearby` (idle workers nearest to this base). The system SHALL also compute `mineral_saturation = actual_mineral / ideal_mineral`, `gas_saturation = actual_gas / ideal_gas`, and `total_saturation = (actual_mineral + actual_gas) / (ideal_mineral + ideal_gas)`. Legacy fields `ideal_workers`, `current_workers`, and `saturation_ratio` SHALL be retained but mapped as `ideal_workers = ideal_mineral + ideal_gas`, `current_workers = nexus.assigned_harvesters`, `saturation_ratio = total_saturation`.

#### Scenario: Main base saturation at game start
- **WHEN** the game starts with 1 nexus, 8 mineral patches, 0 gas buildings, and 12 workers (all on minerals)
- **THEN** ideal_mineral_workers SHALL equal 16, ideal_gas_workers SHALL equal 0, actual_mineral_workers SHALL equal 12, and total_saturation SHALL be 0.75

#### Scenario: Saturated base with gas
- **WHEN** a nexus has 8 mineral patches, 2 gas buildings, 16 mineral workers, and 6 gas workers
- **THEN** mineral_saturation SHALL be 1.0, gas_saturation SHALL be 1.0, and total_saturation SHALL be 1.0

#### Scenario: Oversaturated base detected
- **WHEN** a nexus has 8 mineral patches, 2 gas buildings, 18 mineral workers, and 6 gas workers
- **THEN** mineral_saturation SHALL be > 1.0 and total_saturation SHALL be > 1.0

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

### Requirement: Per-base saturation status is classified
The system SHALL classify each base with a `status` field computed from its saturation metrics. A base SHALL be `"oversaturated"` when `mineral_saturation > 1.1` or `gas_saturation > 1.0` (with at least one geyser present). A base SHALL be `"undersaturated"` when `mineral_saturation < 0.7` or (`gas_saturation < 0.5` and gas_geysers > 0). Otherwise the base SHALL be `"optimal"`.

#### Scenario: Oversaturated base by minerals
- **WHEN** a base has 8 mineral patches, 2 gas buildings, 18 mineral workers, and 6 gas workers
- **THEN** status SHALL be "oversaturated"

#### Scenario: Oversaturated base by gas
- **WHEN** a base has 8 mineral patches, 1 gas building, 16 mineral workers, and 4 gas workers
- **THEN** status SHALL be "oversaturated"

#### Scenario: Undersaturated base
- **WHEN** a base has 8 mineral patches, 2 gas buildings, 6 mineral workers, and 0 gas workers
- **THEN** status SHALL be "undersaturated"

#### Scenario: Optimal base
- **WHEN** a base has 8 mineral patches, 2 gas buildings, 14 mineral workers, and 5 gas workers
- **THEN** status SHALL be "optimal"

### Requirement: Idle workers are detected per base
The system SHALL count idle workers (workers with no current order) nearest to each base and include that count in the base's feature dict as `idle_workers_nearby`.

#### Scenario: Idle worker detected
- **WHEN** 2 idle workers are closer to base 1 than to any other base
- **THEN** base 1's `idle_workers_nearby` SHALL be 2

#### Scenario: No idle workers
- **WHEN** all workers have active orders
- **THEN** `idle_workers_nearby` SHALL be 0 for all bases
