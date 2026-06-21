## Context

The bot currently uses a single-unit production model: it picks the top-1 recommended counter and produces only that unit from all available structures. This creates armies of 16 Immortals vs diverse enemy compositions. Upgrades are gated behind `minerals < 300` which blocks research when gas is abundant. The bot never builds Stargate or Twilight Council because the counter system doesn't drive tech tree decisions. Attack decisions require impossible `army_value_ratio` thresholds against diversified enemies.

## Goals / Non-Goals

**Goals:**
- Produce a proportional mix of units from the top-3 counters
- Research upgrades when combined resources (minerals+gas) are sufficient
- Build Stargate/Twilight when counters require their units
- Attack when hoarding army for 60+ seconds with acceptable ratio

**Non-Goals:**
- Per-unit micro management
- Build order optimization beyond tech structure placement
- Changing the counter scoring algorithm itself
- New unit types or abilities

## Decisions

### D1: Top-3 proportional production

`manage_army()` reads the top-3 counters. Gateway-bound counters (Zealot, Stalker, Adept, Sentry, HT/Archon, DT) are produced from Gateway/Warpgate proportionally to their scores. If Immortal is top-1, Robo produces Immortals. If Phoenix/VoidRay is top-2/3, Stargate produces them. Each structure type produces its best-matching counter.

**Alternative**: Fixed 2:1:1 ratio. Rejected because the optimal mix depends on enemy composition (e.g., vs mass Marine, Colossus should dominate).

### D2: Combined resource upgrade gate

Replace `minerals < FORGE_MINERAL_THRESHOLD` with `minerals + vespene < 500`. This allows upgrades when gas is abundant even if minerals fluctuate. Twilight and Forge upgrades both benefit. `FORGE_MINERAL_THRESHOLD` constant becomes `UPGRADE_RESOURCE_THRESHOLD = 500`.

**Alternative**: Separate mineral and gas thresholds. Rejected as unnecessarily complex for the current upgrade set.

### D3: Counter-driven tech tree

In `manage_tech()`, after the Gateway emergency check, the bot examines the top-3 counters. If any requires Stargate or Twilight and the structure doesn't exist, it builds the structure. Priority: Stargate over Twilight (air units are more critical as counters). One tech structure per step to avoid over-investment.

**Alternative**: Dedicated tech switch system. Rejected as premature optimization — the counter-driven approach is simpler and covers the use case.

### D4: 60-second hoard attack trigger

In `evaluate_decision()`, add condition: if `time_in_state >= 60` (in DEFEND for 60s), `army_count >= 8`, and `army_value_ratio > 0.8`, transition to ATTACK. This prevents the bot from accumulating army indefinitely without using it. The 0.8 threshold is lower than the phase-based ratio (1.2-1.5) because staying passive too long is worse than a slightly unfavorable fight.

**Alternative**: Supply-based trigger at 70% supply. Rejected because the bot could reach 70% supply with workers alone, and the timeout-based approach directly addresses the "hoarding" pathology.

## Risks / Trade-offs

- **[Risk] Top-3 mixing could spread production too thin** → Mitigation: The proportional scoring ensures the best counter still gets the most production. The secondary counters get proportionally less but still contribute diversity.
- **[Risk] Tech structure construction could delay Gateway production during early pressure** → Mitigation: Tech structures are only built when counters demand them AND no such structure exists. During early game, manage_early_game() handles the build order before manage_tech takes over.
- **[Risk] 60s timeout could trigger bad attacks** → Mitigation: The `army_value_ratio > 0.8` guard prevents attacks when significantly outmatched. The timeout is 60s (a full minute of hoarding) which is conservative.
