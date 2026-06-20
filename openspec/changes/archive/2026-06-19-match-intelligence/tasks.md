## 1. Foundation & Configuration

- [x] 1.1 Create `.env.example` with all `SC2AI_LLM_*` variables and documented defaults
- [x] 1.2 Add `reports/` to `.gitignore`
- [x] 1.3 Verify `.env` is in `.gitignore`

## 2. Observation Pipeline Enhancements

- [x] 2.1 Add `enemy_army_composition` field to `extract_features()` in `src/ml/observation.py`
- [x] 2.2 Add per-step feature persistence: write features to `features.jsonl` each `on_step`
- [x] 2.3 Create `reports/{match_id}/` directory on first `on_step` call

## 3. Event Detection

- [x] 3.1 Create `src/ml/events.py` with `detect_events()` function and `Event` dataclass
- [x] 3.2 Implement `supply_block` event detection (supply_left < 3, no pylon pending)
- [x] 3.3 Implement `enemy_push` event detection (enemy_visible delta > 10)
- [x] 3.4 Implement `worker_stalled` event detection (idle nexus, can afford probe)
- [x] 3.5 Implement `resource_float` event detection (minerals > 500, idle gateways)
- [x] 3.6 Implement `tech_milestone` event detection (cyber core done, warp gate done)
- [x] 3.7 Implement `attack_ready` event detection (supply_used >= ATTACK_SUPPLY)
- [x] 3.8 Persist detected events to `events.jsonl` each step
- [x] 3.9 Integrate event detection into `core.py` `on_step` (before managers)

## 4. Tactical Camera

- [x] 4.1 Add `CameraMode` enum to `src/bot/strategy.py`
- [x] 4.2 Implement `select_camera_mode()` using `BuildPhase` + detected events
- [x] 4.3 Rewrite `manage_camera()` to use tactical mode selection
- [x] 4.4 Implement SCOUT mode: follow probe in early game
- [x] 4.5 Implement ENGAGE mode: lock camera on army during attack
- [x] 4.6 Implement DEFEND mode: focus on enemy location when event detected

## 5. Match Reporting

- [x] 5.1 Create `src/ml/report.py` with `generate_report()` function
- [x] 5.2 Implement `report.json` generation (structured LLM-friendly format)
- [x] 5.3 Implement `report.md` generation (human-readable summary)
- [x] 5.4 Implement `report.html` generation (2-column army, sparklines, events list)
- [x] 5.5 Implement `reports/index.html` generation/regeneration (sortable match table)
- [x] 5.6 Call `generate_report()` from `core.py` `on_end`
- [x] 5.7 Include `.env.example` creation task in report module documentation

## 6. CLI Configuration

- [x] 6.1 Add `argparse` to `scripts/run.py` with `--realtime` flag
- [x] 6.2 Add `--map` argument supporting specific map name or `random`
- [x] 6.3 Validate map existence and report available maps on error
- [x] 6.4 Preserve all existing OS auto-detection behavior

## 7. Strategy Analysis Pipeline

- [x] 7.1 Create `scripts/analyze.sh` with CLI argument parsing (`--matches`, `--model`, `--dry-run`)
- [x] 7.2 Load `.env` configuration in the script
- [x] 7.3 Implement `jq`-based aggregation of `reports/*/report.json` files
- [x] 7.4 Compute cross-match aggregate metrics (avg supply_blocks, winrate, avg_unspent, etc.)
- [x] 7.5 Implement `.codegraph` snippet retrieval for problem areas (supply_block → manage_pylons, etc.)
- [x] 7.6 Implement LLM API call via `curl` using `SC2AI_LLM_*` environment variables
- [x] 7.7 Support `--model` override from CLI
- [x] 7.8 Support `--dry-run` to print prompt without API call
- [x] 7.9 Save analysis output to `reports/analysis/analysis_YYYYMMDD_HHMMSS.md`
- [x] 7.10 Handle errors gracefully (missing `jq`, missing `.env`, API failure)

## 8. Testing

- [x] 8.1 Add tests for `detect_events()` — supply_block, enemy_push, worker_stalled
- [x] 8.2 Add tests for `extract_features()` with `enemy_army_composition` field
- [x] 8.3 Add tests for `report.json` output shape (required fields present)
- [x] 8.4 Add tests for CLI arg parsing (`--realtime`, `--map`, `--map random`)
- [x] 8.5 Add tests for `analyze.sh` error cases (missing jq, missing .env, missing reports/)
- [x] 8.6 Add tests for `.env.example` presence and variable coverage

## 9. Verification

- [x] 9.1 Run `uv run pytest` and verify all tests pass
- [x] 9.2 Verify `uv run python scripts/run.py --help` shows all CLI options
- [x] 9.3 Verify `scripts/analyze.sh --dry-run` produces valid output
- [x] 9.4 Verify `reports/` and `.env` are gitignored
