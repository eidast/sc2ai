## ADDED Requirements

### Requirement: Workers are transferred from oversaturated to undersaturated bases
The system SHALL implement `manage_worker_transfer()` in `MyBot` that runs autonomously on every `on_step`. When at least one base has `status == "oversaturated"` AND at least one other base has `status == "undersaturated"`, the system SHALL pick one idle or excess mineral worker (mineral_worker count above 16 per base) from the oversaturated base and SHALL order it to gather minerals at the undersaturated base. At most one worker SHALL be transferred per `on_step`.

#### Scenario: Transfer from oversaturated to undersaturated
- **WHEN** base 1 has mineral_saturation 1.2 (oversaturated) and base 2 has mineral_saturation 0.5 (undersaturated)
- **THEN** one idle or excess mineral worker from base 1 SHALL be ordered to gather minerals at base 2

#### Scenario: No transfer when all bases optimal
- **WHEN** all bases have status "optimal"
- **THEN** no worker transfer orders SHALL be issued

#### Scenario: No transfer when no undersaturated target exists
- **WHEN** base 1 is oversaturated but all other bases are also saturated or oversaturated
- **THEN** no worker transfer orders SHALL be issued

#### Scenario: At most one worker transferred per step
- **WHEN** multiple oversaturated bases and multiple undersaturated bases exist
- **THEN** exactly one worker SHALL be transferred per `on_step`

### Requirement: Idle workers are reassigned to undersaturated gas geysers
The system SHALL, on every `on_step`, check all assimilators (ready) for undersaturation (assigned_harvesters < 3). If any assimilator has fewer than 3 workers AND no idle or excess mineral worker is available, the system SHALL skip gas reassignment. If idle workers or excess mineral workers exist, the closest such worker SHALL be ordered to gather from the undersaturated assimilator.

#### Scenario: Idle worker assigned to undersaturated gas
- **WHEN** an assimilator has 1 assigned harvester and an idle worker exists near the same base
- **THEN** the idle worker SHALL be ordered to gather from that assimilator

#### Scenario: Excess mineral worker assigned to gas
- **WHEN** an assimilator has 0 assigned harvesters, no idle workers exist, but a base has mineral_saturation > 1.0
- **THEN** a mineral-gathering worker from the oversaturated base SHALL be ordered to gather from the undersaturated assimilator

#### Scenario: Fully saturated gas skipped
- **WHEN** all assimilators have exactly 3 assigned harvesters
- **THEN** no gas reassignment SHALL occur regardless of idle worker count

### Requirement: Probe production stops when all bases are saturated or oversaturated
The system SHALL NOT train new probes when `undersaturated_bases == 0` (all bases have status "optimal" or "oversaturated"), even if total worker count is below 70. This prevents training probes that would immediately become idle or excess.

#### Scenario: Probe training suppressed when all bases saturated
- **WHEN** the bot has 40 workers, 2 bases, both with status "optimal", and supply and minerals are available
- **THEN** no probe SHALL be trained

#### Scenario: Probe training resumes when base becomes undersaturated
- **WHEN** a new expansion is started and its status becomes "undersaturated"
- **THEN** probe training SHALL resume at the undersaturated base

### Requirement: MAX_WORKERS is dynamically capped in late game
The system SHALL compute a dynamic maximum worker count as `dynamic_max = sum(b.ideal_workers for b in bases) * 1.1`. When `game_time > 900` and `dynamic_max < 70`, the effective max workers SHALL be capped at `dynamic_max`. Probe training SHALL respect the lower of 70 and this dynamic cap.

#### Scenario: Dynamic cap in late game with 2 bases
- **WHEN** game_time > 900, 2 bases with ideal_workers 20 and 18, making dynamic_max = 41
- **THEN** the effective max worker limit SHALL be 41 instead of 70

#### Scenario: Dynamic cap not applied before late game
- **WHEN** game_time < 900 and dynamic_max is 41
- **THEN** the max worker limit SHALL remain 70
