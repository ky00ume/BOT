"""affinity.py — NPC 호감도 시스템"""
import datetime
from ui_theme import C, ansi, header_box, divider

AFFINITY_LEVELS = [
    {"level": 0, "name": "낯선이",       "threshold": 0,   "discount": 0},
    {"level": 1, "name": "지인",          "threshold": 50,  "discount": 5},
    {"level": 2, "name": "친구",          "threshold": 150, "discount": 10},
    {"level": 3, "name": "절친",          "threshold": 350, "discount": 15},
    {"level": 4, "name": "영혼의 동반자", "threshold": 700, "discount": 20},
]

NPC_GIFT_PREFS = {
    "다몬": {
        "loves":    ["iron_bar", "mithril_bar", "coal"],
        "likes":    ["copper_bar", "tin_bar"],
        "dislikes": ["gt_flower_01", "fragrant_flower"],
        "default":  3,
    },
    "오멜룸": {
        "loves":    ["lavender", "fragrant_flower", "healing_herb"],
        "likes":    ["herb", "strawberry", "cherry"],
        "dislikes": ["poison_herb", "toxic_mushroom", "slag"],
        "default":  3,
    },
    "몰": {
        "loves":    ["gold_bar", "diamond"],
        "likes":    ["silver_bar", "gold_ore"],
        "dislikes": ["gt_herb_01", "gt_wood_01"],
        "default":  3,
    },
    "아라벨라": {
        "loves":    ["mana_herb", "mana_pool", "moonlight_dew"],
        "likes":    ["mana_flower", "healing_herb"],
        "dislikes": ["coal", "slag"],
        "default":  3,
    },
    "제블로어": {
        "loves":    ["wp_sword_02", "ar_shield_02"],
        "likes":    ["iron_bar", "copper_bar"],
        "dislikes": ["poison_herb", "toxic_mushroom"],
        "default":  3,
    },
    "브룩샤": {
        "loves":    ["ck_special_01", "honey", "butter"],
        "likes":    ["herb", "mushroom", "egg"],
        "dislikes": ["slag", "coal"],
        "default":  3,
    },
    "실렌": {
        "loves":    ["fs_dragon_01", "fs_gold_eel_01"],
        "likes":    ["fs_salmon_01", "fs_tuna_01"],
        "dislikes": ["poison_herb"],
        "default":  3,
    },
    "알피라": {
        "loves":    ["wine", "honey"],
        "likes":    ["gt_flower_01", "fragrant_flower"],
        "dislikes": ["slag", "coal"],
        "default":  3,
    },
    "엘레라신": {
        "loves":    ["diamond", "eye_of_truth"],
        "likes":    ["gold_bar", "mithril_bar"],
        "dislikes": ["gt_herb_01"],
        "default":  3,
    },
    "게일의 환영": {
        "loves":    ["mana_herb", "mp_crystal", "moonlight_dew"],
        "likes":    ["mana_flower", "mana_pool"],
        "dislikes": ["coal", "slag"],
        "default":  3,
    },
    "카엘릭": {
        "loves":    ["wp_sword_02", "iron_bar"],
        "likes":    ["copper_bar", "ar_shield_02"],
        "dislikes": ["gt_flower_01", "fragrant_flower"],
        "default":  3,
    },
}


def _calc_level(points: int) -> dict:
    current = AFFINITY_LEVELS[0]
    for lv in AFFINITY_LEVELS:
        if points >= lv["threshold"]:
            current = lv
        else:
            break
    return current


class AffinityManager:
    DAILY_TALK_LIMIT = 5   # NPC당 일일 대화 최대 횟수
    DAILY_GIFT_LIMIT = 2   # NPC당 일일 선물 최대 횟수

    def __init__(self, player):
        self.player      = player
        self.affinities  = {}
        # 일일 제한 구조: {"NPC이름": {"talk": 횟수, "gift": 횟수, "date": "YYYY-MM-DD"}}
        self.daily_limits = {}
        # 선물 반복 페널티 구조: {"NPC이름": {"item_id": 횟수}}
        self.gift_history = {}

    def _today(self) -> str:
        return datetime.date.today().isoformat()

    def _get_daily(self, npc_name: str) -> dict:
        """오늘 날짜 기준으로 일일 제한 데이터를 반환합니다. 날짜가 다르면 초기화."""
        today = self._today()
        entry = self.daily_limits.get(npc_name)
        if not entry or entry.get("date") != today:
            entry = {"talk": 0, "gift": 0, "date": today}
            self.daily_limits[npc_name] = entry
        return entry

    def check_talk_limit(self, npc_name: str) -> tuple:
        """대화 가능 여부를 반환합니다. (가능: True, 남은 횟수) / (불가: False, 0)"""
        daily = self._get_daily(npc_name)
        used = daily.get("talk", 0)
        remaining = self.DAILY_TALK_LIMIT - used
        return (remaining > 0, max(0, remaining))

    def record_talk(self, npc_name: str):
        """대화 횟수를 기록합니다."""
        daily = self._get_daily(npc_name)
        daily["talk"] = daily.get("talk", 0) + 1

    def check_gift_limit(self, npc_name: str) -> tuple:
        """선물 가능 여부를 반환합니다. (가능: True, 남은 횟수) / (불가: False, 0)"""
        daily = self._get_daily(npc_name)
        used = daily.get("gift", 0)
        remaining = self.DAILY_GIFT_LIMIT - used
        return (remaining > 0, max(0, remaining))

    def record_gift(self, npc_name: str):
        """선물 횟수를 기록합니다."""
        daily = self._get_daily(npc_name)
        daily["gift"] = daily.get("gift", 0) + 1

    def get_gift_repeat_multiplier(self, npc_name: str, item_id: str) -> float:
        """선물 반복 페널티 배율을 반환합니다."""
        npc_history = self.gift_history.get(npc_name, {})
        count = npc_history.get(item_id, 0)
        if count == 0:
            return 1.0
        elif count == 1:
            return 0.7
        elif count == 2:
            return 0.4
        else:
            return 0.2

    def record_gift_item(self, npc_name: str, item_id: str):
        """선물 아이템 히스토리를 기록합니다."""
        if npc_name not in self.gift_history:
            self.gift_history[npc_name] = {}
        self.gift_history[npc_name][item_id] = self.gift_history[npc_name].get(item_id, 0) + 1

    def add_affinity(self, npc_name: str, amount: int) -> tuple:
        old_points   = self.affinities.get(npc_name, 0)
        old_lv       = _calc_level(old_points)
        new_points   = old_points + amount
        self.affinities[npc_name] = new_points
        new_lv       = _calc_level(new_points)
        leveled_up   = new_lv["level"] > old_lv["level"]
        return (new_points, leveled_up, new_lv["name"])

    def get_level(self, npc_name: str) -> dict:
        pts = self.affinities.get(npc_name, 0)
        return _calc_level(pts)

    def get_level_name(self, npc_name: str) -> str:
        return self.get_level(npc_name)["name"]

    def get_shop_discount_pct(self, npc_name: str) -> int:
        return self.get_level(npc_name)["discount"]

    def show_affinity(self, npc_name: str = None) -> str:
        lines = [header_box("💖 NPC 호감도")]

        targets = [npc_name] if npc_name else list(self.affinities.keys())

        if not targets:
            lines.append(f"  {C.DARK}아직 NPC와 교류한 기록이 없슴미댜.{C.R}")
        else:
            for name in targets:
                pts  = self.affinities.get(name, 0)
                lv   = _calc_level(pts)
                disc = lv["discount"]
                next_lv = None
                for al in AFFINITY_LEVELS:
                    if al["threshold"] > pts:
                        next_lv = al
                        break

                bar_filled = min(10, int(pts / max(next_lv["threshold"] if next_lv else pts + 1, 1) * 10))
                bar_str    = "█" * bar_filled + "░" * (10 - bar_filled)

                lines.append(f"\n  {C.GOLD}{name}{C.R}  [{lv['name']}]")
                lines.append(f"    {C.WHITE}{bar_str}{C.R}  {pts}pt")
                if disc:
                    lines.append(f"    {C.GREEN}상점 할인 -{disc}%{C.R}")
                if next_lv:
                    need = next_lv["threshold"] - pts
                    lines.append(f"    {C.DARK}다음 단계까지 {need}pt 필요{C.R}")

        lines.append(divider())
        return ansi("\n".join(lines))

    def to_dict(self) -> dict:
        return {
            "affinities":   self.affinities,
            "daily_limits": self.daily_limits,
            "gift_history": self.gift_history,
        }

    def from_dict(self, data: dict):
        self.affinities   = data.get("affinities", {})
        self.daily_limits = data.get("daily_limits", {})
        self.gift_history = data.get("gift_history", {})
        return self

    def give_gift(self, npc_name: str, item_id: str) -> tuple:
        """
        선물 처리. 일일 제한, 반복 페널티, NPC별 고유 반응 대사 적용.
        Returns: (amount, reaction, leveled, lv_name, limit_exceeded)
        """
        from npc_dialogue_db import NPC_GIFT_REACTIONS

        # 특수 NPC 처리
        special_npcs = {"라파엘", "카르니스", "루바토"}
        if npc_name in special_npcs:
            reactions = NPC_GIFT_REACTIONS.get(npc_name, {})
            msg = reactions.get("special", "선물은 필요 없어.")
            return (0, msg, False, self.get_level_name(npc_name), False)

        # 일일 선물 제한 확인
        allowed, remaining = self.check_gift_limit(npc_name)
        if not allowed:
            return (0, "오늘은 더 이상 선물을 받기 어려울 것 같아요.", False, self.get_level_name(npc_name), True)

        prefs = NPC_GIFT_PREFS.get(npc_name, {"default": 3})
        reactions = NPC_GIFT_REACTIONS.get(npc_name, {})

        if item_id in prefs.get("loves", []):
            base_amount = 15
            reaction = reactions.get("loves", "정말 좋아해요! 눈이 반짝반짝✨")
        elif item_id in prefs.get("likes", []):
            base_amount = 8
            reaction = reactions.get("likes", "괜찮은 선물이네요~")
        elif item_id in prefs.get("dislikes", []):
            base_amount = -5
            reaction = reactions.get("dislikes", "이건 좀...")
        else:
            base_amount = prefs.get("default", 3)
            reaction = reactions.get("default", "고마워요.")

        # 반복 페널티 (싫어하는 선물은 페널티 없음)
        if base_amount > 0:
            multiplier = self.get_gift_repeat_multiplier(npc_name, item_id)
            amount = max(1, int(base_amount * multiplier))
        else:
            amount = base_amount

        # 기록
        self.record_gift(npc_name)
        self.record_gift_item(npc_name, item_id)

        pts, leveled, lv_name = self.add_affinity(npc_name, amount)
        return (amount, reaction, leveled, lv_name, False)
