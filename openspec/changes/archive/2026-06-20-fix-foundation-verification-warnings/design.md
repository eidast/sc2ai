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
