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

### Requirement: Excess workers are used for secondary scouting
The system SHALL deploy a secondary scout using an idle or excess mineral worker when the following conditions are met: (a) the worker scout is not already active, (b) at least 1 idle worker exists OR at least one base is oversaturated, (c) game_time > 180 seconds, and (d) the average scout metadata confidence across known enemy unit types is below 0.4. The worker scout SHALL follow the same waypoint list as the main scout (enemy start locations and expansions).

#### Scenario: Worker scout activated with idle workers
- **WHEN** 2 idle workers exist, game_time is 300s, and scout confidence is 0.3
- **THEN** one idle worker SHALL be designated as the worker scout and sent to the first unscouted waypoint

#### Scenario: Worker scout not activated in early game
- **WHEN** game_time is 90s and idle workers exist
- **THEN** no worker scout SHALL be activated

#### Scenario: Worker scout not activated when confidence is high
- **WHEN** idle workers exist but average scout confidence is 0.8
- **THEN** no worker scout SHALL be activated

#### Scenario: Worker scout returns to mining after completing waypoints
- **WHEN** the worker scout has visited all waypoints
- **THEN** the worker SHALL be ordered to gather minerals at the nearest base (returning to the economy)

#### Scenario: Dead worker scout does not block replacement
- **WHEN** the worker scout unit no longer exists (killed)
- **THEN** the worker scout state SHALL reset and a new worker SHALL be eligible for deployment on the next step if conditions are met

#### Scenario: Worker scout does not retreat
- **WHEN** the worker scout takes damage from enemy units
- **THEN** no retreat order SHALL be issued (unlike the main scout probe)

#### Scenario: Worker scout and main scout do not conflict
- **WHEN** both main scout and worker scout are active
- **THEN** both SHALL operate independently using the shared waypoint list without interfering with each other
