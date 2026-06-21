## 1. Chrono Boost production

- [ ] 1.1 In `manage_probes()`, after `nexus.train()`, chrono boost the Nexus if energy >= 50
- [ ] 1.2 Import `AbilityId.EFFECT_CHRONOBOOSTENERGYCOST` and use `UnitOrder.is_chronoboost` equivalent via ability cast
- [ ] 1.3 Produce from ALL idle production structures in `manage_army()` (no break after first production)

## 2. Offensive idle army posture

- [ ] 2.1 In `manage_defense()`, when no bases threatened and decision is DEFEND, move idle army toward `enemy_start_locations[0]`
- [ ] 2.2 Keep defense-priority: if enemy near base, defense overrides offensive push

## 3. Worker harassment (manage_harass)

- [ ] 3.1 Create `manage_harass()` method in `MyBot`
- [ ] 3.2 If Stargate exists, no Oracle exists, Stargate idle: train Oracle
- [ ] 3.3 If Oracle exists: send to nearest enemy expansion, activate Pulsar Beam on workers
- [ ] 3.4 If Oracle shields < 20%: retreat to nearest friendly Nexus
- [ ] 3.5 If 5+ idle Zealots exist: send 3 to attack enemy expansion
- [ ] 3.6 Add `manage_harass` call in `on_step()` between `manage_army()` and `manage_defense()`

## 4. Micro: pullback + kite

- [ ] 4.1 In `manage_defense()`, for units within ENGAGE_RANGE of enemy: if HP < 30% max and shields == 0, move to nearest Nexus
- [ ] 4.2 For Stalkers within ENGAGE_RANGE of melee enemy (attack range < 2): move away from enemy

## 5. Tests

- [ ] 5.1 Add `tests/test_tactical.py` with tests for chrono boost, offensive posture, harassment, micro
- [ ] 5.2 Run `uv run pytest` — all tests pass

## 6. Verification

- [ ] 6.1 Run 3 simulations vs Terran Hard
- [ ] 6.2 Run 3 simulations vs Protoss Hard
- [ ] 6.3 Verify improved win rate on Hard
