## ADDED Requirements

### Requirement: Pressure level is assessed every step
The system SHALL compute a `PressureLevel` (NONE, LOW, MEDIUM, HIGH) on every `on_step` call after feature extraction. The assessment SHALL use: `army_value_ratio`, `enemy_push_active`, `enemy_nearby` count at bases, and `enemy_visible_units` count. Each signal SHALL contribute weighted points, and the total points SHALL map to a pressure level. The system SHALL apply 5-second hysteresis: the level SHALL only change if the new signal-based level has been sustained for at least 5 seconds of game time.

#### Scenario: No pressure when safe
- **WHEN** army_value_ratio > 0.9, no enemy_push, no enemies near bases, enemy_visible_units < 20
- **THEN** pressure level SHALL be NONE

#### Scenario: Low pressure when slightly behind
- **WHEN** army_value_ratio = 0.7, no enemy_push, no enemies near bases
- **THEN** pressure level SHALL be LOW

#### Scenario: Medium pressure with enemy push
- **WHEN** army_value_ratio = 0.4, enemy_push is active, enemies near a base
- **THEN** pressure level SHALL be MEDIUM

#### Scenario: High pressure when overwhelmed
- **WHEN** army_value_ratio < 0.3, enemy_push is active, enemies near a base, enemy_visible_units > 40
- **THEN** pressure level SHALL be HIGH

#### Scenario: Hysteresis prevents rapid oscillation
- **WHEN** the signal-based level changes from LOW to MEDIUM at t=10.0, but changes back to LOW at t=12.0
- **THEN** the pressure level SHALL remain LOW (not enough sustained time at MEDIUM)

#### Scenario: Sustained change propagates
- **WHEN** the signal-based level is LOW from t=10.0 to t=16.0
- **THEN** the pressure level SHALL change to LOW at t=15.0 (5 seconds sustained)

### Requirement: Expansion thresholds adapt to pressure
`manage_expansion()` SHALL use pressure-adaptive thresholds. At NONE: saturation threshold 0.65, mineral bank 350. At LOW: saturation 0.75, bank 400. At MEDIUM: saturation 0.85, bank 500. At HIGH: expansion SHALL be suppressed (no expansion regardless of saturation or minerals).

#### Scenario: Fast expand when safe
- **WHEN** pressure is NONE, saturation ratio is 0.70, and can afford Nexus
- **THEN** the bot SHALL expand

#### Scenario: Delayed expand under low pressure
- **WHEN** pressure is LOW, saturation ratio is 0.70, and can afford Nexus
- **THEN** the bot SHALL NOT expand (saturation 0.70 < 0.75 threshold)

#### Scenario: No expansion under high pressure
- **WHEN** pressure is HIGH, saturation ratio is 1.0, minerals > 500
- **THEN** the bot SHALL NOT expand

#### Scenario: Mineral banking triggers even below saturation
- **WHEN** pressure is NONE, minerals > 350, and can afford Nexus
- **THEN** the bot SHALL expand regardless of saturation ratio

### Requirement: Gateway production target adapts to pressure
`manage_tech()` SHALL add a pressure-based bonus to the gateway target count. The bonus SHALL be +0 for NONE, +1 for LOW, +2 for MEDIUM, +3 for HIGH. The mineral float extra gateway count SHALL be +2 for NONE, +3 for LOW, +4 for MEDIUM, +5 for HIGH.

#### Scenario: Extra gateways under medium pressure
- **WHEN** pressure is MEDIUM, 1 base, minerals < 500
- **THEN** target gateway count SHALL be 6 (baseline 4 + pressure 2)

#### Scenario: Maximum gateways under high pressure with float
- **WHEN** pressure is HIGH, 2 bases, minerals > 500
- **THEN** target gateway count SHALL be min(16, 4 + 3 + 2*3 + 5) = 16 (capped)

### Requirement: Army production prioritizes all structures under high pressure
`manage_army()` SHALL, when pressure is HIGH, attempt production from Gateways, Warpgates, Robotics Facilities, and Stargates regardless of whether a Gateway-only unit was recommended by the strategy engine. Under NONE/LOW/MEDIUM, existing production behavior SHALL be preserved.

#### Scenario: High pressure produces from all structures
- **WHEN** pressure is HIGH, 1 Warpgate idle, 1 Robo idle, 1 Stargate idle
- **THEN** the bot SHALL attempt to produce from Warpgate (Stalker), Robo (Immortal), and Stargate (Void Ray) in the same step

#### Scenario: Normal pressure preserves existing behavior
- **WHEN** pressure is LOW, 1 Gateway idle, 1 Robo idle
- **THEN** the bot SHALL produce from Gateway only (existing behavior)

### Requirement: Pressure level is exposed to policy telemetry
The system SHALL include `pressure_level` in decision records written to `decisions.jsonl`, using the enum name as a string.

#### Scenario: Pressure recorded in telemetry
- **WHEN** a decision record is written and pressure is MEDIUM
- **THEN** the record SHALL include `"pressure_level": "MEDIUM"`
