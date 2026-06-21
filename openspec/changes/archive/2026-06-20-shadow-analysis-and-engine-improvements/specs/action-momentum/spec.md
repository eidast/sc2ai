## ADDED Requirements

### Requirement: PriorityEngine applies continuity bonus
The `PriorityEngine.evaluate()` method SHALL apply a multiplicative bonus to candidate actions that match the previously recommended action.

#### Scenario: Continuity bonus applied to same target and type
- **WHEN** a candidate action has the same `target` and `type` as the previous step's selected action
- **THEN** its score SHALL be multiplied by 1.15 before comparison with other candidates

#### Scenario: No continuity bonus for different action
- **WHEN** a candidate action has a different `target` or `type` from the previous action
- **THEN** its score SHALL remain unchanged

#### Scenario: No continuity bonus on first evaluation
- **WHEN** `evaluate()` is called with `prev_action=None` (first step or no prior action)
- **THEN** no continuity bonus SHALL be applied to any candidate

#### Scenario: NOOP actions do not receive or grant momentum
- **WHEN** the previous action was NOOP (type=NOOP, target="")
- **THEN** no continuity bonus SHALL be applied to any candidate

### Requirement: Momentum bonus does not override hard constraints
The continuity bonus SHALL NOT override reachability filtering or resource constraints.

#### Scenario: Unreachable action cannot win via momentum
- **WHEN** a candidate action is unreachable (supply blocked, missing resources, missing tech tree)
- **THEN** the action SHALL be excluded before momentum is considered
