"""items.py — 아이템 데이터 모듈

정적 아이템 데이터는 data/items.json 에서 로드한다.
BAGS, COSTUME_ITEMS, SNACK_ITEMS 등 다른 모듈에서 관리되는 항목은
기존과 동일하게 각 모듈에서 임포트하여 ALL_ITEMS에 병합한다.
"""
import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "items.json"

with _DATA_PATH.open(encoding="utf-8") as _f:
    _data = json.load(_f)

WEAPONS: dict = _data["WEAPONS"]
ARMORS: dict = _data["ARMORS"]
CONSUMABLES: dict = _data["CONSUMABLES"]
GATHERING_ITEMS: dict = _data["GATHERING_ITEMS"]
LOOT_ITEMS: dict = _data["LOOT_ITEMS"]
FISH_ITEMS: dict = _data["FISH_ITEMS"]
COOKED_DISHES: dict = _data["COOKED_DISHES"]
DROP_ITEMS: dict = _data["DROP_ITEMS"]
INGREDIENTS: dict = _data["INGREDIENTS"]
BAR_ITEMS: dict = _data["BAR_ITEMS"]
NEW_ORE_ITEMS: dict = _data["NEW_ORE_ITEMS"]
SPECIAL_ITEMS: dict = _data["SPECIAL_ITEMS"]
TOOLS: dict = _data["TOOLS"]
MATERIALS: dict = _data["MATERIALS"]
WALK_MATERIALS: dict = _data["WALK_MATERIALS"]
GROCERIES: dict = _data["GROCERIES"]
WOODCUT_ITEMS: dict = _data["WOODCUT_ITEMS"]
STORY_QUEST_ITEMS: dict = _data["STORY_QUEST_ITEMS"]
QUEST_DELIVER_ITEMS: dict = _data["QUEST_DELIVER_ITEMS"]
SKILL_BOOKS: dict = _data["SKILL_BOOKS"]
SPECIAL_USE_ITEMS: dict = _data["SPECIAL_USE_ITEMS"]
TINKER_BELL_ITEMS: dict = _data["TINKER_BELL_ITEMS"]

ALL_ITEMS: dict = {
    **WEAPONS,
    **ARMORS,
    **CONSUMABLES,
    **GATHERING_ITEMS,
    **LOOT_ITEMS,
    **FISH_ITEMS,
    **COOKED_DISHES,
    **DROP_ITEMS,
    **INGREDIENTS,
    **BAR_ITEMS,
    **NEW_ORE_ITEMS,
    **SPECIAL_ITEMS,
    **TOOLS,
    **MATERIALS,
    **GROCERIES,
    **WOODCUT_ITEMS,
    **WALK_MATERIALS,
    **STORY_QUEST_ITEMS,
    **QUEST_DELIVER_ITEMS,
    **SKILL_BOOKS,
    **SPECIAL_USE_ITEMS,
    **TINKER_BELL_ITEMS,
}

# ─── 가방 ──────────────────────────────────────────────────────────────────
# BAGS는 database.py에서 관리하며, JSON 로딩 이후에 임포트한다.
from database import BAGS  # noqa: E402
ALL_ITEMS.update(BAGS)

# ─── 의장·간식 아이템 ─────────────────────────────────────────────────────────
# COSTUME_ITEMS/SNACK_ITEMS는 costume_data.py에서 관리하며, JSON 로딩 이후에 임포트한다.
from costume_data import COSTUME_ITEMS, SNACK_ITEMS  # noqa: E402
ALL_ITEMS.update(COSTUME_ITEMS)
ALL_ITEMS.update(SNACK_ITEMS)
