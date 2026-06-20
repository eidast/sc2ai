## Context

The sc2ai bot currently plays a Protoss macro strategy: produce probes (up to 70), expand to 2 bases, build army, attack at 200 supply. Three weaknesses were identified from reviewing match data and the HTML report:

1. **Observation pipeline is asymmetric** — only enemy composition is tracked. Our own army is just a count. No per-base information (saturation, threats) is captured, making intelligent decisions impossible.
2. **Probe distribution is naive** — `manage_probes()` trains at any idle nexus regardless of local saturation. `manage_expansion()` hard-stops at 2 bases. The main base gets oversaturated while expansions starve.
3. **No defensive behavior** — The army only moves when `attack_triggered` (supply ≥ 200). `_enemy_push_active` exists but only controls camera, not army positioning.

The report HTML also has a rendering bug: 2 table headers for 3 data columns, causing enemy Terran unit composition to visually appear under "Our Army".

**Current code touched:**
- `src/ml/observation.py` (30 lines) — `extract_features()`
- `src/bot/core.py` (283 lines) — `manage_probes()`, `manage_expansion()`, `manage_attack()`, `bot_info` in `on_end()`
- `src/ml/report.py` (333 lines) — `_build_army_snapshots()`, `generate_report_html()`
- `src/ml/events.py` (144 lines) — `detect_events()` and detectors
- `src/bot/strategy.py` (33 lines) — constants

**python-sc2 APIs available:**
- `nexus.assigned_harvesters` — workers assigned to a base
- `self.mineral_field` / `self.vespene_geyser` — neutral resources
- `units.closer_than(distance, position)` — spatial queries
- `self.expansion_locations` — dict of possible expansion positions
- `unit.move(position)`, `unit.attack(target)` — unit commands
- `self.idle_worker_count` — idle worker count

## Goals / Non-Goals

**Goals:**
- Extend `extract_features()` to capture our army composition, per-base saturation, and per-base threats — while keeping the existing flat dict format for JSONL compatibility.
- Redesign `manage_probes()` to train at the least saturated nexus and stop when a base is full.
- Redesign `manage_expansion()` to expand when all current bases near saturation (no hard cap at 2).
- Add `manage_defense()` with a 3-state machine (PEACEFUL / THREATENED / ENGAGED) that repositions army based on threats.
- Fix the report HTML table layout and use actual opponent race from game data instead of hardcoding "Terran".
- Add new event types: `base_under_attack`, `base_oversaturated`.
- All existing tests must continue to pass. New tests for saturation math, threat evaluation, and feature extraction extensions.

**Non-Goals:**
- Probe transfer between bases (complex, high risk of ping-pong). New probes go to the right base; existing ones are not relocated.
- Full behavior tree / state machine for the entire bot. Defense uses its own 3-state machine internally, but the bot's main loop remains sequential method calls.
- Static defense (photon cannons) as a required feature — it will be a stretch goal, not blocking.
- ML model integration — this change improves the observation pipeline that ML will consume, but does not add ML itself.
- Combat micro (kiting, focus fire, ability usage) — defense is about positioning and basic attack-move, not micro.

## Decisions

### D1: Feature format — flat dict vs dataclass

**Decision:** Keep flat dict for JSONL/logging. Optionally add a `GameState` dataclass later that wraps the dict for type-safe internal consumption.

**Rationale:** The flat dict goes directly to `features.jsonl` without serialization overhead. A dataclass wrapper can be added non-breakingly later when ML needs typed data. The contract with the logging pipeline is stable.

**Alternatives considered:**
- Pure dataclass: Would need custom JSON serialization, breaking the simple `json.dumps(features)` flow.
- Nested dict: More structure but harder to query in notebooks/analysis. Keeping it flat with list fields for bases keeps query simplicity.

### D2: Per-base saturation model

**Decision:** Calculate ideal workers as `(minerals_nearby * 2) + (gas_buildings_nearby * 3)`. Use `nexus.assigned_harvesters` for current. Saturation ratio = current / ideal. Train probes at the nexus with lowest ratio below 0.9.

**Rationale:** SC2 optimal is 2 workers per mineral patch and 3 per gas. `assigned_harvesters` is a python-sc2 property that directly gives the current count. Using a ratio-based approach (0.9 threshold) avoids edge cases where 21/22 is considered "undersaturated" and we train one extra probe for a single missing slot.

**Alternatives considered:**
- Per-mineral-patch assignment tracking: Too granular. We don't need to know which probe is on which patch, just how many per base.
- Fixed ideal (e.g., always 22): Wrong for bases with fewer patches or gases.

### D3: Expansion trigger — saturation-based vs supply-based

**Decision:** Expand when ALL current bases have saturation ratio ≥ 0.9 AND we can afford a Nexus. Remove the `townhalls.amount >= 2` hard cap.

**Rationale:** The old logic (expand at supply 20, stop at 2) is a fixed timing that ignores actual economic state. Saturation-based expansion is reactive: if we're mining efficiently everywhere, it's time to grow. This scales naturally to 3+ bases.

**Alternatives considered:**
- Fixed timing (e.g., always expand at 4:00): Predictable but fragile to map differences and harassment.
- Hybrid (supply + saturation): More complex, no clear benefit over pure saturation.

### D4: Defense state machine — inline in manage_defense()

**Decision:** Implement a 3-state machine (PEACEFUL / THREATENED / ENGAGED) entirely within `manage_defense()`. States are determined fresh each step from current features — no persistent state needed.

```
PEACEFUL:   No enemies within THREAT_RANGE (15) of any base
            → Move idle army to defensive rally point (midpoint between bases)

THREATENED: Enemy units within THREAT_RANGE of a base
            → Move idle army toward the most threatened base

ENGAGED:    Army units within ENGAGE_RANGE (8) of enemy near a base
            → Attack nearest enemy unit
```

**Rationale:** Stateless per-step evaluation is simpler and more robust than tracking state transitions. If the enemy retreats between steps, we immediately go back to PEACEFUL. If they push again, we re-engage. No hysteresis bugs.

**Alternatives considered:**
- Persistent state machine with hysteresis: Prevents oscillation but adds complexity. Not needed at current bot skill level.
- Utility-based scoring: Overengineered for the current bot. A simple distance threshold works fine.

### D5: Threat scoring

**Decision:** For each base, threat = sum of `supply_cost` (or default 1) of enemy units within THREAT_RANGE. Sort bases by threat score descending. Defend the highest-threat base first.

**Rationale:** A siege tank (3 supply, high damage) is more threatening than a marine (1 supply). Using supply_cost as a proxy for threat avoids needing a full combat simulator. If `supply_cost` is unavailable, default to 1 (equal threat per unit).

**Alternatives considered:**
- Damage-per-second scoring: Requires game data lookups, more complex, not justified for basic defense.
- Closest-base-only: Ignores the possibility that a more dangerous force is approaching a different base.

### D6: Report HTML fix — opponent race

**Decision:** Use `self.enemy_race` (available from python-sc2) in `body_info` instead of the hardcoded `"Terran"`. The `bot_info` dict in `on_end()` passes this through to `generate_report()`.

**Rationale:** The data is already available via `self.enemy_race.name`. No new API needed.

### D7: Table column fix

**Decision:** Change the army snapshots table from 2 headers (Time, Units) with 3 data cells to 3 headers (Time, Our Army, Enemy Visible) matching the 3 data cells. Split "Our Army Composition" and "Enemy Army Composition" into separate, clearly labeled tables.

**Rationale:** The root cause is a template bug — 3 `<td>` elements in the loop but only 2 `<th>` in the header. Fixing the header and splitting into separate sections makes the report readable.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Saturation calculation may be wrong for non-standard bases (gold minerals, few patches) | Probes trained unnecessarily at wrong base | Use `closer_than` with fixed radius per base; test on multiple maps |
| Defense may pull army away right before a planned attack | Army out of position, attack delayed | Defense runs BEFORE `manage_attack()` in dispatch order; attack takes priority at 200 supply |
| Threat scoring via supply_cost may underweight high-damage units (e.g., widow mines) | Bot doesn't defend appropriately against certain comps | Acceptable for v1; tune with real game data later |
| `assigned_harvesters` may not be available on all python-sc2 versions | Crash in manage_probes | Fallback to counting workers within base radius if property is unavailable |
| Expanding too aggressively (3rd base at unsafe timing) | Vulnerable to early pressure, lose base | Only expand when no threat; manage_defense protects newest base first |
| New features increase features.jsonl size | More disk usage per match | Fields are small (ints, short strings); per-base list is compact |

## Migration Plan

1. All changes are additive to the features dict — existing JSONL readers will ignore new fields.
2. Existing `manage_probes()` and `manage_expansion()` are replaced, not extended — the old behavior is not preserved.
3. Report HTML format changes are visual-only — no migration needed for report consumers.
4. No database schema changes, no API changes, no external dependency changes.

**Rollback:** Revert to previous commit. No data migration needed.

## Open Questions

1. **Photon cannon placement:** Should this be included in v1 or deferred? The design sketch exists but adds complexity (forge requirement, placement logic, resource trade-off). → Defer, but keep as a follow-up task.
2. **Rally point for PEACEFUL state:** Midpoint between main and natural? Between all bases? Closer to enemy? → Start with midpoint between main and natural; iterate based on game results.
3. **THREAT_RANGE constant:** Is 15 the right distance? → Tune through gameplay. Start at 15, which is approximately vision range.
4. **Probe transfer:** Is it worth implementing now? → No (Non-Goal). Training at correct base handles 80% of the problem.
