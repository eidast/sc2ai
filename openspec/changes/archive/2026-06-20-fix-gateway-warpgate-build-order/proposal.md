## Why

The bot suffers from a cascading build-order failure that prevents any army production after Warpgate Research completes — or earlier, if the early game build phases time out. Four independent bugs in `manage_early_game()`, `manage_gas()`, and `manage_tech()` chain together: (1) gas is built before Pylon, delaying the entire opening; (2) `manage_early_game()` hard-stops at t=90 regardless of completion; (3) `manage_tech()` and `manage_gas()` check only `GATEWAY` but never `WARPGATE`, so after research they see "zero Gateways" permanently; (4) the resulting emergency Gateway build loop cancels every Gateway before construction finishes. In simulations against Zerg and Terran, the bot accumulated 5000–8000 minerals with zero army units and was destroyed. This must be fixed before any ML training or further gameplay iteration.

## What Changes

- **manage_tech()**: Replace `GATEWAY`-only checks with `GATEWAY + WARPGATE` combined checks, so Warpgates satisfy the Gateway prerequisite and stop the emergency build loop.
- **manage_gas()**: Add Pylon prerequisite before building the first Assimilator. Replace `GATEWAY`-only checks with `GATEWAY + WARPGATE` combined checks for the gas expansion gate.
- **manage_early_game()**: Remove the unconditional `t >= 90` return; let the phase machine run until all phases complete regardless of game time. Keep per-phase 15s timeouts.
- **manage_army()**: Use combined `GATEWAY + WARPGATE` idle count for the Gateway training loop so production works even when only Warpgates exist.

## Capabilities

### New Capabilities
<!-- None — all changes are bugfixes to existing capabilities -->

### Modified Capabilities
- `early-game-build-order`: Gateway emergency fallback and prerequisite checks must account for Warpgates as equivalent to Gateways.
- `gas-economy`: The "no second assimilator before Gateway" gate must check combined GATEWAY + WARPGATE. Gas construction must also wait for a Pylon.

## Impact

- **Affected code**: `src/bot/core.py` — `manage_early_game()`, `manage_gas()`, `manage_tech()`, `manage_army()`
- **No API changes**, no new dependencies
- **No breaking changes** — all existing behavior is preserved where it was working (e.g., vs Protoss where the enemy was weak enough that the bot won before the bugs manifested)
- **Tests**: Existing test suite should continue to pass; tests mock python-sc2 imports and don't execute the live SC2 game loop
