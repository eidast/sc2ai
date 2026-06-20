## MODIFIED Requirements

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

## ADDED Requirements

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
