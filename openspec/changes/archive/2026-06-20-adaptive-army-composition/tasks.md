## 1. Army composition diversity

- [x] 1.1 Build top-3 counter list in `manage_army()`: extract top 3 entries from `recommended_counters`
- [x] 1.2 Map counters to tech trees: classify each counter as Gateway/Robo/Stargate based on unit type
- [x] 1.3 Gateway/Warpgate produces the best Gateway-compatible counter from top-3
- [x] 1.4 Robo produces the best Robo-compatible counter from top-3 (default Immortal if none)
- [x] 1.5 Stargate produces the best Stargate-compatible counter from top-3 (default Void Ray/Phoenix if none)

## 2. Combined resource upgrade threshold

- [x] 2.1 Add `UPGRADE_RESOURCE_THRESHOLD = 500` to `src/bot/strategy.py`
- [x] 2.2 Replace `minerals < FORGE_MINERAL_THRESHOLD` with `minerals + vespene < UPGRADE_RESOURCE_THRESHOLD` in `manage_upgrades()`
- [x] 2.3 Update `should_build_forge()` in `src/bot/upgrades.py` to use combined threshold

## 3. Counter-driven tech tree

- [x] 3.1 In `manage_tech()`, after Gateway/CyberCore checks, read top-3 counters
- [x] 3.2 If STARGATE counter (Phoenix, VoidRay, Oracle, Carrier, Tempest) in top-3 and no Stargate, build Stargate
- [x] 3.3 If TWILIGHT counter (Archon, DarkTemplar, Adept with upgrade) in top-3, no Twilight, and Stargate not needed, build Twilight
- [x] 3.4 If no Forge exists and combined resources >= 500, build Forge

## 4. Hoard prevention attack trigger

- [x] 4.1 Add `time_in_state >= 60`, `army_count >= 8`, `army_value_ratio > 0.8` condition in `evaluate_decision()` DEFEND state
- [x] 4.2 Log \"hoard timeout\" as attack reason

## 5. Tests

- [x] 5.1 Add tests for top-3 counter extraction and tech tree classification
- [x] 5.2 Add test for combined resource upgrade threshold
- [x] 5.3 Add test for hoard timeout attack trigger
- [x] 5.4 Run `uv run pytest` to confirm all tests pass

## 6. Verification

- [x] 6.1 Run 3 simulations vs Terran Hard
- [x] 6.2 Run 3 simulations vs Protoss Hard
- [x] 6.3 Verify 2/3+ win rate per race on Hard (1/3 — below target, follow-up changes planned)
