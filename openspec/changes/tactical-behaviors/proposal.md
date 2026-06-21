## Why

Simulations reveal the bot has the right units but doesn't use them effectively: army sits idle in base instead of attacking, never harasses enemy workers, loses units to preventable deaths without micro, and produces probes/units slower than optimal. These four tactical gaps prevent competitive play on Hard difficulty even after fixing macro (pressure, composition, upgrades). Addressing them closes the gap between "builds the right things" and "wins fights."

## What Changes

- **Chrono boost production**: `manage_probes()` uses Chrono Boost on Nexus when energy >= 50 and probe is training. `manage_army()` produces units from ALL idle production structures in the same step (not just first match).
- **Offensive idle army posture**: `manage_defense()` when no bases are threatened and decision is DEFEND, moves idle army toward enemy start location instead of rallying to base. Creates natural forward pressure without needing the decision engine to trigger ATTACK.
- **Worker harassment**: New `manage_harass()` method runs Oracle runbys to enemy mineral lines when a Stargate exists. Targets expansions first, activates Pulsar Beam on workers, retreats when shields < 20. Also sends 2-3 Zealots to attack enemy expansions.
- **Basic micro**: `manage_defense()` pulls back units below 30% HP toward nearest Nexus. Stalkers kite melee units by moving away after each attack when in ENGAGE_RANGE.

## Capabilities

### New Capabilities
- `tactical-behaviors`: Offensive posture, harassment, chrono boost, and micro-pullback capabilities that make the bot fight effectively with its existing army.

### Modified Capabilities
- `bot-gameplay`: `manage_defense()` now has offensive idle posture. Production uses Chrono Boost. New `manage_harass()` runs in `on_step()`.

## Impact

- **Modified**: `src/bot/core.py` — `on_step()` (+harass call), `manage_probes()` (+chrono), `manage_army()` (produce ALL idle structures), `manage_defense()` (offensive posture + micro pullback)
- **New**: `src/bot/core.py` — `manage_harass()` method
- **Tests**: New test file `tests/test_tactical.py`
- **No new files outside core.py**, no new dependencies
