## 1. Add combined Gateway+Warpgate helper

- [x] 1.1 Add `_gateway_count()` method to `MyBot` that returns `structures(GATEWAY).amount + structures(WARPGATE).amount`

## 2. Fix manage_early_game() hard-stop

- [x] 2.1 Remove `if self.time >= 90: return` from `manage_early_game()` — let phases complete naturally with per-phase timeouts

## 3. Fix manage_gas() build order and Gateway check

- [x] 3.1 Add Pylon prerequisite guard at top of `manage_gas()`: if no Pylon exists, return without building gas
- [x] 3.2 Replace `structures(GATEWAY).amount == 0` with `self._gateway_count() == 0` on line 629 (second-assimilator gate)

## 4. Fix manage_tech() Warpgate awareness

- [x] 4.1 Replace `structures(GATEWAY).amount == 0` with `self._gateway_count() == 0` on line 691 (emergency fallback check)
- [x] 4.2 Replace `gateways.amount` with combined Gateway+Warpgate count on line 719 (production capacity target comparison)

## 5. Fix manage_army() Gateway production guard

- [x] 5.1 Add early-exit guard in `manage_army()` Gateway training loop: if combined Gateway+Warpgate ready idle count is zero, skip training to avoid dead code

## 6. Verify with tests and simulation

- [x] 6.1 Run `uv run pytest` to confirm existing tests still pass
- [x] 6.2 Run simulations against Terran and Zerg to confirm the gateway spam loop is eliminated and army production works
