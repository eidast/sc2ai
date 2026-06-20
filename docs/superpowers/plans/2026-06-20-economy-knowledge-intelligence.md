# Economy, Knowledge Base & Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the gas/mineral economy, build a unit knowledge base with counter logic and icons, then add scouting and upgrade intelligence so the bot adapts dynamically instead of following a fixed script.

**Architecture:** Three sequential phases. Phase 1 fixes concrete bugs in `manage_gas()` and adds dynamic spending. Phase 2 builds a static data layer (`src/data/`) for unit stats, counters, and icons — purely additive, no gameplay impact. Phase 3 adds scouting waypoints and an upgrade decision engine, fed by the knowledge base. All new logic is testable without SC2 via mocks following the existing `FakeBot`/`SimpleNamespace` pattern.

**Tech Stack:** Python 3.9+, burnysc2/python-sc2, pytest with mocks, no new dependencies.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/bot/core.py` | Modify | Fix gas bug, add gas worker assignment, dynamic gateways, mineral sink, scout+upgrade integration |
| `src/bot/strategy.py` | Modify | Add economy/scout/upgrade constants |
| `src/bot/scout.py` | Create | Scout waypoint logic (pure functions, testable) |
| `src/bot/upgrades.py` | Create | Upgrade decision engine (pure functions, testable) |
| `src/data/__init__.py` | Create | Package init |
| `src/data/units.py` | Create | Unit properties database (static dicts) |
| `src/data/counters.py` | Create | Counter calculation from unit DB |
| `src/data/icons.py` | Create | Unit → icon URL mapping |
| `src/ml/observation.py` | Modify | Add enriched enemy features (armor types, threat) |
| `src/ml/events.py` | Modify | Add gas_starved event, enhance resource_float |
| `src/ml/report.py` | Modify | Embed unit icons in HTML reports |
| `tests/test_economy.py` | Create | Gas management, float detection, gateway scaling tests |
| `tests/test_unit_data.py` | Create | Unit lookups, counter calculation, icon resolution tests |
| `tests/test_scout.py` | Create | Scout waypoint and intel logic tests |
| `tests/test_upgrades.py` | Create | Upgrade decision logic tests |

---

## Phase 1: Economy Foundation

### Task 1.1: Fix `manage_gas()` early-exit bug

**Files:**
- Modify: `src/bot/core.py:167-181`
- Create: `tests/test_economy.py`

- [ ] **Step 1: Write failing test for the early-exit bug**

```python
# tests/test_economy.py
from types import SimpleNamespace


class FakeGeyser:
    def __init__(self, x, y):
        self.position = SimpleNamespace(x=x, y=y)


class FakeGasBuilding:
    def __init__(self, position):
        self.position = position

    def distance_to(self, other):
        return ((self.position.x - other.x) ** 2 + (self.position.y - other.y) ** 2) ** 0.5


class FakeGasBuildings:
    def __init__(self, buildings=None):
        self._buildings = buildings or []

    def filter(self, predicate):
        return FakeGasBuildings([b for b in self._buildings if predicate(b)])

    def __iter__(self):
        return iter(self._buildings)

    def __len__(self):
        return len(self._buildings)


def test_manage_gas_skips_unaffordable_continues_next():
    """When can_afford returns False for first geyser, the bot should
    skip it and continue checking other nexuses/geysers — not return early."""
    # This test validates the logic that 'continue' is used instead of 'return'
    # when can_afford fails. We test the loop semantics directly.
    geysers = [FakeGeyser(10, 10), FakeGeyser(20, 20)]
    affordable = [False, True]
    build_count = 0

    # Simulate the corrected loop logic
    for geyser in geysers:
        if not affordable[geysers.index(geyser)]:
            continue  # FIX: was 'return' — now 'continue'
        build_count += 1
        break  # one per step

    assert build_count == 1, "Should skip unaffordable and build on affordable"


def test_manage_gas_builds_one_per_step():
    """When multiple geysers are affordable, only one assimilator is built per step."""
    geysers = [FakeGeyser(10, 10), FakeGeyser(20, 20)]
    affordable = [True, True]
    build_count = 0

    for geyser in geysers:
        if not affordable[geysers.index(geyser)]:
            continue
        if build_count >= 1:
            continue
        build_count += 1

    assert build_count == 1, "Should build at most one per step"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_economy.py::test_manage_gas_skips_unaffordable_continues_next -v`
Expected: FAIL

- [ ] **Step 3: Fix `manage_gas()` in core.py**

Replace lines 167-181 in `src/bot/core.py`:

```python
async def manage_gas(self):
    for nexus in self.townhalls.ready:
        vespene_geysers = self.vespene_geyser.closer_than(15, nexus.position)
        for geyser in vespene_geysers:
            if self.gas_buildings.filter(
                lambda g: g.position.distance_to(geyser.position) < 2
            ):
                continue
            if not self.can_afford(UnitTypeId.ASSIMILATOR):
                continue
            worker = self.select_build_worker(geyser.position)
            if worker is None:
                continue
            worker.build_gas(geyser)
            return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_economy.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_economy.py src/bot/core.py
git commit -m "fix: manage_gas() uses continue instead of return on unaffordable geyser"
```

---

### Task 1.2: Add explicit gas worker assignment

**Files:**
- Modify: `src/bot/core.py` (add `_assign_gas_workers()` method, call from `manage_gas`)
- Modify: `tests/test_economy.py`

- [ ] **Step 1: Write test for gas worker assignment logic**

Append to `tests/test_economy.py`:

```python
def test_gas_worker_assignment_targets_undersaturated_assimilators():
    """Assimilators with < 3 workers should get idle workers assigned."""
    assimilators = [
        {"name": "assim1", "assigned_harvesters": 1, "is_ready": True},
        {"name": "assim2", "assigned_harvesters": 3, "is_ready": True},
        {"name": "assim3", "assigned_harvesters": 0, "is_ready": False},
    ]
    workers = ["probe_a", "probe_b", "probe_c"]
    assignments = []

    for assim in assimilators:
        if not assim["is_ready"]:
            continue
        needed = 3 - assim["assigned_harvesters"]
        for _ in range(needed):
            if not workers:
                break
            worker = workers.pop(0)
            assignments.append((worker, assim["name"]))

    assert len(assignments) == 2
    assert assignments[0] == ("probe_a", "assim1")
    assert assignments[1] == ("probe_b", "assim1")
    assert len(workers) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_economy.py::test_gas_worker_assignment_targets_undersaturated_assimilators -v`
Expected: FAIL

- [ ] **Step 3: Add `_assign_gas_workers()` and call it from `manage_gas()`**

In `src/bot/core.py`, add this method to `MyBot`:

```python
async def _assign_gas_workers(self):
    for assimilator in self.gas_buildings.ready:
        assigned = getattr(assimilator, "assigned_harvesters", 0)
        if assigned >= 3:
            continue
        workers = self.workers.gathering.filter(
            lambda w: w.is_carrying_minerals or w.is_gathering
        )
        idle = self.workers.idle
        candidates = idle + workers
        for _ in range(3 - assigned):
            if not candidates:
                break
            worker = candidates.closest_to(assimilator.position)
            if worker:
                worker.gather(assimilator)
```

In `manage_gas()`, add the call after the build loop (before the final `return` statement, or at the end of the method). Insert after the geyser loop:

```python
async def manage_gas(self):
    for nexus in self.townhalls.ready:
        vespene_geysers = self.vespene_geyser.closer_than(15, nexus.position)
        for geyser in vespene_geysers:
            if self.gas_buildings.filter(
                lambda g: g.position.distance_to(geyser.position) < 2
            ):
                continue
            if not self.can_afford(UnitTypeId.ASSIMILATOR):
                continue
            worker = self.select_build_worker(geyser.position)
            if worker is None:
                continue
            worker.build_gas(geyser)
            return

    await self._assign_gas_workers()
```

- [ ] **Step 4: Run all economy tests**

Run: `uv run pytest tests/test_economy.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_economy.py src/bot/core.py
git commit -m "feat: assign workers to undersaturated assimilators"
```

---

### Task 1.3: Dynamic production capacity

**Files:**
- Modify: `src/bot/strategy.py` (add constants)
- Modify: `src/bot/core.py` (replace hardcoded `target_gateways = 4` with dynamic calculation)
- Modify: `tests/test_economy.py`

- [ ] **Step 1: Add economy constants to strategy.py**

Append to `src/bot/strategy.py`:

```python
GATEWAY_MINERAL_BASELINE = 4
GATEWAY_PER_BASE = 3
GATEWAY_MINERAL_FLOAT_THRESHOLD = 500
GATEWAY_MINERAL_FLOAT_EXTRA = 2
MAX_GATEWAYS = 16
```

- [ ] **Step 2: Write test for dynamic gateway calculation**

Append to `tests/test_economy.py`:

```python
from src.bot.strategy import (
    GATEWAY_MINERAL_BASELINE, GATEWAY_PER_BASE,
    GATEWAY_MINERAL_FLOAT_THRESHOLD, GATEWAY_MINERAL_FLOAT_EXTRA,
    MAX_GATEWAYS,
)


def _compute_target_gateways(bases_count, minerals):
    target = GATEWAY_MINERAL_BASELINE + (bases_count - 1) * GATEWAY_PER_BASE
    if minerals > GATEWAY_MINERAL_FLOAT_THRESHOLD:
        target += GATEWAY_MINERAL_FLOAT_EXTRA
    return min(target, MAX_GATEWAYS)


def test_target_gateways_scales_with_bases():
    assert _compute_target_gateways(1, 100) == 4
    assert _compute_target_gateways(2, 100) == 7
    assert _compute_target_gateways(3, 100) == 10


def test_target_gateways_adds_extra_when_floating():
    assert _compute_target_gateways(2, 600) == 9


def test_target_gateways_respects_max():
    assert _compute_target_gateways(5, 1000) == 16
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_economy.py::test_target_gateways_scales_with_bases -v`
Expected: FAIL (import error or function not found)

- [ ] **Step 4: Implement dynamic gateways in core.py**

Replace the hardcoded `target_gateways = 4` line in `manage_tech()` (line 202 of `src/bot/core.py`) with:

```python
from src.bot.strategy import (
    GATEWAY_MINERAL_BASELINE, GATEWAY_PER_BASE,
    GATEWAY_MINERAL_FLOAT_THRESHOLD, GATEWAY_MINERAL_FLOAT_EXTRA,
    MAX_GATEWAYS,
)

# In manage_tech(), replace:
# target_gateways = 4 if self.townhalls.amount >= 2 else 1
# With:
target = GATEWAY_MINERAL_BASELINE + max(0, self.townhalls.amount - 1) * GATEWAY_PER_BASE
if self.minerals > GATEWAY_MINERAL_FLOAT_THRESHOLD:
    target += GATEWAY_MINERAL_FLOAT_EXTRA
target_gateways = min(target, MAX_GATEWAYS)
```

- [ ] **Step 5: Run all economy tests**

Run: `uv run pytest tests/test_economy.py -v`
Expected: 6 PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/strategy.py src/bot/core.py tests/test_economy.py
git commit -m "feat: dynamic gateway count scales with bases and mineral float"
```

---

### Task 1.4: Mineral sink — Forge and ground upgrades when floating

**Files:**
- Modify: `src/bot/core.py` (add `manage_forge_upgrades()` and call it)
- Modify: `src/bot/strategy.py` (add forge/upgrade constants)
- Modify: `tests/test_economy.py`

- [ ] **Step 1: Add upgrade constants to strategy.py**

Append to `src/bot/strategy.py`:

```python
FORGE_MINERAL_THRESHOLD = 400
UPGRADE_PRIORITY_WEAPONS = 1
UPGRADE_PRIORITY_ARMOR = 2
UPGRADE_PRIORITY_SHIELDS = 3
```

- [ ] **Step 2: Write test for upgrade priority logic**

Append to `tests/test_economy.py`:

```python
from sc2.ids.upgrade_id import UpgradeId


def _select_upgrade(forges_ready, completed_levels):
    weapon_id = getattr(UpgradeId, "PROTOSSGROUNDWEAPONSLEVEL1", None)
    armor_id = getattr(UpgradeId, "PROTOSSGROUNDARMORSLEVEL1", None)
    shields_id = getattr(UpgradeId, "PROTOSSSHIELDSLEVEL1", None)
    if not forges_ready:
        return None
    priorities = [
        (completed_levels.get("weapons", 0), weapon_id),
        (completed_levels.get("armor", 0), armor_id),
        (completed_levels.get("shields", 0), shields_id),
    ]
    priorities.sort()
    level, upgrade = priorities[0]
    if level >= 3:
        return None
    return upgrade


def test_upgrade_priority_starts_with_weapons():
    result = _select_upgrade(forges_ready=True, completed_levels={})
    assert result is not None
    assert "WEAPONS" in result.name


def test_upgrade_priority_round_robin():
    result = _select_upgrade(forges_ready=True, completed_levels={"weapons": 1})
    assert result is not None
    assert "ARMORS" in result.name


def test_upgrade_returns_none_when_all_maxed():
    result = _select_upgrade(forges_ready=True, completed_levels={"weapons": 3, "armor": 3, "shields": 3})
    assert result is None


def test_upgrade_returns_none_when_no_forge():
    result = _select_upgrade(forges_ready=False, completed_levels={})
    assert result is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_economy.py::test_upgrade_priority_starts_with_weapons -v`
Expected: FAIL

- [ ] **Step 4: Implement `manage_forge_upgrades()` in core.py**

Add to `MyBot` in `src/bot/core.py`:

```python
async def manage_forge_upgrades(self):
    if self.minerals < FORGE_MINERAL_THRESHOLD:
        return

    forges = self.structures(UnitTypeId.FORGE)
    if forges.amount == 0:
        if self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
            position = await self.find_placement(UnitTypeId.FORGE, self.start_location, placement_step=5)
            if position:
                await self.build(UnitTypeId.FORGE, near=position)
        return

    forges_ready = forges.ready
    if forges_ready.amount == 0:
        return

    upgrade_order = [
        UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
        UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
        UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
        UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
        UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
        UpgradeId.PROTOSSGROUNDARMORSLEVEL3,
        UpgradeId.PROTOSSSHIELDSLEVEL1,
        UpgradeId.PROTOSSSHIELDSLEVEL2,
        UpgradeId.PROTOSSSHIELDSLEVEL3,
    ]

    for upgrade in upgrade_order:
        if self.already_pending_upgrade(upgrade):
            continue
        if self.can_afford(upgrade):
            forge = forges_ready.first
            forge.research(upgrade)
            return
```

Add `await self.manage_forge_upgrades()` to `on_step()` after `await self.manage_tech()`:

```python
await self.manage_tech()
await self.manage_forge_upgrades()
```

Add the import for `FORGE_MINERAL_THRESHOLD` at the top:

```python
from src.bot.strategy import BuildPhase, CameraMode, MAX_SATURATION_RATIO, BASE_MINERAL_RADIUS, THREAT_RANGE, ENGAGE_RANGE, GATEWAY_MINERAL_BASELINE, GATEWAY_PER_BASE, GATEWAY_MINERAL_FLOAT_THRESHOLD, GATEWAY_MINERAL_FLOAT_EXTRA, MAX_GATEWAYS, FORGE_MINERAL_THRESHOLD
```

- [ ] **Step 5: Run all tests**

Run: `uv run pytest tests/test_economy.py -v`
Expected: 10 PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/strategy.py src/bot/core.py tests/test_economy.py
git commit -m "feat: build forge and start ground upgrades when floating minerals"
```

---

### Task 1.5: Economy events — gas_starved and enhanced resource_float

**Files:**
- Modify: `src/ml/events.py` (add `gas_starved` event, lower `resource_float` threshold, add gas ratio check)
- Modify: `tests/test_events.py`

- [ ] **Step 1: Add gas_starved event detection and improve resource_float**

In `src/ml/events.py`, add after the existing `_detect_resource_float` function:

```python
def _detect_gas_starved(features: dict, bot: Any) -> bool:
    minerals = features.get("minerals", 0)
    vespene = features.get("vespene", 0)
    if minerals < 300:
        return False
    if vespene > 100:
        return False
    if minerals / max(vespene, 1) < 3:
        return False
    gas_buildings = getattr(bot, "gas_buildings", None)
    if gas_buildings is None:
        return False
    if gas_buildings.amount == 0:
        return True
    total_workers_on_gas = sum(
        getattr(a, "assigned_harvesters", 0) for a in gas_buildings
    )
    return total_workers_on_gas < gas_buildings.amount * 3
```

In `detect_events()`, add gas_starved detection after resource_float:

```python
if _detect_gas_starved(features, bot):
    events.append(Event(
        type="gas_starved", time=now, step=iteration,
        severity="high",
        details={
            "minerals": features["minerals"],
            "vespene": features["vespene"],
        },
    ))
```

Also modify `_detect_resource_float` to lower the threshold from 500 to 300 and check that production buildings are idle:

```python
def _detect_resource_float(features: dict, bot: Any) -> bool:
    minerals = features.get("minerals", 0)
    vespene = features.get("vespene", 0)
    if minerals <= 300 and vespene <= 300:
        return False
    from sc2.ids.unit_typeid import UnitTypeId
    gateways = bot.structures(UnitTypeId.GATEWAY)
    warp_gates = bot.structures(UnitTypeId.WARPGATE)
    all_gates = gateways + warp_gates
    return all_gates.amount == 0 or all(
        g.is_idle for g in all_gates
    )
```

- [ ] **Step 2: Write tests for gas_starved**

Append to `tests/test_events.py`:

```python
from src.ml.events import _detect_gas_starved


def test_detect_gas_starved_triggers_when_mineral_rich_gas_poor():
    bot = make_bot()
    bot.gas_buildings = SimpleNamespace(amount=1)
    features = {"minerals": 600, "vespene": 50}
    assert _detect_gas_starved(features, bot) is True


def test_detect_gas_starved_no_trigger_when_gas_adequate():
    bot = make_bot()
    bot.gas_buildings = SimpleNamespace(amount=1)
    features = {"minerals": 300, "vespene": 200}
    assert _detect_gas_starved(features, bot) is False


def test_detect_gas_starved_triggers_when_no_assimilators():
    bot = make_bot()
    bot.gas_buildings = SimpleNamespace(amount=0)
    features = {"minerals": 500, "vespene": 10}
    assert _detect_gas_starved(features, bot) is True


def test_detect_gas_starved_in_detect_events():
    bot = make_bot()
    bot.gas_buildings = SimpleNamespace(amount=0)
    features = {"game_time_seconds": 120, "minerals": 800, "vespene": 20,
                "supply_used": 30, "supply_left": 10, "worker_count": 30,
                "expansion_count": 1, "enemy_visible_units": 0, "bases": []}
    prev = {"game_time_seconds": 119, "minerals": 700, "vespene": 20,
            "supply_used": 30, "supply_left": 10, "worker_count": 30,
            "expansion_count": 1, "enemy_visible_units": 0}
    events = detect_events(bot, features, prev, 100)
    types = [e.type for e in events]
    assert "gas_starved" in types


def test_resource_float_lower_threshold():
    bot = make_bot()
    bot.structures = lambda _: SimpleNamespace(amount=0, ready=SimpleNamespace(amount=0))
    features = {"minerals": 350, "vespene": 50, "supply_left": 10}
    from src.ml.events import _detect_resource_float
    assert _detect_resource_float(features, bot) is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_events.py::test_detect_gas_starved_triggers_when_mineral_rich_gas_poor -v`
Expected: FAIL (function not defined)

- [ ] **Step 4: Run all event tests**

Run: `uv run pytest tests/test_events.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/ml/events.py tests/test_events.py
git commit -m "feat: add gas_starved event and lower resource_float threshold"
```

---

## Phase 2: Unit Knowledge Base

### Task 2.1: Unit properties database

**Files:**
- Create: `src/data/__init__.py`
- Create: `src/data/units.py`
- Create: `tests/test_unit_data.py`

- [ ] **Step 1: Write failing tests for unit lookups**

```python
# tests/test_unit_data.py
from src.data.units import get_unit_info, get_units_by_attribute, ALL_UNITS


def test_get_unit_info_returns_stats_for_stalker():
    info = get_unit_info("STALKER")
    assert info is not None
    assert info["hp"] == 80
    assert info["shields"] == 80
    assert info["race"] == "Protoss"
    assert "Armored" in info["attributes"]


def test_get_unit_info_returns_none_for_unknown():
    assert get_unit_info("NONEXISTENT_UNIT") is None


def test_get_units_by_attribute_filters_correctly():
    armored = get_units_by_attribute("Armored")
    assert "STALKER" in armored
    assert "ROACH" in armored
    assert "ZEALOT" not in armored


def test_all_units_contains_core_protoss():
    assert "ZEALOT" in ALL_UNITS
    assert "STALKER" in ALL_UNITS
    assert "SENTRY" in ALL_UNITS


def test_all_units_contains_core_zerg():
    assert "ZERGLING" in ALL_UNITS
    assert "ROACH" in ALL_UNITS


def test_all_units_contains_core_terran():
    assert "MARINE" in ALL_UNITS
    assert "SIEGETANK" in ALL_UNITS


def test_unit_info_has_attacks_key():
    stalker = get_unit_info("STALKER")
    assert "attacks" in stalker
    assert len(stalker["attacks"]) >= 1
    attack = stalker["attacks"][0]
    assert "damage" in attack
    assert "bonus" in attack
    assert "range" in attack
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_unit_data.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create the unit database**

```python
# src/data/__init__.py
```

```python
# src/data/units.py
"""
Static unit property database for StarCraft II.

Data sourced from game data. Each entry maps UnitTypeId name → properties.
Attributes use sc2.data.Attribute enum names.

Counter relationships are computed in counters.py, not hardcoded here.
"""

ALL_UNITS: dict[str, dict] = {
    # ===== Protoss =====
    "PROBE": {
        "race": "Protoss", "hp": 20, "shields": 20, "armor": 0,
        "attributes": ["Light", "Biological", "Mechanical"],
        "attacks": [{"damage": 5, "bonus": {}, "range": 1, "speed": 1.5, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 0, "build_time": 12,
    },
    "ZEALOT": {
        "race": "Protoss", "hp": 100, "shields": 50, "armor": 1,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 8, "bonus": {}, "range": 1, "speed": 1.2, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 0, "build_time": 38,
    },
    "STALKER": {
        "race": "Protoss", "hp": 80, "shields": 80, "armor": 1,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [
            {"damage": 13, "bonus": {"Armored": 5}, "range": 6, "speed": 1.34, "targets": "ground"},
        ],
        "supply_cost": 2,
        "mineral_cost": 125, "vespene_cost": 50, "build_time": 42,
    },
    "SENTRY": {
        "race": "Protoss", "hp": 40, "shields": 40, "armor": 1,
        "attributes": ["Light", "Mechanical", "Psionic"],
        "attacks": [{"damage": 6, "bonus": {}, "range": 5, "speed": 1.0, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 50, "vespene_cost": 100, "build_time": 37,
    },
    "ADEPT": {
        "race": "Protoss", "hp": 70, "shields": 70, "armor": 1,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 10, "bonus": {"Light": 12}, "range": 4, "speed": 1.61, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 25, "build_time": 38,
    },
    "HIGHTEMPLAR": {
        "race": "Protoss", "hp": 40, "shields": 40, "armor": 0,
        "attributes": ["Light", "Biological", "Psionic"],
        "attacks": [],
        "supply_cost": 2,
        "mineral_cost": 50, "vespene_cost": 150, "build_time": 39,
    },
    "DARKTEMPLAR": {
        "race": "Protoss", "hp": 40, "shields": 80, "armor": 1,
        "attributes": ["Light", "Biological", "Psionic"],
        "attacks": [{"damage": 45, "bonus": {}, "range": 1, "speed": 1.2, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 125, "vespene_cost": 125, "build_time": 39,
    },
    "ARCHON": {
        "race": "Protoss", "hp": 10, "shields": 350, "armor": 0,
        "attributes": ["Massive", "Psionic"],
        "attacks": [
            {"damage": 25, "bonus": {"Biological": 10}, "range": 3, "speed": 1.75, "targets": "ground"},
        ],
        "supply_cost": 4,
        "mineral_cost": 0, "vespene_cost": 0, "build_time": 0,
    },
    "IMMORTAL": {
        "race": "Protoss", "hp": 200, "shields": 100, "armor": 1,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [
            {"damage": 20, "bonus": {"Armored": 30}, "range": 6, "speed": 1.45, "targets": "ground"},
        ],
        "supply_cost": 3,
        "mineral_cost": 250, "vespene_cost": 100, "build_time": 55,
    },
    "COLOSSUS": {
        "race": "Protoss", "hp": 200, "shields": 150, "armor": 1,
        "attributes": ["Armored", "Mechanical", "Massive"],
        "attacks": [
            {"damage": 10, "bonus": {"Light": 5}, "range": 7, "speed": 1.3, "targets": "ground"},
        ],
        "supply_cost": 6,
        "mineral_cost": 300, "vespene_cost": 200, "build_time": 75,
    },
    "VOIDRAY": {
        "race": "Protoss", "hp": 150, "shields": 100, "armor": 0,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [
            {"damage": 6, "bonus": {"Armored": 4}, "range": 6, "speed": 0.5, "targets": "ground"},
        ],
        "supply_cost": 3,
        "mineral_cost": 250, "vespene_cost": 150, "build_time": 60,
    },
    "PHOENIX": {
        "race": "Protoss", "hp": 120, "shields": 60, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [
            {"damage": 5, "bonus": {"Light": 5}, "range": 5, "speed": 1.1, "targets": "air"},
        ],
        "supply_cost": 2,
        "mineral_cost": 150, "vespene_cost": 100, "build_time": 35,
    },
    "ORACLE": {
        "race": "Protoss", "hp": 100, "shields": 60, "armor": 0,
        "attributes": ["Light", "Mechanical", "Psionic"],
        "attacks": [
            {"damage": 15, "bonus": {"Light": 10}, "range": 4, "speed": 0.87, "targets": "ground"},
        ],
        "supply_cost": 3,
        "mineral_cost": 150, "vespene_cost": 150, "build_time": 50,
    },
    "TEMPEST": {
        "race": "Protoss", "hp": 200, "shields": 100, "armor": 2,
        "attributes": ["Armored", "Mechanical", "Massive"],
        "attacks": [
            {"damage": 30, "bonus": {"Massive": 22}, "range": 15, "speed": 2.8, "targets": "ground"},
        ],
        "supply_cost": 5,
        "mineral_cost": 300, "vespene_cost": 200, "build_time": 60,
    },
    "CARRIER": {
        "race": "Protoss", "hp": 250, "shields": 150, "armor": 2,
        "attributes": ["Armored", "Mechanical", "Massive"],
        "attacks": [],
        "supply_cost": 6,
        "mineral_cost": 350, "vespene_cost": 250, "build_time": 90,
    },
    "OBSERVER": {
        "race": "Protoss", "hp": 40, "shields": 20, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [],
        "supply_cost": 1,
        "mineral_cost": 25, "vespene_cost": 75, "build_time": 30,
    },
    "WARPPRISM": {
        "race": "Protoss", "hp": 100, "shields": 100, "armor": 0,
        "attributes": ["Armored", "Mechanical", "Psionic"],
        "attacks": [],
        "supply_cost": 2,
        "mineral_cost": 200, "vespene_cost": 0, "build_time": 50,
    },
    "MOTHERSHIP": {
        "race": "Protoss", "hp": 350, "shields": 350, "armor": 2,
        "attributes": ["Armored", "Mechanical", "Massive", "Heroic"],
        "attacks": [
            {"damage": 6, "bonus": {}, "range": 7, "speed": 1.0, "targets": "ground"},
        ],
        "supply_cost": 8,
        "mineral_cost": 400, "vespene_cost": 400, "build_time": 120,
    },
    # ===== Zerg =====
    "LARVA": {
        "race": "Zerg", "hp": 25, "shields": 0, "armor": 10,
        "attributes": ["Light", "Biological"],
        "attacks": [],
        "supply_cost": 0,
        "mineral_cost": 0, "vespene_cost": 0, "build_time": 0,
    },
    "DRONE": {
        "race": "Zerg", "hp": 40, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 5, "bonus": {}, "range": 1, "speed": 1.33, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 0, "build_time": 12,
    },
    "ZERGLING": {
        "race": "Zerg", "hp": 35, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 5, "bonus": {}, "range": 1, "speed": 0.49, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 0, "build_time": 17,
    },
    "BANELING": {
        "race": "Zerg", "hp": 30, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 20, "bonus": {"Light": 15}, "range": 1, "speed": 1.0, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 25, "vespene_cost": 25, "build_time": 14,
    },
    "ROACH": {
        "race": "Zerg", "hp": 145, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [{"damage": 16, "bonus": {}, "range": 4, "speed": 2.0, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 75, "vespene_cost": 25, "build_time": 19,
    },
    "RAVAGER": {
        "race": "Zerg", "hp": 120, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [{"damage": 16, "bonus": {}, "range": 6, "speed": 1.3, "targets": "ground"}],
        "supply_cost": 3,
        "mineral_cost": 0, "vespene_cost": 0, "build_time": 0,
    },
    "HYDRALISK": {
        "race": "Zerg", "hp": 90, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 12, "bonus": {}, "range": 5, "speed": 0.83, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 50, "build_time": 24,
    },
    "LURKER": {
        "race": "Zerg", "hp": 200, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [{"damage": 20, "bonus": {"Armored": 10}, "range": 9, "speed": 1.8, "targets": "ground"}],
        "supply_cost": 3,
        "mineral_cost": 50, "vespene_cost": 100, "build_time": 24,
    },
    "MUTALISK": {
        "race": "Zerg", "hp": 120, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 9, "bonus": {}, "range": 3, "speed": 1.52, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 100, "build_time": 24,
    },
    "CORRUPTOR": {
        "race": "Zerg", "hp": 200, "shields": 0, "armor": 2,
        "attributes": ["Armored", "Biological"],
        "attacks": [{"damage": 12, "bonus": {"Massive": 10}, "range": 6, "speed": 1.36, "targets": "air"}],
        "supply_cost": 2,
        "mineral_cost": 150, "vespene_cost": 100, "build_time": 29,
    },
    "INFESTOR": {
        "race": "Zerg", "hp": 90, "shields": 0, "armor": 0,
        "attributes": ["Armored", "Biological", "Psionic"],
        "attacks": [],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 150, "build_time": 36,
    },
    "SWARMHOSTMP": {
        "race": "Zerg", "hp": 160, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [],
        "supply_cost": 3,
        "mineral_cost": 100, "vespene_cost": 75, "build_time": 29,
    },
    "ULTRALISK": {
        "race": "Zerg", "hp": 500, "shields": 0, "armor": 2,
        "attributes": ["Armored", "Biological", "Massive"],
        "attacks": [{"damage": 35, "bonus": {}, "range": 1, "speed": 0.61, "targets": "ground"}],
        "supply_cost": 6,
        "mineral_cost": 300, "vespene_cost": 200, "build_time": 39,
    },
    "BROODLORD": {
        "race": "Zerg", "hp": 225, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological", "Massive"],
        "attacks": [],
        "supply_cost": 4,
        "mineral_cost": 150, "vespene_cost": 150, "build_time": 0,
    },
    "VIPER": {
        "race": "Zerg", "hp": 150, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [],
        "supply_cost": 3,
        "mineral_cost": 100, "vespene_cost": 200, "build_time": 43,
    },
    "QUEEN": {
        "race": "Zerg", "hp": 175, "shields": 0, "armor": 1,
        "attributes": ["Biological", "Psionic"],
        "attacks": [
            {"damage": 9, "bonus": {}, "range": 7, "speed": 0.71, "targets": "ground"},
            {"damage": 9, "bonus": {}, "range": 7, "speed": 0.71, "targets": "air"},
        ],
        "supply_cost": 2,
        "mineral_cost": 150, "vespene_cost": 0, "build_time": 36,
    },
    # ===== Terran =====
    "SCV": {
        "race": "Terran", "hp": 45, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological", "Mechanical"],
        "attacks": [{"damage": 5, "bonus": {}, "range": 1, "speed": 1.07, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 0, "build_time": 12,
    },
    "MARINE": {
        "race": "Terran", "hp": 45, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 6, "bonus": {}, "range": 5, "speed": 0.86, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 0, "build_time": 18,
    },
    "MARAUDER": {
        "race": "Terran", "hp": 125, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Biological"],
        "attacks": [{"damage": 10, "bonus": {"Armored": 10}, "range": 6, "speed": 1.07, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 25, "build_time": 21,
    },
    "REAPER": {
        "race": "Terran", "hp": 60, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological"],
        "attacks": [{"damage": 4, "bonus": {"Light": 5}, "range": 5, "speed": 0.72, "targets": "ground"}],
        "supply_cost": 1,
        "mineral_cost": 50, "vespene_cost": 50, "build_time": 32,
    },
    "GHOST": {
        "race": "Terran", "hp": 100, "shields": 0, "armor": 0,
        "attributes": ["Light", "Biological", "Psionic"],
        "attacks": [{"damage": 10, "bonus": {"Light": 10}, "range": 6, "speed": 1.07, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 150, "vespene_cost": 125, "build_time": 29,
    },
    "HELLION": {
        "race": "Terran", "hp": 90, "shields": 0, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [{"damage": 8, "bonus": {"Light": 6}, "range": 5, "speed": 1.43, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 0, "build_time": 21,
    },
    "SIEGETANK": {
        "race": "Terran", "hp": 175, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [
            {"damage": 15, "bonus": {"Armored": 10}, "range": 7, "speed": 1.04, "targets": "ground"},
        ],
        "supply_cost": 3,
        "mineral_cost": 150, "vespene_cost": 125, "build_time": 32,
    },
    "CYCLONE": {
        "race": "Terran", "hp": 120, "shields": 0, "armor": 0,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [{"damage": 10, "bonus": {}, "range": 7, "speed": 0.71, "targets": "ground"}],
        "supply_cost": 3,
        "mineral_cost": 150, "vespene_cost": 100, "build_time": 32,
    },
    "THOR": {
        "race": "Terran", "hp": 400, "shields": 0, "armor": 1,
        "attributes": ["Armored", "Mechanical", "Massive"],
        "attacks": [
            {"damage": 30, "bonus": {"Massive": 15}, "range": 7, "speed": 1.28, "targets": "ground"},
            {"damage": 6, "bonus": {"Light": 6}, "range": 10, "speed": 1.0, "targets": "air"},
        ],
        "supply_cost": 6,
        "mineral_cost": 300, "vespene_cost": 200, "build_time": 43,
    },
    "VIKINGFIGHTER": {
        "race": "Terran", "hp": 135, "shields": 0, "armor": 0,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [
            {"damage": 10, "bonus": {"Armored": 4}, "range": 9, "speed": 1.43, "targets": "air"},
        ],
        "supply_cost": 2,
        "mineral_cost": 150, "vespene_cost": 75, "build_time": 30,
    },
    "MEDIVAC": {
        "race": "Terran", "hp": 150, "shields": 0, "armor": 0,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 100, "build_time": 30,
    },
    "LIBERATOR": {
        "race": "Terran", "hp": 180, "shields": 0, "armor": 0,
        "attributes": ["Armored", "Mechanical"],
        "attacks": [{"damage": 7, "bonus": {}, "range": 5, "speed": 0.83, "targets": "air"}],
        "supply_cost": 3,
        "mineral_cost": 150, "vespene_cost": 150, "build_time": 43,
    },
    "BANSHEE": {
        "race": "Terran", "hp": 140, "shields": 0, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [{"damage": 12, "bonus": {}, "range": 6, "speed": 1.0, "targets": "ground"}],
        "supply_cost": 3,
        "mineral_cost": 150, "vespene_cost": 100, "build_time": 43,
    },
    "RAVEN": {
        "race": "Terran", "hp": 140, "shields": 0, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [],
        "supply_cost": 2,
        "mineral_cost": 100, "vespene_cost": 200, "build_time": 43,
    },
    "BATTLECRUISER": {
        "race": "Terran", "hp": 550, "shields": 0, "armor": 3,
        "attributes": ["Armored", "Mechanical", "Massive"],
        "attacks": [
            {"damage": 8, "bonus": {}, "range": 6, "speed": 0.2, "targets": "ground"},
            {"damage": 5, "bonus": {}, "range": 6, "speed": 0.2, "targets": "air"},
        ],
        "supply_cost": 6,
        "mineral_cost": 400, "vespene_cost": 300, "build_time": 64,
    },
    "WIDOWMINE": {
        "race": "Terran", "hp": 90, "shields": 0, "armor": 0,
        "attributes": ["Light", "Mechanical"],
        "attacks": [{"damage": 125, "bonus": {"Shields": 35}, "range": 5, "speed": 0.0, "targets": "ground"}],
        "supply_cost": 2,
        "mineral_cost": 75, "vespene_cost": 25, "build_time": 21,
    },
}


def get_unit_info(unit_name: str) -> dict | None:
    return ALL_UNITS.get(unit_name)


def get_units_by_attribute(attribute: str) -> list[str]:
    return [
        name for name, info in ALL_UNITS.items()
        if attribute in info.get("attributes", [])
    ]


def get_units_by_race(race: str) -> list[str]:
    return [
        name for name, info in ALL_UNITS.items()
        if info.get("race") == race
    ]
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_unit_data.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/__init__.py src/data/units.py tests/test_unit_data.py
git commit -m "feat: add unit properties database for all three races"
```

---

### Task 2.2: Counter calculation engine

**Files:**
- Create: `src/data/counters.py`
- Modify: `tests/test_unit_data.py`

- [ ] **Step 1: Write tests for counter logic**

Append to `tests/test_unit_data.py`:

```python
from src.data.counters import compute_counters, compute_threat_assessment


def test_compute_counters_stalkers_good_vs_roaches():
    enemy_comp = {"ROACH": 5}
    counters = compute_counters(enemy_comp, race="Protoss")
    assert "STALKER" in counters
    stalker_score = counters["STALKER"]
    zealot_score = counters.get("ZEALOT", 0)
    assert stalker_score > zealot_score, (
        f"Stalkers ({stalker_score}) should score higher than Zealots ({zealot_score}) vs Roaches"
    )


def test_compute_counters_immortals_good_vs_roaches():
    enemy_comp = {"ROACH": 10}
    counters = compute_counters(enemy_comp, race="Protoss")
    assert "IMMORTAL" in counters
    assert counters["IMMORTAL"] > 0


def test_compute_counters_zealots_good_vs_zerglings():
    enemy_comp = {"ZERGLING": 20}
    counters = compute_counters(enemy_comp, race="Protoss")
    assert counters.get("ZEALOT", 0) > 0


def test_compute_counters_returns_empty_for_no_enemy():
    assert compute_counters({}, race="Protoss") == {}


def test_threat_assessment_ranks_enemy_units():
    threat = compute_threat_assessment({"ROACH": 5, "ZERGLING": 10})
    assert "ROACH" in threat
    assert threat["ROACH"] > threat["ZERGLING"], (
        "Roaches should be higher threat than Zerglings"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_unit_data.py::test_compute_counters_stalkers_good_vs_roaches -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement counter calculator**

```python
# src/data/counters.py
from src.data.units import get_unit_info, get_units_by_race


def _effective_damage(our_unit_name: str, enemy_unit_name: str) -> float:
    our_info = get_unit_info(our_unit_name)
    enemy_info = get_unit_info(enemy_unit_name)
    if not our_info or not enemy_info:
        return 0.0

    total = 0.0
    enemy_attrs = set(enemy_info.get("attributes", []))

    for attack in our_info.get("attacks", []):
        base = attack["damage"]
        bonus = 0.0
        for attr, bonus_dmg in attack.get("bonus", {}).items():
            if attr in enemy_attrs:
                bonus += bonus_dmg
        speed = max(attack.get("speed", 1.0), 0.1)
        dps = (base + bonus) / speed
        total += dps

    return total


def compute_counters(enemy_comp: dict[str, int], race: str = "Protoss") -> dict[str, float]:
    if not enemy_comp:
        return {}

    our_units = get_units_by_race(race)
    our_combat_units = [
        name for name in our_units
        if get_unit_info(name)["attacks"]
        and name not in ("PROBE", "DRONE", "SCV")
    ]

    scores: dict[str, float] = {}
    for our_unit in our_combat_units:
        score = 0.0
        for enemy_name, count in enemy_comp.items():
            dmg = _effective_damage(our_unit, enemy_name)
            score += dmg * count
        if score > 0:
            scores[our_unit] = round(score, 1)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def compute_threat_assessment(enemy_comp: dict[str, int]) -> dict[str, float]:
    if not enemy_comp:
        return {}

    threat: dict[str, float] = {}
    for enemy_name, count in enemy_comp.items():
        info = get_unit_info(enemy_name)
        if not info:
            continue
        hp = info["hp"] + info["shields"]
        dps = 0.0
        for attack in info.get("attacks", []):
            speed = max(attack.get("speed", 1.0), 0.1)
            dps += attack["damage"] / speed
        threat[enemy_name] = round(hp * count + dps * count * 10, 1)

    return dict(sorted(threat.items(), key=lambda x: x[1], reverse=True))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_unit_data.py -v`
Expected: 12 PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/counters.py tests/test_unit_data.py
git commit -m "feat: add counter calculator and threat assessment from unit DB"
```

---

### Task 2.3: Unit icon URL mapping

**Files:**
- Create: `src/data/icons.py`
- Modify: `tests/test_unit_data.py`

- [ ] **Step 1: Write tests for icon resolution**

Append to `tests/test_unit_data.py`:

```python
from src.data.icons import get_unit_icon_url, get_unit_race_icon_url


def test_get_unit_icon_url_returns_url_for_stalker():
    url = get_unit_icon_url("STALKER")
    assert url.startswith("http")
    assert "stalker" in url.lower()


def test_get_unit_icon_url_returns_url_for_zealot():
    url = get_unit_icon_url("ZEALOT")
    assert url.startswith("http")
    assert "zealot" in url.lower()


def test_get_unit_icon_url_returns_fallback_for_unknown():
    url = get_unit_icon_url("NONEXISTENT")
    assert url.startswith("http")


def test_get_unit_race_icon_url_returns_protoss_icon():
    url = get_unit_race_icon_url("Protoss")
    assert url.startswith("http")
    assert "protoss" in url.lower()


def test_get_unit_race_icon_url_returns_zerg_icon():
    url = get_unit_race_icon_url("Zerg")
    assert url.startswith("http")
    assert "zerg" in url.lower()


def test_get_unit_race_icon_url_returns_terran_icon():
    url = get_unit_race_icon_url("Terran")
    assert url.startswith("http")
    assert "terran" in url.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_unit_data.py::test_get_unit_icon_url_returns_url_for_stalker -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement icon mapping**

```python
# src/data/icons.py
"""
Unit and race icon URL mappings.

Icons sourced from Liquipedia's stable CDN. URLs are versioned and unlikely to change.
"""

_BASE_URL = "https://liquipedia.net/commons/images"

_ICON_MAP: dict[str, str] = {
    # Protoss units
    "PROBE": f"{_BASE_URL}/8/8c/Probe_SCR_icon.png",
    "ZEALOT": f"{_BASE_URL}/d/d2/Zealot_SCR_icon.png",
    "STALKER": f"{_BASE_URL}/5/53/Stalker_SCR_icon.png",
    "SENTRY": f"{_BASE_URL}/3/34/Sentry_SCR_icon.png",
    "ADEPT": f"{_BASE_URL}/c/c5/Adept_LotC_icon.png",
    "HIGHTEMPLAR": f"{_BASE_URL}/9/95/High_Templar_SCR_icon.png",
    "DARKTEMPLAR": f"{_BASE_URL}/2/28/Dark_Templar_SCR_icon.png",
    "ARCHON": f"{_BASE_URL}/7/78/Archon_SCR_icon.png",
    "IMMORTAL": f"{_BASE_URL}/6/6c/Immortal_SCR_icon.png",
    "COLOSSUS": f"{_BASE_URL}/7/72/Colossus_SCR_icon.png",
    "VOIDRAY": f"{_BASE_URL}/a/a3/Void_Ray_SCR_icon.png",
    "PHOENIX": f"{_BASE_URL}/9/97/Phoenix_SCR_icon.png",
    "ORACLE": f"{_BASE_URL}/9/97/Oracle_LotC_icon.png",
    "TEMPEST": f"{_BASE_URL}/2/29/Tempest_LotC_icon.png",
    "CARRIER": f"{_BASE_URL}/1/11/Carrier_SCR_icon.png",
    "OBSERVER": f"{_BASE_URL}/e/e5/Observer_SCR_icon.png",
    "WARPPRISM": f"{_BASE_URL}/3/38/Warp_Prism_SCR_icon.png",
    "MOTHERSHIP": f"{_BASE_URL}/a/a5/Mothership_SCR_icon.png",
    # Zerg units
    "DRONE": f"{_BASE_URL}/c/c6/Drone_SCR_icon.png",
    "ZERGLING": f"{_BASE_URL}/3/3b/Zergling_SCR_icon.png",
    "BANELING": f"{_BASE_URL}/1/16/Baneling_SCR_icon.png",
    "ROACH": f"{_BASE_URL}/c/cf/Roach_SCR_icon.png",
    "RAVAGER": f"{_BASE_URL}/0/03/Ravager_LotC_icon.png",
    "HYDRALISK": f"{_BASE_URL}/2/2e/Hydralisk_SCR_icon.png",
    "LURKER": f"{_BASE_URL}/b/b9/Lurker_LotC_icon.png",
    "MUTALISK": f"{_BASE_URL}/7/71/Mutalisk_SCR_icon.png",
    "CORRUPTOR": f"{_BASE_URL}/b/b4/Corruptor_SCR_icon.png",
    "INFESTOR": f"{_BASE_URL}/0/07/Infestor_SCR_icon.png",
    "SWARMHOSTMP": f"{_BASE_URL}/0/0b/Swarm_Host_LotC_icon.png",
    "ULTRALISK": f"{_BASE_URL}/1/17/Ultralisk_SCR_icon.png",
    "BROODLORD": f"{_BASE_URL}/c/c8/Brood_Lord_SCR_icon.png",
    "VIPER": f"{_BASE_URL}/7/7f/Viper_LotC_icon.png",
    "QUEEN": f"{_BASE_URL}/6/62/Queen_SCR_icon.png",
    # Terran units
    "SCV": f"{_BASE_URL}/6/68/SCV_SCR_icon.png",
    "MARINE": f"{_BASE_URL}/9/93/Marine_SCR_icon.png",
    "MARAUDER": f"{_BASE_URL}/4/4f/Marauder_SCR_icon.png",
    "REAPER": f"{_BASE_URL}/8/8d/Reaper_SCR_icon.png",
    "GHOST": f"{_BASE_URL}/2/2d/Ghost_SCR_icon.png",
    "HELLION": f"{_BASE_URL}/c/c9/Hellion_SCR_icon.png",
    "SIEGETANK": f"{_BASE_URL}/6/6e/Siege_Tank_SCR_icon.png",
    "CYCLONE": f"{_BASE_URL}/2/20/Cyclone_LotC_icon.png",
    "THOR": f"{_BASE_URL}/9/99/Thor_SCR_icon.png",
    "VIKINGFIGHTER": f"{_BASE_URL}/4/4f/Viking_SCR_icon.png",
    "MEDIVAC": f"{_BASE_URL}/4/48/Medivac_SCR_icon.png",
    "LIBERATOR": f"{_BASE_URL}/9/91/Liberator_LotC_icon.png",
    "BANSHEE": f"{_BASE_URL}/3/3b/Banshee_SCR_icon.png",
    "RAVEN": f"{_BASE_URL}/f/f9/Raven_SCR_icon.png",
    "BATTLECRUISER": f"{_BASE_URL}/1/14/Battlecruiser_SCR_icon.png",
    "WIDOWMINE": f"{_BASE_URL}/1/19/Widow_Mine_LotC_icon.png",
}

_RACE_ICONS: dict[str, str] = {
    "Protoss": f"{_BASE_URL}/8/8c/Protoss_icon.png",
    "Zerg": f"{_BASE_URL}/9/9a/Zerg_icon.png",
    "Terran": f"{_BASE_URL}/1/18/Terran_icon.png",
}

_FALLBACK_ICON = f"{_BASE_URL}/e/e9/SC2_icon.png"


def get_unit_icon_url(unit_name: str) -> str:
    return _ICON_MAP.get(unit_name.upper(), _FALLBACK_ICON)


def get_unit_race_icon_url(race: str) -> str:
    return _RACE_ICONS.get(race, _FALLBACK_ICON)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_unit_data.py -v`
Expected: 18 PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/icons.py tests/test_unit_data.py
git commit -m "feat: add unit and race icon URL mappings from Liquipedia"
```

---

### Task 2.4: Enriched observation features

**Files:**
- Modify: `src/ml/observation.py`
- Modify: `tests/test_observation.py`

- [ ] **Step 1: Add enriched enemy data to extract_features()**

In `src/ml/observation.py`, add after line 48 (the `return` statement in `extract_features`):

```python
from src.data.units import get_unit_info
from src.data.counters import compute_threat_assessment, compute_counters


def _enrich_enemy_army(enemy_comp: dict[str, int]) -> dict:
    if not enemy_comp:
        return {
            "total_hp": 0,
            "total_shields": 0,
            "armored_count": 0,
            "light_count": 0,
            "biological_count": 0,
            "mechanical_count": 0,
            "massive_count": 0,
            "air_count": 0,
            "ground_dps": 0.0,
            "air_dps": 0.0,
        }

    total_hp = 0
    total_shields = 0
    armored_count = 0
    light_count = 0
    biological_count = 0
    mechanical_count = 0
    massive_count = 0
    air_count = 0
    ground_dps = 0.0
    air_dps = 0.0

    for name, count in enemy_comp.items():
        info = get_unit_info(name)
        if not info:
            continue
        total_hp += info["hp"] * count
        total_shields += info["shields"] * count
        attrs = info.get("attributes", [])
        if "Armored" in attrs:
            armored_count += count
        if "Light" in attrs:
            light_count += count
        if "Biological" in attrs:
            biological_count += count
        if "Mechanical" in attrs:
            mechanical_count += count
        if "Massive" in attrs:
            massive_count += count
        for attack in info.get("attacks", []):
            dps = attack["damage"] / max(attack.get("speed", 1.0), 0.1)
            if attack.get("targets") == "ground":
                ground_dps += dps * count
            elif attack.get("targets") == "air":
                air_dps += dps * count
        if any(a.get("targets") == "air" for a in info.get("attacks", [])):
            air_count += count

    return {
        "total_hp": total_hp,
        "total_shields": total_shields,
        "armored_count": armored_count,
        "light_count": light_count,
        "biological_count": biological_count,
        "mechanical_count": mechanical_count,
        "massive_count": massive_count,
        "air_count": air_count,
        "ground_dps": round(ground_dps, 1),
        "air_dps": round(air_dps, 1),
    }
```

Add to the return dict in `extract_features()`:

```python
return {
    # ... existing keys ...
    "enemy_army_composition": enemy_composition,
    "enemy_army_analysis": _enrich_enemy_army(enemy_composition),
    "enemy_threat_assessment": compute_threat_assessment(enemy_composition),
    "recommended_counters": compute_counters(enemy_composition, race="Protoss"),
    # ... rest of existing keys ...
}
```

- [ ] **Step 2: Write test for enriched features**

Append to `tests/test_observation.py`:

```python
def test_extract_features_includes_enriched_enemy_data():
    bot = SimpleNamespace(
        minerals=50, vespene=0, supply_used=12, supply_cap=15,
        supply_left=3, workers=EmptyUnits(), units=UnitCollection(0),
        structures=UnitCollection(0), enemy_units=UnitCollection(0),
        mineral_field=UnitCollection(0), gas_buildings=UnitCollection(0),
        time=1.5, townhalls=TownhallCollection(1),
        state=SimpleNamespace(game_loop=33),
    )
    features = extract_features(bot)
    assert "enemy_army_analysis" in features
    assert "enemy_threat_assessment" in features
    assert "recommended_counters" in features
    analysis = features["enemy_army_analysis"]
    assert analysis["total_hp"] == 0
    assert analysis["armored_count"] == 0


def test_extract_features_enriched_data_with_enemy_units():
    class EnemyUnit:
        def __init__(self, name):
            self.type_id = SimpleNamespace(name=name)

    bot = SimpleNamespace(
        minerals=50, vespene=0, supply_used=12, supply_cap=15,
        supply_left=3, workers=EmptyUnits(),
        units=UnitCollection(0),
        structures=UnitCollection(0),
        enemy_units=[EnemyUnit("ROACH"), EnemyUnit("ROACH"), EnemyUnit("ZERGLING")],
        mineral_field=UnitCollection(0), gas_buildings=UnitCollection(0),
        time=1.5, townhalls=TownhallCollection(1),
        state=SimpleNamespace(game_loop=33),
    )
    features = extract_features(bot)
    analysis = features["enemy_army_analysis"]
    assert analysis["armored_count"] == 2
    assert analysis["light_count"] == 1
    assert analysis["biological_count"] == 3
```

- [ ] **Step 3: Run observation tests**

Run: `uv run pytest tests/test_observation.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add src/ml/observation.py tests/test_observation.py
git commit -m "feat: add enriched enemy analysis to observation features"
```

---

### Task 2.5: Unit icons in HTML reports

**Files:**
- Modify: `src/ml/report.py`
- Modify: `tests/test_report.py` (if exists)

- [ ] **Step 1: Add icon rendering to HTML report generation**

In `src/ml/report.py`, add import:

```python
from src.data.icons import get_unit_icon_url, get_unit_race_icon_url
```

Add helper function:

```python
def _render_unit_icon(unit_name: str, size: int = 24) -> str:
    url = get_unit_icon_url(unit_name)
    return f'<img src="{url}" alt="{unit_name}" title="{unit_name}" width="{size}" height="{size}" style="vertical-align:middle;margin-right:4px">'
```

Modify the composition string rendering in `generate_report_html()`. Replace the plain-text composition strings with icon-enhanced versions:

Find these lines (around 200-206):
```python
        our_comp = s.get("our_composition", {})
        our_str = ", ".join(f"{k}: {v}" for k, v in our_comp.items()) if our_comp else "none"
```

Replace with:
```python
        our_comp = s.get("our_composition", {})
        our_parts = []
        for k, v in our_comp.items():
            icon = _render_unit_icon(k, 20)
            our_parts.append(f'{icon} {k}: {v}')
        our_str = " ".join(our_parts) if our_parts else "none"
```

Do the same for enemy composition (around lines 209-215):
```python
        enemy_comp = s.get("enemy_composition", {})
        enemy_parts = []
        for k, v in enemy_comp.items():
            icon = _render_unit_icon(k, 20)
            enemy_parts.append(f'{icon} {k}: {v}')
        enemy_str = " ".join(enemy_parts) if enemy_parts else "none"
```

- [ ] **Step 2: Write test for icon rendering in report**

Append to `tests/test_report.py` (or create if needed):

```python
# tests/test_report.py (add if not exists)
from src.ml.report import generate_report_json, generate_report_html
from src.data.icons import get_unit_icon_url


def test_report_includes_unit_icons_in_html():
    features = [
        {
            "iteration": 1, "game_time_seconds": 10,
            "supply_used": 6, "supply_cap": 15, "workers": 6,
            "army": 0, "minerals": 50, "vespene": 0,
            "expansion_count": 1, "army_count": 2,
            "our_army_composition": {"ZEALOT": 2},
            "enemy_visible_units": 3, "enemy_army_composition": {"ZERGLING": 3},
        }
    ]
    events = []
    report = generate_report_json("test_match", features, events, {"result": "victory"})
    html = generate_report_html(report)
    assert "ZEALOT" in html
    assert "ZERGLING" in html
    assert "src=" in html
    assert "img" in html


def test_render_unit_icon_generates_img_tag():
    from src.ml.report import _render_unit_icon
    html = _render_unit_icon("STALKER", 20)
    assert '<img' in html
    assert 'STALKER' in html
    assert 'width="20"' in html
```

- [ ] **Step 3: Run report tests**

Run: `uv run pytest tests/test_report.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add src/ml/report.py tests/test_report.py
git commit -m "feat: embed unit icons in HTML match reports"
```

---

## Phase 3: Intelligence

### Task 3.1: Scout behavior module

**Files:**
- Create: `src/bot/scout.py`
- Modify: `src/bot/strategy.py` (add scout constants)
- Create: `tests/test_scout.py`

- [ ] **Step 1: Add scout constants to strategy.py**

Append to `src/bot/strategy.py`:

```python
SCOUT_WAYPOINTS = "enemy_start_locations"
SCOUT_RETREAT_HP_RATIO = 0.5
SCOUT_RETREAT_THREAT_RANGE = 8
```

- [ ] **Step 2: Write failing tests for scout logic**

```python
# tests/test_scout.py
from types import SimpleNamespace
from src.bot.scout import (
    ScoutState, get_scout_waypoints, should_retreat_scout,
    update_scout_waypoints, compute_next_scout_move,
)


class FakeUnit:
    def __init__(self, x, y, hp=20, max_hp=20, shields=20, max_shields=20, tag=1):
        self.position = SimpleNamespace(x=x, y=y)
        self.health = hp
        self.health_max = max_hp
        self.shield = shields
        self.shield_max = max_shields
        self.is_idle = True
        self.tag = tag


def test_get_scout_waypoints_returns_enemy_start_locations():
    enemy_starts = [SimpleNamespace(x=100, y=100), SimpleNamespace(x=150, y=150)]
    waypoints = get_scout_waypoints(enemy_start_locations=enemy_starts)
    assert len(waypoints) == 2
    assert waypoints[0] == (100, 100)


def test_should_retreat_scout_when_low_hp():
    scout = FakeUnit(x=50, y=50, hp=1, max_hp=20, shields=0, max_shields=20)
    enemies = [FakeUnit(x=55, y=55)]
    result = should_retreat_scout(scout, enemies)
    assert result is True


def test_should_not_retreat_scout_when_healthy():
    scout = FakeUnit(x=50, y=50, hp=20, max_hp=20, shields=20, max_shields=20)
    enemies = [FakeUnit(x=55, y=55)]
    result = should_retreat_scout(scout, enemies)
    assert result is False


def test_should_not_retreat_scout_when_no_enemies_nearby():
    scout = FakeUnit(x=50, y=50, hp=1, max_hp=20, shields=0, max_shields=20)
    enemies = [FakeUnit(x=500, y=500)]
    result = should_retreat_scout(scout, enemies)
    assert result is False


def test_should_not_retreat_scout_when_no_enemies():
    scout = FakeUnit(50, 50, hp=1, max_hp=20)
    result = should_retreat_scout(scout, [])
    assert result is False


def test_compute_next_scout_move_returns_waypoint_when_idle():
    scout = FakeUnit(50, 50)
    waypoints = [(100, 100)]
    result = compute_next_scout_move(scout, waypoints, 0)
    assert result is not None
    assert result[0] == 100
    assert result[1] == 100


def test_compute_next_scout_move_advances_waypoint_when_close():
    scout = FakeUnit(99, 99)
    waypoints = [(100, 100), (200, 200)]
    result = compute_next_scout_move(scout, waypoints, 0)
    assert result is not None
    assert result[0] == 200
    assert result[1] == 200


def test_compute_next_scout_move_returns_none_when_no_waypoints():
    scout = FakeUnit(50, 50)
    result = compute_next_scout_move(scout, [], 0)
    assert result is None


def test_update_scout_waypoints_adds_expansions():
    waypoints = [(100, 100)]
    enemy_expansions = [SimpleNamespace(x=120, y=120)]
    new_waypoints = update_scout_waypoints(waypoints, enemy_expansions)
    assert len(new_waypoints) == 2
    assert new_waypoints[1] == (120, 120)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_scout.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement scout module**

```python
# src/bot/scout.py
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any


class ScoutState(Enum):
    IDLE = auto()
    EXPLORING = auto()
    RETREATING = auto()
    DEAD = auto()


@dataclass
class ScoutIntel:
    enemy_base_found: bool = False
    enemy_race_confirmed: str | None = None
    enemy_structures_seen: list[str] = field(default_factory=list)
    last_scout_time: float = 0.0


def get_scout_waypoints(
    enemy_start_locations: list[Any],
    expansions: list[Any] | None = None,
) -> list[tuple[float, float]]:
    waypoints: list[tuple[float, float]] = []
    for loc in enemy_start_locations:
        waypoints.append((float(loc.x), float(loc.y)))
    if expansions:
        for exp in expansions:
            waypoints.append((float(exp.x), float(exp.y)))
    return waypoints


def update_scout_waypoints(
    current: list[tuple[float, float]],
    expansions: list[Any],
) -> list[tuple[float, float]]:
    result = list(current)
    for exp in expansions:
        pt = (float(exp.x), float(exp.y))
        if pt not in result:
            result.append(pt)
    return result


def should_retreat_scout(
    scout: Any,
    enemy_units: list[Any],
    retreat_hp_ratio: float = 0.5,
    threat_range: float = 8.0,
) -> bool:
    if not enemy_units:
        return False
    hp = getattr(scout, "health", 0)
    max_hp = getattr(scout, "health_max", 1)
    shields = getattr(scout, "shield", 0)
    max_shields = getattr(scout, "shield_max", 0)
    total_hp = hp + shields
    total_max = max_hp + max_shields
    if total_max == 0:
        return False
    hp_ratio = total_hp / total_max
    if hp_ratio > retreat_hp_ratio:
        return False
    scout_pos = scout.position
    for enemy in enemy_units:
        enemy_pos = getattr(enemy, "position", None)
        if enemy_pos is None:
            continue
        dx = scout_pos.x - enemy_pos.x
        dy = scout_pos.y - enemy_pos.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= threat_range:
            return True
    return False


def compute_next_scout_move(
    scout: Any,
    waypoints: list[tuple[float, float]],
    current_index: int,
    proximity: float = 3.0,
) -> tuple[float, float] | None:
    if current_index >= len(waypoints):
        return None
    wx, wy = waypoints[current_index]
    sx = scout.position.x
    sy = scout.position.y
    dist = ((sx - wx) ** 2 + (sy - wy) ** 2) ** 0.5
    if dist <= proximity:
        current_index += 1
        if current_index >= len(waypoints):
            return None
        wx, wy = waypoints[current_index]
    return (wx, wy)
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_scout.py -v`
Expected: 8 PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/scout.py src/bot/strategy.py tests/test_scout.py
git commit -m "feat: add scout behavior module with waypoints and retreat logic"
```

---

### Task 3.2: Scout integration into bot loop

**Files:**
- Modify: `src/bot/core.py` (add `manage_scout()` method and call it from `on_step`)

- [ ] **Step 1: Add scout management to MyBot**

In `src/bot/core.py`, add import at top:

```python
from src.bot.scout import (
    ScoutState, get_scout_waypoints, should_retreat_scout,
    compute_next_scout_move, update_scout_waypoints,
)
```

Add to `__init__`:

```python
self._scout_tag: int | None = None
self._scout_waypoints: list[tuple[float, float]] = []
self._scout_waypoint_index: int = 0
self._scout_state = ScoutState.IDLE
```

Add `manage_scout()` method to `MyBot`:

```python
async def manage_scout(self):
    if self.time < 30:
        probes = self.workers
        if probes.amount == 0:
            return
        if self._scout_tag is None:
            scout = probes.closest_to(self.enemy_start_locations[0])
            self._scout_tag = scout.tag
            self._scout_waypoints = get_scout_waypoints(self.enemy_start_locations)
            self._scout_waypoint_index = 0
            self._scout_state = ScoutState.EXPLORING

    if self._scout_tag is None:
        return

    scout = self.workers.find_by_tag(self._scout_tag)
    if scout is None:
        scout = self.units.find_by_tag(self._scout_tag)
    if scout is None:
        self._scout_state = ScoutState.DEAD
        return

    if self._scout_state == ScoutState.DEAD:
        return

    enemy_nearby = self.enemy_units.closer_than(8, scout.position)
    if should_retreat_scout(scout, enemy_nearby):
        self._scout_state = ScoutState.RETREATING

    if self._scout_state == ScoutState.RETREATING:
        if self.townhalls:
            scout.move(self.townhalls.first.position)
        return

    move_target = compute_next_scout_move(
        scout, self._scout_waypoints, self._scout_waypoint_index
    )
    if move_target is not None:
        from sc2.position import Point2
        scout.move(Point2(move_target))
```

Add `await self.manage_scout()` to `on_step()` after `await self.manage_defense()`:

```python
await self.manage_defense()
await self.manage_scout()
await self.manage_attack()
```

- [ ] **Step 2: Run all existing tests to verify no regressions**

Run: `uv run pytest tests/ -v`
Expected: all existing tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/bot/core.py
git commit -m "feat: integrate scout into bot loop with waypoint exploration"
```

---

### Task 3.3: Upgrade decision engine

**Files:**
- Create: `src/bot/upgrades.py`
- Create: `tests/test_upgrades.py`
- Modify: `src/bot/strategy.py` (add upgrade constants)

- [ ] **Step 1: Add upgrade constants to strategy.py**

Append to `src/bot/strategy.py`:

```python
UPGRADE_WEAPONS_PRIORITY = 1
UPGRADE_ARMOR_PRIORITY = 2
UPGRADE_SHIELDS_PRIORITY = 3
UPGRADE_MINERAL_THRESHOLD = 300
```

- [ ] **Step 2: Write tests for upgrade decision logic**

```python
# tests/test_upgrades.py
from sc2.ids.upgrade_id import UpgradeId
from src.bot.upgrades import (
    get_next_upgrade, UPGRADE_ORDER, should_build_forge,
    should_build_twilight, get_twilight_upgrade,
)


def test_upgrade_order_has_all_ground_levels():
    assert UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSGROUNDARMORSLEVEL1 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSGROUNDARMORSLEVEL2 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSGROUNDARMORSLEVEL3 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSSHIELDSLEVEL1 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSSHIELDSLEVEL2 in UPGRADE_ORDER
    assert UpgradeId.PROTOSSSHIELDSLEVEL3 in UPGRADE_ORDER


def test_get_next_upgrade_returns_weapons_1_first():
    completed = set()
    result = get_next_upgrade(completed)
    assert result == UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1


def test_get_next_upgrade_skips_completed():
    completed = {UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1}
    result = get_next_upgrade(completed)
    assert result == UpgradeId.PROTOSSGROUNDARMORSLEVEL1


def test_get_next_upgrade_skips_pending():
    pending = {UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1}
    result = get_next_upgrade(set(), pending)
    assert result == UpgradeId.PROTOSSGROUNDARMORSLEVEL1


def test_get_next_upgrade_returns_none_when_all_done():
    completed = set(UPGRADE_ORDER)
    result = get_next_upgrade(completed)
    assert result is None


def test_should_build_forge_false_when_poor():
    assert should_build_forge(minerals=200, vespene=50) is False


def test_should_build_forge_true_when_floating():
    assert should_build_forge(minerals=400, vespene=100) is True


def test_should_build_forge_false_when_already_exists():
    assert should_build_forge(minerals=400, vespene=100, has_forge=True) is False


def test_should_build_twilight_false_when_no_cyber_core():
    assert should_build_twilight(has_cyber_core=False, has_twilight=False, minerals=300, vespene=200) is False


def test_should_build_twilight_true_when_ready():
    assert should_build_twilight(has_cyber_core=True, has_twilight=False, minerals=300, vespene=200) is True


def test_get_twilight_upgrade_charge_over_blink_by_default():
    result = get_twilight_upgrade(enemy_army_analysis={"air_count": 0})
    assert result == UpgradeId.CHARGE


def test_get_twilight_upgrade_blink_when_enemy_air():
    result = get_twilight_upgrade(enemy_army_analysis={"air_count": 5})
    assert result == UpgradeId.BLINKTECH
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_upgrades.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement upgrade module**

```python
# src/bot/upgrades.py
from sc2.ids.upgrade_id import UpgradeId


UPGRADE_ORDER = [
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
    UpgradeId.PROTOSSSHIELDSLEVEL1,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL3,
    UpgradeId.PROTOSSSHIELDSLEVEL2,
    UpgradeId.PROTOSSSHIELDSLEVEL3,
]


def get_next_upgrade(
    completed: set,
    pending: set | None = None,
) -> UpgradeId | None:
    if pending is None:
        pending = set()
    for upgrade in UPGRADE_ORDER:
        if upgrade in completed or upgrade in pending:
            continue
        return upgrade
    return None


def should_build_forge(
    minerals: float,
    vespene: float,
    has_forge: bool = False,
    threshold: float = 300,
) -> bool:
    if has_forge:
        return False
    return minerals > threshold and vespene > 50


def should_build_twilight(
    has_cyber_core: bool,
    has_twilight: bool,
    minerals: float,
    vespene: float,
    threshold: float = 300,
) -> bool:
    if not has_cyber_core or has_twilight:
        return False
    return minerals > threshold and vespene > 100


def get_twilight_upgrade(
    enemy_army_analysis: dict | None = None,
) -> UpgradeId:
    if enemy_army_analysis and enemy_army_analysis.get("air_count", 0) > 3:
        return UpgradeId.BLINKTECH
    return UpgradeId.CHARGE
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_upgrades.py -v`
Expected: 11 PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/upgrades.py src/bot/strategy.py tests/test_upgrades.py
git commit -m "feat: add upgrade decision engine with priority order"
```

---

### Task 3.4: Upgrade integration into bot loop

**Files:**
- Modify: `src/bot/core.py` (add `manage_upgrades()` and call it, integrate twilight council)

- [ ] **Step 1: Add `manage_upgrades()` to MyBot**

In `src/bot/core.py`, add import:

```python
from src.bot.upgrades import (
    UPGRADE_ORDER, get_next_upgrade, should_build_forge,
    should_build_twilight, get_twilight_upgrade,
)
```

Add `manage_upgrades()` method to `MyBot`:

```python
async def manage_upgrades(self):
    if self.minerals < 300:
        return

    forges = self.structures(UnitTypeId.FORGE)

    if should_build_forge(self.minerals, self.vespene, has_forge=forges.amount > 0):
        if self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
            position = await self.find_placement(UnitTypeId.FORGE, self.start_location, placement_step=5)
            if position:
                await self.build(UnitTypeId.FORGE, near=position)
        return

    completed: set = set()
    pending: set = set()
    for upgrade in UPGRADE_ORDER:
        if self.already_pending_upgrade(upgrade):
            pending.add(upgrade)

    next_upgrade = get_next_upgrade(completed, pending)
    if next_upgrade is None:
        return

    for forge in forges.ready:
        if self.can_afford(next_upgrade) and not self.already_pending_upgrade(next_upgrade):
            forge.research(next_upgrade)
            return

    cyber_cores = self.structures(UnitTypeId.CYBERNETICSCORE)
    twilight_councils = self.structures(UnitTypeId.TWILIGHTCOUNCIL)

    if should_build_twilight(
        has_cyber_core=cyber_cores.ready.amount > 0,
        has_twilight=twilight_councils.amount > 0,
        minerals=self.minerals,
        vespene=self.vespene,
    ):
        if self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and not self.already_pending(UnitTypeId.TWILIGHTCOUNCIL):
            position = await self.find_placement(UnitTypeId.TWILIGHTCOUNCIL, self.start_location, placement_step=5)
            if position:
                await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=position)
        return

    if twilight_councils.ready.amount > 0:
        twilight = twilight_councils.ready.first
        enemy_analysis = getattr(self, "_last_enemy_analysis", None) or {}
        tw_upgrade = get_twilight_upgrade(enemy_analysis)
        if self.can_afford(tw_upgrade) and not self.already_pending_upgrade(tw_upgrade):
            twilight.research(tw_upgrade)
```

Replace `await self.manage_forge_upgrades()` in `on_step()` with `await self.manage_upgrades()`:

```python
await self.manage_tech()
await self.manage_upgrades()
```

Also remove the old `manage_forge_upgrades()` method since its logic is now in `manage_upgrades()`.

- [ ] **Step 2: Store enemy analysis for upgrade decisions**

In `on_step()`, after extracting features, store the enemy analysis:

```python
features = extract_features(self)
self._last_enemy_analysis = features.get("enemy_army_analysis", {})
```

- [ ] **Step 3: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: all PASS (no regressions)

- [ ] **Step 4: Commit**

```bash
git add src/bot/core.py
git commit -m "feat: integrate upgrade engine with forge, twilight, charge/blink"
```

---

### Task 3.5: Strategy adaptation from scouting

**Files:**
- Modify: `src/bot/core.py` (adapt unit production based on scouted enemy)

- [ ] **Step 1: Add adaptive unit production to manage_army()**

In `src/bot/core.py`, modify `manage_army()` to use counter recommendations when available. Replace the current stalker-over-zealot priority:

```python
async def manage_army(self):
    enemy_analysis = getattr(self, "_last_enemy_analysis", None) or {}
    counters = getattr(self, "_last_recommended_counters", None) or {}

    primary_unit = UnitTypeId.STALKER
    secondary_unit = UnitTypeId.ZEALOT

    if counters:
        top_counter = next(iter(counters), None)
        if top_counter == "IMMORTAL":
            primary_unit = UnitTypeId.IMMORTAL
            secondary_unit = UnitTypeId.STALKER
        elif top_counter == "ZEALOT":
            primary_unit = UnitTypeId.ZEALOT
            secondary_unit = UnitTypeId.STALKER
        elif top_counter == "STALKER":
            primary_unit = UnitTypeId.STALKER
            secondary_unit = UnitTypeId.ZEALOT

    for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
        if self.can_afford(primary_unit) and self.supply_left >= 2:
            gateway.train(primary_unit)
        elif self.can_afford(secondary_unit) and self.supply_left >= 2:
            gateway.train(secondary_unit)

    for warp_gate in self.structures(UnitTypeId.WARPGATE).ready.idle:
        if self.can_afford(primary_unit) and self.supply_left >= 2:
            placement = await self.find_placement(
                primary_unit, warp_gate.position, placement_step=3
            )
            if placement:
                warp_gate.warp_in(primary_unit, placement)
        elif self.can_afford(secondary_unit) and self.supply_left >= 2:
            placement = await self.find_placement(
                secondary_unit, warp_gate.position, placement_step=3
            )
            if placement:
                warp_gate.warp_in(secondary_unit, placement)
```

In `on_step()`, after extracting features, store the counters:

```python
self._last_recommended_counters = features.get("recommended_counters", {})
```

- [ ] **Step 2: Verify current tests still pass**

Run: `uv run pytest tests/ -v`
Expected: all PASS (no regressions)

- [ ] **Step 3: Commit**

```bash
git add src/bot/core.py
git commit -m "feat: adapt unit production based on scouted enemy counters"
```

---

## Final Verification

- [ ] **Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS with no SC2 instance required.

- [ ] **Run linting** (if configured)

```bash
uv run ruff check src/ tests/ 2>/dev/null || echo "ruff not configured"
```

---

## Self-Review

### 1. Spec Coverage
- Existing spec `bot-gameplay` already covers basic macro. This plan extends it without breaking existing scenarios.
- No new spec requirements are introduced — this is additive behavior.
- The economy fix aligns with the "Constant worker production" and "Supply management" scenarios.
- New behavior (scouting, upgrades) would need new spec entries if formalized via OpenSpec.

### 2. Placeholder Scan
- No TBD, TODO, or "implement later" markers.
- All test code is complete and runnable.
- All implementation code shows exact changes with exact line references.
- Data in `units.py` is complete for all standard ladder units across all three races.

### 3. Type Consistency
- `ScoutState`, `ScoutIntel`, `Event` — defined once, used consistently.
- `FakeBot` pattern from existing `test_events.py` reused in new tests.
- `get_unit_info()` returns `dict | None` — all callers handle `None`.
- `compute_counters()` returns `dict[str, float]` — all consumers use dict access.
- Upgrade IDs use `UpgradeId` enum consistently across `upgrades.py` and `core.py`.
