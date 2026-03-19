"""gathering.py — 채집 & 채광 시스템"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR, GRADE_ICON_PLAIN

GATHER_ITEMS_BY_SEASON = {
    "spring": [
        {"id": "herb",         "name": "약초",      "grade": "Normal",    "rate": 0.50},
        {"id": "gt_flower_01", "name": "들꽃",      "grade": "Normal",    "rate": 0.30},
        {"id": "mushroom",     "name": "버섯",      "grade": "Normal",    "rate": 0.15},
        {"id": "mana_herb",    "name": "마나 허브", "grade": "Rare",      "rate": 0.05},
    ],
    "summer": [
        {"id": "herb",         "name": "약초",      "grade": "Normal",    "rate": 0.40},
        {"id": "mushroom",     "name": "버섯",      "grade": "Normal",    "rate": 0.35},
        {"id": "gt_wood_01",   "name": "나무 조각", "grade": "Normal",    "rate": 0.20},
        {"id": "honey",        "name": "꿀",        "grade": "Normal",    "rate": 0.05},
    ],
    "autumn": [
        # rates는 가중치 비율 (합이 1.0일 필요 없음, _pick_by_rate가 비례 계산)
        {"id": "mushroom",     "name": "버섯",      "grade": "Normal",    "rate": 0.50},
        {"id": "gt_wood_01",   "name": "나무 조각", "grade": "Normal",    "rate": 0.25},
        {"id": "honey",        "name": "꿀",        "grade": "Normal",    "rate": 0.15},
        {"id": "eye_of_truth", "name": "진실의 눈", "grade": "Epic",      "rate": 0.01},  # 약 1.1% 확률
    ],
    "winter": [
        {"id": "herb",         "name": "약초",      "grade": "Normal",    "rate": 0.30},
        {"id": "coal",         "name": "석탄",      "grade": "Normal",    "rate": 0.40},
        {"id": "mana_herb",    "name": "마나 허브", "grade": "Rare",      "rate": 0.10},
        {"id": "diamond",      "name": "다이아몬드","grade": "Legendary", "rate": 0.005},
    ],
}

MINE_ITEMS = [
    {"id": "copper_ore",  "name": "구리 광석",   "grade": "Normal",    "rate": 0.40, "str_req": 5},
    {"id": "iron_ore",    "name": "철광석",       "grade": "Normal",    "rate": 0.30, "str_req": 8},
    {"id": "coal",        "name": "석탄",         "grade": "Normal",    "rate": 0.20, "str_req": 5},
    {"id": "silver_ore",  "name": "은 광석",      "grade": "Rare",      "rate": 0.07, "str_req": 15},
    {"id": "gold_ore",    "name": "금 광석",      "grade": "Rare",      "rate": 0.03, "str_req": 20},
    {"id": "mithril_ore", "name": "미스릴 광석",  "grade": "Epic",      "rate": 0.005,"str_req": 30},
    {"id": "sulfur",      "name": "유황",         "grade": "Normal",    "rate": 0.10, "str_req": 5},
]


def get_current_season() -> str:
    import datetime
    month = datetime.datetime.now().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def _pick_by_rate(items: list) -> dict:
    total = sum(i["rate"] for i in items)
    roll  = random.uniform(0, total)
    cumul = 0.0
    for item in items:
        cumul += item["rate"]
        if roll <= cumul:
            return item
    return items[-1]


class GatheringEngine:
    def __init__(self, player):
        self.player = player

    async def gather(self, ctx):
        """채집을 수행합니다."""
        energy_cost = 15
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        await ctx.send(ansi(f"  {C.GREEN}🌿 채집을 시작했슴미댜...{C.R}"))
        await asyncio.sleep(random.uniform(3, 6))

        season = get_current_season()
        pool   = GATHER_ITEMS_BY_SEASON.get(season, GATHER_ITEMS_BY_SEASON["spring"])
        item   = _pick_by_rate(pool)
        count  = random.randint(1, 3)
        grade  = item["grade"]

        added     = self.player.add_item(item["id"], count)
        rank_msg  = self.player.train_skill("gathering", 10.0)

        try:
            from village import village_manager
            village_manager.add_contribution(2, "gathering")
        except Exception:
            pass

        # PIL 카드 시도
        card_sent = False
        if added:
            try:
                import fishing_card
                buf  = fishing_card.generate_gather_card(item["name"], count, grade, grade=grade)
                file = discord.File(buf, filename="gather_result.png")
                embed = discord.Embed(
                    title=f"🌿 채집 결과 [{grade}]",
                    color=0x228833,
                )
                embed.set_image(url="attachment://gather_result.png")
                if rank_msg:
                    embed.set_footer(text=rank_msg)
                await ctx.send(embed=embed, file=file)
                card_sent = True
            except Exception:
                pass

        if not card_sent:
            grade_mark = GRADE_ICON_PLAIN.get(grade, "⚬")
            season_kr  = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}.get(season, season)
            if added:
                lines = [
                    header_box("🌿 채집 완료!"),
                    f"  계절: {C.CYAN}{season_kr}{C.R}",
                    f"  {grade_mark} {C.WHITE}{item['name']}{C.R} x{count} 획득!",
                    f"  {C.GOLD}채집 숙련도 +10{C.R}",
                ]
                if rank_msg:
                    lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
            else:
                lines = [f"  {C.RED}✖ 인벤토리 부족으로 {item['name']}을(를) 주울 수 없슴미댜!{C.R}"]
            await ctx.send(ansi("\n".join(lines)))

    async def mine(self, ctx):
        """채광을 수행합니다."""
        energy_cost = 20
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        await ctx.send(ansi(f"  {C.GOLD}⛏ 곡괭이를 휘둘렀슴미댜...{C.R}"))
        await asyncio.sleep(random.uniform(4, 7))

        str_stat = self.player.base_stats.get("str", 10)
        available = [i for i in MINE_ITEMS if str_stat >= i["str_req"]]
        if not available:
            available = [MINE_ITEMS[0]]

        item   = _pick_by_rate(available)
        count  = random.randint(1, 2)
        grade  = item["grade"]

        added    = self.player.add_item(item["id"], count)
        rank_msg = self.player.train_skill("mining", 12.0)

        try:
            from village import village_manager
            village_manager.add_contribution(2, "gathering")
        except Exception:
            pass

        card_sent = False
        if added:
            try:
                import fishing_card
                buf  = fishing_card.generate_gather_card(item["name"], count, grade, grade=grade)
                file = discord.File(buf, filename="mine_result.png")
                embed = discord.Embed(title=f"⛏ 채광 결과 [{grade}]", color=0xaa8833)
                embed.set_image(url="attachment://mine_result.png")
                if rank_msg:
                    embed.set_footer(text=rank_msg)
                await ctx.send(embed=embed, file=file)
                card_sent = True
            except Exception:
                pass

        if not card_sent:
            grade_mark = GRADE_ICON_PLAIN.get(grade, "⚬")
            if added:
                lines = [
                    header_box("⛏ 채광 완료!"),
                    f"  힘(STR): {C.RED}{str_stat}{C.R}",
                    f"  {grade_mark} {C.WHITE}{item['name']}{C.R} x{count} 획득!",
                    f"  {C.GOLD}채광 숙련도 +12{C.R}",
                ]
                if rank_msg:
                    lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
            else:
                lines = [f"  {C.RED}✖ 인벤토리 부족으로 {item['name']}을(를) 담을 수 없슴미댜!{C.R}"]
            await ctx.send(ansi("\n".join(lines)))
