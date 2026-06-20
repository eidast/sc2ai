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
