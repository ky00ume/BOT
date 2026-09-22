"""비전의 탑 수서 발전기와 생활 설비의 최소 progression 규칙."""
from __future__ import annotations

SUSSUR_BLOOM_ID = "sussur_bloom"

FACILITIES = {
    "lift": {"name": "승강기", "storage_bonus": 0, "cost": {}},
    "storage": {"name": "하층 보관 설비", "storage_bonus": 40, "cost": {"iron_ore": 3, "spider_web": 2}},
    "pantry": {"name": "식재료 보관 설비", "storage_bonus": 20, "cost": {"iron_ore": 2, "herb": 3}},
    "alchemy": {"name": "연금술 작업 설비", "storage_bonus": 0, "cost": {"mp_crystal": 1, "iron_ore": 2}},
    "gear_storage": {"name": "장비 보관 설비", "storage_bonus": 40, "cost": {"iron_ore": 4, "hard_horn": 1}},
}

DEFAULT_TOWER_STORAGE_SLOTS = 120


def ensure_tower_state(player) -> dict:
    state = getattr(player, "tower_state", None)
    if not isinstance(state, dict):
        state = {}
    state.setdefault("generator_online", False)
    state.setdefault("facilities", {})
    player.tower_state = state
    return state


def restore_generator(player) -> bool:
    """수서 꽃 하나를 소비해 발전기를 복구한다. 이미 복구된 경우 소비하지 않는다."""
    state = ensure_tower_state(player)
    if state["generator_online"]:
        return False
    if getattr(player, "inventory", {}).get(SUSSUR_BLOOM_ID, 0) < 1:
        return False
    if not player.remove_item(SUSSUR_BLOOM_ID, 1):
        return False
    state["generator_online"] = True
    # 원작의 탑 복구 감각을 살려 승강기는 발전기 복구와 함께 깨어난다.
    state["facilities"]["lift"] = True
    return True


def facility_online(player, facility: str) -> bool:
    state = ensure_tower_state(player)
    return bool(state["generator_online"] and state["facilities"].get(facility, False))


def facility_cost(facility: str) -> dict[str, int]:
    return dict(FACILITIES.get(facility, {}).get("cost", {}))


def can_restore_facility(player, facility: str) -> bool:
    if facility not in FACILITIES or facility == "lift":
        return False
    state = ensure_tower_state(player)
    if not state["generator_online"] or state["facilities"].get(facility):
        return False
    inv = getattr(player, "inventory", {})
    return all(inv.get(item_id, 0) >= count for item_id, count in facility_cost(facility).items())


def restore_facility(player, facility: str) -> bool:
    """동력이 들어온 뒤 필요한 휴대 재료를 소비해 설비를 복구한다."""
    if not can_restore_facility(player, facility):
        return False
    for item_id, count in facility_cost(facility).items():
        if not player.remove_item(item_id, count):
            return False
    ensure_tower_state(player)["facilities"][facility] = True
    recalculate_storage(player)
    return True


def recalculate_storage(player) -> int:
    state = ensure_tower_state(player)
    total = DEFAULT_TOWER_STORAGE_SLOTS
    if state["generator_online"]:
        for key, data in FACILITIES.items():
            if state["facilities"].get(key):
                total += data["storage_bonus"]
    player.home_storage_slots = total
    return total
