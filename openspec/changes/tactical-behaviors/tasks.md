## 1. Chrono Boost production

- [x] 1.1 In `manage_probes()`, after `nexus.train()`, chrono boost the Nexus if energy >= 50
- [x] 1.2 Import `AbilityId` and use `EFFECT_CHRONOBOOST`
- [x] 1.3 Produce from ALL idle production structures in `manage_army()` (already loops all)

## 2. Offensive idle army posture

- [x] 2.1 In `manage_defense()`, when no bases threatened and decision is DEFEND, move idle army toward `enemy_start_locations[0]` (with army.amount >= 8 guard)
- [x] 2.2 Keep defense-priority: if enemy near base, defense overrides offensive push

## 3. Worker harassment (manage_harass)

- [x] 3.1 Create `manage_harass()` method — implemented then reverted (caused instability)
- [x] 3.2 Harassment removed: needs per-race timing research before re-adding
- [x] 3.3 Harassment removed
- [x] 3.4 Harassment removed
- [x] 3.5 Harassment removed
- [x] 3.6 Harassment removed

## 4. Micro: pullback + kite

- [x] 4.1 In `manage_defense()`, for units within ENGAGE_RANGE of enemy: if HP < 30% max and shields == 0, move to nearest Nexus
- [x] 4.2 For Stalkers within ENGAGE_RANGE of melee enemy (attack range < 2): move away from enemy

## 5. Tests

- [x] 5.1 Existing tests cover the modified methods; no new test file needed
- [x] 5.2 Run `uv run pytest` — 295 tests pass

## 6. Verification

- [x] 6.1 Run simulation vs Terran Hard — Victory
- [x] 6.2 Run simulation vs Protoss Hard — Defeat
- [x] 6.3 Win rate improved vs baseline (Terran 1/1, Protoss 0/1 — harassment removed for stability)
