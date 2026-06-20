## Context

The bot currently plays a fixed Protoss macro script: produce probes → build pylons → build 4 gateways → make stalkers → attack at 200 supply. It has no enemy awareness, no scouting, no upgrade progression, and a concrete gas management bug that causes massive mineral floating. The bot is at the ML phase of the roadmap — these three layers (economy, knowledge, intelligence) are the prerequisites for an AI that can make informed decisions.

All existing code runs without StarCraft II via mock-based tests. The bot uses python-sc2's BotAI interface. Reports are generated as JSON, Markdown, and self-contained HTML.

## Goals / Non-Goals

**Goals:**
- Fix the gas management loop so assimilators are built at all bases regardless of affordability at one geyser
- Assign workers to undersaturated assimilators explicitly
- Scale gateway count dynamically (4→16) based on bases and mineral float
- Build a Forge and start ground upgrades when floating minerals
- Detect gas-starvation as an event (high minerals, low gas)
- Create a static unit properties database for all ladder units across all three races
- Implement a counter calculator based on effective damage (armor type bonuses)
- Map unit names to Liquipedia icon URLs
- Add enemy army analysis (armor types, DPS, threat) to observation features
- Embed unit icons in HTML match reports
- Send a probe to scout enemy starting locations with retreat logic
- Build Twilight Council and research Charge or Blink based on scouted enemy
- Adapt army unit production based on counter recommendations

**Non-Goals:**
- Observer-based or multi-unit scouting (probe scout only in this iteration)
- Air upgrades, Robotics Bay upgrades, Fleet Beacon upgrades (ground upgrades only)
- Dynamic build orders (the build order remains gateways → cyber → expand; only production and upgrades adapt)
- ML model integration (this provides the features and infrastructure, not the model)
- Advanced scouting (enemy tech tree inference, expansion tracking beyond waypoints)
- Stargate or Robotics Facility production (stays on gateway units)
- Changing attack trigger logic (200 supply attack remains)

## Decisions

### 1. Unit data: static Python dicts over JSON/YAML files

**Chosen**: Python dicts in `src/data/units.py`
**Alternatives**: JSON file loaded at runtime

Rationale: Python dicts are importable, type-checkable, and have zero runtime parsing cost. The data is static (SC2 unit stats don't change) so there's no benefit to externalizing it. JSON would require loading code, error handling, and wouldn't benefit from IDE autocomplete. All tests can import directly without mocking file I/O.

### 2. Counter calculation: effective DPS over hardcoded rock-paper-scissors

**Chosen**: Calculate effective damage (base damage + armor-type bonuses) for each of-our-units vs each enemy-unit, rank by score.
**Alternatives**: Hardcoded map of "X counters Y", or machine learning.

Rationale: Effective DPS is mathematically grounded in the actual game data and works for any unit combination without maintenance. Hardcoded counters would be incomplete (what about mixtures?) and require constant updates. ML would be the eventual goal but we need solid features first.

### 3. Icons: Liquipedia CDN over embedded base64 or local assets

**Chosen**: Link to Liquipedia's public CDN URLs in `src/data/icons.py`
**Alternatives**: Download and embed images as base64, or require local SC2 extraction

Rationale: Liquipedia has stable, publicly-accessible icon URLs for every SC2 unit and race. No need to distribute image files or extract from game data. The HTML reports are self-contained except for these external image references. If offline viewing is needed later, a caching layer can be added.

### 4. Gas worker assignment: explicit `worker.gather()` over auto-assignment

**Chosen**: After building an assimilator, on subsequent steps, find idle/nearby workers and explicitly order them to `gather()` from undersaturated assimilators.
**Alternatives**: Rely on SC2's built-in auto-assignment of idle workers to gas.

Rationale: Auto-assignment is non-deterministic and may not prioritize gas over minerals. Explicit assignment gives us control over saturation and ensures gas income starts immediately after the assimilator completes.

### 5. Scout waypoints: simple ordered list over state machine

**Chosen**: A list of `(x, y)` waypoints with a current index. Advance when scout is within 3 units of the current waypoint.
**Alternatives**: Full state machine with explore/retreat/harass/watch states, or grid-based exploration.

Rationale: For a single scout probe with linear exploration (enemy start → enemy start → expansions), a waypoint list is simpler to implement, test, and debug. A state machine would add complexity without benefit at this stage.

### 6. Upgrade priority: Weapons → Armor → Shields cycling

**Chosen**: Cycle through ground upgrades in order: Weapons 1 → Armor 1 → Weapons 2 → Armor 2 → Shields 1 → Weapons 3 → Armor 3 → Shields 2 → Shields 3.
**Alternatives**: All weapons first, all armor first, or context-dependent priority.

Rationale: Standard Protoss macro prioritizes attack upgrades because they improve time-to-kill. Armor follows for survivability. Shields last because they're shared across all units but cost more. This can be made context-dependent later (e.g., armor first vs Terran bio).

### 7. Twilight upgrade: Blink if enemy has air, otherwise Charge

**Chosen**: If enemy army analysis shows `air_count > 3`, research Blink (Stalkers are anti-air). Otherwise research Charge (Zealots are general-purpose).
**Alternatives**: Always Blink, always Charge, or random.

Rationale: Simple heuristic that matches Protoss gameplay. Blink stalkers are essential vs air units (Mutalisks, Banshees, Void Rays). Charge zealots are better vs ground compositions. More sophisticated analysis (enemy armor types, our own composition) can refine this later.

### 8. Adaptive production: counter scores over fixed priority

**Chosen**: Use `compute_counters()` to score each unit type against the current enemy composition. Map the top counter to a gateway-trainable unit (Zealot, Stalker). If Immortal is the top counter, produce Stalkers as a fallback (Immortals come from Robotics, not Gateway).
**Alternatives**: Always Stalker-first, or Zealot-first.

Rationale: Ties production decisions to the actual enemy composition using the same knowledge base that powers reports. Gateway-only units keep the change simple. Robotics production can be added later.

### 9. Economy thresholds: 300 minerals for forge/upgrades

**Chosen**: Start building Forge and researching upgrades when minerals exceed 300 (with vespene ≥ 50 for forge cost).
**Alternatives**: Time-based (e.g., "start upgrades at 5 minutes"), or supply-based.

Rationale: Resource-based thresholds are more adaptive than time-based ones. If the bot is under pressure and spending minerals on units, it won't start upgrades prematurely. If it's floating, upgrades begin naturally.

## Risks / Trade-offs

- **[Risk] Liquipedia CDN URLs may change** → Mitigation: The URL pattern is stable (versioned by game patch). If a URL breaks, it only affects report visuals, not gameplay. The `get_unit_icon_url()` function has a fallback URL.
- **[Risk] Counter calculator may recommend units we can't build yet** → Mitigation: `compute_counters()` returns all Protoss units. The bot's `manage_army()` maps results to buildable gateway units. Tech-gated units are skipped.
- **[Risk] Scout probe may die early, leaving no intel** → Mitigation: Retreat logic at 50% HP. If scout dies, `ScoutState.DEAD` prevents errors. No intel means default strategy (stalker-first production).
- **[Risk] Dynamic gateway count may produce more than supply allows** → Mitigation: Existing supply checks in `manage_army()` prevent production when supply is capped. Gateway count only affects production *capacity*, not spending.
- **[Trade-off] Gateway scaling is linear, not adaptive to enemy pressure** → Acceptable: The bot still defends (manage_defense runs before everything). Under heavy pressure, gateways won't be built because minerals go to units.
- **[Trade-off] Unit database is static and won't reflect balance patches** → Acceptable: SC2 is no longer receiving balance patches. If needed, the dict can be updated manually.

## Migration Plan

No migration needed — all changes are additive. The bot's existing macro behaviors (probes, pylons, expansion, army, defense, attack, camera) are preserved unchanged. New managers are added to `on_step()` without modifying the existing dispatch order beyond inserting new `await` calls.

Rollback: revert the commit. No data format changes, no configuration changes, no database migrations.
