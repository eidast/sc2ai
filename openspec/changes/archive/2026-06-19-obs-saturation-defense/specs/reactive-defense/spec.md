## ADDED Requirements

### Requirement: Threat is evaluated per base each step
The system SHALL evaluate defensive threat for each owned townhall on every `on_step` by counting enemy units within THREAT_RANGE (15) and scoring threat as the sum of enemy unit supply costs (defaulting to 1 per unit if supply_cost is unavailable). Bases SHALL be sorted by threat score descending.

#### Scenario: No enemies near any base
- **WHEN** no enemy units are within THREAT_RANGE of any owned nexus
- **THEN** threat score for all bases SHALL be 0

#### Scenario: Enemies near one base
- **WHEN** 3 enemy marines (supply 1 each) and 1 siege tank (supply 3) are within THREAT_RANGE of the natural
- **THEN** the natural's threat score SHALL be 6 and it SHALL be marked as the most threatened base

#### Scenario: Enemies near multiple bases
- **WHEN** base A has threat score 4 and base B has threat score 10
- **THEN** base B SHALL be prioritized for defense

### Requirement: Army repositions defensively in PEACEFUL state
The system SHALL move idle army units to a defensive rally point when no threats are detected. The rally point SHALL be the midpoint between the main and natural bases, or the main base ramp if only one base exists.

#### Scenario: Army rallies between two bases
- **WHEN** the bot has 2 nexuses and no threats are detected
- **THEN** idle army units SHALL be ordered to move to the midpoint between the main and natural positions

#### Scenario: Army rallies at ramp with one base
- **WHEN** the bot has 1 nexus and no threats are detected
- **THEN** idle army units SHALL be ordered to move to the main base ramp

### Requirement: Army defends threatened bases
The system SHALL order idle army units to move toward the most threatened base when enemy units are within THREAT_RANGE. When army units are within ENGAGE_RANGE (8) of enemy units near a threatened base, they SHALL attack the nearest enemy.

#### Scenario: Army moves to threatened base
- **WHEN** an enemy force is detected within THREAT_RANGE of the natural and army units are idle at main
- **THEN** army units SHALL be ordered to move to the natural position

#### Scenario: Army engages when in range
- **WHEN** army units are within ENGAGE_RANGE of enemy units near a threatened base
- **THEN** each idle army unit SHALL attack the closest enemy unit to its position

#### Scenario: Defense yields to attack at max supply
- **WHEN** the bot reaches 200 supply and `attack_triggered` is True
- **THEN** `manage_attack()` SHALL take priority and units SHALL attack the enemy start location regardless of defense state

### Requirement: Enemy push detection considers base proximity
The system SHALL refine `enemy_push` event detection to consider whether the enemy unit increase is near any of our bases, not just a raw count delta. An enemy push SHALL still be detected on raw delta > 10 for backward compatibility.

#### Scenario: Push detected near base
- **WHEN** enemy visible units increase by 15 and at least 5 are within THREAT_RANGE of a base
- **THEN** an `enemy_push` event SHALL be emitted with `near_base: true` in details

#### Scenario: Push detected far from base
- **WHEN** enemy visible units increase by 15 but none are within THREAT_RANGE of any base
- **THEN** an `enemy_push` event SHALL be emitted with `near_base: false` in details

### Requirement: Base under attack event is detected
The system SHALL emit a `base_under_attack` event when enemy units are within THREAT_RANGE of any owned townhall AND at least one enemy unit is attacking (has an attack order targeting our units or structures near the base).

#### Scenario: Enemy attacking structures near base
- **WHEN** enemy marines are within THREAT_RANGE and have attack orders targeting our structures at the natural
- **THEN** a `base_under_attack` event SHALL be emitted with the base position in details

#### Scenario: Enemy near base but not attacking
- **WHEN** enemy units are within THREAT_RANGE but moving (not attacking)
- **THEN** no `base_under_attack` event SHALL be emitted
