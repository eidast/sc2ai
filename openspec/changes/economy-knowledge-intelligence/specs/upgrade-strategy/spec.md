## ADDED Requirements

### Requirement: Forge is built when floating minerals
The system SHALL build a Forge when minerals exceed 300 and vespene exceeds 50, provided no Forge already exists or is pending.

#### Scenario: Forge built when floating
- **WHEN** minerals > 300 and vespene > 50 and no Forge exists
- **THEN** the bot SHALL issue a build order for a Forge

#### Scenario: Forge not built when poor
- **WHEN** minerals ≤ 300
- **THEN** the bot SHALL NOT attempt to build a Forge

#### Scenario: Forge not duplicated
- **WHEN** minerals > 300 and a Forge already exists or is pending
- **THEN** the bot SHALL NOT attempt to build another Forge

### Requirement: Ground upgrades are researched in priority order
The system SHALL cycle through ground weapon, armor, and shield upgrades using a defined priority order. The order SHALL be: Weapons 1 → Armor 1 → Weapons 2 → Armor 2 → Shields 1 → Weapons 3 → Armor 3 → Shields 2 → Shields 3.

#### Scenario: First upgrade is Weapons 1
- **WHEN** a Forge is ready and no upgrades have been researched or are pending
- **THEN** the bot SHALL research PROTOSSGROUNDWEAPONSLEVEL1

#### Scenario: Pending upgrades are skipped
- **WHEN** Weapons 1 is already being researched
- **THEN** `get_next_upgrade()` SHALL return Armor 1

#### Scenario: Completed upgrades are skipped
- **WHEN** Weapons 1 is already completed
- **THEN** `get_next_upgrade()` SHALL return Armor 1

#### Scenario: No upgrade when all maxed
- **WHEN** all ground upgrades (weapons 3, armor 3, shields 3) are completed
- **THEN** `get_next_upgrade()` SHALL return None

### Requirement: Twilight Council is built after Cyber Core
The system SHALL build a Twilight Council when a Cybernetics Core is ready, minerals exceed 300, and vespene exceeds 100, provided no Twilight Council exists.

#### Scenario: Twilight built when ready
- **WHEN** Cyber Core is ready and minerals > 300 and vespene > 100 and no Twilight exists
- **THEN** the bot SHALL issue a build order for a Twilight Council

#### Scenario: Twilight not built without Cyber Core
- **WHEN** no Cyber Core exists
- **THEN** the bot SHALL NOT attempt to build a Twilight Council

### Requirement: Twilight upgrade adapts to enemy
The system SHALL research Blink if scouted enemy has more than 3 air units. Otherwise, the system SHALL research Charge.

#### Scenario: Blink vs air-heavy enemy
- **WHEN** enemy army analysis shows `air_count > 3` and a Twilight Council is ready
- **THEN** the bot SHALL research Blink (BLINKTECH)

#### Scenario: Charge by default
- **WHEN** enemy army analysis shows `air_count ≤ 3` (or no analysis available) and a Twilight Council is ready
- **THEN** the bot SHALL research Charge (CHARGE)
