## ADDED Requirements

### Requirement: Match reports are generated after each game
The system SHALL generate a match report for every completed game in the `reports/{match_id}/` directory, where `match_id` is the timestamped replay filename without extension. A match report SHALL include at minimum three output files.

#### Scenario: Report directory created on game end
- **WHEN** a match ends (win or loss)
- **THEN** a subdirectory SHALL exist at `reports/{match_id}/` containing report files

#### Scenario: Report files are written
- **WHEN** a match ends
- **THEN** `reports/{match_id}/report.json`, `report.html`, and `report.md` SHALL all exist

### Requirement: JSON report is LLM-consumable
The system SHALL produce a `report.json` file with structured match data in a flat JSON format suitable for LLM consumption. The JSON SHALL include timeline snapshots, army composition history, pre-aggregated metrics, and key events.

#### Scenario: JSON report contains required top-level fields
- **WHEN** `report.json` is generated
- **THEN** it SHALL contain at minimum: `match_id`, `map`, `opponent_race`, `opponent_difficulty`, `our_race`, `duration_seconds`, `result`, `timeline`, `army_snapshots`, `metrics`, and `key_events`

#### Scenario: Timeline snapshots contain feature data
- **WHEN** `report.json.timeline` is inspected
- **THEN** each snapshot SHALL contain: `step`, `time`, `supply_used`, `supply_cap`, `workers`, `army`, `minerals`, `vespene`, `expansion_count`

#### Scenario: Metrics are pre-aggregated
- **WHEN** `report.json.metrics` is inspected
- **THEN** it SHALL contain: `avg_unspent_minerals`, `avg_unspent_vespene`, `supply_blocks` (list with time+duration), `peak_workers`, `worker_target`

#### Scenario: Key events are included
- **WHEN** `report.json.key_events` is inspected
- **THEN** each event SHALL have: `time`, `type` (one of: `game_start`, `supply_block`, `enemy_push`, `worker_stalled`, `resource_float`, `tech_milestone`, `expansion_started`, `attack_ready`, `game_end`)

### Requirement: HTML report is browsable with army comparison
The system SHALL produce a `report.html` file that renders correctly in a browser without any web server or JavaScript. The HTML SHALL display a two-column army composition comparison between our units and enemy visible units at regular time intervals.

#### Scenario: HTML report opens in browser
- **WHEN** `report.html` is opened directly in a web browser via `file://` protocol
- **THEN** the report SHALL render correctly with no console errors and no network requests

#### Scenario: Two-column army composition displayed
- **WHEN** viewing the HTML report
- **THEN** left column SHALL show "Nuestro Ejercito" with our unit counts per time snapshot AND right column SHALL show "Ejercito Enemigo" with visible enemy unit counts

#### Scenario: Supply sparkline visualized
- **WHEN** viewing the HTML report
- **THEN** a supply graph SHALL be displayed using unicode block characters showing supply progression for both players

#### Scenario: Critical events highlighted
- **WHEN** viewing the HTML report
- **THEN** supply_block and enemy_push events SHALL be visually highlighted (e.g., with warning icon)

#### Scenario: No external dependencies
- **WHEN** inspecting the HTML source
- **THEN** no external CSS, JavaScript, or font files SHALL be referenced

### Requirement: Markdown report is human-readable
The system SHALL produce a `report.md` file with a readable summary of the match including the outcome, duration, key events, and metrics summary.

#### Scenario: Markdown summary exists
- **WHEN** `report.md` is generated
- **THEN** it SHALL include the match outcome, opponent info, duration, and a bullet list of key events

### Requirement: Index page lists all matches
The system SHALL maintain a `reports/index.html` file listing all completed matches in a sortable HTML table with columns for date, map, result, duration, and max supply reached.

#### Scenario: Index page lists all matches
- **WHEN** `reports/index.html` is opened in a browser
- **THEN** every match subdirectory in `reports/` SHALL appear as a row in the table

#### Scenario: Index links to individual reports
- **WHEN** a match row in the index is interacted with
- **THEN** clicking the match name SHALL navigate to its `report.html`

#### Scenario: Index updates after new match
- **WHEN** a new match completes
- **THEN** `reports/index.html` SHALL be regenerated to include the new match

### Requirement: Match data is persisted incrementally during gameplay
The system SHALL write `features.jsonl` (one JSON object per step) and `events.jsonl` (one JSON object per detected event) incrementally during `on_step` so data is not lost if the game crashes before `on_end`.

#### Scenario: Features file contains per-step data
- **WHEN** `on_step` is called at iteration N
- **THEN** the extracted features for that step SHALL be appended to `reports/{match_id}/features.jsonl`

#### Scenario: Events file contains detected events
- **WHEN** an event is detected during `on_step`
- **THEN** the event SHALL be appended to `reports/{match_id}/events.jsonl`

#### Scenario: Incomplete match data survives crash
- **WHEN** the game process terminates before `on_end` is called
- **THEN** `features.jsonl` and `events.jsonl` SHALL contain data up to the last completed step
