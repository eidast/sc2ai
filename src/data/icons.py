"""
Unit icon generation using inline SVGs.

Each icon is a small colored circle with the unit's initial letter.
Race colors: Protoss = gold, Zerg = purple, Terran = orange.
No external dependencies — works fully offline.
"""

from src.data.units import get_unit_info

_RACE_COLORS: dict[str, str] = {
    "Protoss": "#f5c542",
    "Zerg": "#9c27b0",
    "Terran": "#ff6d00",
}
_FALLBACK_COLOR = "#555555"


def _get_unit_initial(unit_name: str) -> str:
    name = unit_name.upper()
    if name == "HIGHTEMPLAR":
        return "HT"
    if name == "DARKTEMPLAR":
        return "DT"
    if name == "SIEGETANK":
        return "ST"
    if name == "BATTLECRUISER":
        return "BC"
    if name == "WARPPRISM":
        return "WP"
    if name == "VIKINGFIGHTER":
        return "VK"
    if name == "SWARMHOSTMP":
        return "SH"
    if name == "WIDOWMINE":
        return "WM"
    if name == "MOTHERSHIP":
        return "MS"
    return name[0]


def render_unit_icon_svg(unit_name: str, size: int = 24) -> str:
    info = get_unit_info(unit_name)
    race = info["race"] if info else "Unknown"
    color = _RACE_COLORS.get(race, _FALLBACK_COLOR)
    initial = _get_unit_initial(unit_name)
    font_size = size * 0.55
    if len(initial) == 2:
        font_size = size * 0.4

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{size/2 - 1}" fill="{color}" '
        f'stroke="#444" stroke-width="1"/>'
        f'<text x="{size/2}" y="{size*0.68}" text-anchor="middle" '
        f'fill="#1a1a2e" font-size="{font_size}" font-weight="bold" '
        f'font-family="monospace">{initial}</text>'
        f'</svg>'
    )


def get_unit_icon_html(unit_name: str, size: int = 24) -> str:
    svg = render_unit_icon_svg(unit_name, size)
    return f'{svg}'


def get_unit_icon_data_uri(unit_name: str, size: int = 24) -> str:
    import base64
    svg = render_unit_icon_svg(unit_name, size)
    encoded = base64.b64encode(svg.encode()).decode()
    return f'data:image/svg+xml;base64,{encoded}'
