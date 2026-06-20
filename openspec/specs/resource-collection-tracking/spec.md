## ADDED Requirements

### Requirement: Collected resources are tracked in features
The system SHALL include `collected_minerals` and `collected_vespene` in the feature vector returned by `extract_features()`, sourced from `bot.state.score.collected_minerals` and `bot.state.score.collected_vespene`. These values represent the cumulative total resources gathered since the start of the game.

#### Scenario: Collected minerals and vespene appear in features
- **WHEN** `extract_features()` is called during a running game
- **THEN** the returned dictionary SHALL contain `collected_minerals` (int) and `collected_vespene` (int) as cumulative totals

#### Scenario: Collected resources are zero when score is unavailable
- **WHEN** `bot.state` or `bot.state.score` is not available (e.g., early initialization, testing)
- **THEN** `collected_minerals` and `collected_vespene` SHALL default to 0

#### Scenario: Collected resources increase monotonically
- **WHEN** features are extracted across multiple steps during a game
- **THEN** `collected_minerals` and `collected_vespene` SHALL never decrease between consecutive feature frames

#### Scenario: Collected resources are persisted to features.jsonl
- **WHEN** features are written to `features.jsonl` each step
- **THEN** `collected_minerals` and `collected_vespene` SHALL be included in the JSONL output

### Requirement: Spending efficiency is computed from collected resources
The report SHALL compute a spending efficiency metric from the collected resource totals and average unspent resources, and display it in the metrics dashboard.

#### Scenario: Efficiency is calculated correctly
- **WHEN** a match has `collected_minerals = 50000`, `avg_unspent_minerals = 1200`, and `total_steps = 13000`
- **THEN** the mineral efficiency SHALL be approximately `(50000 - 1200 * 13000 / 13000) / 50000 * 100` = 68.8% (displayed rounded to 1 decimal)

#### Scenario: Vespene efficiency is also calculated
- **WHEN** a match has valid collected and unspent vespene data
- **THEN** the report SHALL also compute and display vespene spending efficiency
