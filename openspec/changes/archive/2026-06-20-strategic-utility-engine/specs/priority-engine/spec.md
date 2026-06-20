## ADDED Requirements

### Requirement: Priority engine evaluates all reachable actions
The system SHALL evaluate, on every step, all actions that are currently reachable (prerequisites met, resources affordable, supply available) and assign each a utility score using the priority formulas from the active YAML profile.

#### Scenario: Action evaluated with bias context
- **WHEN** `PriorityEngine.evaluate()` is called with a bias vector containing `gateway_units: 0.6`
- **THEN** the STALKER priority formula SHALL use 0.6 for `gateway_units` in its computation

#### Scenario: Unreachable action excluded
- **WHEN** an action requires CYBERNETICSCORE which the bot does not own
- **THEN** that action SHALL be excluded from evaluation

#### Scenario: Action excluded by supply block
- **WHEN** `supply_left` is 0
- **THEN** actions that consume supply (train units) SHALL be excluded from evaluation

#### Scenario: Action excluded by resource shortage
- **WHEN** minerals are insufficient for an action's cost
- **THEN** that action SHALL be excluded from evaluation

### Requirement: Priority engine returns highest-scoring action
The system SHALL select the action with the highest utility score from all evaluated actions and return it as a structured `Action` object containing type, target, and score.

#### Scenario: Single clear winner
- **WHEN** STALKER scores 0.87 and all other actions score below 0.87
- **THEN** the returned Action SHALL have `type=BUILD_UNIT`, `target=STALKER`, `score=0.87`

#### Scenario: Tie broken deterministically
- **WHEN** two actions have identical utility scores
- **THEN** the system SHALL break ties using a deterministic rule (alphabetical by action name)

#### Scenario: No actions reachable
- **WHEN** no actions are reachable (blocked, no resources, no supply)
- **THEN** `evaluate()` SHALL return an Action with `type=NOOP` and `score=0.0`

### Requirement: Priority formulas use available built-in functions
The system SHALL provide a set of built-in functions accessible from priority formulas in YAML: `own_ratio(unit_name, category)`, `has_structure(structure_name)`, `has_upgrade(upgrade_name)`, `minerals`, `vespene`, `supply_left`, `supply_used`, `workers`, and `game_time`.

#### Scenario: own_ratio returns current composition ratio
- **WHEN** the bot has 5 Stalkers out of 20 total army units
- **THEN** `own_ratio('STALKER', 'army')` SHALL evaluate to 0.25

#### Scenario: has_structure checks structure ownership
- **WHEN** the bot owns a ready CYBERNETICSCORE
- **THEN** `has_structure('CYBERNETICSCORE')` SHALL evaluate to 1.0

#### Scenario: has_structure returns 0 when absent
- **WHEN** the bot does not own a FORGE
- **THEN** `has_structure('FORGE')` SHALL evaluate to 0.0

#### Scenario: has_upgrade checks upgrade completion
- **WHEN** WARPGATERESEARCH is completed
- **THEN** `has_upgrade('WARPGATERESEARCH')` SHALL evaluate to 1.0

#### Scenario: Unknown function in formula ignored gracefully
- **WHEN** a priority formula references an undefined function
- **THEN** the formula SHALL evaluate to 0.0 and log a warning

### Requirement: Priority engine filters actions by category
The system SHALL categorize each action (BUILD_UNIT, BUILD_STRUCTURE, RESEARCH_UPGRADE, ECO_ACTION) and expose the winning action so that the corresponding `manage_*` function can execute it.

#### Scenario: Action category matches manage function
- **WHEN** the winning action has `type=BUILD_STRUCTURE` and `target=GATEWAY`
- **THEN** `manage_tech()` SHALL receive this action for execution

#### Scenario: Action category directs to correct executor
- **WHEN** the winning action has `type=RESEARCH_UPGRADE` and `target=WARPGATERESEARCH`
- **THEN** `manage_upgrades()` SHALL receive this action for execution
