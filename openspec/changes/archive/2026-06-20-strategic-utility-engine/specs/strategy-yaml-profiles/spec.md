## ADDED Requirements

### Requirement: YAML profiles define strategy configuration
The system SHALL support loading strategy profiles from YAML files. Each profile SHALL define `name`, `race`, optional `description`, `initial_biases`, `scouting_adjustments`, `priority_formulas`, and `meta` sections.

#### Scenario: Valid YAML profile loads successfully
- **WHEN** a YAML file contains all required sections with valid values
- **THEN** `StrategyLoader.load(path)` SHALL return a validated `StrategyProfile` object

#### Scenario: Missing required section fails validation
- **WHEN** a YAML file is missing the `initial_biases` section
- **THEN** `StrategyLoader.load(path)` SHALL raise a `ValidationError` with a descriptive message

#### Scenario: Invalid bias value fails validation
- **WHEN** `initial_biases` contains a value outside [0.0, 1.0] (e.g., 1.5 or -0.2)
- **THEN** `StrategyLoader.load(path)` SHALL raise a `ValidationError`

### Requirement: Scouting adjustments use condition expressions
The system SHALL support condition expressions in `scouting_adjustments` that reference observation features using dot notation (e.g., `enemy_army_analysis.air_count`) and comparison operators (`>`, `<`, `>=`, `<=`, `==`, `!=`).

#### Scenario: Simple numeric comparison evaluates correctly
- **WHEN** features contain `enemy_army_analysis.air_count = 8` and condition is `enemy_army_analysis.air_count > 5`
- **THEN** the condition SHALL evaluate to True

#### Scenario: Simple numeric comparison evaluates to false
- **WHEN** features contain `enemy_army_analysis.air_count = 3` and condition is `enemy_army_analysis.air_count > 5`
- **THEN** the condition SHALL evaluate to False

#### Scenario: Condition references non-existent feature
- **WHEN** condition references `enemy_army_analysis.unknown_field` which does not exist in features
- **THEN** the condition SHALL evaluate to False and log a warning

### Requirement: Priority formulas use expression strings
The system SHALL evaluate `priority_formulas` as arithmetic expressions with access to bias values, built-in functions, and game state variables.

#### Scenario: Formula uses bias variables
- **WHEN** formula is `"gateway_units * 0.6"` and `gateway_units` bias is 0.5
- **THEN** the evaluated result SHALL be 0.3

#### Scenario: Formula with built-in function
- **WHEN** formula is `"(1 - own_ratio('STALKER', 'army')) * gateway_units"` and the bot has 50% Stalkers
- **THEN** the formula SHALL use 0.5 for `own_ratio` result

#### Scenario: Invalid formula syntax returns zero
- **WHEN** a formula string contains a syntax error (e.g., unmatched parentheses)
- **THEN** the formula SHALL evaluate to 0.0 and log an error

### Requirement: Meta parameters are configurable per profile
The system SHALL support `meta` parameters in YAML: `bias_speed` (float, default 0.3), `scout_decay_rate` (float, default 0.05), `max_workers` (int, default 70), `target_bases` (int, default 4).

#### Scenario: Meta defaults applied when omitted
- **WHEN** the YAML profile does not specify `meta.bias_speed`
- **THEN** `bias_speed` SHALL be 0.3

#### Scenario: Meta override from YAML
- **WHEN** the YAML profile specifies `meta: { bias_speed: 0.5 }`
- **THEN** `bias_speed` SHALL be 0.5

### Requirement: Multiple profiles coexist and are selectable by race
The system SHALL support loading all profiles from a directory and filtering by race. The active profile SHALL be selectable at match start.

#### Scenario: Profiles filtered by race
- **WHEN** three profiles exist: two with `race: Protoss`, one with `race: Zerg`
- **THEN** `StrategyLoader.load_all("Protoss")` SHALL return the two Protoss profiles

#### Scenario: Default profile when none specified
- **WHEN** no explicit profile name is provided and race is Protoss
- **THEN** the system SHALL load the profile named `standard_macro` as default
