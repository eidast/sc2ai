## ADDED Requirements

### Requirement: Repository is created on GitHub
The system SHALL have a public GitHub repository at `github.com/eidast/sc2ai` with a descriptive description and appropriate topics.

#### Scenario: Repo exists and is public
- **WHEN** visiting `https://github.com/eidast/sc2ai`
- **THEN** the repository SHALL be publicly accessible with a README visible on the landing page

### Requirement: Python project uses uv for dependency management
The system SHALL use `uv` as the package manager with a `pyproject.toml` file declaring `burnysc2` as the primary dependency.

#### Scenario: Dependencies install cleanly
- **WHEN** running `uv sync` in the project root
- **THEN** all dependencies SHALL install without errors and `burnysc2` SHALL be importable

### Requirement: Bilingual README
The project SHALL include a README.md with content in both Spanish (first) and English (second), explaining the project's purpose, setup instructions, and how to run the bot.

#### Scenario: README is accessible and bilingual
- **WHEN** viewing the repository on GitHub
- **THEN** the README SHALL display Spanish content followed by English content, with clear language section headers

### Requirement: Bitácora journal tracks project evolution
The project SHALL include a `docs/bitacora/` directory with dated markdown entries that chronicle development decisions, challenges, and learnings in Spanish.

#### Scenario: First bitácora entry exists
- **WHEN** the project scaffold is created
- **THEN** a dated entry (`docs/bitacora/2026-06-19.md`) SHALL exist documenting the project's inception

### Requirement: .gitignore excludes generated and local files
The project SHALL include a `.gitignore` that excludes: `__pycache__/`, `.venv/`, `maps/`, `replays/`, `.DS_Store`, and Python bytecode.

#### Scenario: Clean repository state
- **WHEN** running `git status` after setup
- **THEN** no generated files, replays, or map files SHALL appear as untracked

### Requirement: Project directory structure follows documented layout
The system SHALL organize source code into `src/bot/`, `src/ml/`, and `src/utils/` with `__init__.py` files, plus `docs/`, `scripts/`, and `tests/` at the root.

#### Scenario: Module imports work
- **WHEN** running `python -c "from src.bot.core import MyBot"`
- **THEN** the import SHALL succeed without errors
