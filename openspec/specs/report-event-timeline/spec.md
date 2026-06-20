## ADDED Requirements

### Requirement: d3.js timeline renders event ranges interactively
The HTML report SHALL include an interactive SVG timeline built with d3.js v7 that visualizes event ranges as horizontal bars and point events as markers. d3.js SHALL be embedded inline in the HTML (no CDN, no external file reference), ensuring the report works when opened via `file://`.

#### Scenario: Timeline shows horizontal bars for persistent events
- **WHEN** an event type has one or more ranges with duration > 0
- **THEN** the timeline SHALL render a horizontal `<rect>` bar spanning from the range start time to end time on the X axis, positioned in a lane corresponding to the event type on the Y axis

#### Scenario: Bars are color-coded by severity
- **WHEN** a bar is rendered for an event range
- **THEN** high severity events SHALL use red (#e94560), medium severity SHALL use yellow (#f5c542), and info severity SHALL use blue (#4a9eff)

#### Scenario: Timeline shows point markers for instant events
- **WHEN** an event has duration=0 or is a point event (tech_milestone, expansion_started, game_start)
- **THEN** the timeline SHALL render a `<circle>` or diamond marker at the event's time position in its respective lane

#### Scenario: Timeline supports zoom and pan
- **WHEN** the user scrolls or drags on the timeline SVG
- **THEN** the timeline SHALL support zoom (via d3.zoom) and horizontal pan to explore time ranges in detail

#### Scenario: Timeline shows tooltip on hover
- **WHEN** the user hovers over a bar or marker
- **THEN** a tooltip SHALL appear showing the event type, time range, count, and severity

#### Scenario: Timeline renders with no events
- **WHEN** a match has zero events (empty events array)
- **THEN** the timeline SHALL render an empty SVG with axis labels and a message "No events recorded" instead of crashing

#### Scenario: Timeline data is embedded in HTML
- **WHEN** the HTML report is opened via `file://` protocol
- **THEN** the d3.js library SHALL be fully available (embedded as inline `<script>`) and the timeline SHALL render without network requests

### Requirement: Event timeline data is structured for d3 consumption
The report generation SHALL produce a JSON-serializable timeline data structure with separated ranged events and point events, suitable for d3.js rendering.

#### Scenario: Timeline data has ranged events
- **WHEN** consolidated events include supply_block with range 120s-2300s
- **THEN** the timeline data SHALL contain `ranges: [{type: "supply_block", severity: "high", start: 120.0, end: 2300.0, count: 8180}]`

#### Scenario: Timeline data has point events
- **WHEN** consolidated events include a single tech_milestone at 180s
- **THEN** the timeline data SHALL contain `points: [{type: "tech_milestone", time: 180.0, severity: "info", details: "Cybernetics Core completed"}]`

#### Scenario: Timeline data includes game duration
- **WHEN** a match lasted 2347 seconds
- **THEN** the timeline data SHALL include `duration: 2347.0` for X-axis scaling

### Requirement: Saturation timeline data is included in report JSON
The match report JSON SHALL include a `saturation_timeline` field containing snapshots of per-base saturation captured at 60-second intervals. Each snapshot SHALL include per-base breakdown (mineral_workers, gas_workers, mineral_saturation, gas_saturation, status, idle) and aggregate totals (total workers, oversaturated count, undersaturated count, idle workers, average saturations).

#### Scenario: Timeline data structures are JSON-serializable
- **WHEN** saturation_timeline is generated
- **THEN** all values SHALL be standard JSON types (int, float, str, list, dict) with no NaN or Infinity

#### Scenario: Timeline aggregates match per-base data
- **WHEN** a snapshot has bases with statuses "oversaturated", "optimal", "undersaturated"
- **THEN** `oversaturated_bases` and `undersaturated_bases` in `totals` SHALL match the counts of those statuses in the `bases` array
