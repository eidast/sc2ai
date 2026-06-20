## ADDED Requirements

### Requirement: Priority engine runs before manage_* block
The system SHALL invoke `PriorityEngine.evaluate()` once per step before the `manage_*` block in `on_step`, and SHALL pass the resulting `Action` to the appropriate `manage_*` function.

#### Scenario: Action passed to correct manager
- **WHEN** `evaluate()` returns `Action(type=BUILD_UNIT, target=STALKER)`
- **THEN** `manage_army()` SHALL receive this action and attempt to train a Stalker

#### Scenario: No action produced
- **WHEN** `evaluate()` returns `Action(type=NOOP)`
- **THEN** all `manage_*` functions SHALL be skipped for this step

### Requirement: manage_* functions accept strategy context
The system SHALL modify each `manage_*` function to accept an optional `Action` parameter. When provided, the function SHALL prioritize executing that action over its internal autonomous logic.

#### Scenario: manage_tech executes provided action
- **WHEN** `manage_tech()` receives `Action(type=BUILD_STRUCTURE, target=GATEWAY)` and Gateways are needed
- **THEN** it SHALL build a Gateway using the action's parameters

#### Scenario: manage_tech falls back when no action provided
- **WHEN** `manage_tech()` receives no action or `Action(type=NOOP)`
- **THEN** it SHALL execute its original autonomous logic as fallback

#### Scenario: manage_army trains the target unit
- **WHEN** `manage_army()` receives `Action(type=BUILD_UNIT, target=VOIDRAY)` and a Stargate is ready
- **THEN** it SHALL queue a Void Ray from the available Stargate

### Requirement: manage_upgrades delegates to priority engine
The system SHALL modify `manage_upgrades()` to accept `Action(type=RESEARCH_UPGRADE, target=...)` from the priority engine instead of using hardcoded `UPGRADE_ORDER`.

#### Scenario: Upgrade action from engine
- **WHEN** `manage_upgrades()` receives `Action(type=RESEARCH_UPGRADE, target=PROTOSSGROUNDWEAPONSLEVEL1)` and a Forge is ready
- **THEN** it SHALL research Weapons Level 1

#### Scenario: Fallback to hardcoded order when no action
- **WHEN** `manage_upgrades()` receives no action and a Forge is idle
- **THEN** it SHALL fall back to the existing `UPGRADE_ORDER` logic

### Requirement: manage_tech delegates build decisions to priority engine
The system SHALL modify `manage_tech()` to accept `Action(type=BUILD_STRUCTURE, target=...)` from the priority engine for tech building decisions.

#### Scenario: Stargate build action from engine
- **WHEN** `manage_tech()` receives `Action(type=BUILD_STRUCTURE, target=STARGATE)` and prerequisites are met
- **THEN** it SHALL build a Stargate

#### Scenario: manage_tech ignores unusable action
- **WHEN** `manage_tech()` receives an action for a structure whose prerequisites are not met
- **THEN** it SHALL skip execution and log a warning

### Requirement: Existing manage_* behaviors preserved when no action
The system SHALL preserve the existing behavior of `manage_probes`, `manage_pylons`, `manage_gas`, `manage_expansion`, `manage_defense`, `manage_attack`, and `manage_scout` when they receive no strategy action, ensuring backward compatibility.

#### Scenario: manage_probes unchanged without action
- **WHEN** `manage_probes()` receives no action
- **THEN** it SHALL behave identically to the current implementation

#### Scenario: manage_defense unchanged without action
- **WHEN** `manage_defense()` receives no action
- **THEN** it SHALL use its existing reactive defense logic

### Requirement: FSM retains safety override capability
The system SHALL allow the existing FSM (`decision.py`) to produce overrides that take precedence over the priority engine's action for critical decisions (surrender, victory, supply-cap attack).

#### Scenario: FSM forces surrender override
- **WHEN** FSM transitions to SURRENDER state
- **THEN** the priority engine SHALL NOT be evaluated and the game loop SHALL stop

#### Scenario: FSM triggers supply cap attack
- **WHEN** FSM transitions to ATTACK due to supply >= 200
- **THEN** the priority engine SHALL be restricted to only combat unit actions
