## Why

The bot plays matches but we have no visibility into what happened — no per-match reports, no strategy analysis, no feedback loop. The camera jumps abruptly. The launcher has no CLI parameters. We need a pipeline that captures match data, detects key events during gameplay, generates browsable reports, and feeds structured data to an LLM for strategy improvement suggestions. This closes the gap between "the bot plays" and "we learn from how it plays."

## What Changes

- Add runtime event detection (`supply_block`, `enemy_push`, `worker_stalled`, etc.) in `on_step`, making the bot reactive to game state
- Add phase-driven tactical camera that follows units based on `BuildPhase` and detected events
- Generate per-match reports in `reports/{match_id}/`: JSON (LLM-friendly), HTML (browsable, 2-column army comparison), MD (readable)
- Generate `reports/index.html` listing all matches with sortable table
- Add `--realtime` and `--map <name|random>` CLI arguments to `scripts/run.py`
- Add `scripts/analyze.sh` bash pipeline: aggregates match reports, retrieves relevant code via `.codegraph`, calls OpenCode Zen/Go LLM API, produces strategy improvement suggestions
- Add `.env.example` for LLM API configuration (`SC2AI_LLM_*` variables)
- Add `AGENTS.md` at project root with coding agent instructions

## Capabilities

### New Capabilities

- `event-detection`: Runtime detection of gameplay events (supply_block, enemy_push, worker_stalled, resource_float, tech_milestone, attack_ready) during `on_step`. Tactical camera that follows units using phase + event state instead of static priority.
- `match-reporting`: Post-match report generation in JSON (structured, LLM-consumable), HTML (browsable with 2-column army composition timeline), and MD formats. Index page listing all matches.
- `strategy-analysis`: Bash pipeline (`scripts/analyze.sh`) that aggregates match data across multiple matches, retrieves relevant code snippets via `.codegraph`, and calls the OpenCode Zen/Go LLM API to produce strategy improvement suggestions.
- `cli-config`: Enhanced `scripts/run.py` with argparse support for `--realtime` (normal speed), `--map <name|random>` (specific or random map selection).

### Modified Capabilities

- `observation-pipeline`: `extract_features()` adds `enemy_army_composition` to the feature dict to support army comparison in reports.
- `bot-gameplay`: `on_step` now runs event detection and tactical camera before existing managers. `on_end` triggers report generation.
- `cross-platform-launcher`: `scripts/run.py` now accepts CLI arguments while preserving OS auto-detection.

## Impact

- **New files**: `src/ml/events.py`, `src/ml/report.py`, `scripts/analyze.sh`, `.env.example`, `AGENTS.md`
- **Modified files**: `src/bot/core.py` (camera, events, report trigger, `on_end`), `src/bot/strategy.py` (camera modes), `src/ml/observation.py` (new fields), `scripts/run.py` (argparse)
- **New directories**: `reports/` (gitignored), `reports/analysis/`
- **Dependencies**: `jq` (bash script), curl (bash script) — both standard on macOS/WSL
- **Environment**: `.env` with `SC2AI_LLM_*` variables required for `analyze.sh`
- **No breaking changes**: All existing behavior preserved; new features are additive
