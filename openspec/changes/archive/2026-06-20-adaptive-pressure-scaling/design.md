## Context

The bot currently uses hardcoded thresholds in `manage_expansion()`, `manage_tech()`, and `manage_army()` that don't account for enemy pressure. On Hard difficulty, the AI attacks earlier and more aggressively, keeping worker counts low and preventing the saturation-based expansion trigger. The bot stays on 1 base with minimal production and loses.

The pressure system adds a single new module (`src/bot/pressure.py`) that assesses enemy threat level each step. Three existing managers read the pressure level and adjust their thresholds accordingly.

## Goals / Non-Goals

**Goals:**
- Assess pressure level each step from already-available features (no new data collection)
- Make expansion thresholds adapt to pressure (faster expansion when safe, suppressed when threatened)
- Make gateway count adapt to pressure (more gates when under attack)
- Make production prioritize defense units when under high pressure
- Add fast-expand to early game when pressure is low
- Achieve 2/3+ win rate on Hard difficulty

**Non-Goals:**
- Per-race pressure tuning (same logic for all races)
- New scouting or vision system
- Changing unit composition logic beyond priority ordering
- Modifying the decision engine (ATTACK/DEFEND/SURRENDER)

## Decisions

### D1: Pressure module is a standalone function, not a class

`assess_pressure()` is a pure function taking features + previous state and returning the new pressure level. No class, no internal state stored on the module. The bot stores the pressure level as `self._pressure_level` and the timestamp as `self._pressure_level_start`.

**Alternative**: A `PressureTracker` class with internal state. Rejected because the function is stateless enough and testing pure functions is simpler.

### D2: Hysteresis uses a 5-second minimum duration

Pressure level changes only propagate after 5 consecutive seconds at the new signal level. This prevents oscillation when an enemy unit briefly enters/leaves base range or a single unit dies.

**Alternative**: Exponential moving average of pressure signals. Rejected because EMA introduces lag on genuine spikes that need immediate response.

### D3: Five pressure signals, weighted additively

Signals and their weights:
- `army_value_ratio < 0.3` → +3, `< 0.6` → +2, `< 0.9` → +1
- `enemy_push_active` → +2
- `enemy_nearby > 5` at any base → +2
- `enemy_visible_units > 20` → +1, `> 40` → another +1

Mapping: 0-1 → NONE, 2-3 → LOW, 4-6 → MEDIUM, 7+ → HIGH.

**Alternative**: Machine-learned weights. Rejected because training data doesn't exist yet (this is the system that will generate it).

### D4: Pressure level injected into managers via `self._pressure_level`

The `on_step()` method calls `assess_pressure()` after feature extraction and stores the result. Each manager reads `self._pressure_level` directly rather than receiving it as a parameter. This minimizes signature changes.

**Alternative**: Pass `pressure_level` as a parameter to each manager. Rejected because it would require changing 4+ method signatures for a value that doesn't change mid-step.

### D5: Expansion thresholds use a lookup table, not formulas

Rather than `MAX_SATURATION_RATIO * pressure_factor`, we use explicit per-level values. This is more readable and avoids edge cases with multiplication.

| Level | Saturation threshold | Mineral bank threshold |
|-------|---------------------|----------------------|
| NONE  | 0.65                | 350                   |
| LOW   | 0.75                | 400                   |
| MEDIUM| 0.85                | 500                   |
| HIGH  | (no expansion)      | (no expansion)        |

**Alternative**: Formula-based with a single pressure multiplier. Rejected because the relationship isn't linear (HIGH should block expansion entirely, not just slow it).

### D6: Gateway target increases additively with pressure

`GATEWAY_MINERAL_BASELINE` stays at 4. Pressure adds `+0/+1/+2/+3` gateways. `GATEWAY_MINERAL_FLOAT_EXTRA` becomes `+2/+3/+4/+5` depending on pressure. This means on HIGH: 7 gateways on 1 base, up to 16 (capped) on multiple bases.

## Risks / Trade-offs

- **[Risk] Fast expand when pressure is low could be greedy and die to a timing attack** → Mitigation: The pressure system detects the push when it arrives (army_value_ratio drops, enemy_push fires) and switches to HIGH within 5s, suppressing further expansion. The existing defense system handles the actual fight.
- **[Risk] Pressure system doesn't account for invisible/burrowed units** → Mitigation: Detection already covers this — invisible units still increment `enemy_visible_units` when revealed by observers. Burrowed units without detection won't be counted, which is acceptable (if we can't see them, we can't react to them anyway).
- **[Risk] `worker_count` signal was considered but removed to avoid complexity** → The pressure from worker losses is already captured indirectly by `army_value_ratio` (fewer workers = less economy = less army).
