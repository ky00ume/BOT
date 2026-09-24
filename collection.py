"""collection.py — 수집일기(도감) 시스템"""
import json
import os
from utils.logger import setup_logger

logger = setup_logger('collection')

COLLECTION_FILE = os.path.join(os.path.dirname(__file__), "collections.json")

CATEGORY_ICONS = {
    "낚시":  "🎣",
    "요리":  "🍳",
    "채집":  "🌿",
    "채광":  "⛏️",
    "벌목":  "🪓",
    "제련":  "🔥",
    "몬스터": "🐾",
}

CATEGORY_MILESTONES = {
    "낚시": (5, 12, 22),
    "요리": (10, 25, 47),
    "채집": (10, 30, 53),
    "채광": (5, 10, 18),
    "벌목": (3, 5, 7),
    "제련": (3, 6, 9),
    "몬스터": (5, 10, 17),
}

CATEGORY_REWARD_LABELS = {
    "낚시": "낚시 숙련", "요리": "요리 연구", "채집": "야외 관찰",
    "채광": "광물 연구", "벌목": "목재 연구", "제련": "금속 연구", "몬스터": "생태 연구",
}

COLLECTION_MILESTONES = (
    {"count": 5, "label": "견습 수집가", "bonus": "기력 최대치 +2", "max_energy": 2},
    {"count": 10, "label": "수집가", "bonus": "DEX +1", "stat": "dex", "value": 1},
    {"count": 20, "label": "탐구가", "bonus": "기력 최대치 +3", "max_energy": 3},
    {"count": 30, "label": "박물학도", "bonus": "LUCK +1", "stat": "luck", "value": 1},
    {"count": 50, "label": "박물학자", "bonus": "DEX +1 · LUCK +1", "stats": {"dex": 1, "luck": 1}},
    {"count": 75, "label": "대수집가", "bonus": "기력 최대치 +5", "max_energy": 5},
    {"count": 100, "label": "세계의 기록자", "bonus": "STR/INT/DEX/WILL/LUCK +1", "stats": {"str": 1, "int": 1, "dex": 1, "will": 1, "luck": 1}},
)


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
            logger.warning('collection: _load 실패 — 빈 도감으로 초기화', exc_info=True)
            self._data = {}

    def _save(self):
        try:
            with open(COLLECTION_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.error('collection: _save 실패', exc_info=True)

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

    def total_unique(self) -> int:
        return sum(len(items) for items in self._data.values() if isinstance(items, dict))

    def milestone_status(self) -> list[dict]:
        total = self.total_unique()
        return [{**m, "unlocked": total >= m["count"]} for m in COLLECTION_MILESTONES]

    def next_milestone(self) -> dict | None:
        total = self.total_unique()
        return next((m for m in COLLECTION_MILESTONES if total < m["count"]), None)

    def apply_player_bonuses(self, player) -> list[str]:
        """현재 도감 종 수에 맞는 영구 보너스를 멱등 적용한다."""
        flags = getattr(player, "_flags", None)
        if flags is None:
            player._flags = {}
            flags = player._flags
        claimed = set(flags.get("collection_milestones", []))
        awarded = []
        total = self.total_unique()
        for m in COLLECTION_MILESTONES:
            if total < m["count"] or m["count"] in claimed:
                continue
            if m.get("max_energy"):
                player.max_energy += m["max_energy"]
                player.energy = min(player.max_energy, player.energy + m["max_energy"])
            stats = dict(m.get("stats", {}))
            if m.get("stat"):
                stats[m["stat"]] = stats.get(m["stat"], 0) + m.get("value", 0)
            for stat, value in stats.items():
                player.base_stats[stat] = player.base_stats.get(stat, 0) + value
            claimed.add(m["count"])
            awarded.append(f"{m['label']} — {m['bonus']}")
        flags["collection_milestones"] = sorted(claimed)
        return awarded

    def category_milestone_status(self, category: str) -> list[dict]:
        count = len(self._data.get(category, {}))
        thresholds = CATEGORY_MILESTONES.get(category, ())
        return [{"count": n, "unlocked": count >= n, "label": CATEGORY_REWARD_LABELS.get(category, category)} for n in thresholds]

    def apply_category_bonuses(self, player, category: str) -> list[str]:
        flags = getattr(player, "_flags", None)
        if flags is None:
            player._flags = {}; flags = player._flags
        claimed = set(flags.get("collection_category_milestones", []))
        count = len(self._data.get(category, {}))
        awarded = []
        thresholds = CATEGORY_MILESTONES.get(category, ())
        for idx, target in enumerate(thresholds, 1):
            key = f"{category}:{target}"
            if count < target or key in claimed:
                continue
            # 카테고리 완성은 작지만 체감되는 영구 보너스. 데이터 규모에 맞춰 3단계로 제한한다.
            if idx == 1:
                player.max_energy += 1; player.energy = min(player.max_energy, player.energy + 1); bonus = "기력 최대치 +1"
            elif idx == 2:
                stat = "luck" if category in ("낚시", "채집", "몬스터") else "dex"
                player.base_stats[stat] = player.base_stats.get(stat, 0) + 1; bonus = ("LUCK +1" if stat == "luck" else "DEX +1")
            else:
                player.max_energy += 2; player.energy = min(player.max_energy, player.energy + 2); bonus = "기력 최대치 +2"
            claimed.add(key); awarded.append(f"{CATEGORY_REWARD_LABELS.get(category, category)} {target}종 — {bonus}")
        flags["collection_category_milestones"] = sorted(claimed)
        return awarded

    def apply_all_bonuses(self, player, category: str | None = None) -> list[str]:
        rewards = self.apply_player_bonuses(player)
        if category:
            rewards += self.apply_category_bonuses(player, category)
        return rewards

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
