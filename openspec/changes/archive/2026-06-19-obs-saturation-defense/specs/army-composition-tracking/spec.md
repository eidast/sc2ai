## ADDED Requirements

### Requirement: Our army composition is tracked
The system SHALL include `our_army_composition` in extracted features, containing a mapping of our own unit type names to counts (e.g., `{"STALKER": 5, "ZEALOT": 3}`), excluding workers and observers. The format SHALL mirror the existing `enemy_army_composition` field.

#### Scenario: Army composition with multiple unit types
- **WHEN** the bot has 5 Stalkers, 3 Zealots, and 12 Probes
- **THEN** `our_army_composition` SHALL be `{"STALKER": 5, "ZEALOT": 3}` (probes excluded)

#### Scenario: Army composition when no army exists
- **WHEN** the bot has only probes and no combat units
- **THEN** `our_army_composition` SHALL be an empty dict `{}`

#### Scenario: Army composition excludes non-combat units
- **WHEN** the bot has 1 Observer, 2 Stalkers, and 15 Probes
- **THEN** `our_army_composition` SHALL exclude the Observer and Probes, resulting in `{"STALKER": 2}`

### Requirement: Our structure composition is tracked
The system SHALL include `our_structures` in extracted features, containing a mapping of our structure type names to counts (e.g., `{"GATEWAY": 2, "CYBERNETICSCORE": 1, "NEXUS": 2}`).

#### Scenario: Structure composition at mid-game
- **WHEN** the bot has 2 Nexuses, 3 Gateways, 1 Cybernetics Core, and 2 Pylons
- **THEN** `our_structures` SHALL contain `{"NEXUS": 2, "GATEWAY": 3, "CYBERNETICSCORE": 1, "PYLON": 2}`

#### Scenario: Structure composition excludes pending buildings
- **WHEN** a Gateway is under construction (not ready)
- **THEN** the pending Gateway SHALL be included in the count (it exists as a structure)

### Requirement: Our army composition appears in match reports
The system SHALL include `our_army_composition` in army snapshots within the generated JSON, Markdown, and HTML reports. The HTML report SHALL display our army composition in a dedicated table separate from the enemy composition table.

#### Scenario: HTML report shows our composition
- **WHEN** a match report is generated with `our_army_composition` data
- **THEN** the HTML SHALL contain a table labeled "Our Army Composition" with unit types and counts

#### Scenario: JSON report includes our composition in snapshots
- **WHEN** `generate_report_json()` is called with features containing `our_army_composition`
- **THEN** each army snapshot SHALL include an `our_composition` field
