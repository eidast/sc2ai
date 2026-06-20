## ADDED Requirements

### Requirement: Saturation timeline data is included in report JSON
The match report JSON SHALL include a `saturation_timeline` field containing snapshots of per-base saturation captured at 60-second intervals. Each snapshot SHALL include per-base breakdown (mineral_workers, gas_workers, mineral_saturation, gas_saturation, status, idle) and aggregate totals (total workers, oversaturated count, undersaturated count, idle workers, average saturations).

#### Scenario: Timeline data structures are JSON-serializable
- **WHEN** saturation_timeline is generated
- **THEN** all values SHALL be standard JSON types (int, float, str, list, dict) with no NaN or Infinity

#### Scenario: Timeline aggregates match per-base data
- **WHEN** a snapshot has bases with statuses "oversaturated", "optimal", "undersaturated"
- **THEN** `oversaturated_bases` and `undersaturated_bases` in `totals` SHALL match the counts of those statuses in the `bases` array
