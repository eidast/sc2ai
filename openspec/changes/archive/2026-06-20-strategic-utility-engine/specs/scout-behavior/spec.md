## ADDED Requirements

### Requirement: Scout records metadata per enemy unit type
The system SHALL update scout metadata (unit type → `{last_seen, confidence}`) whenever enemy units are visible during scouting. This metadata SHALL be accessible to the observation pipeline for inclusion in extracted features.

#### Scenario: Scout update on enemy sighting
- **WHEN** the scout probe has vision of enemy units during exploration
- **THEN** the scout system SHALL record or update metadata for each visible enemy unit type

#### Scenario: Scout metadata persists between steps
- **WHEN** a unit type was observed in a previous step but is not visible in the current step
- **THEN** its metadata SHALL persist with decaying confidence, not be deleted

#### Scenario: Dead scout stops updating metadata
- **WHEN** the scout state is DEAD
- **THEN** no new metadata SHALL be recorded (existing metadata continues to decay)

### Requirement: Scout metadata feeds BiasCalculator
The system SHALL provide scout metadata to the `BiasCalculator` for use in scouting adjustment evaluation, including `confidence` weighting of observed enemy composition.

#### Scenario: BiasCalculator uses scout confidence
- **WHEN** a scouting adjustment references `enemy_army_analysis.air_count > 5` and the air unit observations have confidence 0.9
- **THEN** the adjustment SHALL be applied with weight 0.9 (not full 1.0)

#### Scenario: Low confidence observation has reduced impact
- **WHEN** a scouting adjustment references unit types with confidence 0.2
- **THEN** the adjustment's effect SHALL be scaled by 0.2, making it minimally impactful

## MODIFIED Requirements

### Requirement: Scout explores enemy starting locations
The system SHALL send a probe to explore enemy starting locations at the beginning of the game. The scout SHALL follow an ordered list of waypoints derived from enemy start locations. While exploring, the scout SHALL record metadata for every enemy unit type observed.

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
