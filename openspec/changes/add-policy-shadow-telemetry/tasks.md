## 1. Policy Configuration

- [ ] 1.1 Add policy mode fields to `MyBot` initialization with default `heuristic` behavior.
- [ ] 1.2 Expose policy mode, experiment id, model name, and model version through the run script CLI/config path.
- [ ] 1.3 Add validation so unsupported policy modes fail clearly before starting a match.

## 2. Decision Telemetry

- [ ] 2.1 Initialize `reports/{match_id}/decisions.jsonl` on the first game step.
- [ ] 2.2 Convert heuristic `Action` objects into JSON-serializable decision payloads.
- [ ] 2.3 Record policy mode, selected policy, decision state, heuristic profile, heuristic action, action score, and bias vector after heuristic action evaluation.
- [ ] 2.4 In `ml_shadow`, preserve heuristic execution while allowing an optional shadow prediction payload to be recorded when present.
- [ ] 2.5 Ensure decision logging does not duplicate the full feature snapshot and does not break if no action or bias calculator exists yet.

## 3. Report Metadata

- [ ] 3.1 Build a match-level policy metadata object with mode, selected policy, heuristic profile, model name, model version, experiment id, and code version/defaults.
- [ ] 3.2 Pass policy metadata through `bot_info` into report generation.
- [ ] 3.3 Include a top-level `policy` object in `report.json` with stable default values for missing metadata.
- [ ] 3.4 Display policy metadata in generated Markdown and HTML reports.
- [ ] 3.5 Include policy fields in generated report index entries while remaining compatible with older reports.

## 4. Tests

- [ ] 4.1 Add tests that default bot/run configuration uses `heuristic` mode.
- [ ] 4.2 Add tests for valid and invalid policy mode CLI/config handling.
- [ ] 4.3 Add tests for decision record serialization shape, including no-action and missing-bias cases.
- [ ] 4.4 Add report tests verifying policy metadata appears in JSON, Markdown, HTML, and index outputs.
- [ ] 4.5 Add regression tests confirming `ml_shadow` selects the heuristic action and does not alter gameplay control.

## 5. Verification

- [ ] 5.1 Run `uv run pytest` and fix any failures.
- [ ] 5.2 Run or inspect report generation with a minimal sample to confirm policy fields render correctly.
- [ ] 5.3 Confirm generated `decisions.jsonl` records are valid JSONL and contain no non-serializable objects.
