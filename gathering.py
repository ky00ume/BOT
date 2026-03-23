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
        {"id": "healing_herb",   "name": "힐링허브",    "grade": "Normal",    "rate": 0.35},
        {"id": "lavender",       "name": "라벤더",      "grade": "Rare",      "rate": 0.08},
        {"id": "fragrant_flower","name": "향기로운꽃",  "grade": "Normal",    "rate": 0.25},
        {"id": "strawberry",     "name": "딸기",        "grade": "Normal",    "rate": 0.20},
        {"id": "cherry",         "name": "체리",        "grade": "Rare",      "rate": 0.07},
        {"id": "lettuce",        "name": "상추",        "grade": "Normal",    "rate": 0.18},
        {"id": "wild_berry",     "name": "야생 열매",   "grade": "Normal",    "rate": 0.20},
        {"id": "healing_root",   "name": "치유의 뿌리", "grade": "Rare",      "rate": 0.06},
        {"id": "mana_flower",    "name": "마나꽃",      "grade": "Rare",      "rate": 0.05},
        {"id": "antidote_herb",  "name": "해독초",      "grade": "Normal",    "rate": 0.10},
        {"id": "wild_garlic",    "name": "산마늘",      "grade": "Normal",    "rate": 0.15},
        {"id": "soybean",        "name": "대두",        "grade": "Normal",    "rate": 0.12},
    ],
    "summer": [
        {"id": "herb",           "name": "약초",        "grade": "Normal",    "rate": 0.40},
        {"id": "mushroom",       "name": "버섯",        "grade": "Normal",    "rate": 0.35},
        {"id": "gt_wood_01",     "name": "나무 조각",   "grade": "Normal",    "rate": 0.20},
        {"id": "honey",          "name": "꿀",          "grade": "Normal",    "rate": 0.05},
        {"id": "mana_pool",      "name": "마나풀",      "grade": "Rare",      "rate": 0.06},
        {"id": "shiitake",       "name": "표고버섯",    "grade": "Normal",    "rate": 0.28},
        {"id": "grape",          "name": "포도",        "grade": "Normal",    "rate": 0.22},
        {"id": "lemon",          "name": "레몬",        "grade": "Normal",    "rate": 0.15},
        {"id": "tomato",         "name": "토마토",      "grade": "Normal",    "rate": 0.25},
        {"id": "cucumber",       "name": "오이",        "grade": "Normal",    "rate": 0.20},
        {"id": "onion",          "name": "양파",        "grade": "Normal",    "rate": 0.18},
        {"id": "wild_berry",     "name": "야생 열매",   "grade": "Normal",    "rate": 0.18},
        {"id": "blue_berry",     "name": "블루베리",    "grade": "Normal",    "rate": 0.15},
        {"id": "energy_leaf",    "name": "원기잎",      "grade": "Normal",    "rate": 0.10},
        {"id": "soybean",        "name": "대두",        "grade": "Normal",    "rate": 0.15},
        {"id": "wheat",          "name": "밀",          "grade": "Normal",    "rate": 0.12},
        {"id": "mana_flower",    "name": "마나꽃",      "grade": "Rare",      "rate": 0.04},
    ],
    "autumn": [
        {"id": "mushroom",       "name": "버섯",        "grade": "Normal",    "rate": 0.50},
        {"id": "gt_wood_01",     "name": "나무 조각",   "grade": "Normal",    "rate": 0.25},
        {"id": "honey",          "name": "꿀",          "grade": "Normal",    "rate": 0.15},
        {"id": "eye_of_truth",   "name": "진실의 눈",   "grade": "Epic",      "rate": 0.01},
        {"id": "pine_mushroom",  "name": "송이버섯",    "grade": "Rare",      "rate": 0.10},
        {"id": "reishi",         "name": "영지버섯",    "grade": "Epic",      "rate": 0.03},
        {"id": "glow_mushroom",  "name": "발광버섯",    "grade": "Rare",      "rate": 0.06},
        {"id": "apple",          "name": "사과",        "grade": "Normal",    "rate": 0.30},
        {"id": "carrot",         "name": "당근",        "grade": "Normal",    "rate": 0.22},
        {"id": "potato",         "name": "감자",        "grade": "Normal",    "rate": 0.25},
        {"id": "forest_nut",     "name": "숲 열매",     "grade": "Normal",    "rate": 0.25},
        {"id": "golden_apple",   "name": "황금사과",    "grade": "Epic",      "rate": 0.005},
        {"id": "rice",           "name": "쌀",          "grade": "Normal",    "rate": 0.20},
        {"id": "wheat",          "name": "밀",          "grade": "Normal",    "rate": 0.18},
        {"id": "pine_nut",       "name": "잣",          "grade": "Rare",      "rate": 0.05},
        {"id": "healing_root",   "name": "치유의 뿌리", "grade": "Rare",      "rate": 0.04},
        {"id": "energy_leaf",    "name": "원기잎",      "grade": "Normal",    "rate": 0.08},
    ],
    "winter": [
        {"id": "herb",           "name": "약초",        "grade": "Normal",    "rate": 0.30},
        {"id": "coal",           "name": "석탄",        "grade": "Normal",    "rate": 0.40},
        {"id": "mana_herb",      "name": "마나 허브",   "grade": "Rare",      "rate": 0.10},
        {"id": "diamond",        "name": "다이아몬드",  "grade": "Legendary", "rate": 0.005},
        {"id": "poison_herb",    "name": "독초",        "grade": "Rare",      "rate": 0.07},
        {"id": "toxic_mushroom", "name": "독버섯",      "grade": "Normal",    "rate": 0.12},
        {"id": "lavender",       "name": "라벤더",      "grade": "Rare",      "rate": 0.05},
        {"id": "antidote_herb",  "name": "해독초",      "grade": "Normal",    "rate": 0.08},
        {"id": "moonlight_dew",  "name": "달빛 이슬",   "grade": "Epic",      "rate": 0.002},
        {"id": "healing_root",   "name": "치유의 뿌리", "grade": "Rare",      "rate": 0.03},
        {"id": "forest_nut",     "name": "숲 열매",     "grade": "Normal",    "rate": 0.10},
    ],
}

MINE_ITEMS = [
    # 일반 광석: str_req 만족 시 채굴 가능 (rank_req 없음 = 랭크 무관)
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
    # 보석류 (채광 스킬 랭크 F 이상 필요, 랭크별 확률 차등)
    {"id": "gem_ruby",      "name": "루비",        "grade": "Rare",      "rate": 0.020, "str_req": 10, "rank_req": "F"},
    {"id": "gem_sapphire",  "name": "사파이어",    "grade": "Rare",      "rate": 0.018, "str_req": 12, "rank_req": "E"},
    {"id": "gem_emerald",   "name": "에메랄드",    "grade": "Rare",      "rate": 0.015, "str_req": 15, "rank_req": "D"},
    {"id": "gem_topaz",     "name": "토파즈",      "grade": "Rare",      "rate": 0.012, "str_req": 18, "rank_req": "C"},
    {"id": "gem_amethyst",  "name": "자수정",      "grade": "Rare",      "rate": 0.012, "str_req": 18, "rank_req": "C"},
    {"id": "gem_aquamarine","name": "아쿠아마린",  "grade": "Epic",      "rate": 0.006, "str_req": 25, "rank_req": "B"},
    {"id": "gem_diamond",   "name": "다이아몬드",  "grade": "Legendary", "rate": 0.001, "str_req": 40, "rank_req": "A"},
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


# ── 벌목 랭크별 테이블 ────────────────────────────────────────────────────────
WOODCUT_TABLE = {
    "F": {
        "id":            "scrap_branch",
        "name":          "잡목 가지",
        "grade":         "Normal",
        "energy_cost":   10,
        "exp":           5,
        "rank_req_level": 1,
        "desc":          "F랭 벌목: 잡목 가지를 채취합니다. (기력 10, EXP 5)",
    },
    "E": {
        "id":            "worn_lumber",
        "name":          "낡은 목재",
        "grade":         "Normal",
        "energy_cost":   12,
        "exp":           8,
        "rank_req_level": 5,
        "desc":          "E랭 벌목: 낡은 목재를 채취합니다. (기력 12, EXP 8)",
    },
    "D": {
        "id":            "hardwood",
        "name":          "단단한 나무",
        "grade":         "Rare",
        "energy_cost":   15,
        "exp":           12,
        "rank_req_level": 10,
        "desc":          "D랭 벌목: 단단한 나무를 채취합니다. (기력 15, EXP 12)",
    },
    "C": {
        "id":            "dark_lumber",
        "name":          "흑목 원목",
        "grade":         "Rare",
        "energy_cost":   18,
        "exp":           18,
        "rank_req_level": 20,
        "desc":          "C랭 벌목: 흑목 원목을 채취합니다. (기력 18, EXP 18)",
    },
    "B": {
        "id":            "premium_wood",
        "name":          "고급 원목",
        "grade":         "Epic",
        "energy_cost":   20,
        "exp":           25,
        "rank_req_level": 30,
        "desc":          "B랭 벌목: 고급 원목을 채취합니다. (기력 20, EXP 25)",
    },
    "A": {
        "id":            "rare_timber",
        "name":          "희귀 목재",
        "grade":         "Epic",
        "energy_cost":   22,
        "exp":           35,
        "rank_req_level": 45,
        "desc":          "A랭 벌목: 희귀 목재를 채취합니다. (기력 22, EXP 35)",
    },
    "1": {
        "id":            "ancient_timber",
        "name":          "전설의 고목",
        "grade":         "Legendary",
        "energy_cost":   25,
        "exp":           50,
        "rank_req_level": 60,
        "desc":          "1랭 벌목: 전설의 고목을 채취합니다. (기력 25, EXP 50)",
    },
}


class GatheringEngine:
    def __init__(self, player):
        self.player = player

    async def gather(self, ctx):
        """채집을 수행합니다."""
        energy_cost = 8
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

        from economy import Economy
        from gather_bridge import gather_bridge
        economy = Economy(self.player)
        gather_result = gather_bridge.on_gather_complete(
            economy, item["id"], item["name"], count, grade
        )
        added    = gather_result["added"]
        rank_msg = self.player.train_skill("gathering", 10.0)

        if gather_result["is_new_collection"]:
            await ctx.send(
                f"📖✨ **새로운 도감 등록!** 🌿 `{item['name']}` 이(가) 채집 도감에 추가됐슴미댜!"
            )

        card_sent = False
        season_kr = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}.get(season, season)
        if added:
            try:
                import fishing_card
                buf  = fishing_card.generate_gather_card(item["name"], count, grade)
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
        energy_cost = 10
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        await ctx.send(ansi(f"  {C.GOLD}⛏ 곡괭이를 휘둘렀슴미댜...{C.R}"))
        await asyncio.sleep(random.uniform(4, 7))

        str_stat = self.player.base_stats.get("str", 10)
        available = [i for i in MINE_ITEMS if str_stat >= i["str_req"]]

        # 채광 스킬 랭크에 따른 보석 필터링
        mining_rank = self.player.skill_ranks.get("mining", "연습")
        rank_order_local = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]
        rank_idx = rank_order_local.index(mining_rank) if mining_rank in rank_order_local else 0

        def _rank_ok(item):
            req = item.get("rank_req")
            if not req:
                return True
            if req not in rank_order_local:
                return True
            return rank_idx >= rank_order_local.index(req)

        available = [i for i in available if _rank_ok(i)]
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
                buf  = fishing_card.generate_gather_card(item["name"], count, grade)
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

    async def woodcut(self, ctx):
        """벌목을 수행합니다."""
        energy_cost = 9
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        await ctx.send(ansi(f"  {C.GREEN}🪓 도끼를 휘둘렀슴미댜...{C.R}"))
        await asyncio.sleep(random.uniform(3, 6))

        str_stat = self.player.base_stats.get("str", 10)

        # 힘 스탯에 따라 더 좋은 나무 획득 가능
        wood_table = [
            {"id": "gt_wood_01",  "name": "나무 조각",      "grade": "Normal",    "rate": 0.50, "str_req": 1},
            {"id": "wood_log",    "name": "원목",            "grade": "Normal",    "rate": 0.35, "str_req": 5},
            {"id": "hardwood",    "name": "단단한 목재",     "grade": "Rare",      "rate": 0.12, "str_req": 15},
            {"id": "ancient_wood","name": "고대 목재",       "grade": "Epic",      "rate": 0.025,"str_req": 30},
            {"id": "treant_core", "name": "나무정령 심장",   "grade": "Legendary", "rate": 0.005,"str_req": 50},
        ]
        available = [i for i in wood_table if str_stat >= i["str_req"]]
        if not available:
            available = [wood_table[0]]

        item   = _pick_by_rate(available)
        count  = random.randint(1, 3)
        grade  = item["grade"]

        added    = self.player.add_item(item["id"], count)
        rank_msg = self.player.train_skill("woodcutting", 11.0)

        try:
            from village import village_manager
            village_manager.add_contribution(2, "gathering")
        except Exception:
            pass

        card_sent = False
        if added:
            try:
                import fishing_card
                buf  = fishing_card.generate_gather_card(item["name"], count, grade)
                file = discord.File(buf, filename="woodcut_result.png")
                embed = discord.Embed(
                    title=f"🪓 와! {item['name']}을(를) 벌목했슴미댜!!",
                    color=GRADE_EMBED_COLOR.get(grade, 0x8B4513),
                )
                embed.set_image(url="attachment://woodcut_result.png")
                footer_parts = [f"힘(STR): {str_stat}", f"{grade} 등급"]
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
                    header_box("🪓 벌목 완료!"),
                    f"  힘(STR): {C.RED}{str_stat}{C.R}",
                    f"  {grade_mark} {C.WHITE}{item['name']}{C.R} x{count} 획득!",
                    f"  {C.GOLD}벌목 숙련도 +11{C.R}",
                ]
                if rank_msg:
                    lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
            else:
                lines = [f"  {C.RED}✖ 인벤토리 부족으로 {item['name']}을(를) 담을 수 없슴미댜!{C.R}"]
            await ctx.send(ansi("\n".join(lines)))
