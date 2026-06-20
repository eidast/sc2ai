## Context

The bot currently plays through deterministic heuristic logic. `extract_features()` captures game state, `evaluate_decision()` manages the strategic state machine, and `BiasCalculator` plus `PriorityEngine` select macro `Action` values from strategy profiles. Reports already persist `features.jsonl`, `events.jsonl`, replay paths, match metadata, and generated JSON/Markdown/HTML summaries.

The project is ready for an ML transition, but direct ML control would add risk before the data and reporting loop exists. This change introduces the telemetry and metadata layer needed to treat the current heuristic as a baseline teacher while preserving gameplay behavior.

## Goals / Non-Goals

**Goals:**

- Introduce explicit policy modes: `heuristic` and `ml_shadow`.
- Preserve identical action execution in both modes: the heuristic remains the controlling policy.
- Persist a `decisions.jsonl` stream per match for supervised learning and later model comparison.
- Capture enough metadata to attribute match outcomes to policy mode, heuristic profile, experiment id, model id, and code version.
- Surface policy metadata in report JSON, Markdown, HTML, and index data so A/B runs can be analyzed later.
- Keep the design compatible with a future `MLPolicy` without adding a real model dependency now.

**Non-Goals:**

- Training a model.
- Adding scikit-learn, PyTorch, TensorFlow, or other ML dependencies.
- Letting ML control gameplay.
- Implementing reinforcement learning or self-play.
- Replacing the existing heuristic strategy, decision FSM, or priority engine.

## Decisions

### Decision: Use shadow telemetry before ML control

`ml_shadow` SHALL run the same executed actions as `heuristic`, but MAY record an ML prediction when a shadow policy is available. This makes early ML work safe: reports and datasets can be built without causing match regressions.

Alternative considered: add an `ml` mode immediately. Rejected because action validation, confidence handling, fallback logic, and model quality are not ready.

### Decision: Persist policy decisions in `decisions.jsonl`

Policy decision records SHALL be stored separately from `features.jsonl` and `events.jsonl`. Features are large state snapshots, events are interpreted occurrences, and decisions are policy outputs. Keeping them separate makes datasets easier to construct and keeps existing feature/event consumers stable.

Alternative considered: embed decisions into every feature snapshot. Rejected because it couples policy output to the observation contract and bloats features used by tests and reports.

### Decision: Start with the existing `Action` abstraction

The first decision label SHALL use the existing `Action` shape: `type`, `target`, `score`, and optional metadata. This aligns with `PriorityEngine` and avoids inventing a new ML target before the current macro policy boundary is proven.

Alternative considered: train first on `DecisionState`. Rejected as the primary target because it is too coarse and changes less frequently, though it remains useful metadata.

### Decision: Store report-level policy metadata

Each match report SHALL include a `policy` object with mode, selected policy, heuristic profile, optional model metadata, optional experiment id, and optional code version. This supports A/B attribution even before an aggregate experiment runner exists.

Alternative considered: infer policy from CLI args or filenames. Rejected because reports must be self-contained and durable.

### Decision: Make ML prediction optional

In `ml_shadow`, the decision record SHALL always include the heuristic decision. The ML prediction section MAY be omitted or null until a model implementation exists. This allows the telemetry change to land before model loading is designed.

Alternative considered: require a dummy model prediction. Rejected because fake predictions add noise and can be confused with real model output.

## Risks / Trade-offs

- Decision logs may become large during long games -> write compact JSONL records and avoid duplicating the full features dict in `decisions.jsonl`.
- Policy metadata can drift if assembled in multiple places -> centralize the match-level policy metadata before passing it to report generation.
- Shadow mode might be mistaken for ML control -> reports and decision records must distinguish `selected_policy: "heuristic"` from optional `shadow_policy` prediction data.
- Future model inputs may need normalized features -> this change records raw telemetry first; dataset transformation can be a later capability.
- Git/code version may be unavailable in some environments -> version fields can use `unknown` while preserving the metadata shape.

## Migration Plan

1. Add policy mode/configuration defaults so existing runs use `heuristic` without CLI changes.
2. Add decision logging only after the match report directory is initialized.
3. Extend `bot_info` passed to report generation with a `policy` object.
4. Extend report rendering to display policy metadata when present and fall back to `unknown` for old reports.
5. Add tests for default heuristic behavior, shadow telemetry shape, and report JSON shape.

Rollback is simple: disable or ignore `decisions.jsonl` generation and omit the `policy` object from report generation. Existing report consumers should remain compatible because the new fields are additive.

## Open Questions

- Should `experiment_id` come from CLI only, environment variable only, or both?
- Should code version be captured from Git at runtime, or passed in by scripts to avoid shelling out from bot code?
- How often should decision records be written if the chosen action does not change: every step, every log interval, or only on change? The initial implementation should prefer enough data for training while avoiding full feature duplication.
