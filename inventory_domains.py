"""휴대품/장비/전리품/비전의 탑 보관함의 최소 도메인 규칙.

기존 ``Player.inventory`` 는 호환성을 위해 휴대품 가방으로 유지한다.
새 보관 영역은 Player에 별도 dict로 붙여 점진적으로 UI/전투/귀가 흐름과 연결한다.
"""
from __future__ import annotations

from items import ALL_ITEMS

EQUIPMENT_TYPES = {"weapon", "armor"}
DEFAULT_GEAR_BAG_SLOTS = 8
DEFAULT_HOME_STORAGE_SLOTS = 120


def is_equipment(item_id: str) -> bool:
    return ALL_ITEMS.get(item_id, {}).get("type") in EQUIPMENT_TYPES


def add_stack(container: dict[str, int], item_id: str, count: int = 1) -> bool:
    if count <= 0:
        return False
    container[item_id] = container.get(item_id, 0) + count
    return True


def remove_stack(container: dict[str, int], item_id: str, count: int = 1) -> bool:
    if count <= 0 or container.get(item_id, 0) < count:
        return False
    container[item_id] -= count
    if container[item_id] <= 0:
        del container[item_id]
    return True


def unique_slots(container: dict[str, int]) -> int:
    return len(container)
