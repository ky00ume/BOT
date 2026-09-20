"""Canonical player-facing places for Churider's Underdark home region.

Legacy storage keys (for example ``마을``) stay unchanged so existing saves and
content tables remain compatible. UI and new events should use these names.
"""
ARCANE_TOWER = "비전의 탑"
ARCANE_TOWER_ROOM = "비전의 탑 · 츄라이더의 방"
MYCONID_COLONY = "마이코니드 군락"
UNDERDARK = "언더다크"

# Existing save/movement key -> canonical display name.
LOCATION_DISPLAY_NAMES = {
    "마을": MYCONID_COLONY,
}


def display_location(location: str | None) -> str:
    if not location:
        return ARCANE_TOWER
    return LOCATION_DISPLAY_NAMES.get(location, location)
