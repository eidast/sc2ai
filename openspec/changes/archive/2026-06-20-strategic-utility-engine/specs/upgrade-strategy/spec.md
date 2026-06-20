## MODIFIED Requirements

### Requirement: Forge is built when floating minerals
The system SHALL build a Forge when the PriorityEngine determines it has the highest utility score among reachable actions, OR when the fallback hardcoded logic triggers (minerals exceed 300 and vespene exceeds 50, provided no Forge already exists or is pending). The PriorityEngine SHALL take precedence when it produces an action.

#### Scenario: PriorityEngine triggers forge
- **WHEN** `PriorityEngine.evaluate()` returns `Action(type=BUILD_STRUCTURE, target=FORGE)` and prerequisites are met
- **THEN** the bot SHALL attempt to build a Forge

#### Scenario: Hardcoded fallback builds forge
- **WHEN** no PriorityEngine action is active AND minerals > 300 AND vespene > 50 AND no Forge exists
- **THEN** the bot SHALL issue a build order for a Forge (existing behavior preserved)

#### Scenario: Forge not built when poor
- **WHEN** minerals ≤ 300 and no PriorityEngine action targets a Forge
- **THEN** the bot SHALL NOT attempt to build a Forge

#### Scenario: Forge not duplicated
- **WHEN** a Forge already exists or is pending and no PriorityEngine action targets a Forge
- **THEN** the bot SHALL NOT attempt to build another Forge

### Requirement: Ground upgrades are researched in priority order
The system SHALL delegate upgrade selection to the PriorityEngine when it produces a `RESEARCH_UPGRADE` action. When no PriorityEngine action is active, the system SHALL fall back to the defined priority order (Weapons 1 → Armor 1 → Weapons 2 → Armor 2 → Shields 1 → Weapons 3 → Armor 3 → Shields 2 → Shields 3).

#### Scenario: PriorityEngine selects upgrade
- **WHEN** `PriorityEngine.evaluate()` returns `Action(type=RESEARCH_UPGRADE, target=PROTOSSGROUNDWEAPONSLEVEL1)` and a Forge is ready
- **THEN** the bot SHALL research Weapons Level 1

#### Scenario: Fallback to priority order
- **WHEN** no PriorityEngine action is active AND a Forge is ready AND Weapons 1 is not researched or pending
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
The system SHALL build a Twilight Council when the PriorityEngine determines it has the highest utility score, OR when the fallback hardcoded logic triggers (a Cybernetics Core is ready, minerals exceed 300, vespene exceeds 100, and no Twilight Council exists).

#### Scenario: PriorityEngine triggers twilight
- **WHEN** PriorityEngine returns `Action(type=BUILD_STRUCTURE, target=TWILIGHTCOUNCIL)` and prerequisites are met
- **THEN** the bot SHALL attempt to build a Twilight Council

#### Scenario: Fallback builds twilight
- **WHEN** no PriorityEngine action is active AND Cyber Core is ready AND minerals > 300 AND vespene > 100 AND no Twilight exists
- **THEN** the bot SHALL issue a build order for a Twilight Council

#### Scenario: Twilight not built without Cyber Core
- **WHEN** no Cyber Core exists and no PriorityEngine action targets a Twilight Council
- **THEN** the bot SHALL NOT attempt to build a Twilight Council

### Requirement: Twilight upgrade adapts to enemy
The system SHALL delegate twilight upgrade selection to the PriorityEngine when it produces a research action. When no PriorityEngine action is active, the system SHALL fall back to: research Blink if scouted enemy has more than 3 air units; otherwise research Charge.

#### Scenario: PriorityEngine selects blink upgrade
- **WHEN** PriorityEngine returns `Action(type=RESEARCH_UPGRADE, target=BLINKTECH)` and a Twilight Council is ready
- **THEN** the bot SHALL research Blink

#### Scenario: Fallback blink vs air enemy
- **WHEN** no PriorityEngine action is active AND enemy army analysis shows `air_count > 3` AND a Twilight Council is ready
- **THEN** the bot SHALL research Blink (BLINKTECH)

#### Scenario: Fallback charge by default
- **WHEN** no PriorityEngine action is active AND enemy army analysis shows `air_count ≤ 3` (or no analysis available) AND a Twilight Council is ready
- **THEN** the bot SHALL research Charge (CHARGE)
