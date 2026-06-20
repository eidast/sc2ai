# Fix Foundation Verification Warnings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve and document the five verification warnings found after `sc2-foundation` without expanding scope.

**Architecture:** Add a small follow-up OpenSpec change named `fix-foundation-verification-warnings`, then make focused TDD changes in launch-map handling, bot logging configuration, feature logging, README structure, and automated tests. Keep gameplay behavior unchanged.

**Tech Stack:** Python 3.13, pytest, burnysc2/python-sc2, uv, OpenSpec spec-driven artifacts.

---

## File Structure

- Create: `openspec/changes/fix-foundation-verification-warnings/.openspec.yaml` — declares the follow-up change schema.
- Create: `openspec/changes/fix-foundation-verification-warnings/proposal.md` — explains why this follow-up exists.
- Create: `openspec/changes/fix-foundation-verification-warnings/design.md` — records design decisions for the warning fixes.
- Create: `openspec/changes/fix-foundation-verification-warnings/tasks.md` — tracks implementation tasks.
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/bot-gameplay/spec.md` — documents clear map-missing behavior.
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/observation-pipeline/spec.md` — documents configurable logging interval and dictionary logging.
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/project-foundation/spec.md` — documents README order and automated coverage.
- Create: `tests/test_run_script.py` — tests map resolution behavior without launching SC2.
- Create: `tests/test_bot_logging.py` — tests `MyBot` logging interval configuration.
- Create: `tests/test_logger.py` — tests feature dictionary logging.
- Create: `tests/test_observation.py` — tests required feature keys/default-friendly extraction.
- Create: `tests/test_readme.py` — tests Spanish section precedes English section.
- Modify: `scripts/run.py` — add map resolution helper and clear missing-map error.
- Modify: `src/bot/core.py` — accept and use `log_interval` instance configuration.
- Modify: `src/utils/logger.py` — include the feature dictionary in log output.
- Modify: `README.md` — restructure into Spanish first and English second.

### Task 1: Create Follow-Up OpenSpec Artifacts

**Files:**
- Create: `openspec/changes/fix-foundation-verification-warnings/.openspec.yaml`
- Create: `openspec/changes/fix-foundation-verification-warnings/proposal.md`
- Create: `openspec/changes/fix-foundation-verification-warnings/design.md`
- Create: `openspec/changes/fix-foundation-verification-warnings/tasks.md`
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/bot-gameplay/spec.md`
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/observation-pipeline/spec.md`
- Create: `openspec/changes/fix-foundation-verification-warnings/specs/project-foundation/spec.md`

- [ ] **Step 1: Create the change metadata**

Create `openspec/changes/fix-foundation-verification-warnings/.openspec.yaml`:

```yaml
schema: spec-driven
created: 2026-06-20
```

- [ ] **Step 2: Create the proposal**

Create `openspec/changes/fix-foundation-verification-warnings/proposal.md`:

```markdown
## Why

The `sc2-foundation` implementation is complete, but verification found five warnings that should be corrected before archiving: missing-map errors are not project-specific, feature logging interval is not configurable, feature logs do not emit the feature dictionary, README language ordering is not Spanish-first then English-second, and there is no automated scenario coverage.

## What Changes

- Add clear missing-map reporting for the configured SC2 map.
- Make `MyBot` feature logging interval configurable at initialization.
- Include the feature dictionary in feature log output.
- Reorganize README content into Spanish first and English second.
- Add focused pytest coverage for the corrected behaviors.

## Capabilities

### Changed Capabilities

- `bot-gameplay`: clearer launch-time diagnostics when the configured map is unavailable.
- `observation-pipeline`: configurable feature logging interval and dictionary-based feature logging.
- `project-foundation`: stricter README language ordering and automated coverage for foundation scenarios.

## Impact

- **Code**: `scripts/run.py`, `src/bot/core.py`, `src/utils/logger.py`
- **Docs**: `README.md`
- **Tests**: new pytest files under `tests/`
- **Out of scope**: gameplay strategy changes, full SC2 match automation, ML model work
```

- [ ] **Step 3: Create the design artifact**

Create `openspec/changes/fix-foundation-verification-warnings/design.md`:

```markdown
## Context

This follow-up change resolves the five warnings discovered during verification of `sc2-foundation`. It intentionally avoids changing gameplay strategy or introducing ML behavior.

## Decisions

### Decision 1: Keep map handling in the launch script

`scripts/run.py` is the only caller that resolves the configured map. A small `resolve_map()` helper keeps launch diagnostics close to the launch configuration and makes the behavior testable without starting StarCraft II.

### Decision 2: Configure logging interval through `MyBot.__init__`

The bot already owns logging cadence in `on_step()`. Accepting `log_interval: int = 22` preserves the default while allowing callers and tests to use another interval.

### Decision 3: Preserve readable logs while including the feature dictionary

`log_features()` will include the full feature dictionary in the log message. The step number remains explicit so console output stays easy to scan.

### Decision 4: README uses two clear language sections

The README will contain a Spanish section first and an English section second. Content remains equivalent across sections.

### Decision 5: Test only local behavior

Automated tests will not launch SC2. They cover map lookup failure, logging configuration, logging output, feature extraction shape, and README ordering.

## Non-Goals

- No full match execution in tests.
- No change to build order, combat, camera behavior, or replay semantics.
- No broad documentation rewrite beyond README language ordering.
```

- [ ] **Step 4: Create the tasks artifact**

Create `openspec/changes/fix-foundation-verification-warnings/tasks.md`:

```markdown
## 1. OpenSpec documentation

- [x] 1.1 Create follow-up change artifacts for the five verification warnings

## 2. Launch map handling

- [ ] 2.1 Add failing tests for configured map resolution and clear missing-map errors
- [ ] 2.2 Implement map resolution helper in `scripts/run.py`

## 3. Observation logging

- [ ] 3.1 Add failing tests for configurable `MyBot(log_interval=44)` behavior
- [ ] 3.2 Add failing tests for feature dictionary log output
- [ ] 3.3 Implement configurable log interval and dictionary logging

## 4. Project documentation

- [ ] 4.1 Add failing test for Spanish-first then English-second README ordering
- [ ] 4.2 Restructure `README.md` into clear Spanish and English sections

## 5. Feature extraction coverage

- [ ] 5.1 Add test for required `extract_features()` keys and empty/default-friendly values

## 6. Verification

- [ ] 6.1 Run `uv run pytest`
- [ ] 6.2 Run `openspec status --change "fix-foundation-verification-warnings" --json`
```

- [ ] **Step 5: Create bot-gameplay delta spec**

Create `openspec/changes/fix-foundation-verification-warnings/specs/bot-gameplay/spec.md`:

```markdown
## MODIFIED Requirements

### Requirement: Bot launches and connects to StarCraft II
The system SHALL launch a StarCraft II game instance and connect a Protoss bot to it using the python-sc2 `run_game` interface. The launch script SHALL resolve the configured map before starting the game and report a clear project-specific error if the map is unavailable.

#### Scenario: Game starts successfully
- **WHEN** the user runs the bot launch script and the configured map is installed
- **THEN** StarCraft II opens, loads the specified map, and the bot begins receiving `on_step` calls

#### Scenario: Missing map is reported clearly
- **WHEN** the configured map is not found in the Maps directory
- **THEN** the system SHALL report an error message containing the missing map name, the expected Maps directory, and the `scripts/setup_maps.sh` helper path
```

- [ ] **Step 6: Create observation-pipeline delta spec**

Create `openspec/changes/fix-foundation-verification-warnings/specs/observation-pipeline/spec.md`:

```markdown
## MODIFIED Requirements

### Requirement: Features are logged every N steps
The system SHALL log extracted features at a configurable interval (default every 22 steps, approximately 1 second) using Python's `logging` module. The bot SHALL allow callers to override this interval during initialization.

#### Scenario: Features appear in log output
- **WHEN** the bot runs with logging enabled at INFO level
- **THEN** the extracted feature dictionary SHALL appear in the console/log output at the configured interval

#### Scenario: Logging interval is configurable
- **WHEN** the bot is initialized with `log_interval=44`
- **THEN** features SHALL be logged every 44 steps instead of the default 22
```

- [ ] **Step 7: Create project-foundation delta spec**

Create `openspec/changes/fix-foundation-verification-warnings/specs/project-foundation/spec.md`:

```markdown
## MODIFIED Requirements

### Requirement: Bilingual README
The project SHALL include a README.md with content in both Spanish and English. Spanish content SHALL appear first, followed by English content, and each language SHALL have a clear section header.

#### Scenario: README is accessible and bilingual
- **WHEN** viewing the repository on GitHub
- **THEN** the README SHALL display Spanish content followed by English content, with clear language section headers

## ADDED Requirements

### Requirement: Foundation behavior has automated coverage
The project SHALL include pytest coverage for foundation behavior that can be validated without launching a full StarCraft II match.

#### Scenario: Local verification runs successfully
- **WHEN** running `uv run pytest`
- **THEN** tests for map error handling, logging interval configuration, feature dictionary logging, feature extraction shape, and README language ordering SHALL pass
```

- [ ] **Step 8: Validate OpenSpec change status**

Run: `openspec status --change "fix-foundation-verification-warnings" --json`

Expected: JSON reports schema `spec-driven`, artifacts present, and incomplete tasks remain.

### Task 2: Add Tests for Launch Map Handling

**Files:**
- Create: `tests/test_run_script.py`
- Modify later: `scripts/run.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_run_script.py`:

```python
import pytest

from scripts.run import MAP_NAME, resolve_map


class FakeMaps:
    def __init__(self, result):
        self.result = result
        self.requested = None

    def get(self, name):
        self.requested = name
        return self.result


def test_resolve_map_returns_configured_map():
    expected_map = object()
    fake_maps = FakeMaps(expected_map)

    resolved = resolve_map(fake_maps)

    assert resolved is expected_map
    assert fake_maps.requested == MAP_NAME


def test_resolve_map_reports_missing_map_clearly():
    fake_maps = FakeMaps(None)


    with pytest.raises(RuntimeError) as exc_info:
        resolve_map(fake_maps)

    message = str(exc_info.value)
    assert MAP_NAME in message
    assert "/Applications/StarCraft II/Maps/" in message
    assert "scripts/setup_maps.sh" in message
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_run_script.py -v`

Expected: FAIL during import because `scripts.run` does not define `MAP_NAME` or `resolve_map`.

- [ ] **Step 3: Implement minimal launch helper**

Modify `scripts/run.py` to:

```python
from sc2 import maps
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer

from src.bot.core import MyBot


MAP_NAME = "AcropolisLE"
MAPS_DIR = "/Applications/StarCraft II/Maps/"


def resolve_map(map_registry=maps):
    selected_map = map_registry.get(MAP_NAME)
    if selected_map is None:
        raise RuntimeError(
            f"Missing StarCraft II map: {MAP_NAME}. "
            f"Install ladder maps under {MAPS_DIR} or run scripts/setup_maps.sh."
        )
    return selected_map


def main():
    run_game(
        resolve_map(),
        [
            Bot(Race.Protoss, MyBot(), fullscreen=True),
            Computer(Race.Terran, Difficulty.Medium),
        ],
        realtime=False,
        disable_fog=True,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_run_script.py -v`

Expected: 2 passed.

- [ ] **Step 5: Mark OpenSpec tasks complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, change:

```markdown
- [ ] 2.1 Add failing tests for configured map resolution and clear missing-map errors
- [ ] 2.2 Implement map resolution helper in `scripts/run.py`
```

to:

```markdown
- [x] 2.1 Add failing tests for configured map resolution and clear missing-map errors
- [x] 2.2 Implement map resolution helper in `scripts/run.py`
```

### Task 3: Add Tests and Implementation for Configurable Logging

**Files:**
- Create: `tests/test_bot_logging.py`
- Create: `tests/test_logger.py`
- Modify: `src/bot/core.py`
- Modify: `src/utils/logger.py`

- [ ] **Step 1: Write failing bot interval tests**

Create `tests/test_bot_logging.py`:

```python
from src.bot.core import MyBot


def test_bot_uses_default_log_interval():
    bot = MyBot()

    assert bot.log_interval == 22


def test_bot_accepts_custom_log_interval():
    bot = MyBot(log_interval=44)

    assert bot.log_interval == 44
```

- [ ] **Step 2: Write failing logger test**

Create `tests/test_logger.py`:

```python
import logging

from src.utils.logger import log_features


def test_log_features_emits_feature_dictionary(caplog):
    features = {
        "minerals": 50,
        "vespene": 0,
        "supply_used": 12,
        "supply_cap": 15,
        "worker_count": 12,
        "army_count": 0,
        "enemy_visible_units": 0,
        "game_time_seconds": 9.5,
        "expansion_count": 1,
    }
    logger = logging.getLogger("test_log_features_emits_feature_dictionary")

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_features(logger, features, 44)

    assert "features={" in caplog.text
    assert "'minerals': 50" in caplog.text
    assert "'game_time_seconds': 9.5" in caplog.text
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_bot_logging.py tests/test_logger.py -v`

Expected: FAIL because `MyBot.__init__` does not accept `log_interval`, `bot.log_interval` does not exist, and logger output does not contain `features={`.

- [ ] **Step 4: Implement configurable interval**

Modify `src/bot/core.py`:

```python
class MyBot(BotAI):
    MAX_WORKERS = 70
    ATTACK_SUPPLY = 200

    def __init__(self, log_interval: int = 22):
        super().__init__()
        self.attack_triggered = False
        self.logger = setup_logger()
        self.log_interval = log_interval
        self._last_log = 0
```

Also change the interval check in `on_step()` to:

```python
        if iteration - self._last_log >= self.log_interval:
            log_features(self.logger, features, iteration)
            self._last_log = iteration
```

- [ ] **Step 5: Implement dictionary logging**

Modify `src/utils/logger.py` `log_features()` to:

```python
def log_features(logger: logging.Logger, features: dict, iteration: int):
    logger.info("step=%d features=%s", iteration, features)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_bot_logging.py tests/test_logger.py -v`

Expected: 3 passed.

- [ ] **Step 7: Mark OpenSpec tasks complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, mark tasks `3.1`, `3.2`, and `3.3` complete.

### Task 4: Add Feature Extraction Coverage

**Files:**
- Create: `tests/test_observation.py`

- [ ] **Step 1: Write the feature extraction test**

Create `tests/test_observation.py`:

```python
from types import SimpleNamespace

from src.ml.observation import extract_features


class EmptyUnits:
    amount = 0

    def __bool__(self):
        return False


class UnitCollection:
    def __init__(self, amount):
        self.amount = amount


    def exclude_type(self, _unit_types):
        return self


def test_extract_features_returns_required_keys_with_empty_defaults():
    bot = SimpleNamespace(
        minerals=50,
        vespene=0,
        supply_used=12,
        supply_cap=15,
        supply_left=3,
        workers=EmptyUnits(),
        units=UnitCollection(0),
        enemy_units=[],
        time=1.5,
        townhalls=UnitCollection(1),
        state=SimpleNamespace(game_loop=33),
    )

    features = extract_features(bot)

    assert features["minerals"] == 50
    assert features["vespene"] == 0
    assert features["supply_used"] == 12
    assert features["supply_cap"] == 15
    assert features["worker_count"] == 0
    assert features["army_count"] == 0
    assert features["enemy_visible_units"] == 0
    assert features["game_time_seconds"] == 1.5
    assert features["expansion_count"] == 1
```

- [ ] **Step 2: Run test to verify it passes against existing behavior**

Run: `uv run pytest tests/test_observation.py -v`

Expected: 1 passed. This task adds missing coverage for existing behavior; no production code change is required if it passes.

- [ ] **Step 3: Mark OpenSpec task complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, mark task `5.1` complete.

### Task 5: Add README Ordering Test and Restructure README

**Files:**
- Create: `tests/test_readme.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing README test**

Create `tests/test_readme.py`:

```python
from pathlib import Path


def test_readme_is_spanish_first_then_english():
    readme = Path("README.md").read_text(encoding="utf-8")

    spanish_index = readme.index("## Español")
    english_index = readme.index("## English")

    assert spanish_index < english_index
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_readme.py -v`

Expected: FAIL because README does not contain `## Español` and `## English` section headers.

- [ ] **Step 3: Replace README with Spanish-first then English-second content**

Modify `README.md` to:

```markdown
# sc2ai

> De script a mente, paso a paso.

## Español

**sc2ai** es un proyecto recreativo y académico para construir un bot de StarCraft II que juega partidas completas. Empezamos con lógica programada y la arquitectura está diseñada para evolucionar hacia machine learning.

El bot juega **Protoss** con un estilo macro: expandir, producir sondas y ejército, y atacar cuando alcanza 200 de suministro.

### Requisitos

- **StarCraft II** instalado en macOS: `/Applications/StarCraft II/`
- **Python 3.9+** probado con 3.13
- **uv** para gestión de dependencias
- **Mapas** de ladder descargados en `/Applications/StarCraft II/Maps/`

### Instalación

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

### Mapas

Descarga los map packs oficiales de Blizzard o de [AI Arena](https://aiarena.net/wiki/maps/) y extráelos en:

```text
/Applications/StarCraft II/Maps/
```

También puedes usar el helper:

```bash
./scripts/setup_maps.sh
```

### Ejecutar

```bash
uv run python scripts/run.py
```

El bot juega Protoss contra la IA integrada de Blizzard (Terran, dificultad Media) en modo acelerado.

### Estructura

```text
src/
├── bot/          # Lógica del bot (extiende BotAI)
├── ml/           # Extracción de features, futuro ML
└── utils/        # Logging, replays
docs/
├── bitacora/     # Diario del proyecto (ES)
└── setup.md      # Guía de instalación detallada
scripts/
└── run.py        # Script de lanzamiento
```

### Hoja de ruta

1. **Fundación**: bot scripted con macro básico
2. **Observación**: extracción de features y logging
3. **ML**: primer modelo tomando decisiones
4. **RL**: reinforcement learning con replays propios

### Licencia

MIT. Ver [LICENSE](LICENSE).

---

## English

> From script to mind, step by step.

**sc2ai** is a recreational and academic project to build a StarCraft II bot that plays full matches. We start with scripted logic, and the architecture is designed to evolve into machine learning.

The bot plays **Protoss** with a macro style: expand, produce probes and army, and attack when maxed at 200 supply.

### Requirements

- **StarCraft II** installed on macOS: `/Applications/StarCraft II/`
- **Python 3.9+** tested with 3.13
- **uv** for dependency management
- **Ladder maps** downloaded into `/Applications/StarCraft II/Maps/`

### Setup

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

### Maps

Download Blizzard's official map packs or maps from [AI Arena](https://aiarena.net/wiki/maps/) and extract them into:

```text
/Applications/StarCraft II/Maps/
```

You can also use the helper:

```bash
./scripts/setup_maps.sh
```

### Run

```bash
uv run python scripts/run.py
```

The bot plays Protoss against Blizzard's built-in AI (Terran, Medium difficulty) in accelerated mode.

### Structure

```text
src/
├── bot/          # Bot logic (extends BotAI)
├── ml/           # Feature extraction, future ML
└── utils/        # Logging, replays
docs/
├── bitacora/     # Project journal (ES)
└── setup.md      # Detailed setup guide
scripts/
└── run.py        # Launch script
```

### Roadmap

1. **Foundation**: scripted bot with basic macro
2. **Observation**: feature extraction and logging
3. **ML**: first model making decisions
4. **RL**: reinforcement learning with local replays

### License

MIT. See [LICENSE](LICENSE).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_readme.py -v`

Expected: 1 passed.

- [ ] **Step 5: Mark OpenSpec tasks complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, mark tasks `4.1` and `4.2` complete.

### Task 6: Final Verification and OpenSpec Task Completion

**Files:**
- Modify: `openspec/changes/fix-foundation-verification-warnings/tasks.md`

- [ ] **Step 1: Run full pytest suite**

Run: `uv run pytest`

Expected: all tests pass.

- [ ] **Step 2: Mark verification pytest task complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, mark task `6.1` complete.

- [ ] **Step 3: Run OpenSpec status**

Run: `openspec status --change "fix-foundation-verification-warnings" --json`

Expected: JSON reports schema `spec-driven` and one remaining task before marking `6.2`.

- [ ] **Step 4: Mark OpenSpec status task complete**

In `openspec/changes/fix-foundation-verification-warnings/tasks.md`, mark task `6.2` complete.

- [ ] **Step 5: Confirm final OpenSpec status**

Run: `openspec status --change "fix-foundation-verification-warnings" --json`

Expected: JSON reports `isComplete: true` or all tasks complete.

- [ ] **Step 6: Run final full pytest suite**

Run: `uv run pytest`

Expected: all tests pass.

## Plan Self-Review

- Spec coverage: all five warnings map to explicit tasks and acceptance tests.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: planned names are stable: `MAP_NAME`, `MAPS_DIR`, `resolve_map`, `MyBot(log_interval=44)`, `bot.log_interval`, and `log_features()`.
