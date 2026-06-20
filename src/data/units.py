"""
Static unit property database for StarCraft II.

Data sourced from game data. Each entry maps UnitTypeId name -> properties.
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
