## ADDED Requirements

### Requirement: Policy mode is explicit for each match
The system SHALL support explicit policy modes `heuristic` and `ml_shadow` for each bot run. If no policy mode is configured, the system SHALL use `heuristic`.

#### Scenario: Default policy mode
- **WHEN** the bot is started without a policy mode
- **THEN** the active policy mode SHALL be `heuristic`

#### Scenario: Shadow policy mode configured
- **WHEN** the bot is started with policy mode `ml_shadow`
- **THEN** the active policy mode SHALL be `ml_shadow`

### Requirement: Shadow mode preserves heuristic control
The system SHALL keep the heuristic policy as the only action-executing policy in both `heuristic` and `ml_shadow` modes.

#### Scenario: Heuristic mode executes heuristic action
- **WHEN** policy mode is `heuristic` and the heuristic selects an action
- **THEN** the selected action SHALL be the heuristic action

#### Scenario: Shadow mode executes heuristic action
- **WHEN** policy mode is `ml_shadow` and the heuristic selects an action
- **THEN** the selected action SHALL be the heuristic action

#### Scenario: Shadow prediction does not control gameplay
- **WHEN** policy mode is `ml_shadow` and an ML shadow prediction exists
- **THEN** the system SHALL NOT execute the ML shadow prediction instead of the heuristic action

### Requirement: Policy decisions are recorded as JSONL
The system SHALL persist policy decision records to `reports/{match_id}/decisions.jsonl` during gameplay.

#### Scenario: Decision file created for match
- **WHEN** a match starts and the report directory is initialized
- **THEN** the system SHALL prepare `reports/{match_id}/decisions.jsonl` for policy decision records

#### Scenario: Heuristic decision recorded
- **WHEN** the heuristic policy evaluates a macro action
- **THEN** the system SHALL append a JSON line containing time, step, policy mode, selected policy, decision state, heuristic action, and heuristic profile

#### Scenario: Bias vector recorded when available
- **WHEN** the heuristic bias calculator has a current bias vector
- **THEN** the decision record SHALL include the bias vector as JSON-serializable numeric values

#### Scenario: Shadow prediction recorded when available
- **WHEN** policy mode is `ml_shadow` and a shadow prediction is available
- **THEN** the decision record SHALL include the shadow prediction and whether it agrees with the heuristic action

#### Scenario: Shadow prediction absent
- **WHEN** policy mode is `ml_shadow` and no shadow prediction implementation is available
- **THEN** the decision record SHALL still include the heuristic decision and SHALL remain valid JSON

### Requirement: Policy metadata identifies experiment context
The system SHALL include match-level policy metadata suitable for A/B analysis.

#### Scenario: Policy metadata in match report
- **WHEN** a match report is generated
- **THEN** the report SHALL include a `policy` object with `mode`, `selected_policy`, `heuristic_profile`, `model_name`, `model_version`, `experiment_id`, and `code_version` keys

#### Scenario: Unknown optional metadata
- **WHEN** optional model, experiment, or code version values are not configured
- **THEN** the corresponding policy metadata values SHALL be `unknown` or null while preserving the `policy` object shape

### Requirement: A/B attribution data is available per report
The system SHALL make policy metadata available in generated reports so results can be grouped by policy mode and version.

#### Scenario: Report result attributed to policy
- **WHEN** a report contains result `victory` or `defeat`
- **THEN** the report SHALL also contain policy metadata that identifies the mode and selected policy responsible for the result

#### Scenario: Report index includes policy fields
- **WHEN** the report index is generated from match reports
- **THEN** each indexed match SHALL expose policy mode, selected policy, heuristic profile, model name, model version, and experiment id when available
