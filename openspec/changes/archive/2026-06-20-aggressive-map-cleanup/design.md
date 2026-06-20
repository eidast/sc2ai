## Context

`manage_attack()` currently sends idle army units to `self.enemy_start_locations[0]` whenever the decision engine is in `ATTACK`. This is enough for direct attacks but not for endgame cleanup. If enemy structures remain at expansions, gas locations, or other map points, the bot can fail to find them and the match can continue until a timeout or tie.

The existing victory handling should remain conservative: official SC2 `player_result` is authoritative, and the fallback `WON` state should only trigger after no enemy units or structures are visible for a sustained period. This change focuses on making `ATTACK` actively finish the map instead of changing result semantics.

## Goals / Non-Goals

**Goals:**

- Make attacking armies prioritize visible enemy structures.
- Add aggressive cleanup movement through known map locations when no structures are visible.
- Advance cleanup targets as the army reaches each location.
- Keep macro production and existing decision engine behavior intact during cleanup.
- Keep the implementation small and local to attack target selection.

**Non-Goals:**

- No pathfinding rewrite.
- No new scouting subsystem.
- No new CLI flags or bot constructor arguments.
- No changes to surrender thresholds or SC2 result interpretation.

## Decisions

### Decision: cleanup is part of `manage_attack()`

Cleanup only applies while the decision state is `ATTACK`. This keeps behavior aligned with the decision engine and avoids moving the army away during `DEFEND` or `RECOVER`.

Alternative considered: add a new FSM state such as `CLEANUP`. Rejected because the current need is target selection inside attack mode, not a separate strategic phase.

### Decision: visible structures have priority over waypoints

When `self.enemy_structures` is non-empty, idle army units attack the closest visible enemy structure. This directly addresses leftover refineries and expansion buildings and avoids wandering past known targets.

Alternative considered: always sweep waypoints and let units auto-acquire targets. Rejected because it is slower and less deterministic.

### Decision: sweep known starts and expansions when no structure is visible

When no enemy structures are visible, the bot builds cleanup targets from the enemy start location and known expansion locations. The bot keeps an internal `_cleanup_target_index` and advances it when the army is close to the current point.

Alternative considered: use only enemy start locations. Rejected because the observed failure involves structures away from the starting base.

## Risks / Trade-offs

- Aggressive sweep can overextend the army before every enemy combat unit is dead → cleanup only runs in `ATTACK`, where attack commands already take priority over defense.
- Expansion location APIs may differ slightly across maps/python-sc2 versions → implementation should use existing attributes defensively and fall back to `enemy_start_locations`.
- Reissuing attack commands every step can create noise → only idle army units should receive cleanup orders, matching current `manage_attack()` behavior.
