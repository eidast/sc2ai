## ADDED Requirements

### Requirement: Shadow profiles run in parallel with heuristic
The system SHALL support running 1+ strategy profiles as shadow engines in `ml_shadow` mode. Each shadow engine SHALL have its own `BiasCalculator` and `PriorityEngine`, independent from the heuristic engine. Shadow predictions SHALL be analyzable via the `analyze_shadows.py` script.

#### Scenario: Single shadow profile configured
- **WHEN** the bot is started with `--policy-mode ml_shadow --shadow-profile stargate_open`
- **THEN** the system SHALL create one shadow engine using the `stargate_open` profile

#### Scenario: Multiple shadow profiles configured
- **WHEN** the bot is started with `--policy-mode ml_shadow --shadow-profile stargate_open --shadow-profile robo_open`
- **THEN** the system SHALL create two shadow engines, one per profile

#### Scenario: Shadow profile not found
- **WHEN** the bot is started with `--policy-mode ml_shadow --shadow-profile nonexistent`
- **THEN** the system SHALL raise a clear error indicating the profile was not found and listing available profiles

#### Scenario: Shadow prediction recorded for each profile
- **WHEN** a step executes in `ml_shadow` mode with shadow engines active
- **THEN** the decision record SHALL include a `shadow_predictions` array with one entry per shadow profile, each containing `profile` (string) and `recommended_action` (Action shape with `type`, `target`, `score`)

#### Scenario: Shadow prediction empty array when no shadows
- **WHEN** a step executes in `ml_shadow` mode with no shadow engines configured
- **THEN** the decision record SHALL include `shadow_predictions` as an empty array `[]`

#### Scenario: Shadow engines do not control gameplay
- **WHEN** shadow engines produce predictions
- **THEN** the system SHALL NOT use shadow predictions to issue commands — only the heuristic action SHALL control gameplay

#### Scenario: Shadow engines use same observations
- **WHEN** a step executes, the system SHALL pass the same `features` and `scout_metadata` dict to all bias calculators (active and shadow)
- **THEN** each calculator SHALL interpret observations through its own profile's `initial_biases` and `scouting_adjustments`

#### Scenario: Shadow data is analyzable post-match
- **WHEN** a match completes with `ml_shadow` mode
- **THEN** the `decisions.jsonl` SHALL be readable by `scripts/analyze_shadows.py` to produce comparative metrics

### Requirement: BiasCalculator does not mutate shared scout metadata
The `BiasCalculator.update()` method SHALL NOT modify the `scout_metadata` dictionary passed to it. Scout decay SHALL be applied exclusively by `ScoutMetadata.apply_decay()`.

#### Scenario: Scout decay applied once per step
- **WHEN** `ScoutMetadata.apply_decay()` is called in `on_step`
- **THEN** confidence values in scout metadata SHALL be decayed exactly once per step

#### Scenario: BiasCalculator is a pure consumer
- **WHEN** `BiasCalculator.update()` receives scout metadata
- **THEN** the input dictionary SHALL remain unchanged after the call
