## ADDED Requirements

### Requirement: Army value is calculated for both players
The system SHALL compute the economic value (mineral_cost + vespene_cost) of the player's and enemy's combat armies, excluding worker and non-combat units.

#### Scenario: Our army value computed
- **WHEN** the bot has 5 Stalkers and 3 Zealots
- **THEN** `our_army_value` SHALL equal `5 * 175 + 3 * 100 = 1175`

#### Scenario: Enemy army value excludes workers
- **WHEN** the enemy has 2 Marines, 3 SCVs, and 1 Marauder visible
- **THEN** `enemy_army_value` SHALL equal `2 * 50 + 1 * 125 = 225` (SCVs excluded)

#### Scenario: Army value excludes non-combat units
- **WHEN** the enemy has Overlords, Drones, or Observers visible
- **THEN** `enemy_army_value` SHALL NOT count these units

#### Scenario: Army value zero when no combat units visible
- **WHEN** no enemy combat units are visible
- **THEN** `enemy_army_value` SHALL be 0

#### Scenario: Our army value zero with only probes
- **WHEN** the bot has only Probes
- **THEN** `our_army_value` SHALL be 0

### Requirement: Army value ratio is included in features
The system SHALL include `army_value_ratio` computed as `our_army_value / max(enemy_army_value, 1)` to prevent division by zero.

#### Scenario: Ratio with advantage
- **WHEN** our_army_value = 2000 and enemy_army_value = 1000
- **THEN** `army_value_ratio` SHALL be 2.0

#### Scenario: Ratio with disadvantage
- **WHEN** our_army_value = 500 and enemy_army_value = 2000
- **THEN** `army_value_ratio` SHALL be 0.25

#### Scenario: Ratio with no enemy combat units
- **WHEN** enemy_army_value is 0
- **THEN** `army_value_ratio` SHALL equal `our_army_value` (division by 1)

### Requirement: Non-combat enemy types are excluded from analysis
The system SHALL define a set of unit types considered non-combat for enemy army analysis purposes.

#### Scenario: Workers are non-combat
- **WHEN** the enemy has SCV, Drone, or Probe units
- **THEN** these units SHALL be excluded from `enemy_army_value` and `enemy_t3_count`

#### Scenario: Supply and non-combat units excluded
- **WHEN** the enemy has Overlord, Overseer, Larva, Egg, MULE, Changeling, or Observer units
- **THEN** these units SHALL be excluded from `enemy_army_value`

#### Scenario: Queen is combat unit
- **WHEN** the enemy has Queens
- **THEN** Queens SHALL be included in `enemy_army_value` (they have combat attacks)

### Requirement: Enemy worker count is tracked
The system SHALL include `enemy_worker_count` in extracted features, counting only SCV/Drone/Probe units visible.

#### Scenario: Workers visible
- **WHEN** 25 SCVs are visible on the map
- **THEN** `enemy_worker_count` SHALL be 25

#### Scenario: Workers tracked separately from combat
- **WHEN** the enemy has SCVs and Marines visible
- **THEN** `enemy_worker_count` SHALL count only SCVs; Marines count toward `enemy_army_value` and `enemy_visible_units`
