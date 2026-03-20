"""gacha.py — 몰의 수상한 상자 (가챠)"""
import random
import discord
from ui_theme import C, ansi, header_box, divider, GRADE_ICON_PLAIN, EMBED_COLOR

GACHA_POOL = {
    "Normal": [
        {"id": "con_potion_h",  "name": "회복 포션"},
        {"id": "lt_leather_01", "name": "가죽"},
        {"id": "herb",          "name": "허브"},
        {"id": "gt_herb_01",    "name": "들풀"},
        {"id": "water",         "name": "물"},
    ],
    "Rare": [
        {"id": "iron_bar",      "name": "철 주괴"},
        {"id": "silver_ore",    "name": "은 광석"},
        {"id": "mp_crystal",    "name": "마력 결정"},
        {"id": "wing",          "name": "날개"},
        {"id": "mana_herb",     "name": "마나 허브"},
    ],
    "Epic": [
        {"id": "ruby",          "name": "루비"},
        {"id": "eye_of_truth",  "name": "진실의 눈"},
        {"id": "fire_wand",     "name": "화염 완드"},
        {"id": "mithril_ore",   "name": "미스릴 광석"},
    ],
    "Legendary": [
        {"id": "diamond",       "name": "다이아몬드"},
        {"id": "ancient_scale", "name": "고대 비늘"},
        {"id": "dark_matter",   "name": "어둠의 결정"},
    ],
}

GRADE_RATES = {"Normal": 0.60, "Rare": 0.30, "Epic": 0.09, "Legendary": 0.01}
GACHA_COST    = 500
GACHA_10_COST = 4500

_GRADE_COLORS = {
    "Normal":    0xaaaaaa,
    "Rare":      0x00cc77,
    "Epic":      0xaa44ff,
    "Legendary": 0xffd700,
}


class GachaEngine:
    def __init__(self, player):
        self.player = player

    def _pick_grade(self, guarantee_rare: bool = False) -> str:
        if guarantee_rare:
            pool  = {g: r for g, r in GRADE_RATES.items() if g != "Normal"}
        else:
            pool  = GRADE_RATES
        total = sum(pool.values())
        roll  = random.uniform(0, total)
        cumul = 0.0
        for grade, rate in pool.items():
            cumul += rate
            if roll <= cumul:
                return grade
        return list(pool.keys())[-1]

    def _pick_item(self, grade: str) -> dict:
        items = GACHA_POOL.get(grade, GACHA_POOL["Normal"])
        return random.choice(items)

    def do_gacha(self, count: int = 1) -> list:
        cost = GACHA_COST * count
        if self.player.gold < cost:
            return []

        self.player.gold -= cost
        results = []
        for _ in range(count):
            grade  = self._pick_grade()
            item   = self._pick_item(grade)
            added  = self.player.add_item(item["id"])
            results.append({"grade": grade, "item": item, "added": added})
        return results

    def do_gacha_10(self) -> list:
        if self.player.gold < GACHA_10_COST:
            return []

        self.player.gold -= GACHA_10_COST
        results   = []
        has_rare  = False
        for i in range(10):
            guarantee = (i == 9 and not has_rare)
            grade     = self._pick_grade(guarantee_rare=guarantee)
            if grade != "Normal":
                has_rare = True
            item  = self._pick_item(grade)
            added = self.player.add_item(item["id"])
            results.append({"grade": grade, "item": item, "added": added})
        return results

    def show_result(self, results: list) -> discord.Embed:
        if not results:
            embed = discord.Embed(
                title="🎰 뽑기 실패",
                description=f"골드가 부족함미댜! (1회 {GACHA_COST:,}G / 10회 {GACHA_10_COST:,}G)",
                color=0xcc2200,
            )
            return embed

        grade_order = ["Legendary", "Epic", "Rare", "Normal"]
        top_grade   = "Normal"
        for g in grade_order:
            if any(r["grade"] == g for r in results):
                top_grade = g
                break

        embed = discord.Embed(
            title=f"🎰 뽑기 결과 ({len(results)}회)",
            color=_GRADE_COLORS.get(top_grade, 0xaaaaaa),
        )

        lines = []
        for r in results:
            grade = r["grade"]
            item  = r["item"]
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            note  = "" if r["added"] else " *(인벤 부족)*"
            lines.append(f"{icon} **[{grade}]** {item['name']}{note}")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"현재 골드: {self.player.gold:,}G")
        return embed

    def get_cost_text(self) -> str:
        return (
            f"🎰 뽑기 비용: **{GACHA_COST:,}G** / 10회: **{GACHA_10_COST:,}G** (1회 무료)\n"
            f"현재 골드: **{self.player.gold:,}G**"
        )
