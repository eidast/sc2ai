## ADDED Requirements

### Requirement: Repository is created on GitHub
The system SHALL have a public GitHub repository at `github.com/eidast/sc2ai` with a descriptive description and appropriate topics.

#### Scenario: Repo exists and is public
- **WHEN** visiting `https://github.com/eidast/sc2ai`
- **THEN** the repository SHALL be publicly accessible with a README visible on the landing page

### Requirement: Python project uses uv for dependency management
The system SHALL use `uv` as the package manager with a `pyproject.toml` file declaring `burnysc2` as the primary dependency. The project SHALL be configured as an installable package using `hatchling` as the build backend so that `uv sync` installs it in editable mode, making `src` importable without manual `PYTHONPATH` configuration.

#### Scenario: Dependencies install cleanly
- **WHEN** running `uv sync` in the project root
- **THEN** all dependencies SHALL install without errors, `burnysc2` SHALL be importable, and the project itself SHALL be installed in editable mode

### Requirement: Bilingual README
The project SHALL include a README.md with content in both Spanish and English. Spanish content SHALL appear first, followed by English content, and each language SHALL have a clear section header.

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

### Requirement: Foundation behavior has automated coverage
The project SHALL include pytest coverage for foundation behavior that can be validated without launching a full StarCraft II match.

#### Scenario: Local verification runs successfully
- **WHEN** running `uv run pytest`
- **THEN** tests for map error handling, logging interval configuration, feature dictionary logging, feature extraction shape, and README language ordering SHALL pass

### Requirement: Module imports work after editable install
The project SHALL be importable as `src` after `uv sync` completes, without requiring manual `sys.path` manipulation or `PYTHONPATH` environment variables.

#### Scenario: Module imports work
- **WHEN** running `uv run python -c "from src.bot.core import MyBot"`
- **THEN** the import SHALL succeed without errors

#### Scenario: Script launch works after editable install
- **WHEN** running `uv run python scripts/run.py`
- **THEN** the import `from src.bot.core import MyBot` SHALL succeed and the script SHALL proceed to map resolution
