## Why

The bot currently plays blind: it doesn't know its own army composition, doesn't distribute probes across expansions (oversaturating the main while leaving expansions starved), and has zero defensive reactions to enemy attacks. The report HTML is also broken — it shows enemy Terran units in the "Our Army" column due to a table column mismatch. The observation pipeline only captures enemy data, missing critical information about our own state that both gameplay decisions and future ML models need.

## What Changes

- **Observation pipeline**: `extract_features()` now captures our army composition (unit types + counts), per-base worker saturation (ideal vs actual), threat proximity per base, and our structure composition — all in the existing flat dict format for JSONL compatibility.
- **Probe management**: Probes are trained at the *least saturated* nexus instead of any idle nexus. Expansion decisions are driven by saturation (expand when all current bases are near saturation, not hard-capped at 2).
- **Defense system**: New `manage_defense()` method with a 3-state machine (PEACEFUL → THREATENED → ENGAGED). Evaluates threat per base, repositions army defensively, and engages when enemies are in range. Adds optional photon cannon placement at expansions.
- **Report fixes**: HTML table corrected (3 headers matching 3 data columns). `opponent_race` no longer hardcoded. Separate "Our Army Composition" and "Enemy Army Composition" sections with proper unit breakdowns. Per-base saturation chart added.
- **Events extension**: New event types: `base_under_attack`, `base_oversaturated`. Existing `enemy_push` detection refined to consider proximity to bases.

## Capabilities

### New Capabilities
- `per-base-saturation`: Worker distribution across bases based on per-base mineral/gas ideal counts. Expansion decisions driven by saturation metrics rather than hard cap at 2 bases.
- `reactive-defense`: Threat evaluation per base, 3-state defensive behavior (peaceful repositioning / threatened movement / engaged combat), optional photon cannon placement at expansions.
- `army-composition-tracking`: Our own unit composition (types and counts) tracked in features, mirroring the existing enemy composition tracking.

### Modified Capabilities
- `observation-pipeline`: `extract_features()` extended with new fields (our_army_composition, bases[], our_structures). Existing fields and format preserved — **no breaking changes** to the JSONL contract. Report generation uses new fields for correct display.
- `bot-gameplay`: `manage_probes()` behavior changed from "train at any idle nexus" to "train at least saturated nexus". `manage_expansion()` changed from "stop at 2 bases" to "expand when all current bases near saturation". New `manage_defense()` added to `on_step()` dispatch. Report HTML structure changed for correct multi-column layout.

## Impact

- `src/ml/observation.py` — extended with our army composition, per-base stats, structure tracking
- `src/bot/core.py` — `manage_probes()` rewritten, `manage_expansion()` rewritten, new `manage_defense()` added, `bot_info` opponent_race fixed, `on_step()` dispatches new manager
- `src/ml/report.py` — HTML template restructured for correct 3-column tables, new per-base saturation section, opponent race from actual game data
- `src/ml/events.py` — new event detectors: `base_under_attack`, `base_oversaturated`
- `src/bot/strategy.py` — new constants for saturation thresholds, threat ranges
- `tests/` — new test coverage for saturation calculations, threat evaluation, feature extraction extensions
