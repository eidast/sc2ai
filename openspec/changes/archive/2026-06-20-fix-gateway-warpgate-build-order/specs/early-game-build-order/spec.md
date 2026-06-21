## MODIFIED Requirements

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

### Requirement: Gateway emergency fallback in manage_tech
`manage_tech` SHALL check if any Gateway or Warpgate exists using a combined count of both structures. If the combined count is zero and game_time >= 120s, it SHALL log a warning and build a Gateway immediately via `_build_if_able`, regardless of what the strategy engine recommends. If the combined count is zero but game_time < 120s, the early game phase machine (`manage_early_game`) is still responsible for building the first Gateway, and `manage_tech` SHALL NOT interfere.

#### Scenario: Gateway built as emergency fallback when no Gateways or Warpgates
- **WHEN** game_time >= 120s, no Gateway and no Warpgate exist, and the strategy engine recommends Forge
- **THEN** `manage_tech` SHALL ignore the Forge recommendation and build a Gateway, logging: "NO GATEWAY at t=125.0 — emergency build"

#### Scenario: Emergency fallback skipped when Warpgate exists
- **WHEN** game_time >= 120s, no Gateway exists but at least one Warpgate exists
- **THEN** `manage_tech` SHALL NOT trigger the emergency Gateway build and SHALL proceed to Cybernetics Core and tech structure checks normally

## ADDED Requirements

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
