"""collection.py — 수집일기(도감) 시스템"""
import json
import os

COLLECTION_FILE = os.path.join(os.path.dirname(__file__), "collections.json")

CATEGORY_ICONS = {
    "낚시":  "🎣",
    "요리":  "🍳",
    "채집":  "🌿",
    "채광":  "⛏️",
}


class CollectionManager:
    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        if not os.path.isfile(COLLECTION_FILE):
            self._data = {}
            return
        try:
            with open(COLLECTION_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            with open(COLLECTION_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register(self, category: str, item_id: str, name: str, grade: str = "Normal", size: float = 0.0) -> tuple[bool, int]:
        """
        도감에 아이템을 등록합니다.
        Returns:
            (is_new: bool, total_count: int)
            is_new=True이면 이번이 첫 등록.
        """
        if category not in self._data:
            self._data[category] = {}

        cat = self._data[category]
        is_new = item_id not in cat

        if is_new:
            cat[item_id] = {
                "name":      name,
                "grade":     grade,
                "best_size": size,
                "count":     1,
            }
        else:
            cat[item_id]["count"] = cat[item_id].get("count", 0) + 1
            if size > cat[item_id].get("best_size", 0):
                cat[item_id]["best_size"] = size

        self._save()
        return is_new, cat[item_id]["count"]

    def get_progress(self, category: str, total_possible: int) -> tuple[int, int, float]:
        """(collected, total_possible, percent) 반환"""
        collected = len(self._data.get(category, {}))
        pct = (collected / total_possible * 100) if total_possible > 0 else 0.0
        return collected, total_possible, pct

    def show_collection(self, category: str) -> str:
        from ui_theme import C, ansi, header_box, divider, section, GRADE_ICON_PLAIN
        icon = CATEGORY_ICONS.get(category, "📖")
        lines = [header_box(f"{icon} {category} 도감")]

        cat_data = self._data.get(category, {})
        if not cat_data:
            lines.append(f"  {C.DARK}(아직 등록된 항목이 없슴미댜!){C.R}")
            return ansi("\n".join(lines))

        grade_order = {"Legendary": 0, "Epic": 1, "Rare": 2, "Normal": 3}
        items_sorted = sorted(
            cat_data.items(),
            key=lambda x: (grade_order.get(x[1].get("grade", "Normal"), 9), x[1].get("name", ""))
        )

        for item_id, info in items_sorted:
            grade = info.get("grade", "Normal")
            grade_icon = GRADE_ICON_PLAIN.get(grade, "⚬")
            name = info.get("name", item_id)
            count = info.get("count", 1)
            best_size = info.get("best_size", 0)
            size_str = f" 최대 {best_size:.1f}cm" if best_size > 0 else ""
            lines.append(
                f"  {grade_icon} {C.WHITE}{name}{C.R}  "
                f"{C.DARK}x{count}{size_str}{C.R}"
            )

        lines.append(divider())
        lines.append(f"  {C.GOLD}총 {len(cat_data)}종 수집완료{C.R}")
        return ansi("\n".join(lines))

    def show_all_categories(self) -> str:
        from ui_theme import C, ansi, header_box, divider
        lines = [header_box("📖 수집 도감")]
        for cat, icon in CATEGORY_ICONS.items():
            count = len(self._data.get(cat, {}))
            lines.append(f"  {icon} {C.WHITE}{cat} 도감{C.R}  {C.GOLD}{count}종 수집{C.R}")
        lines.append(divider())
        lines.append(f"  {C.GREEN}/도감 [카테고리]{C.R} 로 상세 확인!")
        return ansi("\n".join(lines))

    def to_dict(self) -> dict:
        return self._data

    def from_dict(self, data: dict):
        self._data = data
        self._save()


collection_manager = CollectionManager()
