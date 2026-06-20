## ADDED Requirements

### Requirement: Scout explores enemy starting locations
The system SHALL send a probe to explore enemy starting locations at the beginning of the game. The scout SHALL follow an ordered list of waypoints derived from enemy start locations.

#### Scenario: Scout dispatched at game start
- **WHEN** game time is less than 30 seconds and a probe is available
- **THEN** a probe closest to the enemy start location SHALL be designated as the scout and sent toward the first enemy start location

#### Scenario: Scout advances to next waypoint
- **WHEN** the scout is within 3 units of its current waypoint
- **THEN** the scout SHALL be ordered to move to the next waypoint in the list

#### Scenario: Scout stops when all waypoints visited
- **WHEN** the scout has visited all waypoints
- **THEN** no further movement orders SHALL be issued to the scout (it remains idle)

### Requirement: Scout retreats when threatened
The system SHALL order the scout to retreat when its total HP (health + shields) drops below 50% of maximum AND an enemy unit is within 8 range.

#### Scenario: Low HP scout with nearby enemy retreats
- **WHEN** scout total HP is below 50% and an enemy unit is within 8 range
- **THEN** the scout SHALL be ordered to move toward the nearest friendly townhall

#### Scenario: Low HP scout without nearby enemies continues
- **WHEN** scout total HP is below 50% but no enemy unit is within 8 range
- **THEN** the scout SHALL continue its current waypoint exploration

#### Scenario: Healthy scout does not retreat
- **WHEN** scout total HP is above 50% regardless of enemy proximity
- **THEN** the scout SHALL NOT receive retreat orders

### Requirement: Dead scout is handled gracefully
The system SHALL detect when the scout unit no longer exists and transition to a DEAD state without errors.

#### Scenario: Scout killed
- **WHEN** `find_by_tag` returns None for the stored scout tag
- **THEN** the scout state SHALL be set to DEAD and no further scout orders SHALL be issued
