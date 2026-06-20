## Context

The sc2ai bot currently plays Protoss macro matches but produces no per-match intelligence. After a game, only a `.SC2Replay` file remains — opaque binary data. The `extract_features()` pipeline already captures game state snapshots during `on_step` but only logs them to console. The camera jumps between hardcoded priorities each step. The launch script has no CLI parameters.

We need to close the loop: capture structured match data, detect key events during gameplay, generate browsable reports, and feed data to an LLM for strategy analysis. This design defines the architecture for that pipeline without adding heavy dependencies.

## Goals / Non-Goals

**Goals:**
- Detect gameplay events in `on_step` (supply block, enemy push, worker stall, etc.) without adding significant overhead
- Implement tactical camera that follows units based on game phase and detected events
- Generate per-match reports in three formats: JSON (LLM-consumable), HTML (browsable), MD (readable)
- Provide browsable `reports/index.html` listing all matches
- Add `--realtime` and `--map <name|random>` CLI arguments to the launcher
- Create a bash-based analysis pipeline (`analyze.sh`) that calls the OpenCode Zen/Go LLM API
- Use `.codegraph` to retrieve relevant code snippets for LLM prompts
- Configure LLM API via `.env` with a committed `.env.example` template
- Zero new Python dependencies; `jq` and `curl` are already standard on macOS/WSL

**Non-Goals:**
- No real-time LLM calls during gameplay (analysis is post-match)
- No ML model training or inference (that's a future phase)
- No database or ORM (filesystem is sufficient for match reports)
- No interactive web server (HTML files open directly in browser)
- No JavaScript or external charting libraries (pure HTML+CSS, sparklines unicode)
- No ladder/multiplayer integration

## Decisions

### Decision 1: Event detection via feature comparison

**What**: Compare current features against previous step's features in `on_step` to detect state transitions (supply block starts, enemy appears, etc.).

**Rationale**: We already compute `extract_features()` every step. Comparing consecutive snapshots is O(1) and requires no additional SC2 API calls. Events are simple boolean checks on feature deltas.

**Alternatives considered**: 
- Listening to SC2 game events (more accurate but requires deeper python-sc2 integration) → deferred
- Full replay parsing (accurate but post-hoc, not realtime) → complementary, not replacement

```
detect_events(prev: dict, curr: dict) → list[Event]:
    events = []
    if curr.supply_left < 3 and not pylon_pending:
        events.append(Event("supply_block"))
    if curr.enemy_visible - prev.enemy_visible > 10:
        events.append(Event("enemy_push"))
    if townhalls.idle and workers < MAX_WORKERS:
        events.append(Event("worker_stalled"))
    ...
```

### Decision 2: Tactical camera as a state machine

**What**: Camera behavior driven by `BuildPhase` (from existing `strategy.py`) + detected events, not a static priority list.

**Rationale**: A hardcoded priority list (`army > enemy > base`) is adequate but doesn't adapt to game context. During early game, the player wants to watch the scout probe. During an attack, the camera should lock onto the engagement. The phase+event model provides this without heavy computation.

```
States:
  SCOUT   → follow scout probe (EARLY_GAME)
  EXPAND  → monitor natural expansion (EXPANDING)
  DEFEND  → focus on threat location (event: enemy_near_base)
  ARMY    → follow army (MID_GAME, event: army_moving)
  ENGAGE  → lock on engagement (MAXED, event: attack_triggered)

Transitions triggered by BuildPhase changes + events
```

**Alternatives considered**: 
- Interpolation/lerp for smoothness (adds complexity, deferred for now)
- Following a single "leader" unit (simpler but less informative)

### Decision 3: Three-format report generation

**What**: Each match produces `report.json` (LLM), `report.html` (browser), `report.md` (human). Data persisted as `features.jsonl` and `events.jsonl` during gameplay.

**Rationale**: 
- **JSON**: Structured, machine-readable. An LLM can consume it directly — each snapshot is self-contained, metrics are pre-aggregated, events are typed.
- **HTML**: Browsable without a server. Two-column army comparison, sparklines for supply/resources, event timeline. Pure HTML+CSS, no JS.
- **MD**: Quick reading for spot-checks.

JSON report structure (LLM contract):
```json
{
  "match_id": "...",
  "map": "...", "opponent_race": "...", "duration_seconds": 512, "result": "defeat",
  "timeline": [{"step": 0, "time": 0, "supply_used": 6, "supply_cap": 15, ...}],
  "army_snapshots": [{"time": 300, "our_units": {...}, "enemy_visible": {...}}],
  "metrics": {"avg_unspent_minerals": 450, "supply_blocks": [...], "peak_workers": 52},
  "key_events": [{"time": 315, "type": "supply_block", "severity": "high"}]
}
```

### Decision 4: Bash + curl for LLM integration

**What**: `scripts/analyze.sh` uses `jq` to aggregate JSON reports, `codegraph` CLI to retrieve relevant source snippets, and `curl` to call the OpenCode Zen/Go API.

**Rationale**: Zero new Python dependencies. `jq` and `curl` are pre-installed on macOS and standard on WSL. The script is simple enough that bash is sufficient — it's a pipeline, not a long-running service.

**Alternatives considered**:
- Python script with `requests` or `openai` package → adds dependency, overkill for a pipeline script
- Direct `codegraph` MCP integration in agent → useful for interactive analysis but not batch automation

### Decision 5: .codegraph as code retrieval bridge

**What**: `analyze.sh` maps detected problem patterns to relevant functions via CodeGraph, then includes those snippets in the LLM prompt.

**Rationale**: Sending entire source files wastes tokens. CodeGraph's indexed symbol graph enables precise retrieval: "supply_block" → `manage_pylons() @ core.py:68` with just that function's source, not the whole file.

```
for event_type in supply_block enemy_push worker_stalled; do
    codegraph node "manage_${function_for(event_type)}"
done
```

This reduces prompt size ~10x vs including all of `core.py`.

### Decision 6: .env with dotenv pattern

**What**: `.env` at project root (gitignored) stores `SC2AI_LLM_*` variables. `.env.example` is committed as a documented template. Both bash (`source .env`) and Python (`os.getenv`) can read these variables.

**Rationale**: Standard pattern across the industry. No `python-dotenv` dependency needed — bash sources directly, Python uses `os.getenv`.

## Risks / Trade-offs

- **[Event detection accuracy]** Per-step feature comparison may miss brief events (e.g., a supply block that lasts < 1 step). → Acceptable; these events are heuristics, not authoritative. Future: could sample more frequently.
- **[Report storage growth]** `features.jsonl` per match could grow large over many matches. → Each file is ~50KB for a 10-min match. At 100 matches = 5MB. Acceptable for now; `reports/` is gitignored.
- **[LLM API cost]** Each analysis call costs tokens. The prompt with 5 matches + code snippets is ~4000 tokens input, ~2000 output = ~$0.01-0.03 with DeepSeek V4 Pro. → Acceptable; `analyze.sh --dry-run` shows prompt without API call.
- **[Camera jank]** Moving camera every step without interpolation may feel jerky in realtime mode. → Acceptable for MVP; Interpolation is a future enhancement.
- **[jq availability on Windows]** `jq` is not pre-installed on Windows outside WSL. → Document WSL requirement for Windows users in `analyze.sh` usage notes.

## Open Questions

- Should army snapshots include unit counts only (Stalker: 4) or per-unit health/shields? → Unit counts for MVP, health later if needed for analysis.
- Should `analyze.sh` support multi-file output (split analysis by problem area) or single consolidated report? → Single report for MVP; split later if output grows too large.
- Should `BuildPhase` transitions be time-based, event-based, or both? → Event-based with time-based fallbacks for safety.
