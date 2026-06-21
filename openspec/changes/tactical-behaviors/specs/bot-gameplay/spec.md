## MODIFIED Requirements

### Requirement: Constant worker production
The system SHALL train probes at the least saturated nexus when `undersaturated_bases > 0`, worker count is below the dynamic max, and supply and minerals are available. The system SHALL cast Chrono Boost on a Nexus that is training a probe when the Nexus has 50+ energy.

#### Scenario: Chrono Boost on probe training
- **WHEN** a Nexus has energy >= 50 and is training a probe
- **THEN** Chrono Boost SHALL be cast on that Nexus

### Requirement: Bot executes defensive behavior during on_step
The system SHALL execute `manage_defense()` on every `on_step` before `manage_attack()`. Defense SHALL evaluate threats per base, reposition idle army units toward threatened bases, and engage enemy units within range. When no base is threatened and decision state is DEFEND, idle army SHALL move toward `enemy_start_locations[0]` instead of rallying defensively. Units below 30% HP with 0 shields SHALL retreat toward the nearest Nexus. Stalkers within range of melee units SHALL move away to maintain distance.

#### Scenario: Defense runs before attack
- **WHEN** `on_step` is called
- **THEN** `manage_defense()` SHALL execute before `manage_attack()` in the dispatch order

#### Scenario: Army pushes forward when safe
- **WHEN** no bases are threatened, decision is DEFEND, and idle army exists
- **THEN** idle army SHALL move toward enemy start location

#### Scenario: Low HP unit retreats
- **WHEN** a unit has HP < 30% max, 0 shields, and is within ENGAGE_RANGE of enemy
- **THEN** the unit SHALL move toward nearest friendly Nexus

#### Scenario: Stalker kites melee
- **WHEN** a Stalker is within ENGAGE_RANGE of a melee unit (attack range < 2)
- **THEN** the Stalker SHALL move away from the enemy

## ADDED Requirements

### Requirement: Bot executes harassment during on_step
The system SHALL execute `manage_harass()` on every `on_step` after `manage_army()` and before `manage_defense()`. Harassment SHALL build one Oracle from an idle Stargate if none exists, send it to enemy mineral lines to use Pulsar Beam, and retreat at low shields. Zealot runbys SHALL be sent when 5+ idle Zealots exist.

#### Scenario: Oracle built for harassment
- **WHEN** a Stargate exists, no Oracle exists, and Stargate is idle
- **THEN** the bot SHALL train one Oracle

#### Scenario: Oracle attacks workers
- **WHEN** Oracle is at enemy expansion with visible workers
- **THEN** Oracle SHALL cast Pulsar Beam on closest worker

#### Scenario: Oracle retreats
- **WHEN** Oracle shields < 20%
- **THEN** Oracle SHALL move to nearest friendly Nexus
