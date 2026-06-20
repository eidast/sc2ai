## 1. Test Coverage

- [x] 1.1 Add unit coverage for visible enemy structure priority over cleanup waypoints
- [x] 1.2 Add unit coverage for selecting a cleanup waypoint when no enemy structures are visible
- [x] 1.3 Add unit coverage for advancing cleanup waypoint after the army reaches the current target

## 2. Cleanup State and Target Selection

- [x] 2.1 Add `_cleanup_target_index` initialization and reset behavior to `MyBot`
- [x] 2.2 Add a helper to build cleanup targets from enemy start and known expansion locations with a safe fallback
- [x] 2.3 Add a helper to select the next cleanup target and advance when the army is near the current target

## 3. Attack Integration

- [x] 3.1 Modify `manage_attack()` to prioritize the closest visible enemy structure
- [x] 3.2 Modify `manage_attack()` to send idle army units to cleanup waypoints when no structures are visible
- [x] 3.3 Preserve existing macro manager ordering and only issue cleanup orders from `manage_attack()` while in `ATTACK`

## 4. Verification

- [x] 4.1 Run targeted tests for cleanup behavior
- [x] 4.2 Run full suite with `uv run pytest`
- [x] 4.3 Validate the OpenSpec change with `openspec validate aggressive-map-cleanup --type change --strict --no-interactive`
