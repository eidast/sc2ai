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
