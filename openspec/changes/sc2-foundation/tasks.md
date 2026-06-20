## 1. Repository and scaffold

- [x] 1.1 Create GitHub repo `eidast/sc2ai` as public with description
- [x] 1.2 Initialize local git, add `.gitignore` (Python, macOS, maps/, replays/)
- [x] 1.3 Create `LICENSE` (MIT) at repo root
- [x] 1.4 Create project directory structure: `src/bot/`, `src/ml/`, `src/utils/`, `docs/bitacora/`, `scripts/`, `tests/`
- [x] 1.5 Add `__init__.py` files to all Python packages

## 2. Dependencies and environment

- [x] 2.1 Create `pyproject.toml` with `burnysc2` dependency and project metadata
- [x] 2.2 Run `uv sync` to install dependencies and generate lockfile
- [x] 2.3 Verify `burnysc2` imports successfully in a Python shell
- [ ] 2.4 Commit lockfile to repository

## 3. Documentation

- [x] 3.1 Write bilingual `README.md` (ES first, EN second) with project overview, setup guide, and how to run
- [x] 3.2 Write first bitácora entry: `docs/bitacora/2026-06-19.md` — project inception story in Spanish
- [x] 3.3 Write `docs/setup.md` with macOS-specific installation guide and map download instructions

## 4. Bot core — Protoss macro

- [x] 4.1 Create `src/bot/core.py` with `MyBot(BotAI)` class skeleton: `on_start`, `on_step`, `on_end`
- [x] 4.2 Implement constant probe production (train probe when < 70 workers and supply available)
- [x] 4.3 Implement Pylon supply management (build pylon when supply_headroom < 4)
- [x] 4.4 Implement natural expansion (build Nexus at natural when ~20 supply with enough minerals)
- [x] 4.5 Implement tech progression: Gateway → Cybernetics Core → Warp Gate research → additional Gateways
- [x] 4.6 Implement army production from Gateways (Stalkers, Zealots)
- [x] 4.7 Implement attack trigger at 200 supply: send all army to enemy start location
- [x] 4.8 Create `src/bot/strategy.py` with build order constants and state machine helpers

## 5. Observation pipeline

- [x] 5.1 Create `src/ml/observation.py` with `extract_features(game_state)` returning a dict with: minerals, vespene, supply_used, supply_cap, worker_count, army_count, enemy_visible_units, game_time_seconds, expansion_count
- [x] 5.2 Create `src/utils/logger.py` with configurable feature logging (interval in steps, log level)
- [x] 5.3 Create `src/utils/replay.py` with replay saving helper: save to `replays/` with timestamped filename
- [x] 5.4 Create `src/ml/README.md` placeholder explaining future ML integration intent
- [x] 5.5 Wire `extract_features()` and logging into `MyBot.on_step()`

## 6. Scripts and execution

- [x] 6.1 Create `scripts/run.py` — launch script using `run_game()` with MyBot vs `Computer(Difficulty.Medium)`, Protoss vs Terran, on a standard map, with `realtime=False`
- [x] 6.2 Create `scripts/setup_maps.sh` — helper script that documents map download URLs and destination paths

## 7. Maps

- [x] 7.1 Download Ladder 2019 Season 3 map pack to `/Applications/StarCraft II/Maps/`
- [x] 7.2 Verify maps are detected: `python -c "from sc2 import maps; print(maps.get('Acropolis'))"` works

## 8. Verification

- [ ] 8.1 Run `scripts/run.py` and confirm SC2 launches, bot plays Protoss macro, match completes
- [ ] 8.2 Verify replay file is saved to `replays/` after match
- [ ] 8.3 Verify feature logs appear in console output
- [ ] 8.4 Verify bot reaches 200 supply and attacks successfully
- [ ] 8.5 Push all commits to GitHub and confirm repo is accessible
