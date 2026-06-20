## ADDED Requirements

### Requirement: Unit properties database is available for query
The system SHALL maintain a static database of StarCraft II unit properties covering all ladder units for Protoss, Zerg, and Terran. Each entry SHALL include HP, shields, armor, attributes (Light, Armored, Biological, Mechanical, Psionic, Massive), attacks with damage/bonus/range/speed/targets, supply cost, mineral cost, vespene cost, and build time.

#### Scenario: Lookup by unit name
- **WHEN** `get_unit_info("STALKER")` is called
- **THEN** the returned dict SHALL contain `hp: 80`, `shields: 80`, `race: "Protoss"`, and `"Armored"` in attributes

#### Scenario: Unknown unit returns None
- **WHEN** `get_unit_info("NONEXISTENT")` is called
- **THEN** the function SHALL return `None`

#### Scenario: Filter by attribute
- **WHEN** `get_units_by_attribute("Armored")` is called
- **THEN** the returned list SHALL include "STALKER" and "ROACH" but not "ZEALOT"

#### Scenario: Filter by race
- **WHEN** `get_units_by_race("Zerg")` is called
- **THEN** the returned list SHALL include "ZERGLING", "ROACH", "HYDRALISK" and SHALL NOT include any Protoss or Terran units

### Requirement: Counter calculator ranks units by effective damage
The system SHALL compute counter scores for Protoss combat units against a given enemy composition. Scores SHALL be based on effective damage per second considering armor-type bonuses. The result SHALL be sorted from highest to lowest score.

#### Scenario: Stalkers rank higher than Zealots vs Roaches
- **WHEN** `compute_counters({"ROACH": 5}, race="Protoss")` is called
- **THEN** the STALKER score SHALL be greater than the ZEALOT score

#### Scenario: Immortals score high vs armored enemies
- **WHEN** `compute_counters({"ROACH": 10}, race="Protoss")` is called
- **THEN** IMMORTAL SHALL appear in results with a positive score

#### Scenario: Empty enemy composition returns empty dict
- **WHEN** `compute_counters({}, race="Protoss")` is called
- **THEN** the function SHALL return an empty dict

### Requirement: Threat assessment ranks enemy units by danger level
The system SHALL compute a threat score for each enemy unit type based on total HP, shields, and DPS multiplied by count.

#### Scenario: Each enemy unit type receives a threat score
- **WHEN** `compute_threat_assessment({"ROACH": 5, "ZERGLING": 10})` is called
- **THEN** the result SHALL be a dict with "ROACH" and "ZERGLING" keys, each mapped to a positive float score

### Requirement: Unit icons are generated as inline SVGs
The system SHALL generate unit icons as inline SVG elements. Each icon SHALL be a colored circle with the unit's initial letter, using race-specific colors: Protoss gold (#f5c542), Zerg purple (#9c27b0), Terran orange (#ff6d00). Unknown units SHALL receive a gray fallback icon. No external network resources SHALL be required.

#### Scenario: Known unit generates SVG
- **WHEN** `render_unit_icon_svg("STALKER")` is called
- **THEN** the returned string SHALL contain `<svg>`, `<circle>`, and `<text>` elements with the Protoss gold color

#### Scenario: Unknown unit generates gray fallback
- **WHEN** `render_unit_icon_svg("NONEXISTENT")` is called
- **THEN** the returned string SHALL contain the fallback color `#555555`

#### Scenario: Data URI generation for HTML embedding
- **WHEN** `get_unit_icon_data_uri("ZEALOT")` is called
- **THEN** the returned string SHALL start with `data:image/svg+xml;base64,`

#### Scenario: Multi-character initials for compound names
- **WHEN** `render_unit_icon_svg("HIGHTEMPLAR")` is called
- **THEN** the text element SHALL contain "HT"
- **WHEN** `render_unit_icon_svg("BATTLECRUISER")` is called
- **THEN** the text element SHALL contain "BC"
