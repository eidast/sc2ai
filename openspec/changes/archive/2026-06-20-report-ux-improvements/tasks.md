## 1. Resource collection tracking

- [x] 1.1 Add `collected_minerals` and `collected_vespene` to `extract_features()` in `src/ml/observation.py` via `bot.state.score`, with safe defaults (0) when score is unavailable
- [x] 1.2 Update `tests/test_observation.py` to verify new fields are present and have correct types

## 2. d3.js vendor dependency

- [x] 2.1 Create `src/ml/vendor/` directory
- [x] 2.2 Download d3.v7.min.js to `src/ml/vendor/d3.v7.min.js`
- [x] 2.3 Add a function `_read_d3_js()` in `src/ml/report.py` that reads the vendor file and returns the JS string

## 3. Event consolidation

- [x] 3.1 Add `_build_event_ranges(events)` to `src/ml/report.py` that collapses consecutive same-type events into `{type, severity, count, first, last, duration}` ranges
- [x] 3.2 Add `_build_timeline_data(event_ranges, duration)` to `src/ml/report.py` that produces the d3-compatible data structure with `ranges[]`, `points[]`, and `duration`
- [x] 3.3 Update `_compute_metrics()` to use consolidated event ranges for the supply_block count instead of iterating raw events
- [x] 3.4 Update `generate_report_json()` to include consolidated event ranges and timeline data in the report

## 4. Metrics dashboard

- [x] 4.1 Add efficiency calculation to `_compute_metrics()`: mineral and vespene spending efficiency from collected totals
- [x] 4.2 Add army metrics to `_compute_metrics()`: max supply, max army size, our army value peak, enemy army value peak, our T3 peak, enemy T3 peak
- [x] 4.3 Render metrics dashboard HTML in `generate_report_html()` as two-column card layout (economy | army) at the top of the content

## 5. HTML report layout restructure

- [x] 5.1 Move header to top (keep existing header, ensure it renders first)
- [x] 5.2 Place metrics dashboard immediately after header
- [x] 5.3 Place consolidated events summary table after dashboard (replacing raw events table)
- [x] 5.4 Place d3 timeline section after events summary
- [x] 5.5 Keep army snapshots, base saturation, and supply sparkline sections after the timeline

## 6. d3 timeline implementation

- [x] 6.1 Add d3 timeline SVG container and inline `<script>` block to `generate_report_html()`, embedding `_read_d3_js()` output
- [x] 6.2 Implement timeline rendering: Y-axis lanes per event type, X-axis time scale, horizontal `<rect>` bars for ranged events
- [x] 6.3 Implement point event markers: `<circle>` or diamond shapes for instant events
- [x] 6.4 Implement color coding: red (#e94560) for high, yellow (#f5c542) for medium, blue (#4a9eff) for info
- [x] 6.5 Implement d3.zoom() with scaleExtent and translateExtent for zoom/pan
- [x] 6.6 Implement hover tooltip with event details (type, time range, count, severity)
- [x] 6.7 Handle edge cases: empty events, single event, very short durations

## 7. Tests

- [x] 7.1 Create `tests/test_report_ux.py` with tests for `_build_event_ranges()` — consecutive same type, interrupted ranges, single events, empty input
- [x] 7.2 Add tests for `_build_timeline_data()` — correct structure, ranges vs points classification, duration field
- [x] 7.3 Add tests for efficiency calculation in `_compute_metrics()` — normal case, zero collected edge case
- [x] 7.4 Add tests for army metrics extraction in `_compute_metrics()` — peak values from feature frames
- [x] 7.5 Verify all existing tests pass with `uv run pytest`

## 8. Verification and cleanup

- [x] 8.1 Run `uv run pytest` to confirm all tests pass (including new ones)
- [x] 8.2 Open a sample `report.html` via `file://` in browser and verify metrics dashboard renders correctly
- [x] 8.3 Verify d3 timeline renders and zoom/pan/tooltips work in browser via `file://`
- [x] 8.4 Verify new fields appear in `features.jsonl` from a sample match
