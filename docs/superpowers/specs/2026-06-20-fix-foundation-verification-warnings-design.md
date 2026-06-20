# Fix Foundation Verification Warnings Design

## Context

The `sc2-foundation` OpenSpec change is complete, but verification found five warnings that should be corrected and documented before archive. This follow-up change is limited to those warnings and does not add new gameplay, ML, UI, or infrastructure scope.

## Scope

This change fixes exactly these warnings:

1. Missing-map handling is not project-specific.
2. Feature logging interval is not configurable at bot initialization.
3. Feature logging does not emit the feature dictionary.
4. README is bilingual but not Spanish-first followed by English-second.
5. Automated scenario coverage is missing.

## Approach

Create a small follow-up OpenSpec change named `fix-foundation-verification-warnings`. The change will add delta specs and tasks for the five warnings, then implement them with test-first changes.

## Components

### Launch Script

`scripts/run.py` will resolve the configured map through a small helper. If the map is unavailable, it will raise a clear error that names `AcropolisLE`, `/Applications/StarCraft II/Maps/`, and `scripts/setup_maps.sh`.

### Bot Logging Configuration

`MyBot` will accept `log_interval: int = 22` in `__init__`. `on_step()` will use the instance value instead of a class-level constant so callers can initialize `MyBot(log_interval=44)`.

### Feature Logging

`log_features()` will log the extracted feature dictionary in the message while preserving readable step context. This satisfies the requirement that feature dictionaries appear in console/log output.

### README Structure

`README.md` will be reorganized into a Spanish section first and an English section second. Content stays equivalent: overview, requirements, setup, maps, run instructions, structure, roadmap, and license.

### Tests

Add focused pytest coverage for behavior that can run without launching StarCraft II:

- Map resolution reports a clear error when the map is missing.
- `MyBot(log_interval=44)` stores and uses the configured interval.
- `log_features()` emits the feature dictionary.
- `extract_features()` returns the required keys with empty/default-friendly values.
- README has Spanish content before English content.

## Data Flow

At launch, `main()` resolves the map before calling `run_game()`. During gameplay, `on_step()` extracts features, logs them when `iteration - _last_log >= log_interval`, then runs existing macro behavior unchanged.

## Error Handling

Map lookup failures become actionable errors with the map name, expected Maps directory, and setup helper. Replay saving behavior is unchanged.

## OpenSpec Updates

The follow-up change will document the corrected behavior in delta specs:

- `bot-gameplay`: clear missing-map error behavior.
- `observation-pipeline`: configurable logging interval and dictionary logging.
- `project-foundation`: README language ordering and automated coverage expectations.

## Non-Goals

- No gameplay strategy changes.
- No full SC2 match automation in tests.
- No ML model work.
- No changes to replay-saving semantics unless needed for tests.

## Acceptance Criteria

- OpenSpec change exists with specs and tasks covering the five warnings.
- All new tests fail before implementation and pass after implementation.
- `uv run pytest` passes.
- Verification warnings are resolved or documented as intentionally out of scope if not mechanically testable.
