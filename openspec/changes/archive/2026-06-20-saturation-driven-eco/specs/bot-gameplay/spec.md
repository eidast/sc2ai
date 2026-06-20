## MODIFIED Requirements

### Requirement: Constant worker production
The system SHALL train probes at the least saturated nexus when `undersaturated_bases > 0`, worker count is below the dynamic max (min(70, sum of ideal_workers × 1.1) when game_time > 900, else 70), and supply and minerals are available. A nexus SHALL be skipped if its status is not "undersaturated". The system SHALL NOT train probes when all bases are "optimal" or "oversaturated", regardless of total worker count.

#### Scenario: Probe trained at undersaturated base
- **WHEN** base 1 is "optimal" (mineral_sat 0.95) and base 2 is "undersaturated" (mineral_sat 0.4), and all conditions met
- **THEN** a probe SHALL be trained at base 2

#### Scenario: No probe trained when all bases saturated
- **WHEN** the bot has 40 workers, 2 bases, both with status "optimal", and supply and minerals are available
- **THEN** no probe SHALL be trained

#### Scenario: Probe trained respects dynamic max in late game
- **WHEN** game_time > 900, dynamic_max is 41, and current workers is 40
- **THEN** the effective max worker limit SHALL be 41 and probe training SHALL respect it

## ADDED Requirements

### Requirement: Worker transfer manager runs autonomously
The system SHALL execute `manage_worker_transfer()` on every `on_step` as part of the `manage_probes()` flow. The manager SHALL: (1) reassign idle or excess mineral workers to undersaturated gas geysers, (2) transfer workers from oversaturated bases to undersaturated bases, and (3) in late game (game_time > 900, all bases oversaturated), suppress further probe production by setting the effective max workers to the dynamic cap.

#### Scenario: manage_worker_transfer runs after probe training
- **WHEN** `on_step` is called
- **THEN** `manage_worker_transfer()` SHALL execute within `manage_probes()`, after the probe training logic but before the method returns

#### Scenario: Worker transfer does not interfere with other managers
- **WHEN** `manage_worker_transfer()` issues a gather order to a worker
- **THEN** the worker transfer SHALL NOT prevent `manage_tech()`, `manage_upgrades()`, `manage_army()`, or `manage_attack()` from executing normally in the same step
