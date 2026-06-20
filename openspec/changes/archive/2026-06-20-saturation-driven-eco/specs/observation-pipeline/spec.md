## MODIFIED Requirements

### Requirement: Per-base saturation data is included
- **WHEN** `extract_features()` is called
- **THEN** `bases` SHALL be a list of dicts, each containing: `position` (tuple of floats), `ideal_workers` (int, retained for backward compatibility), `current_workers` (int), `saturation_ratio` (float, retained as alias for total_saturation), `enemy_nearby` (int), `army_nearby` (int), plus the new fields: `mineral_patches` (int), `gas_geysers` (int), `ideal_mineral_workers` (int), `ideal_gas_workers` (int), `actual_mineral_workers` (int), `actual_gas_workers` (int), `idle_workers_nearby` (int), `mineral_saturation` (float), `gas_saturation` (float), `total_saturation` (float), and `status` (str).

#### Scenario: Enriched base dict includes mineral/gas split
- **WHEN** extract_features is called on a bot with a base that has 8 mineral patches, 2 gas geysers, 14 mineral workers, and 4 gas workers
- **THEN** the base dict SHALL contain `mineral_patches: 8`, `gas_geysers: 2`, `actual_mineral_workers: 14`, `actual_gas_workers: 4`, `mineral_saturation: 0.875`, `gas_saturation: 0.667`, `total_saturation: 0.818`, and `status: "undersaturated"`

#### Scenario: Legacy fields preserved for backward compatibility
- **WHEN** extract_features is called
- **THEN** each base dict SHALL still contain `ideal_workers`, `current_workers`, and `saturation_ratio` with values matching the total mineral+gas workers and saturation
