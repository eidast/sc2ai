## MODIFIED Requirements

### Requirement: Decision engine evaluates game state each step
The system SHALL implement an `evaluate_decision()` function that consumes the current features dict, the current decision state, enemy race, and configuration flags (fog enabled, surrender enabled) and returns the next decision state with a reason string. The decision engine SHALL run after the utility-based PriorityEngine, acting as a safety override layer for critical states (surrender, victory) while the PriorityEngine drives tactical decisions.

#### Scenario: Decision returned each step
- **WHEN** `evaluate_decision()` is called with valid features and state
- **THEN** it SHALL return a `(DecisionState, reason_string)` tuple

#### Scenario: Default state is DEFEND
- **WHEN** the bot starts a new game
- **THEN** the decision state SHALL be `DEFEND`

#### Scenario: Priority engine drives tactical decisions
- **WHEN** the bot is not in SURRENDER or WON state
- **THEN** tactical actions (build orders, unit production, upgrades) SHALL be determined by the PriorityEngine, not by the FSM state

#### Scenario: No state change without condition
- **WHEN** features do not meet any transition condition
- **THEN** the current decision state SHALL be preserved

### Requirement: FSM retains critical override transitions
The system SHALL preserve the FSM's ability to override the PriorityEngine for critical state transitions. The remaining FSM states SHALL be DEFEND (defending/normal play), SURRENDER (hopeless), and WON (victory confirmed). The ATTACK and RECOVER states SHALL be deprecated as first-class decision drivers; the PriorityEngine handles offensive/defensive posture via biases.

#### Scenario: Supply cap attack handled by PriorityEngine
- **WHEN** supply_used >= 200
- **THEN** the PriorityEngine SHALL drive combat unit production rather than the FSM transitioning to ATTACK (fallback override remains available)

#### Scenario: Surrender still managed by FSM
- **WHEN** surrender_enabled is True AND decision state is DEFEND AND surrender conditions are met and sustained
- **THEN** decision SHALL transition to SURRENDER

#### Scenario: Victory still managed by FSM
- **WHEN** enemy eliminated condition is confirmed
- **THEN** decision SHALL transition to WON

### Requirement: FSM transitions RECOVER → DEFEND on rebuild
The system SHALL transition from RECOVER to DEFEND when army and economy have recovered sufficiently. The RECOVER state SHALL be entered when army is destroyed (threshold-driven) but the PriorityEngine SHALL manage rebuilding priorities through biases during this state.

#### Scenario: Recovery complete with PriorityEngine guidance
- **WHEN** decision state is RECOVER AND army_value_ratio >= 0.6 AND worker_count >= 20
- **THEN** decision SHALL transition to DEFEND

#### Scenario: PriorityEngine guides rebuild composition during RECOVER
- **WHEN** decision state is RECOVER
- **THEN** the PriorityEngine SHALL continue evaluating tactical actions with biases adjusted for economic recovery

## ADDED Requirements

### Requirement: FSM states are logged for reporting
The system SHALL log FSM state transitions and the corresponding bias vector state at each transition for match reporting and analysis.

#### Scenario: State transition logged with bias context
- **WHEN** FSM transitions from DEFEND to any other state
- **THEN** the transition SHALL be logged with the current bias vector values

### Requirement: PriorityEngine evaluation precedes FSM evaluation
The system SHALL evaluate the PriorityEngine before the FSM on each step, ensuring tactical decisions are already determined before the FSM applies overrides.

#### Scenario: Engine runs before FSM
- **WHEN** `on_step` executes
- **THEN** `PriorityEngine.evaluate()` SHALL be called before `evaluate_decision()`
