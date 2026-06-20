## MODIFIED Requirements

### Requirement: Game state features are extracted in a structured format
The system SHALL implement an `extract_features()` function that transforms python-sc2's `GameState` into a flat dictionary of numeric and categorical features representing the current game situation.

#### Scenario: Feature extraction returns valid data
- **WHEN** `extract_features()` is called during `on_step`
- **THEN** the returned dictionary SHALL contain at minimum: minerals, vespene, collected_minerals, collected_vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, enemy_army_composition, our_army_composition, our_structures, bases, game_time_seconds, and expansion_count

#### Scenario: Collected resources are available when score exists
- **WHEN** `bot.state.score.collected_minerals` and `bot.state.score.collected_vespene` are accessible
- **THEN** `collected_minerals` and `collected_vespene` SHALL reflect the cumulative totals from game score

#### Scenario: Collected resources default to zero when score unavailable
- **WHEN** `bot.state` or `bot.state.score` is not accessible (testing, early init)
- **THEN** `collected_minerals` and `collected_vespene` SHALL both be 0
