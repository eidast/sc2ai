## ADDED Requirements

### Requirement: Early game build order is deterministic
The system SHALL execute a fixed build order sequence through `manage_early_game()`. The build order MUST be: (1) Pylon when supply_left < 4, (2) Gateway, (3) Cybernetics Core when Gateway is ready, (4) Warp Gate research when Cybernetics Core is ready. Each phase SHALL issue exactly one build order per step and retry on the next step if the build fails. The system SHALL log a diagnostic message on every build attempt (success or failure) including the reason for failure. The phase machine SHALL continue running past 90 seconds of game time until all phases complete; the per-phase 15s timeout SHALL remain as the only skip mechanism.

#### Scenario: Pylon is built before Gateway
- **WHEN** the bot has no Pylon and supply_left < 4
- **THEN** `manage_early_game` SHALL build a Pylon and return, deferring Gateway to the next step

#### Scenario: Gateway built as soon as Pylon is done
- **WHEN** a Pylon exists, no Gateway exists, and the bot can afford a Gateway
- **THEN** `manage_early_game` SHALL build a Gateway and log the attempt

#### Scenario: Cybernetics Core built after Gateway completes
- **WHEN** a ready Gateway exists and no Cybernetics Core exists
- **THEN** `manage_early_game` SHALL build a Cybernetics Core

#### Scenario: Warp Gate research initiated after Cybernetics Core
- **WHEN** a ready Cybernetics Core exists and Warp Gate research is not pending or completed
- **THEN** `manage_early_game` SHALL start Warp Gate research

#### Scenario: Early game cedes control to strategy engine
- **WHEN** all early game phases are complete (Gateway, Cybernetics Core, Warp Gate research started)
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
`manage_tech` SHALL check if any Gateway or Warpgate exists using a combined count of both structures. If the combined count is zero and game_time >= 120s, it SHALL log a warning and build a Gateway immediately via `_build_if_able`, regardless of what the strategy engine recommends. If the combined count is zero but game_time < 120s, the early game phase machine (`manage_early_game`) is still responsible for building the first Gateway, and `manage_tech` SHALL NOT interfere.

#### Scenario: Gateway built as emergency fallback when no Gateways or Warpgates
- **WHEN** game_time >= 120s, no Gateway and no Warpgate exist, and the strategy engine recommends Forge
- **THEN** `manage_tech` SHALL ignore the Forge recommendation and build a Gateway, logging: "NO GATEWAY at t=125.0 — emergency build"

#### Scenario: Emergency fallback skipped when Warpgate exists
- **WHEN** game_time >= 120s, no Gateway exists but at least one Warpgate exists
- **THEN** `manage_tech` SHALL NOT trigger the emergency Gateway build and SHALL proceed to Cybernetics Core and tech structure checks normally

### Requirement: Early-game phase is exposed to policy telemetry
The deterministic early-game build order SHALL expose lightweight phase and override context to policy telemetry without changing build-order behavior.

#### Scenario: Early-game phase recorded during opening
- **WHEN** policy decision telemetry is recorded while `manage_early_game()` is active
- **THEN** the decision record SHALL include the current `early_game_phase`

#### Scenario: Early-game override source recorded
- **WHEN** deterministic early-game logic attempts or constrains a build-order action
- **THEN** the decision record SHALL include `override_source` as `early_game_build_order`

#### Scenario: Early-game executed intent recorded when known
- **WHEN** deterministic early-game logic attempts a Pylon, Gateway, Cybernetics Core, or Warp Gate research action
- **THEN** the decision record SHALL include `executed_intent` identifying that attempted action

#### Scenario: Early-game gameplay unchanged
- **WHEN** policy telemetry is enabled in `heuristic` or `ml_shadow` mode
- **THEN** `manage_early_game()` SHALL preserve the existing deterministic build order and timeout behavior

### Requirement: Gateway and Warpgate are treated as equivalent production structures
All methods that check for Gateway existence as a prerequisite SHALL use the combined count of `UnitTypeId.GATEWAY` and `UnitTypeId.WARPGATE` structures. This applies to `manage_tech()` (emergency fallback, production capacity scaling), `manage_gas()` (second assimilator gate), and `manage_army()` (early-return guard).

#### Scenario: manage_tech proceeds past Gateway check when Warpgates exist
- **WHEN** the bot has 0 Gateways but 3 Warpgates
- **THEN** `manage_tech` SHALL NOT build an emergency Gateway and SHALL proceed to Cybernetics Core and tech structure checks

#### Scenario: manage_gas allows second assimilator when Warpgates exist
- **WHEN** the bot has 1 Assimilator, 0 Gateways, 2 Warpgates, and an unoccupied geyser
- **THEN** `manage_gas` SHALL build a second Assimilator normally

#### Scenario: Gateway production target counts Warpgates
- **WHEN** computing the target gateway count for `manage_tech()`
- **THEN** the system SHALL compare the combined Gateway + Warpgate count against the target, not Gateways alone

### Requirement: Early game fast expand when pressure is low
The system SHALL add a fast-expand phase to `manage_early_game()` after the Cybernetics Core phase. When pressure level is NONE or LOW and `expansion_count < 2`, the bot SHALL attempt to build a Nexus at the natural expansion location. If pressure is MEDIUM or HIGH, or the bot already has 2+ Nexuses, this phase SHALL be skipped.

#### Scenario: Fast expand when pressure is NONE
- **WHEN** early game phase is 2.5 (after CyberCore), pressure is NONE, expansion_count < 2, and can afford Nexus
- **THEN** `manage_early_game` SHALL build a Nexus

#### Scenario: Fast expand skipped under pressure
- **WHEN** early game phase is 2.5, pressure is MEDIUM, expansion_count < 2
- **THEN** `manage_early_game` SHALL skip the Nexus and proceed to phase 3 (Warpgate Research)

#### Scenario: Fast expand skipped when already expanded
- **WHEN** early game phase is 2.5, pressure is NONE, expansion_count >= 2
- **THEN** `manage_early_game` SHALL skip the Nexus and proceed to phase 3
