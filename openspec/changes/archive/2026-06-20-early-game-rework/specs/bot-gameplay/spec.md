## MODIFIED Requirements

### Requirement: Bot plays Protoss macro strategy
The system SHALL execute a Protoss macro playstyle: constant probe production, base expansion, tech progression (including Forge, Twilight Council, and ground upgrades), army production (adaptive based on scouted enemy counters), and attack decisions driven by the strategic decision engine instead of a fixed supply threshold. The bot SHALL detect gameplay events during each step and use them to make the strategy reactive. The bot SHALL use a phase-driven tactical camera to follow units based on game context. The bot SHALL send a scout probe to explore enemy starting locations. The bot SHALL fix gas economy by continuing to the next geyser when an assimilator is unaffordable and assigning workers to undersaturated assimilators. The bot SHALL optionally surrender when the decision engine determines victory is impossible. During the first ~90 seconds of game time, the bot SHALL follow a deterministic build order via `manage_early_game()` to guarantee production infrastructure (Pylon → Gateway → Cybernetics Core → Warp Gate) before yielding control to the strategy engine.

#### Scenario: Tech progression
- **WHEN** the bot has a completed Gateway
- **THEN** the bot SHALL build a Cybernetics Core, then research Warp Gate, and add additional Gateways. The bot SHALL NOT build Forge, Twilight Council, Robotics Facility, or Stargate before a Gateway exists.

#### Scenario: Formula-driven tech requires production prerequisites
- **WHEN** the strategy engine evaluates priority formulas for structures
- **THEN** the formulas for Forge, Twilight Council, Robotics Facility, and Stargate SHALL include `has_structure('GATEWAY')` or `has_structure('CYBERNETICSCORE')` as a multiplication factor so their score is zero when the prerequisite structure is missing

#### Scenario: Natural expansion
- **WHEN** ALL current nexuses have saturation ratio ≥ 0.9 AND the bot can afford a Nexus AND no Nexus is already pending
- **THEN** the bot SHALL send a probe to build a Nexus at the next expansion location. There SHALL be no hard limit on the number of expansions.

#### Scenario: Expansion triggered by mineral banking
- **WHEN** minerals exceed 400 AND no Nexus is pending AND no Nexus is already building
- **THEN** the bot SHALL expand, regardless of base saturation ratio

### Requirement: Gateway production capacity scales with economy (moved from gas-economy)
The system SHALL dynamically compute the target gateway count based on the number of bases and current mineral float. The target SHALL be capped at 16 gateways.

#### Scenario: One base baseline
- **WHEN** the bot has 1 base and minerals < 500
- **THEN** the target gateway count SHALL be 4

#### Scenario: Scales with bases
- **WHEN** the bot has 2 bases and minerals < 500
- **THEN** the target gateway count SHALL be 7

#### Scenario: Extra gateways when floating
- **WHEN** the bot has 2 bases and minerals > 500
- **THEN** the target gateway count SHALL increase by 2

#### Scenario: Respects maximum cap
- **WHEN** the computed target exceeds 16
- **THEN** the target SHALL be capped at 16
