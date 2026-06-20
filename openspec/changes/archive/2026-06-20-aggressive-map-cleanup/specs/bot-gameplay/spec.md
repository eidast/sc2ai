## ADDED Requirements

### Requirement: Bot aggressively cleans up remaining enemy structures
The system SHALL make `manage_attack()` actively search for and destroy remaining enemy structures while the decision engine is in `ATTACK`.

#### Scenario: Visible enemy structure is prioritized
- **WHEN** the decision state is `ATTACK`, army units exist, and at least one enemy structure is visible
- **THEN** idle army units SHALL attack the closest visible enemy structure instead of a generic map waypoint

#### Scenario: Cleanup sweeps known map locations
- **WHEN** the decision state is `ATTACK`, army units exist, and no enemy structures are visible
- **THEN** idle army units SHALL attack a cleanup waypoint selected from the enemy starting location and known expansion locations

#### Scenario: Cleanup advances after reaching waypoint
- **WHEN** the attacking army is close to the current cleanup waypoint
- **THEN** the bot SHALL advance to the next cleanup waypoint for subsequent attack orders

#### Scenario: Macro continues during cleanup
- **WHEN** cleanup attack orders are being issued in `ATTACK`
- **THEN** the bot SHALL continue running the existing macro managers before `manage_attack()` in `on_step()`

#### Scenario: Cleanup does not alter victory result semantics
- **WHEN** cleanup attack behavior is active
- **THEN** the bot SHALL still accept victory only from SC2 `player_result` or the existing sustained no-enemy-visible heuristic
