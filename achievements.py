"""achievements.py — 업적(Achievement) & 타이틀 시스템"""
import json
import os

ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), "achievements.json")

ACHIEVEMENT_DEFS = {
    "first_blood":    {"name": "첫 승리",           "desc": "전투에서 첫 승리를 거두다.",          "counter_key": "battles_won",  "threshold": 1,     "title": "초보 전사"},
    "battle_10":      {"name": "싸움꾼",             "desc": "전투를 10번 이기다.",                 "counter_key": "battles_won",  "threshold": 10,    "title": "싸움꾼"},
    "battle_50":      {"name": "백전노장",            "desc": "전투를 50번 이기다.",                 "counter_key": "battles_won",  "threshold": 50,    "title": "백전노장"},
    "battle_100":     {"name": "전장의 지배자",       "desc": "전투를 100번 이기다.",                "counter_key": "battles_won",  "threshold": 100,   "title": "전장의 지배자"},
    "first_fish":     {"name": "낚시 입문",           "desc": "처음으로 물고기를 낚다.",             "counter_key": "fish_caught",  "threshold": 1,     "title": "낚시 초보"},
    "fish_50":        {"name": "낚시꾼",             "desc": "물고기를 50마리 낚다.",               "counter_key": "fish_caught",  "threshold": 50,    "title": "베테랑 낚시꾼"},
    "legendary_fish": {"name": "전설의 낚시꾼",       "desc": "전설 등급 물고기를 낚다.",            "counter_key": "legendary_fish_caught", "threshold": 1, "title": "전설의 낚시꾼"},
    "first_cook":     {"name": "요리 입문",           "desc": "처음으로 요리를 완성하다.",           "counter_key": "items_cooked", "threshold": 1,     "title": "요리 초보"},
    "cook_30":        {"name": "솜씨 좋은 요리사",    "desc": "요리를 30번 완성하다.",               "counter_key": "items_cooked", "threshold": 30,    "title": "솜씨 좋은 요리사"},
    "rich_1000":      {"name": "첫 번째 동전",        "desc": "골드를 1,000G 이상 보유하다.",        "counter_key": "gold_held",    "threshold": 1000,  "title": "소상공인"},
    "rich_10000":     {"name": "대부호",             "desc": "골드를 10,000G 이상 보유하다.",       "counter_key": "gold_held",    "threshold": 10000, "title": "대부호"},
    "collection_10":  {"name": "수집가",             "desc": "도감에 10종 이상 등록하다.",          "counter_key": "collection_total", "threshold": 10, "title": "수집가"},
    "collection_50":  {"name": "박물학자",           "desc": "도감에 50종 이상 등록하다.",          "counter_key": "collection_total", "threshold": 50, "title": "박물학자"},
    "pet_50":         {"name": "쓰다듬기 전문가",     "desc": "츄라이더를 50번 쓰다듬다.",           "counter_key": "pet_count",    "threshold": 50,    "title": "츄라이더의 친구"},
    "levelup_10":     {"name": "성장하는 중",         "desc": "레벨 10에 도달하다.",                 "counter_key": "player_level", "threshold": 10,    "title": "성장하는 모험가"},
}


class AchievementManager:
    def __init__(self):
        self._counters: dict[str, int] = {}
        self._unlocked: list[str] = []
        self._load()

    def _load(self):
        if not os.path.isfile(ACHIEVEMENTS_FILE):
            return
        try:
            with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._counters = data.get("counters", {})
            self._unlocked = data.get("unlocked", [])
        except Exception:
            pass

    def _save(self):
        try:
            with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "counters": self._counters,
                    "unlocked": self._unlocked,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def increment(self, counter_key: str, amount: int = 1) -> list[str]:
        self._counters[counter_key] = self._counters.get(counter_key, 0) + amount
        newly_unlocked = []

        for ach_id, ach in ACHIEVEMENT_DEFS.items():
            if ach.get("counter_key") != counter_key:
                continue
            if ach_id in self._unlocked:
                continue
            if self._counters.get(counter_key, 0) >= ach["threshold"]:
                self._unlocked.append(ach_id)
                newly_unlocked.append(ach_id)

        if newly_unlocked:
            self._save()
        return newly_unlocked

    def check_special(self, ach_id: str) -> bool:
        if ach_id in self._unlocked:
            return False
        self._unlocked.append(ach_id)
        self._save()
        return True

    def get_unlocked_titles(self) -> list[str]:
        titles = []
        for ach_id in self._unlocked:
            ach = ACHIEVEMENT_DEFS.get(ach_id)
            if ach and ach.get("title"):
                titles.append(ach["title"])
        return titles

    def show_achievements(self) -> str:
        from ui_theme import C, ansi, header_box, divider
        lines = [header_box("🏆 업적 목록")]

        for ach_id, ach in ACHIEVEMENT_DEFS.items():
            unlocked = ach_id in self._unlocked
            status = f"{C.GREEN}✅{C.R}" if unlocked else f"{C.DARK}🔒{C.R}"
            name  = ach["name"]
            desc  = ach["desc"]
            title = ach.get("title", "")
            progress = ""
            ck = ach.get("counter_key")
            if ck and not unlocked:
                cur = self._counters.get(ck, 0)
                thr = ach["threshold"]
                progress = f" ({cur}/{thr})"
            lines.append(
                f"  {status} {C.WHITE}{name}{C.R}{C.DARK}{progress}{C.R}"
            )
            if unlocked:
                lines.append(f"    {C.DARK}{desc}  → 타이틀: {title}{C.R}")
            else:
                lines.append(f"    {C.DARK}{desc}{C.R}")

        lines.append(divider())
        lines.append(f"  달성: {C.GOLD}{len(self._unlocked)}/{len(ACHIEVEMENT_DEFS)}{C.R}")
        return ansi("\n".join(lines))

    def to_dict(self) -> dict:
        return {"counters": self._counters, "unlocked": self._unlocked}

    def from_dict(self, data: dict):
        self._counters = data.get("counters", {})
        self._unlocked = data.get("unlocked", [])
        self._save()


achievement_manager = AchievementManager()
