## ADDED Requirements

### Requirement: Per-base saturation cards display in the HTML dashboard
The HTML report SHALL display per-base saturation cards in the economy section, after the existing mineral/vespene efficiency metrics. Each card SHALL show the base index, mineral saturation bar (actual/ideal with percentage), gas saturation bar (actual/ideal with percentage), and status label. Idle worker count SHALL be shown when non-zero.

#### Scenario: Single base card displays
- **WHEN** the match ends with 1 base at 14/16 minerals (87%) and 4/6 gas (67%)
- **THEN** the HTML dashboard SHALL show a card titled "Base 1" with mineral bar at 87%, gas bar at 67%, and status "undersaturated"

#### Scenario: Multiple base cards display side by side
- **WHEN** the match ends with 3 bases
- **THEN** the HTML dashboard SHALL show 3 cards in a row, one per base

#### Scenario: Idle workers shown in card
- **WHEN** a base has 2 idle workers nearby
- **THEN** the base card SHALL display "Idle: 2" with a warning indicator

#### Scenario: Status color-coded
- **WHEN** a base has status "oversaturated"
- **THEN** the status label SHALL use red/warning styling
- **WHEN** a base has status "optimal"
- **THEN** the status label SHALL use green/good styling
- **WHEN** a base has status "undersaturated"
- **THEN** the status label SHALL use yellow/warn styling
