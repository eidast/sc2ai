## ADDED Requirements

### Requirement: Scout metadata is tracked per unit type
The system SHALL track, for each enemy unit type observed, a `last_seen` timestamp (game_time_seconds) and a `confidence` value that decays exponentially based on `scout_decay_rate` from the active YAML profile.

#### Scenario: First observation timestamps a unit type
- **WHEN** an enemy Marine is seen for the first time at game_time 45.0
- **THEN** the scout metadata for "MARINE" SHALL have `last_seen: 45.0` and `confidence: 1.0`

#### Scenario: Confidence decays over time without re-observation
- **WHEN** an enemy Marine was last seen at game_time 45.0 and current game_time is 75.0 with `decay_rate: 0.05`
- **THEN** its confidence SHALL be `exp(-0.05 * 30)` ≈ 0.22

#### Scenario: Re-observation resets confidence
- **WHEN** an enemy Marine is observed again at game_time 80.0 after previous observation at 45.0
- **THEN** `last_seen` SHALL update to 80.0 and `confidence` SHALL reset to 1.0

#### Scenario: Scout metadata cleared on new match
- **WHEN** a new match starts
- **THEN** all scout metadata SHALL be empty

### Requirement: Building inference is included in features
The system SHALL include `building_inference` in extracted features: a mapping of enemy building types observed to counts, enabling the strategy engine to infer future enemy composition.

#### Scenario: Starports detected
- **WHEN** 2 enemy Starports are visible
- **THEN** `building_inference` SHALL contain `{"STARPORT": 2}`

#### Scenario: Building inference empty when no buildings visible
- **WHEN** no enemy buildings are visible
- **THEN** `building_inference` SHALL be an empty dict `{}`

### Requirement: Economy inference is included in features
The system SHALL include `eco_inference` in extracted features: an estimated enemy economy state (bases_count, gas_count, estimated_workers) based on visible buildings and known game time.

#### Scenario: Enemy bases counted from visible townhalls
- **WHEN** 2 enemy Hatcheries are visible
- **THEN** `eco_inference.bases_count` SHALL be at least 2

#### Scenario: Worker estimate based on game time and bases
- **WHEN** enemy has 2 bases at game_time 300
- **THEN** `eco_inference.estimated_workers` SHALL be a reasonable estimate based on time and base count

### Requirement: Scout age data included in features
The system SHALL include `scout_age` in extracted features: a map from enemy unit type name to `{last_seen: float, confidence: float}` for each unit type ever observed.

#### Scenario: Scout age populated after observations
- **WHEN** enemy Marines and Marauders have been observed at different times
- **THEN** `scout_age` SHALL contain entries for both "MARINE" and "MARAUDER" with their respective timestamps and confidences

#### Scenario: Scout age empty at match start
- **WHEN** the match has just started and no enemy units have been seen
- **THEN** `scout_age` SHALL be an empty dict `{}`
