## 1. Policy Configuration

- [x] 1.1 Add policy mode fields to `MyBot` initialization with default `heuristic` behavior.
- [x] 1.2 Expose policy mode, experiment id, model name, and model version through the run script CLI/config path.
- [x] 1.3 Add validation so unsupported policy modes fail clearly before starting a match.

## 2. Decision Telemetry

- [x] 2.1 Initialize `reports/{match_id}/decisions.jsonl` on the first game step.
- [x] 2.2 Convert utility-engine `Action` objects into JSON-serializable `utility.recommended_action` payloads.
- [x] 2.3 Record policy mode, selected policy, strategic state, heuristic profile, utility recommendation, action score, and `utility.bias_vector` after utility evaluation.
- [x] 2.4 Record `early_game_phase` and `override_source` when deterministic early-game logic or safety fallbacks constrain the utility recommendation.
- [x] 2.5 Record optional `executed_intent` for known manager-level attempts such as early-game Pylon/Gateway/Cybernetics Core/Warp Gate actions.
- [x] 2.6 In `ml_shadow`, preserve heuristic stack execution while allowing an optional shadow prediction payload to be recorded when present.
- [x] 2.7 Ensure decision logging does not duplicate the full feature snapshot and does not break if no action, bias calculator, override, or executed intent exists yet.

## 3. Report Metadata

- [x] 3.1 Build a match-level policy metadata object with mode, selected policy, heuristic profile, model name, model version, experiment id, and code version/defaults.
- [x] 3.2 Pass policy metadata through `bot_info` into report generation.
- [x] 3.3 Include a top-level `policy` object in `report.json` with stable default values for missing metadata.
- [x] 3.4 Display policy metadata in generated Markdown and HTML reports.
- [x] 3.5 Include policy fields in generated report index entries while remaining compatible with older reports.

## 4. Tests

- [x] 4.1 Add tests that default bot/run configuration uses `heuristic` mode.
- [x] 4.2 Add tests for valid and invalid policy mode CLI/config handling.
- [x] 4.3 Add tests for decision record serialization shape, including no-action, missing-bias, no-override, and missing-executed-intent cases.
- [x] 4.4 Add tests that early-game telemetry records `early_game_phase`, `override_source`, and known executed intent without changing build-order behavior.
- [x] 4.5 Add report tests verifying policy metadata appears in JSON, Markdown, HTML, and index outputs.
- [x] 4.6 Add regression tests confirming `ml_shadow` selects the heuristic stack and does not alter gameplay control.

## 5. Verification

- [x] 5.1 Run `uv run pytest` and fix any failures.
- [x] 5.2 Run or inspect report generation with a minimal sample to confirm policy fields render correctly.
- [x] 5.3 Confirm generated `decisions.jsonl` records are valid JSONL and contain no non-serializable objects.
