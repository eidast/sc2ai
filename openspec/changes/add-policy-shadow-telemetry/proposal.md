## Why

The bot has a functional heuristic strategy, but there is no safe way to start moving toward ML without risking gameplay regressions. A shadow policy mode lets the heuristic continue controlling the bot while the system records policy decisions, model metadata, and report fields needed for supervised learning and A/B comparison.

## What Changes

- Add explicit policy modes, starting with `heuristic` and `ml_shadow`.
- Keep gameplay behavior unchanged in `heuristic` and `ml_shadow`: the heuristic remains the only policy that executes actions.
- Persist per-step policy decisions to `reports/{match_id}/decisions.jsonl`.
- Record heuristic decision state, chosen macro action, action score, and bias vector when available.
- Allow an optional ML shadow prediction to be recorded when a model/policy implementation is available later.
- Add policy metadata to match reports so wins/losses can be grouped by mode, heuristic profile, model identity, experiment id, and code version.
- Extend generated reports and report index data with policy information suitable for A/B analysis.
- Do not add model training, ML framework dependencies, RL, or ML-controlled gameplay in this change.

## Capabilities

### New Capabilities
- `policy-shadow-telemetry`: Captures policy mode, heuristic decisions, optional shadow predictions, and report metadata for future ML training and A/B evaluation.

### Modified Capabilities
- `observation-pipeline`: Persist an additional decisions JSONL stream alongside features and events for each match.
- `report-metrics-dashboard`: Include policy metadata in match report JSON/HTML/Markdown outputs so outcomes can be attributed to a policy mode/version.

## Impact

- Affected code: `src/bot/core.py`, `src/strategies/*`, `src/ml/report.py`, `scripts/run.py`, and related tests.
- Affected artifacts: `reports/{match_id}/decisions.jsonl`, `reports/{match_id}/report.json`, `report.md`, `report.html`, and generated report index data.
- No breaking changes to existing heuristic gameplay behavior.
- No new heavy ML dependencies are required for this change.
