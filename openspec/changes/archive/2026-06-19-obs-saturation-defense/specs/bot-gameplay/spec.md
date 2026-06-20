## MODIFIED Requirements

### Requirement: Constant worker production
The system SHALL produce probes continuously, prioritizing training at the nexus with the lowest saturation ratio (current_workers / ideal_workers). A nexus SHALL be skipped for probe training if its saturation ratio is ≥ 0.9. Probes SHALL be trained up to a maximum of 70 total workers.

#### Scenario: Train at least saturated nexus
- **WHEN** the main base has saturation ratio 1.1 and the natural has ratio 0.3, the bot has fewer than 70 probes, and available supply
- **THEN** the bot SHALL queue a probe from the natural nexus, not the main

#### Scenario: Skip saturated bases
- **WHEN** the main base has saturation ratio 0.95 and there are no other nexuses, the bot has fewer than 70 probes, and available supply
- **THEN** the bot SHALL NOT queue a probe (sole base is saturated enough)

#### Scenario: Train when all bases undersaturated
- **WHEN** both main (ratio 0.5) and natural (ratio 0.2) are undersaturated
- **THEN** the bot SHALL queue a probe at the natural (lower ratio)

### Requirement: Natural expansion
The system SHALL expand to new bases when ALL current nexuses have saturation ratio ≥ 0.9 AND the bot can afford a Nexus AND no Nexus is already pending. There SHALL be no hard limit on the number of expansions.

#### Scenario: Expand when all bases saturated
- **WHEN** the bot has 2 nexuses, both with saturation ≥ 0.9, and 400+ minerals
- **THEN** the bot SHALL start building a 3rd Nexus

#### Scenario: Do not expand when base is undersaturated
- **WHEN** the bot has 1 nexus with saturation 0.5
- **THEN** the bot SHALL NOT start a new expansion regardless of mineral count

#### Scenario: Do not expand when cannot afford
- **WHEN** all nexuses are saturated but minerals are below Nexus cost
- **THEN** the bot SHALL NOT start a new expansion

### Requirement: Attack at max supply
The system SHALL send all army units to attack the enemy starting location when 200 supply is reached. When `attack_triggered` is True, attack commands SHALL take priority over defensive repositioning.

#### Scenario: Attack takes priority over defense at max supply
- **WHEN** the bot reaches 200 supply and enemy units are near a base
- **THEN** army units SHALL attack the enemy start location, not defend the base

#### Scenario: Army attacks when max supply reached
- **WHEN** the bot reaches 200 supply
- **THEN** the bot SHALL send all army units to attack the enemy starting location

### Requirement: Bot detects gameplay events during on_step
The system SHALL detect key gameplay events on every `on_step` call by comparing current features against the previous step. Events SHALL include at minimum: `supply_block`, `enemy_push`, `worker_stalled`, `resource_float`, `tech_milestone`, `attack_ready`, `expansion_started`, `base_under_attack`, and `base_oversaturated`.

#### Scenario: Events detected each step
- **WHEN** `on_step` is called
- **THEN** the bot SHALL run event detection and make detected events available to managers

#### Scenario: Base oversaturation event
- **WHEN** a nexus has saturation > 1.0 and another nexus has saturation < 0.9
- **THEN** a `base_oversaturated` event SHALL be emitted

#### Scenario: Base under attack event
- **WHEN** enemy units are within THREAT_RANGE of a nexus and have attack orders
- **THEN** a `base_under_attack` event SHALL be emitted

#### Scenario: No events on first step
- **WHEN** `on_step` is called at iteration 0
- **THEN** no events other than `game_start` SHALL be emitted

### Requirement: Bot generates match reports on game end
The system SHALL generate per-match reports when `on_end` is called, using the persisted `features.jsonl` and `events.jsonl` data. The reports SHALL include JSON, HTML, and Markdown formats. The HTML report SHALL display our army composition and enemy army composition in separate, correctly-aligned tables. The opponent race SHALL be taken from actual game data (`self.enemy_race`) rather than hardcoded.

#### Scenario: Reports generated on game end
- **WHEN** `on_end` is called with a game result
- **THEN** `report.json`, `report.html`, and `report.md` SHALL be written to `reports/{match_id}/`

#### Scenario: HTML report has correct table columns
- **WHEN** an HTML report is generated
- **THEN** the "Our Army" table SHALL have matching header and data column counts, and the "Enemy Army" table SHALL be populated with enemy composition data

#### Scenario: Opponent race from game data
- **WHEN** a report is generated after a match against a Terran opponent
- **THEN** the `opponent_race` field SHALL reflect the actual race (`Terran`, `Protoss`, or `Zerg`) from `self.enemy_race.name`

#### Scenario: Index updated on game end
- **WHEN** a new match report is generated
- **THEN** `reports/index.html` SHALL be regenerated to include the new match

## ADDED Requirements

### Requirement: Bot executes defensive behavior during on_step
The system SHALL execute `manage_defense()` on every `on_step` before `manage_attack()`. Defense SHALL evaluate threats per base, reposition idle army units toward threatened bases, and engage enemy units within range.

#### Scenario: Defense runs before attack
- **WHEN** `on_step` is called
- **THEN** `manage_defense()` SHALL execute before `manage_attack()` in the dispatch order

#### Scenario: Army repositions when threatened
- **WHEN** enemy units are detected near a base and our army is idle elsewhere
- **THEN** idle army units SHALL be ordered to move toward the threatened base

#### Scenario: Army engages when in range
- **WHEN** army units are within 8 range of enemy units near a threatened base
- **THEN** idle army units SHALL attack the closest enemy unit
