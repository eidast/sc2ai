## MODIFIED Requirements

### Requirement: Python project uses uv for dependency management
The system SHALL use `uv` as the package manager with a `pyproject.toml` file declaring `burnysc2` as the primary dependency. The project SHALL be configured as an installable package using `hatchling` as the build backend so that `uv sync` installs it in editable mode, making `src` importable without manual `PYTHONPATH` configuration.

#### Scenario: Dependencies install cleanly
- **WHEN** running `uv sync` in the project root
- **THEN** all dependencies SHALL install without errors, `burnysc2` SHALL be importable, and the project itself SHALL be installed in editable mode

### Requirement: Module imports work after editable install
The project SHALL be importable as `src` after `uv sync` completes, without requiring manual `sys.path` manipulation or `PYTHONPATH` environment variables.

#### Scenario: Module imports work
- **WHEN** running `uv run python -c "from src.bot.core import MyBot"`
- **THEN** the import SHALL succeed without errors

#### Scenario: Script launch works after editable install
- **WHEN** running `uv run python scripts/run.py`
- **THEN** the import `from src.bot.core import MyBot` SHALL succeed and the script SHALL proceed to map resolution
