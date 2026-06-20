## ADDED Requirements

### Requirement: Bias vector initialized from YAML profile
The system SHALL initialize a bias vector from the active YAML strategy profile's `initial_biases` map at match start. Each bias SHALL be a float in [0.0–1.0] with a unique string key.

#### Scenario: Bias vector initialized at game start
- **WHEN** `BiasCalculator` is instantiated with a valid YAML profile
- **THEN** the `bias_vector` SHALL match `initial_biases` from the profile exactly

#### Scenario: Default bias for missing keys
- **WHEN** a scouting adjustment references a bias key not present in `initial_biases`
- **THEN** that bias SHALL default to 0.0 before the adjustment is applied

### Requirement: Scouting adjustments modify biases
The system SHALL evaluate each `scouting_adjustments` rule from the active YAML profile against current observation features and SHALL adjust biases accordingly, weighted by scouting confidence and `bias_speed`.

#### Scenario: Air-heavy scouting increases stargate bias
- **WHEN** `enemy_army_analysis.air_count > 5` matches a scouting rule targeting `stargate_units: +0.25`
- **THEN** the `stargate_units` bias SHALL increase toward the target, scaled by `bias_speed` and scout confidence

#### Scenario: Scouting rule does not match
- **WHEN** no scouting adjustment condition evaluates to True
- **THEN** biases SHALL remain at their previous values (no adjustment applied)

#### Scenario: Multiple scouting rules match simultaneously
- **WHEN** two or more scouting adjustment conditions evaluate to True
- **THEN** all matching adjustments SHALL be applied cumulatively

#### Scenario: Bias stays within [0.0, 1.0]
- **WHEN** any bias is adjusted upward beyond 1.0 or downward below 0.0
- **THEN** the bias SHALL be clamped to [0.0, 1.0]

### Requirement: Scouting confidence decays with time
The system SHALL apply exponential decay to the confidence of scouted enemy information based on time elapsed since the last observation. The decay rate SHALL be configured by `meta.scout_decay_rate` in the YAML profile.

#### Scenario: Recent scouting has high confidence
- **WHEN** an enemy unit type was observed within the last 10 seconds of game time
- **THEN** its scouting confidence SHALL be >= 0.8

#### Scenario: Old scouting has reduced confidence
- **WHEN** an enemy unit type was last observed more than 120 seconds ago
- **THEN** its scouting confidence SHALL be < 0.1

#### Scenario: Never-scouted unit has zero confidence
- **WHEN** an enemy unit type has never been observed
- **THEN** its scouting confidence SHALL be 0.0

### Requirement: Bias speed controls adjustment rate
The system SHALL apply `bias_speed` from the YAML profile as a scalar multiplier on all bias adjustments, controlling how quickly biases respond to new information.

#### Scenario: Low bias speed dampens changes
- **WHEN** `bias_speed` is 0.1 and a scouting rule applies +0.5 to a bias
- **THEN** the effective change in one step SHALL be 0.05 (not the full 0.5)

#### Scenario: High bias speed applies full changes
- **WHEN** `bias_speed` is 1.0 and a scouting rule applies +0.5 to a bias
- **THEN** the effective change in one step SHALL be 0.5

#### Scenario: Bias speed defaults when not configured
- **WHEN** the YAML profile does not specify `meta.bias_speed`
- **THEN** `bias_speed` SHALL default to 0.3

### Requirement: BiasCalculator exposes current bias vector
The system SHALL expose the current bias vector as a read-only property accessible to the PriorityEngine and to logging/reporting.

#### Scenario: Bias vector readable after update
- **WHEN** `BiasCalculator.update()` has been called at least once
- **THEN** `BiasCalculator.bias_vector` SHALL return the current bias values as `dict[str, float]`
