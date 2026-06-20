# AGENTS.md — sc2ai

> De script a mente, paso a paso. / From script to mind, step by step.

## Project overview

- SC2 AI bot playing **Protoss** macro using [burnysc2](https://github.com/BurnySc2/python-sc2) (python-sc2).
- Python **3.9+** (tested on 3.13), managed with **uv**, installed in **editable mode**.
- Public repo under `eidast/sc2ai`. Bilingual: ES (user-facing) / EN (code).
- `.codegraph/` is indexed — prefer `codegraph explore` or `codegraph node` over grep/find.

## Quick reference

```bash
uv sync                          # Install deps + editable install (always run first)
uv run pytest                    # Run all tests (no SC2 instance needed)
uv run python scripts/run.py     # Launch bot vs built-in AI (requires SC2 + maps)
```

## Module map

```
src/bot/core.py        → MyBot(BotAI) — main loop, all manage_*() methods
src/bot/strategy.py    → BuildPhase enum, constants (PROBE_LIMIT, ATTACK_SUPPLY, etc.)
src/ml/observation.py  → extract_features() — GameState → flat dict (contract for ML)
src/ml/events.py       → [PLANNED] Runtime event detection (supply_block, enemy_push, ...)
src/ml/report.py       → [PLANNED] Match report generation (JSON, HTML, MD)
src/utils/logger.py    → setup_logger(), log_features()
src/utils/replay.py    → save_replay() — timestamped .SC2Replay files
scripts/run.py         → CLI launcher with argparse (--realtime, --map, ...)
tests/                 → pytest suite (mock-based, no SC2 required)
docs/bitacora/         → Project journal (ES)
openspec/              → Specs and archived changes
```

## Testing

- `uv run pytest` runs all tests. **No StarCraft II instance is required.**
- Tests mock python-sc2 imports where needed.
- Test files: `test_observation.py`, `test_logger.py`, `test_bot_logging.py`, `test_run_script.py`, `test_readme.py`.

## Code conventions

| Context              | Language |
|----------------------|----------|
| Code, variables, docstrings | English |
| Documentation, bitácora, user-facing text | Spanish |
| Commit messages      | English (preferred) |

- No strict line length. Keep it reasonable.
- Type hints on function signatures where they improve clarity.
- Follow existing patterns in neighboring files.

## Environment

- `.env` at project root (gitignored) stores LLM API configuration.
- `.env.example` is committed as a template with documented defaults.

Key variables:

| Variable                | Purpose                          | Default                              |
|-------------------------|----------------------------------|--------------------------------------|
| `SC2AI_LLM_API_KEY`     | OpenCode Go/Zen API key          | (required)                           |
| `SC2AI_LLM_MODEL`       | Model ID for analysis            | `opencode-go/deepseek-v4-pro`        |
| `SC2AI_LLM_BASE_URL`    | API endpoint                     | `https://opencode.ai/zen/v1`         |
| `SC2AI_LLM_MAX_TOKENS`  | Max output tokens                | `32768`                              |
| `SC2AI_LLM_REASONING_EFFORT` | Reasoning effort (none/minimal/low/medium/high/xhigh) | `max` |
| `SC2AI_LLM_TEMPERATURE` | Sampling temperature             | `0.7`                                |

## OpenSpec workflow

Commands available in this project:

| Command            | Purpose                                      |
|--------------------|----------------------------------------------|
| `/opsx-propose`    | Create new change with proposal + design + tasks |
| `/opsx-apply`      | Implement tasks from a change                |
| `/opsx-verify`     | Verify implementation matches specs          |
| `/opsx-explore`    | Enter explore mode (thinking, no coding)     |
| `/opsx-archive`    | Archive completed change                     |

- Active specs live in `openspec/specs/`.
- Archived changes live in `openspec/changes/archive/`.

## Roadmap

1. ✅ **Foundation** — Scripted Protoss macro bot (expand, produce, attack at 200 supply)
2. ✅ **Observation** — Feature extraction, structured logging, replay saving
3. 🔜 **ML** — First model making decisions (current phase)
4. 🔜 **RL** — Reinforcement learning with own replays

## Important constraints

- Tests **must pass** without StarCraft II installed or running.
- Module imports require `uv sync` first (editable install into `.venv/`).
- Cross-platform: code must work on **macOS** (primary) and **Windows 11**.
- `replays/`, `maps/`, `.env`, `.venv/`, `__pycache__/` are gitignored.
- No ML framework is included yet — architecture is prepared, implementation pending.
