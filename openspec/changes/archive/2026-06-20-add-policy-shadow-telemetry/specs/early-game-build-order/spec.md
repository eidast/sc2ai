## ADDED Requirements

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
