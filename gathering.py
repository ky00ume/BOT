"""gathering.py — 채집 & 채광 시스템"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR, GRADE_ICON_PLAIN, GRADE_EMBED_COLOR

GATHER_ITEMS_BY_SEASON = {
    "spring": [
        {"id": "herb",           "name": "약초",        "grade": "Normal",    "rate": 0.50},
        {"id": "gt_flower_01",   "name": "들꽃",        "grade": "Normal",    "rate": 0.30},
        {"id": "mushroom",       "name": "버섯",        "grade": "Normal",    "rate": 0.15},
        {"id": "mana_herb",      "name": "마나 허브",   "grade": "Rare",      "rate": 0.05},
        # 봄 신규
        {"id": "healing_herb",   "name": "힐링허브",    "grade": "Normal",    "rate": 0.35},
        {"id": "lavender",       "name": "라벤더",      "grade": "Rare",      "rate": 0.08},
        {"id": "fragrant_flower","name": "향기로운꽃",  "grade": "Normal",    "rate": 0.25},
        {"id": "strawberry",     "name": "딸기",        "grade": "Normal",    "rate": 0.20},
        {"id": "cherry",         "name": "체리",        "grade": "Rare",      "rate": 0.07},
        {"id": "lettuce",        "name": "상추",        "grade": "Normal",    "rate": 0.18},
    ],
    "summer": [
        {"id": "herb",           "name": "약초",        "grade": "Normal",    "rate": 0.40},
        {"id": "mushroom",       "name": "버섯",        "grade": "Normal",    "rate": 0.35},
        {"id": "gt_wood_01",     "name": "나무 조각",   "grade": "Normal",    "rate": 0.20},
        {"id": "honey",          "name": "꿀",          "grade": "Normal",    "rate": 0.05},
        # 여름 신규
        {"id": "mana_pool",      "name": "마나풀",      "grade": "Rare",      "rate": 0.06},
        {"id": "shiitake",       "name": "표고버섯",    "grade": "Normal",    "rate": 0.28},
        {"id": "grape",          "name": "포도",        "grade": "Normal",    "rate": 0.22},
        {"id": "lemon",          "name": "레몬",        "grade": "Normal",    "rate": 0.15},
        {"id": "tomato",         "name": "토마토",      "grade": "Normal",    "rate": 0.25},
        {"id": "cucumber",       "name": "오이",        "grade": "Normal",    "rate": 0.20},
        {"id": "onion",          "name": "양파",        "grade": "Normal",    "rate": 0.18},
    ],
    "autumn": [
        # rates는 가중치 비율 (합이 1.0일 필요 없음, _pick_by_rate가 비례 계산)
        {"id": "mushroom",       "name": "버섯",        "grade": "Normal",    "rate": 0.50},
        {"id": "gt_wood_01",     "name": "나무 조각",   "grade": "Normal",    "rate": 0.25},
        {"id": "honey",          "name": "꿀",          "grade": "Normal",    "rate": 0.15},
        {"id": "eye_of_truth",   "name": "진실의 눈",   "grade": "Epic",      "rate": 0.01},
        # 가을 신규
        {"id": "pine_mushroom",  "name": "송이버섯",    "grade": "Rare",      "rate": 0.10},
        {"id": "reishi",         "name": "영지버섯",    "grade": "Epic",      "rate": 0.03},
        {"id": "glow_mushroom",  "name": "발광버섯",    "grade": "Rare",      "rate": 0.06},
        {"id": "apple",          "name": "사과",        "grade": "Normal",    "rate": 0.30},
        {"id": "carrot",         "name": "당근",        "grade": "Normal",    "rate": 0.22},
        {"id": "potato",         "name": "감자",        "grade": "Normal",    "rate": 0.25},
    ],
    "winter": [
        {"id": "herb",           "name": "약초",        "grade": "Normal",    "rate": 0.30},
        {"id": "coal",           "name": "석탄",        "grade": "Normal",    "rate": 0.40},
        {"id": "mana_herb",      "name": "마나 허브",   "grade": "Rare",      "rate": 0.10},
        {"id": "diamond",        "name": "다이아몬드",  "grade": "Legendary", "rate": 0.005},
        # 겨울 신규
        {"id": "poison_herb",    "name": "독초",        "grade": "Rare",      "rate": 0.07},
        {"id": "toxic_mushroom", "name": "독버섯",      "grade": "Normal",    "rate": 0.12},
        {"id": "lavender",       "name": "라벤더",      "grade": "Rare",      "rate": 0.05},
    ],
}

MINE_ITEMS = [
    {"id": "copper_ore",       "name": "구리 광석",      "grade": "Normal",    "rate": 0.40, "str_req": 5},
    {"id": "tin_ore",          "name": "주석 광석",      "grade": "Normal",    "rate": 0.30, "str_req": 5},
    {"id": "iron_ore",         "name": "철광석",         "grade": "Normal",    "rate": 0.30, "str_req": 8},
    {"id": "coal",             "name": "석탄",           "grade": "Normal",    "rate": 0.20, "str_req": 5},
    {"id": "silver_ore",       "name": "은 광석",        "grade": "Rare",      "rate": 0.07, "str_req": 15},
    {"id": "gold_ore",         "name": "금 광석",        "grade": "Rare",      "rate": 0.03, "str_req": 20},
    {"id": "mithril_ore",      "name": "미스릴 광석",    "grade": "Epic",      "rate": 0.005,"str_req": 30},
    {"id": "orichalcum_ore",   "name": "오리할콘 광석",  "grade": "Epic",      "rate": 0.003,"str_req": 40},
    {"id": "adamantium_ore",   "name": "아다만티움 광석","grade": "Legendary", "rate": 0.001,"str_req": 55},
    {"id": "dragonite_ore",    "name": "드래곤나이트 광석","grade": "Legendary","rate": 0.0005,"str_req": 70},
    {"id": "sulfur",           "name": "유황",           "grade": "Normal",    "rate": 0.10, "str_req": 5},
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

        if added:
            try:
                from collection import collection_manager
                is_new, total = collection_manager.register("채집", item["id"], item["name"], grade)
                if is_new:
                    await ctx.send(
                        f"📖✨ **새로운 도감 등록!** 🌿 `{item['name']}` 이(가) 채집 도감에 추가됐슴미댜!"
                    )
            except Exception:
                pass

        # PIL 카드 시도
        card_sent = False
        season_kr = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}.get(season, season)
        if added:
            try:
                import fishing_card
                buf  = fishing_card.generate_gather_card(item["name"], count, grade, grade=grade)
                file = discord.File(buf, filename="gather_result.png")
                embed = discord.Embed(
                    title=f"🌿 와! {item['name']}을(를) 채집했슴미댜!!",
                    color=GRADE_EMBED_COLOR.get(grade, 0x228833),
                )
                embed.set_image(url="attachment://gather_result.png")
                footer_parts = [f"계절: {season_kr}", f"{grade} 등급"]
                if rank_msg:
                    footer_parts.append(rank_msg)
                embed.set_footer(text="  |  ".join(footer_parts))
                await ctx.send(embed=embed, file=file)
                card_sent = True
            except Exception:
                pass

        if not card_sent:
            grade_mark = GRADE_ICON_PLAIN.get(grade, "⚬")
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
                embed = discord.Embed(
                    title=f"⛏ 와! {item['name']}을(를) 캐냈슴미댜!!",
                    color=GRADE_EMBED_COLOR.get(grade, 0xaa8833),
                )
                embed.set_image(url="attachment://mine_result.png")
                footer_parts = [f"{grade} 등급"]
                if rank_msg:
                    footer_parts.append(rank_msg)
                embed.set_footer(text="  |  ".join(footer_parts))
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
