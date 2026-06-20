## Why

The bot can win the army fight but fail to close the match because `manage_attack()` only sends idle army units to the enemy start location. Remaining structures such as refineries or isolated expansion buildings can survive off-target, causing long stalls or ties.

## What Changes

- Add aggressive map cleanup behavior while the decision engine is in `ATTACK`.
- Prioritize visible enemy structures over generic attack waypoints.
- Sweep known expansion locations and the enemy start location when no enemy structures are visible.
- Advance cleanup waypoints as the army reaches each point.
- Preserve macro production, surrender behavior, and SC2 `player_result` victory handling.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-gameplay`: `manage_attack()` will actively clean up remaining enemy structures by prioritizing visible structures and sweeping known map locations instead of only attacking the enemy starting location.

## Impact

- **Modified code**: `src/bot/core.py` attack target selection and minimal cleanup state.
- **Tests**: Add focused tests for cleanup target priority and waypoint advancement.
- **No new dependencies**: Uses existing python-sc2 bot state and map location APIs.
- **No CLI/API changes**: Bot constructor and launcher flags remain unchanged.
