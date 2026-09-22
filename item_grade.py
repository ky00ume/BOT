"""아이템 전반에서 공유하는 보상/재료 등급 규칙."""

GRADE_ORDER = ("Normal", "Rare", "Epic", "Legendary")
GRADE_LABEL = {
    "Normal": "일반",
    "Rare": "희귀",
    "Epic": "영웅",
    "Legendary": "전설",
}
GRADE_ICON = {
    "Normal": "⚬",
    "Rare": "◆",
    "Epic": "❖",
    "Legendary": "✦",
}


def normalize_grade(grade: str | None) -> str:
    return grade if grade in GRADE_ORDER else "Normal"


def item_grade(item_id: str, items: dict | None = None) -> str:
    if items is None:
        from items import ALL_ITEMS
        items = ALL_ITEMS
    return normalize_grade(items.get(item_id, {}).get("grade"))


def grade_display(grade: str | None) -> str:
    grade = normalize_grade(grade)
    return f"{GRADE_ICON[grade]} {GRADE_LABEL[grade]}"
