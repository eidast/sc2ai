## ADDED Requirements

### Requirement: Early game build order is deterministic
The system SHALL execute a fixed build order sequence during the first ~90 seconds of game time through `manage_early_game()`. The build order MUST be: (1) Pylon when supply_left < 4, (2) Gateway, (3) Cybernetics Core when Gateway is ready, (4) Warp Gate research when Cybernetics Core is ready. Each phase SHALL issue exactly one build order per step and retry on the next step if the build fails. The system SHALL log a diagnostic message on every build attempt (success or failure) including the reason for failure.

#### Scenario: Pylon is built before Gateway
- **WHEN** the bot has no Pylon and supply_left < 4 at game time < 90s
- **THEN** `manage_early_game` SHALL build a Pylon and return, deferring Gateway to the next step

#### Scenario: Gateway built as soon as Pylon is done
- **WHEN** a Pylon exists, no Gateway exists, and the bot can afford a Gateway at game time < 90s
- **THEN** `manage_early_game` SHALL build a Gateway and log the attempt

#### Scenario: Cybernetics Core built after Gateway completes
- **WHEN** a ready Gateway exists and no Cybernetics Core exists
- **THEN** `manage_early_game` SHALL build a Cybernetics Core

#### Scenario: Warp Gate research initiated after Cybernetics Core
- **WHEN** a ready Cybernetics Core exists and Warp Gate research is not pending or completed
- **THEN** `manage_early_game` SHALL start Warp Gate research

#### Scenario: Early game cedes control to strategy engine
- **WHEN** all early game phases are complete (Gateway, Cybernetics Core, Warp Gate research started) AND game_time >= 90s
- **THEN** `manage_early_game` SHALL return without building, allowing `manage_tech` and the strategy engine to take over

### Requirement: Build failures are logged with diagnostic detail
The system SHALL log every build attempt in `manage_early_game` and `manage_tech` with a message containing: structure name, affordability (True/False), placement result (True/False), and worker availability. The system SHALL use `_build_if_able()` as the single helper for all structure construction.

#### Scenario: Successful build logged
- **WHEN** a Gateway is successfully ordered through `_build_if_able`
- **THEN** the system SHALL log: "BUILD Gateway — afford:True placement:True worker:tag123"

#### Scenario: Failed build due to no worker
- **WHEN** a build is attempted but no idle worker is available
- **THEN** the system SHALL log: "BUILD Gateway — FAILED: no worker available"

#### Scenario: Failed build due to placement
- **WHEN** `find_placement` returns None for a structure
- **THEN** the system SHALL log: "BUILD Gateway — afford:True placement:False worker:None"

### Requirement: Build phases have timeouts
The system SHALL enforce a 15-second timeout per early-game build phase. If a phase fails to complete within 15 seconds of game time (e.g., `find_placement` returns None repeatedly), the system SHALL skip that phase and proceed to the next one, logging a warning.

#### Scenario: Phase timeout triggers skip
- **WHEN** the Gateway phase has been attempting to build for 15+ seconds of game time without success
- **THEN** the system SHALL log "BUILD Gateway — TIMEOUT after 15s, skipping phase" and proceed to the Cybernetics Core phase

### Requirement: Gateway emergency fallback in manage_tech
After `manage_early_game` has completed (game_time >= 120s), `manage_tech` SHALL check if any Gateway exists. If none exists, it SHALL log a warning and build a Gateway immediately via `_build_if_able`, regardless of what the strategy engine recommends.

#### Scenario: Gateway built as emergency fallback
- **WHEN** game_time >= 120s, no Gateway exists, and the strategy engine recommends Forge
- **THEN** `manage_tech` SHALL ignore the Forge recommendation and build a Gateway, logging: "NO GATEWAY at t=125.0 — emergency build"
