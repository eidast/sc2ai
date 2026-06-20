## Why

This is the foundation of **sc2ai**, a recreational and academic project to build a StarCraft II AI bot that plays complete matches — starting with scripted logic, architected to grow into machine learning. We want a public, documented journey from "hello world" bot to an ML-driven agent, with a bilingual bitácora (journal) capturing the learning process. The python-sc2 ecosystem is mature in 2026 and this is the right moment to build something both fun and educational, shared openly on GitHub.

## What Changes

- Initialize the project repository (`sc2ai`) on GitHub under `eidast` with full scaffolding
- Set up Python dependency management with `uv` and `pyproject.toml` targeting `burnysc2`
- Create a Protoss macro bot that expands, produces probes, builds an army, and attacks when maxed
- Establish bilingual project documentation (ES/EN README, Spanish bitácora)
- Structure the codebase to separate bot logic from game state observation, keeping the door open for ML
- Download and configure ladder maps so the bot can play local matches
- Implement structured game state logging and replay saving

## Capabilities

### New Capabilities

- `bot-gameplay`: A Protoss macro bot that plays full 1v1 matches against the built-in SC2 AI — expanding, producing probes and army, and attacking at max supply. Extends `BotAI` from python-sc2.
- `project-foundation`: Repository structure, bilingual documentation (README ES/EN), dependency management with `uv`, bitácora journal for tracking the project narrative, and `.gitignore` configuration.
- `observation-pipeline`: Extraction of structured game state features from python-sc2's `GameState` into a format suitable for logging, debugging, and future ML consumption. Includes replay saving for data collection.

## Impact

- **Repo**: New public GitHub repo under `eidast/sc2ai`
- **Dependencies**: `burnysc2` (python-sc2), Python 3.13 via pyenv
- **System**: Requires StarCraft II installed at `/Applications/StarCraft II/` with ladder maps
- **Files created**: Full project scaffold (~15 files) — no existing code to modify
