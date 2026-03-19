"""affinity.py — NPC 호감도 시스템"""
from ui_theme import C, ansi, header_box, divider

AFFINITY_LEVELS = [
    {"level": 0, "name": "낯선이",       "threshold": 0,   "discount": 0},
    {"level": 1, "name": "지인",          "threshold": 50,  "discount": 5},
    {"level": 2, "name": "친구",          "threshold": 150, "discount": 10},
    {"level": 3, "name": "절친",          "threshold": 350, "discount": 15},
    {"level": 4, "name": "영혼의 동반자", "threshold": 700, "discount": 20},
]

NPC_GIFT_PREFS = {
    "크람": {
        "loves":    ["iron_bar", "mithril_bar", "coal"],
        "likes":    ["copper_bar", "tin_bar"],
        "dislikes": ["gt_flower_01", "fragrant_flower"],
        "default":  3,
    },
    "레이나": {
        "loves":    ["lavender", "fragrant_flower", "healing_herb"],
        "likes":    ["herb", "strawberry", "cherry"],
        "dislikes": ["poison_herb", "toxic_mushroom", "slag"],
        "default":  3,
    },
    "곤트": {
        "loves":    ["gold_bar", "diamond"],
        "likes":    ["silver_bar", "gold_ore"],
        "dislikes": ["gt_herb_01", "gt_wood_01"],
        "default":  3,
    },
    "엘리": {
        "loves":    ["mana_herb", "mana_pool", "moonlight_dew"],
        "likes":    ["mana_flower", "healing_herb"],
        "dislikes": ["coal", "slag"],
        "default":  3,
    },
    "그레고": {
        "loves":    ["wp_sword_02", "ar_shield_02"],
        "likes":    ["iron_bar", "copper_bar"],
        "dislikes": ["poison_herb", "toxic_mushroom"],
        "default":  3,
    },
    "마리": {
        "loves":    ["ck_special_01", "honey", "butter"],
        "likes":    ["herb", "mushroom", "egg"],
        "dislikes": ["slag", "coal"],
        "default":  3,
    },
    "피터": {
        "loves":    ["fs_dragon_01", "fs_gold_eel_01"],
        "likes":    ["fs_salmon_01", "fs_tuna_01"],
        "dislikes": ["poison_herb"],
        "default":  3,
    },
    "루카스": {
        "loves":    ["wine", "honey"],
        "likes":    ["gt_flower_01", "fragrant_flower"],
        "dislikes": ["slag", "coal"],
        "default":  3,
    },
    "나디아": {
        "loves":    ["diamond", "eye_of_truth"],
        "likes":    ["gold_bar", "mithril_bar"],
        "dislikes": ["gt_herb_01"],
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
    def __init__(self, player):
        self.player      = player
        self.affinities  = {}   # npc_name: int (포인트)

    def add_affinity(self, npc_name: str, amount: int) -> tuple:
        """호감도 추가. (new_points, leveled_up, new_level_name) 반환."""
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
                # 다음 레벨까지 필요한 포인트
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
        return {"affinities": self.affinities}

    def from_dict(self, data: dict):
        self.affinities = data.get("affinities", {})
        return self

    def give_gift(self, npc_name: str, item_id: str) -> tuple:
        """선물 처리. (amount, reaction_msg, leveled_up, lv_name) 반환."""
        prefs = NPC_GIFT_PREFS.get(npc_name, {"default": 3})
        if item_id in prefs.get("loves", []):
            amount   = 15
            reaction = "정말 좋아해요! 눈이 반짝반짝✨"
        elif item_id in prefs.get("likes", []):
            amount   = 8
            reaction = "괜찮은 선물이네요~"
        elif item_id in prefs.get("dislikes", []):
            amount   = -5
            reaction = "이건 좀..."
        else:
            amount   = prefs.get("default", 3)
            reaction = "고마워요."
        pts, leveled, lv_name = self.add_affinity(npc_name, amount)
        return (amount, reaction, leveled, lv_name)
