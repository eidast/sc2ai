## ADDED Requirements

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
