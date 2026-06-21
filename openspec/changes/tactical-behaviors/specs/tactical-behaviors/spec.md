## ADDED Requirements

### Requirement: Chrono Boost accelerates probe production
`manage_probes()` SHALL cast Chrono Boost on the Nexus when the Nexus has 50+ energy and is currently training a probe. The ability SHALL target the Nexus that is training the probe.

#### Scenario: Chrono Boost on probe training
- **WHEN** a Nexus has energy >= 50 and is training a probe
- **THEN** the bot SHALL cast Chrono Boost on that Nexus

#### Scenario: No Chrono Boost without energy
- **WHEN** a Nexus has energy < 50
- **THEN** no Chrono Boost SHALL be cast

### Requirement: Idle army advances toward enemy
When `manage_defense()` detects no threatened bases and the decision state is DEFEND, idle army units SHALL move toward `self.enemy_start_locations[0]` instead of rallying to base. If enemy push is active, defense posture SHALL take priority.

#### Scenario: Idle army pushes forward
- **WHEN** no bases are threatened, decision is DEFEND, and idle army units exist
- **THEN** idle army units SHALL move toward the enemy start location

#### Scenario: Defense overrides push when threatened
- **WHEN** a base is threatened and idle army exists
- **THEN** army SHALL defend the threatened base instead of pushing forward

### Requirement: Oracle worker harassment
A new `manage_harass()` method SHALL build one Oracle from an idle Stargate (if none exists), send it to the nearest enemy expansion mineral line, activate Pulsar Beam on workers, and retreat when shields drop below 20%. After retreat, the Oracle SHALL return to base and the cycle restarts.

#### Scenario: Oracle attacks workers
- **WHEN** an Oracle exists, is at an enemy expansion, and enemy workers are present
- **THEN** the Oracle SHALL cast Pulsar Beam on the closest worker

#### Scenario: Oracle retreats when damaged
- **WHEN** Oracle shields < 20%
- **THEN** the Oracle SHALL move back to the nearest friendly Nexus

### Requirement: Zealot runby harassment
When the bot has 5+ idle Zealots outside of combat, `manage_harass()` SHALL send 3 of them to attack-move toward enemy expansion locations.

#### Scenario: Zealots sent to enemy expansion
- **WHEN** idle Zealot count >= 5 and enemy expansions are known
- **THEN** 3 Zealots SHALL be ordered to attack the enemy expansion location

### Requirement: Low-HP unit pullback
In `manage_defense()`, units within ENGAGE_RANGE of enemies that have HP below 30% of maximum and zero shields SHALL be ordered to move toward the nearest friendly Nexus.

#### Scenario: Damaged unit retreats
- **WHEN** a Zealot has 30/100 HP, 0 shields, and is within 8 range of an enemy
- **THEN** the Zealot SHALL be ordered to move toward the nearest Nexus

#### Scenario: Healthy unit stays
- **WHEN** a Stalker has 80/80 HP, 80/80 shields, and is within 8 range of an enemy
- **THEN** the Stalker SHALL NOT retreat

### Requirement: Stalker kite vs melee
Stalkers within ENGAGE_RANGE of melee enemy units (attack range < 2) SHALL move away from the enemy after each attack to maintain distance.

#### Scenario: Stalker kites Zergling
- **WHEN** a Stalker is within 8 range of a Zergling and Zergling attack range < 2
- **THEN** the Stalker SHALL move directly away from the Zergling
