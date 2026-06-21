## Why

The bot wins 3/3 on Medium difficulty but only 1/3 on Hard, losing to Zerg and Protoss. The root cause is that `manage_expansion()`, `manage_tech()`, and `manage_army()` use fixed thresholds that don't respond to enemy pressure. On Hard, early aggression kills workers (preventing saturation-based expansion), constant spending prevents mineral banking triggers, and the bot stays on 1 base with minimal production until it dies. A pressure-aware system that dynamically adjusts expansion timing, gateway count, and production priorities based on enemy threat level is needed to reach 2/3+ win rate on Hard.

## What Changes

- **New module `src/bot/pressure.py`**: `PressureLevel` enum (NONE/LOW/MED/HIGH) and `assess_pressure()` function using army_value_ratio, enemy_push events, enemy proximity to bases, and visible enemy unit count, with hysteresis to prevent oscillation.
- **`manage_expansion()`**: Uses pressure-adaptive saturation thresholds (0.65→0.85) and mineral banking thresholds (350→500). At HIGH pressure, expansion is suppressed entirely.
- **`manage_early_game()`**: Adds fast-expand phase (Nexus after CyberCore) when pressure ≤ LOW and expansion_count < 2.
- **`manage_tech()`**: Gateway production target gains pressure-based bonus (+0 to +3 gateways) and increased float threshold when under pressure.
- **`manage_army()`**: At HIGH pressure, prioritzes production from all structures (Gateway + Robo + Stargate) simultaneously instead of sequentially.
- **Tests**: New `tests/test_pressure.py` with 10+ unit tests. Updated tests for `manage_expansion`, `manage_tech`, `manage_early_game`. Verification: 3 simulations per race on Hard (9 total).

## Capabilities

### New Capabilities
- `adaptive-pressure-scaling`: Pressure assessment system that dynamically adjusts expansion, production, and defense thresholds based on enemy threat signals.

### Modified Capabilities
- `bot-gameplay`: Expansion and army production thresholds are now pressure-adaptive instead of fixed constants.
- `early-game-build-order`: Early game gains an optional fast-expand phase after CyberCore when pressure is low.

## Impact

- **New file**: `src/bot/pressure.py`
- **Modified**: `src/bot/core.py` — `on_step()` (add pressure assessment), `manage_expansion()`, `manage_early_game()`, `manage_tech()`, `manage_army()`
- **New tests**: `tests/test_pressure.py`
- **Modified tests**: `tests/test_early_game.py`, `tests/test_decision.py`
- **No new dependencies**, no API changes, no CLI changes
