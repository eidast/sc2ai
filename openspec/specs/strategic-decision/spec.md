## ADDED Requirements

### Requirement: Decision engine evaluates game state each step
The system SHALL implement an `evaluate_decision()` function that consumes the current features dict, the current decision state, enemy race, and configuration flags (fog enabled, surrender enabled) and returns the next decision state with a reason string.

#### Scenario: Decision returned each step
- **WHEN** `evaluate_decision()` is called with valid features and state
- **THEN** it SHALL return a `(DecisionState, reason_string)` tuple

#### Scenario: Default state is DEFEND
- **WHEN** the bot starts a new game
- **THEN** the decision state SHALL be `DEFEND`

#### Scenario: No state change without condition
- **WHEN** features do not meet any transition condition
- **THEN** the current decision state SHALL be preserved

### Requirement: FSM transitions DEFEND → ATTACK on advantage
The system SHALL transition from DEFEND to ATTACK when army advantage is detected. The threshold SHALL vary by game phase.

#### Scenario: Early game attack on strong advantage
- **WHEN** game_time < 240s AND army_value_ratio >= 1.5 AND our_army_supply >= 30
- **THEN** decision SHALL transition from DEFEND to ATTACK

#### Scenario: Mid game attack on moderate advantage
- **WHEN** 240s <= game_time < 600s AND army_value_ratio >= 1.2 AND our_army_supply >= 80
- **THEN** decision SHALL transition from DEFEND to ATTACK

#### Scenario: Late game attack on supply or T3 window
- **WHEN** 600s <= game_time < 900s AND (army_value_ratio >= 1.2 OR enemy_t3_count > 0) AND our_army_supply >= 100
- **THEN** decision SHALL transition from DEFEND to ATTACK

#### Scenario: Desperate phase always attacks or surrenders
- **WHEN** game_time >= 900s AND our_army_supply >= 60
- **THEN** decision SHALL transition from DEFEND to ATTACK

#### Scenario: No attack below minimum supply
- **WHEN** our army supply is below the phase minimum
- **THEN** decision SHALL remain in DEFEND regardless of other conditions

#### Scenario: Supply cap attack (legacy behavior)
- **WHEN** supply_used >= 200
- **THEN** decision SHALL transition to ATTACK regardless of phase

#### Scenario: Enemy push triggers counter-attack
- **WHEN** an enemy_push event is active AND our army supply > 30
- **THEN** decision SHALL transition from DEFEND to ATTACK

### Requirement: FSM transitions ATTACK → RECOVER on army lost
The system SHALL transition from ATTACK to RECOVER when our army is effectively destroyed.

#### Scenario: Army destroyed during attack
- **WHEN** decision state is ATTACK AND our army_count < 3
- **THEN** decision SHALL transition to RECOVER

#### Scenario: Attack timeout without damage
- **WHEN** decision state is ATTACK AND 120s have passed since entering ATTACK with no enemy structures destroyed
- **THEN** decision SHALL transition to RECOVER

### Requirement: FSM transitions RECOVER → DEFEND on rebuild
The system SHALL transition from RECOVER to DEFEND when army and economy have recovered sufficiently.

#### Scenario: Recovery complete
- **WHEN** decision state is RECOVER AND army_value_ratio >= 0.6 AND worker_count >= 20
- **THEN** decision SHALL transition to DEFEND

### Requirement: FSM transitions RECOVER → SURRENDER on no comeback
The system SHALL transition from RECOVER to SURRENDER when recovery is impossible. Surrender evaluation SHALL only run when surrender is enabled.

#### Scenario: Surrender conditions met
- **WHEN** surrender_enabled is True AND decision state is RECOVER AND game_time > 300s AND army_value_ratio < 0.15 AND worker_count < 10 AND conditions sustained for 120s
- **THEN** decision SHALL transition to SURRENDER

#### Scenario: Surrender not evaluated when disabled
- **WHEN** surrender_enabled is False
- **THEN** the decision engine SHALL NOT transition to SURRENDER

#### Scenario: Surrender not evaluated during attack
- **WHEN** decision state is ATTACK
- **THEN** the decision engine SHALL NOT evaluate surrender conditions

#### Scenario: Surrender not evaluated in early game
- **WHEN** game_time < 300s
- **THEN** the decision engine SHALL NOT transition to SURRENDER regardless of conditions

### Requirement: Race-specific threshold adjustments
The system SHALL adjust attack thresholds based on the opponent's race.

#### Scenario: Lower thresholds vs Zerg
- **WHEN** enemy race is Zerg
- **THEN** all supply thresholds SHALL be multiplied by 0.85

#### Scenario: Higher thresholds vs Protoss
- **WHEN** enemy race is Protoss
- **THEN** all supply thresholds SHALL be multiplied by 1.1

#### Scenario: Baseline thresholds vs Terran
- **WHEN** enemy race is Terran
- **THEN** all supply thresholds SHALL use the baseline multiplier of 1.0

### Requirement: Fog-aware threshold adjustments
The system SHALL adjust attack thresholds when fog-of-war is enabled, reflecting reduced information certainty.

#### Scenario: Higher thresholds with fog
- **WHEN** fog_enabled is True
- **THEN** all supply thresholds SHALL be multiplied by 1.3

#### Scenario: Baseline thresholds without fog
- **WHEN** fog_enabled is False
- **THEN** all supply thresholds SHALL use their base values without fog adjustment

### Requirement: T3 detection influences attack decision
The system SHALL detect tier-3 enemy units and use them to trigger urgent attack windows when no friendly T3 is available.

#### Scenario: T3 window triggers attack
- **WHEN** enemy_t3_count > 0 AND our_t3_count == 0 AND game_time > 360s AND our_army_supply >= 12
- **THEN** decision SHALL transition from DEFEND to ATTACK with reason "t3_window"

#### Scenario: T3 with advantage does not skip attack
- **WHEN** enemy_t3_count > 0 AND our_t3_count > 0
- **THEN** T3 detection SHALL NOT independently trigger attack (normal advantage rules apply)

### Requirement: Fog-enabled surrender is more tolerant
The system SHALL apply more conservative surrender thresholds when fog-of-war is enabled.

#### Scenario: Surrender harder with fog
- **WHEN** fog_enabled is True
- **THEN** the army_value_ratio surrender threshold SHALL be 0.10 (vs 0.15 default)

### Requirement: Priority formulas include structure prerequisites
All structure-building priority formulas in strategy profiles (YAML) SHALL include production chain prerequisites as multiplication factors. Specifically:
- `GATEWAY` formula SHALL NOT depend on any prerequisite (always buildable for gateway units)
- `CYBERNETICSCORE` formula SHALL require `has_structure('GATEWAY')` as a factor
- `FORGE`, `TWILIGHTCOUNCIL`, `ROBOTICSFACILITY`, `STARGATE` formulas SHALL require `has_structure('CYBERNETICSCORE')` as a factor, ensuring score is zero when the Cybernetics Core is missing

#### Scenario: Forge score is zero without Core
- **WHEN** the bot has no Cybernetics Core and the strategy engine evaluates the Forge formula
- **THEN** the Forge score SHALL be zero because `has_structure('CYBERNETICSCORE')` evaluates to 0

#### Scenario: Robo score is zero without Core
- **WHEN** the bot has no Cybernetics Core and the strategy engine evaluates the Robotics Facility formula
- **THEN** the Robotics Facility score SHALL be zero because `has_structure('CYBERNETICSCORE')` evaluates to 0

#### Scenario: Formula prerequisite chain respects production requirements
- **WHEN** the bot has a Gateway but no Cybernetics Core
- **THEN** the Cybernetics Core formula MAY have a positive score (requires Gateway), but Forge, Robo, Stargate, and Twilight Council formulas SHALL have zero score (require Cybernetics Core)

### Requirement: MyBot exposes configuration flags
The system SHALL accept `surrender_enabled` and `fog_enabled` as constructor parameters on `MyBot`.

#### Scenario: Flags passed to bot
- **WHEN** MyBot is initialized with `surrender_enabled=True, fog_enabled=True`
- **THEN** the decision engine SHALL use these values for threshold evaluation and surrender eligibility
