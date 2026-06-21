## Why

Simulations reveal the bot produces a monoculture army (16 Immortals, zero diversity), banks 4000+ gas without researching upgrades, never builds Stargate or Twilight Council to access counter units, and stays in DEFEND mode until destroyed because the army_value_ratio threshold is unreachable against diverse enemy compositions. These four independent failures make the bot non-competitive on Hard difficulty.

## What Changes

- **Army composition diversity**: `manage_army()` produces a mix of units from the top-3 recommended counters proportional to their scores, instead of only the #1 counter. Gateway units, Robo units, and Stargate units are all produced in the same step based on available production structures.
- **Resource-aware upgrades**: `manage_upgrades()` removes the `minerals < 300` gate that blocks all upgrades when gas is abundant. Upgrades trigger when combined mineral+gas reserves exceed thresholds, enabling the +1/+2/+3 attack/armor progression that is decisive in long games.
- **Attack initiative**: New attack trigger: if the bot has 8+ army units and has been in DEFEND for 60+ seconds with `army_value_ratio > 0.8`, attack. This prevents passive hoarding behavior.
- **Tech tree for counters**: `manage_tech()` checks if the top recommended counter requires Stargate or Twilight Council tech. If so and the required structure doesn't exist, it builds the prerequisite tech structure alongside Gateway production.

## Capabilities

### New Capabilities
- `army-composition-diversity`: System that produces a proportional mix of units from the top-N recommended counters, with per-tech-tree production balancing.

### Modified Capabilities
- `bot-gameplay`: Army production now mixes unit types. Upgrade logic uses combined resource thresholds. Attack decision has new 60s timeout trigger.
- `early-game-build-order`: No changes (this capability is unaffected).

## Impact

- **Modified**: `src/bot/core.py` — `manage_army()` (mix logic), `manage_tech()` (counter-driven tech), `manage_upgrades()` (resource gate)
- **Modified**: `src/bot/strategy.py` — New constants for upgrade thresholds
- **Modified**: `src/bot/decision.py` — New 60s attack timeout trigger
- **No new files**, no new dependencies, no API changes
- **Tests**: Update `test_early_game.py` expansion tests, add army composition tests
