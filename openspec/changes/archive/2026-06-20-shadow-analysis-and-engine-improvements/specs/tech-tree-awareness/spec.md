## ADDED Requirements

### Requirement: PriorityEngine filters actions by tech tree requirements
The `PriorityEngine` SHALL exclude candidate actions whose required structures are not present in the current game state.

#### Scenario: Action with satisfied requirements passes filter
- **WHEN** a formula entry declares `requires: ["ROBOTICSBAY"]` and the player has a completed ROBOTICSBAY
- **THEN** the action SHALL be considered reachable and included in evaluation

#### Scenario: Action with unsatisfied requirements is filtered
- **WHEN** a formula entry declares `requires: ["ROBOTICSBAY"]` and the player does NOT have a completed ROBOTICSBAY
- **THEN** the action SHALL be excluded from evaluation regardless of its formula score

#### Scenario: Action with no requirements is always reachable
- **WHEN** a formula entry has no `requires` field
- **THEN** the action SHALL be considered reachable subject to existing resource and supply checks

#### Scenario: Multiple requirements all must be satisfied
- **WHEN** a formula entry declares `requires: ["ROBOTICSBAY", "TWILIGHTCOUNCIL"]`
- **THEN** the action SHALL be reachable only if BOTH structures exist

### Requirement: YAML schema supports optional requires field
The strategy profile YAML schema SHALL accept an optional `requires` field on each `priority_formulas` entry.

#### Scenario: Legacy string formula still works
- **WHEN** a `priority_formulas` entry is a plain string (e.g., `STALKER: "gateway_units * 0.6"`)
- **THEN** the loader SHALL treat it as a formula with no `requires`

#### Scenario: Dict formula with requires is parsed
- **WHEN** a `priority_formulas` entry is a dict with `formula` and `requires` keys
- **THEN** the loader SHALL extract both fields into the strategy profile

#### Scenario: Dict formula without requires defaults to empty
- **WHEN** a `priority_formulas` entry is a dict with only `formula` (no `requires`)
- **THEN** the loader SHALL treat `requires` as an empty list
