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
    threshold: float = 500,
) -> bool:
    if has_forge:
        return False
    return minerals + vespene > threshold


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
