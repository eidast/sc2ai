## Context

The bot's macro is solid after previous changes (pressure system, army composition, upgrades, tech tree). But it loses fights because: army stays in base instead of pressuring, never harasses workers, doesn't use Chrono Boost, and lets low-HP units die needlessly. These are tactical gaps, not strategic ones.

## Goals / Non-Goals

**Goals:**
- Chrono Boost on Nexus when energy >= 50 and probe training
- Produce from ALL idle production structures every step (not just first match)
- Idle army in DEFEND moves toward enemy start location (not base rally)
- Oracle/Zealot harassment on enemy mineral lines
- Pull back units below 30% HP
- Stalker kite vs melee units

**Non-Goals:**
- Complex micro (blink micro, force fields, prism juggling)
- Multi-pronged attacks
- Drop play (Warp Prism)
- Phoenix lifts

## Decisions

### D1: Chrono Boost on Nexus only

Simple check: if Nexus has energy >= 50 and is training a probe, cast Chrono Boost on it. Don't chrono Warpgates or Robos yet (that requires tracking which production structures are training, adding complexity).

### D2: Offensive idle posture in manage_defense

Current: when no base threatened, rally army to defensive rally point.
New: when no base threatened, move idle army toward `self.enemy_start_locations[0]`. If enemy push detected, defense takes priority. This creates "natural creep" — the army drifts toward the enemy without needing an explicit attack order.

### D3: Harassment as simple Oracle + Zealot runbys

Track a harassment state: IDLE → BUILD_ORACLE → HARASS → RETREAT → IDLE.
- BUILD_ORACLE: train 1 Oracle from Stargate if none exists and Stargate is idle
- HARASS: send Oracle to nearest enemy expansion mineral line, cast Pulsar Beam on workers
- RETREAT: when Oracle shields < 20%, move back to base
- Zealot runby: if 5+ idle Zealots, send 3 to attack enemy expansions

### D4: Micro pullback is reactive, not predictive

For each unit in combat (< ENGAGE_RANGE of enemy), check HP ratio. If HP < 30% and shields == 0, move toward nearest Nexus. For Stalkers vs melee units within range, move back (kite) — check if enemy is melee by looking at attack range.

## Risks / Trade-offs

- **[Risk] Offensive idle posture could wander army into enemy defenses** → Mitigation: Only moves idle units. If enemies are detected nearby, defense logic takes over. Maximum push distance is enemy start location, not beyond.
- **[Risk] Oracle harassment could lose the Oracle** → Mitigation: Retreats at < 20% shields, giving a safety margin. Enemies at Hard difficulty rarely have early anti-air at expansions.
- **[Risk] Micro pullback could cause units to run away from winnable fights** → Mitigation: Only triggers below 30% HP with no shields. A unit at that HP is about to die regardless.
