## ADDED Requirements

### Requirement: Script analyzes shadow decision records
The system SHALL provide a CLI script `scripts/analyze_shadows.py` that reads `decisions.jsonl`, `features.jsonl`, and `events.jsonl` from a match directory and produces comparative metrics.

#### Scenario: Script accepts match ID argument
- **WHEN** the user runs `uv run python scripts/analyze_shadows.py <match_id>`
- **THEN** the script SHALL read `reports/<match_id>/decisions.jsonl`, `features.jsonl`, and `events.jsonl`

#### Scenario: Script errors on missing files
- **WHEN** the specified match directory does not exist or lacks `decisions.jsonl`
- **THEN** the script SHALL exit with a clear error message and non-zero exit code

#### Scenario: Script produces overview metrics
- **WHEN** the script runs successfully
- **THEN** it SHALL report total steps, game time, result, strategic state distribution percentages, and override rate

#### Scenario: Script produces agreement matrix
- **WHEN** the script runs successfully and shadow predictions exist
- **THEN** it SHALL compute and display an N×N agreement matrix where each cell is the percentage of steps where two profiles recommended the same target

#### Scenario: Agreement is computed per target equality
- **WHEN** comparing two profiles' predictions
- **THEN** they SHALL be considered in agreement when both `recommended_action.target` values are equal

#### Scenario: Script produces action distribution
- **WHEN** the script runs successfully
- **THEN** it SHALL report the top-3 most frequent recommended actions per profile with average score and standard deviation

#### Scenario: Script produces bias evolution summary
- **WHEN** the script runs successfully and `utility.bias_vector` is present in decision records
- **THEN** it SHALL report the initial value, final value, and delta for each bias key

#### Scenario: Script produces timeline of key events
- **WHEN** the script runs successfully
- **THEN** it SHALL report a chronological timeline including strategic state transitions, first divergence between profiles, and override periods

#### Scenario: Empty shadow predictions handled
- **WHEN** a decision record has `shadow_predictions: []`
- **THEN** the analysis SHALL skip that record for agreement/distribution but include it in overview

#### Scenario: Script outputs JSON on demand
- **WHEN** the user runs the script with `--format json`
- **THEN** all metrics SHALL be output as a single JSON object to stdout
