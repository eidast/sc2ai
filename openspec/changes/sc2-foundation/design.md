## Context

This is a greenfield project. No existing code or CI exists — just an OpenSpec scaffolding directory. StarCraft II is installed locally on macOS at `/Applications/StarCraft II/` (version Base96883). Python 3.13.13 is available via pyenv. The `gh` CLI is authenticated as `eidast` with `repo` scope. No maps are downloaded yet.

The python-sc2 ecosystem is mature in 2026. BurnySc2/python-sc2 (621★) is the standard Python API for scripted bots. ares-sc2 (v3.9.6, Jun 2026) and sharpy-sc2 are framework extensions. sc2-pathlib provides Rust-based pathfinding with macOS support. pysc2 (DeepMind, 8.3k★) exists but targets ML research, not scripted bots.

## Goals / Non-Goals

**Goals:**
- Create a public GitHub repo (`eidast/sc2ai`) with full project scaffold
- Implement a Protoss macro bot that plays complete matches against built-in AI
- Produce bilingual documentation (README ES/EN) and a Spanish bitácora journal
- Design the codebase so game state observation is decoupled from decision logic
- Enable replay saving and structured logging from day 1
- Use `uv` for dependency management (matches python-sc2's own tooling)

**Non-Goals:**
- No ML model training or inference (only architecture prep)
- No multiplayer/ladder play
- No graphical UI or visualization dashboard
- No unit micro-optimization or advanced combat tactics
- No Docker or Linux headless setup

## Decisions

### Decision 1: python-sc2 (BurnySc2) as the API layer

**Rationale**: python-sc2 provides direct unit commands, full `GameState` access, and a clean `BotAI` base class. It is actively maintained, has a large community (Discord, AI Arena), and is the standard for scripted bots. pysc2 (DeepMind) abstracts away unit-level control into feature grids, which is better for RL but makes scripted bots unnecessarily complex.

**Alternatives considered**: pysc2 (too ML-specific), raw s2client-proto (too low-level), ares-sc2 (adds complexity we don't need yet, though we may adopt it later for combat behaviors).

### Decision 2: uv for dependency management

**Rationale**: python-sc2 itself uses uv (has `uv.lock` in its repo). It's fast, modern, and simpler than poetry. The project uses `pyproject.toml` as the single source of truth for dependencies.

### Decision 3: Separate observation from decision-making

**Rationale**: To keep the door open for ML, `extract_features()` produces a structured snapshot of the game state independent of the decision logic. Today, features feed logging and debugging. Tomorrow, the same features feed a model.

```
on_step():
    features = extract_features(game_state)
    log(features)
    action = decide(features)      # today: scripted, tomorrow: model.predict()
    execute(action)
    save_replay_if_needed()
```

### Decision 4: Bilingual documentation strategy

**Rationale**: Code, variable names, and docstrings are in English (standard convention). README is bilingual (ES first, EN second). The bitácora journal is in Spanish to capture the personal learning narrative. This makes the repo accessible internationally while preserving the recreational/academic voice.

### Decision 5: Protoss macro bot as MVP

**Rationale**: Protoss has clear macro mechanics (chrono boost, warp gates, pylons for supply) that map well to a simple state machine. A macro-focused bot (expand → produce → max → attack) demonstrates the full game loop without requiring complex micro.

### Decision 6: Flat-ish module structure with clear separation

**Rationale**: A deeply nested structure would be over-engineering for the MVP. The layout separates concerns while staying flat enough to navigate:

```
src/
  bot/          # BotAI subclass, strategy logic
  ml/           # Feature extraction, placeholder for future models
  utils/        # Logging, replay helpers
```

## Risks / Trade-offs

- **[macOS only]** The project is developed and tested only on macOS. python-sc2 and sc2-pathlib support macOS, but community tooling (Docker images, ladder runners) is Linux-centric. → Not a problem for local play; document OS requirements clearly.
- **[SC2 version drift]** Blizzard occasionally updates SC2, which can break python-sc2 compatibility. → Pin python-sc2 version; check BurnySc2 repo for version compatibility notes.
- **[Map availability]** Ladder maps must be downloaded separately and placed in the correct directory. → Document this clearly in setup docs; provide a helper script.
- **[Python 3.13]** python-sc2 requires 3.9+. 3.13 is very new and some dependencies may not have wheels. → Test early; fall back to 3.12 if needed.
- **[Simplicity vs. extensibility]** Keeping the bot simple means rewriting parts later for ML. → The `extract_features()` interface is the contract — as long as it stays stable, the decision layer can evolve independently.

## Open Questions

- Should we use `sc2-pathlib` (Rust pathfinding) from the start, or defer to later?
- What specific Protoss unit composition should the macro bot aim for? (Suggest: Stalker + Zealot + Immortal as a safe default)
- Should the bot save every replay, or only replays where something interesting happens (win, loss, first attack)?
