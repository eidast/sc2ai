## ADDED Requirements

### Requirement: Policy decisions are persisted alongside observations
The system SHALL persist policy decision telemetry in the match report directory alongside `features.jsonl` and `events.jsonl`.

#### Scenario: Decisions file path initialized
- **WHEN** `on_step` is called for the first time and `reports/{match_id}/` is created
- **THEN** the bot SHALL initialize a path for `reports/{match_id}/decisions.jsonl`

#### Scenario: Decisions appended during gameplay
- **WHEN** the bot computes a heuristic macro action during `on_step`
- **THEN** the bot SHALL append one JSON-serializable decision record to `decisions.jsonl`

#### Scenario: Existing observations remain unchanged
- **WHEN** decision telemetry is enabled
- **THEN** the bot SHALL continue writing `features.jsonl` and `events.jsonl` using their existing formats
