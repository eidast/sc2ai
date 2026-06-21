## ADDED Requirements

### Requirement: Metrics dashboard renders at top of HTML report
The HTML report SHALL display a consolidated metrics dashboard as the first content section after the header, before army snapshots and base saturation. The dashboard SHALL present key performance indicators in a two-column card layout (economy | army).

#### Scenario: Dashboard displays economy metrics
- **WHEN** the HTML report is generated from a completed match
- **THEN** the dashboard SHALL show collected minerals, collected vespene, average unspent minerals, average unspent vespene, spending efficiency as a percentage, peak workers, worker target, and supply block count in the economy column

#### Scenario: Dashboard displays army metrics
- **WHEN** the HTML report is generated from a completed match
- **THEN** the dashboard SHALL show max supply reached, max supply cap, max army size, our army value peak, enemy army value peak (labeled as "visible"), our T3 count, and enemy T3 count in the army column

#### Scenario: Enemy army value shows visible indicator
- **WHEN** enemy army value is displayed in the dashboard
- **THEN** the value SHALL be labeled with "(visible)" to indicate it is a lower bound under fog-of-war

#### Scenario: Efficiency is computed from collected and unspent
- **WHEN** collected minerals is greater than 0
- **THEN** spending efficiency SHALL be calculated as `(collected - avg_unspent_per_step * total_steps) / collected * 100` and displayed as a percentage

#### Scenario: Efficiency handles zero collected
- **WHEN** collected minerals is 0
- **THEN** efficiency SHALL be displayed as "N/A"

### Requirement: Events are consolidated into ranges for display
The HTML report SHALL consolidate consecutive events of the same type into ranges rather than displaying individual event rows. The events summary table SHALL show each event type with count, first occurrence time, last occurrence time, and duration.

#### Scenario: Consecutive same-type events form a single range
- **WHEN** the events array contains 8,000 consecutive supply_block events from 120s to 2300s
- **THEN** the summary table SHALL display one row for supply_block with count=8000, first=120s, last=2300s, duration=2180s

#### Scenario: Interrupted events form separate ranges
- **WHEN** resource_float events occur at 300-400s and again at 600-800s, separated by other events
- **THEN** the summary table SHALL display two separate rows for resource_float with their respective time ranges

#### Scenario: Point events display without duration
- **WHEN** a tech_milestone event occurs once at 180s
- **THEN** the summary table SHALL display it with count=1 and no duration field (or duration=N/A)

#### Scenario: Events are sorted by severity then count
- **WHEN** the consolidated event list is generated
- **THEN** events SHALL be sorted by severity (high first, then medium, then info), and within the same severity by count descending

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

### Requirement: Reports include policy metadata
The match report JSON, Markdown, and HTML outputs SHALL include policy metadata for the match when available.

#### Scenario: Report JSON includes policy object
- **WHEN** `generate_report_json()` receives bot info containing policy metadata
- **THEN** the returned report dict SHALL include a top-level `policy` object preserving that metadata

#### Scenario: Report JSON defaults policy metadata
- **WHEN** `generate_report_json()` receives no policy metadata
- **THEN** the returned report dict SHALL include a `policy` object with unknown/default values

#### Scenario: Markdown report shows policy summary
- **WHEN** the Markdown report is generated
- **THEN** it SHALL display policy mode, selected policy, heuristic profile, model name, model version, and experiment id

#### Scenario: HTML report shows policy summary
- **WHEN** the HTML report is generated
- **THEN** it SHALL display policy mode, selected policy, heuristic profile, model name, model version, and experiment id in the report header or dashboard area

### Requirement: Report index exposes policy fields
The generated report index SHALL expose policy fields for each match so A/B comparisons can group outcomes by policy identity.

#### Scenario: Index entry includes policy identity
- **WHEN** `generate_index()` reads a match report containing policy metadata
- **THEN** the index entry for that match SHALL include policy mode, selected policy, heuristic profile, model name, model version, and experiment id

#### Scenario: Index handles older reports
- **WHEN** `generate_index()` reads an older report without policy metadata
- **THEN** the index entry SHALL use unknown/default policy values instead of failing
