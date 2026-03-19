import discord
from discord.ext import commands
import random
import signal
import sys
import os
import time as _time

# .env 파일 지원 (python-dotenv 설치 시 자동 로드)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── 내부 모듈 ────────────────────────────────────────────────────────────
from player       import Player
from npcs         import VillageNPC
from shop         import ShopManager
from battle       import BattleEngine
from database     import init_db, save_player_to_db, load_player_from_db
from equipment_window import EquipmentWindow
import status_window
import status as status_mod
from ui_theme     import C, ansi, EMBED_COLOR, FOOTERS
from town_notice  import send_town_notice, make_intro_embed, make_npc_embed, make_commands_embed
from fishing      import FishingEngine
from cooking_db   import CookingEngine
from metallurgy   import MetallurgyEngine
from alarms       import setup_alarms
from responses    import get_drider_response, get_hyness_response, get_majesty_response, get_pet_response
from items        import CONSUMABLES, COOKED_DISHES, ALL_ITEMS
from village      import village_manager
from gathering    import GatheringEngine
from weather      import weather_system
from potion       import PotionEngine
from quest        import QuestManager
from affinity     import AffinityManager
from gacha        import GachaEngine
from music        import MusicEngine
from bulletin     import bulletin_board, weekly_fishing
from shop         import find_item_by_name
from rest         import RestEngine
from crafting     import CraftingEngine
from diary        import diary_manager
from collection   import collection_manager
from achievements import achievement_manager

# ─── 상수 (환경변수로 관리) ────────────────────────────────────────────────
TOKEN              = os.getenv("DISCORD_TOKEN", "")
HYNESS_ID          = int(os.getenv("HYNESS_ID",          "446014281486565387"))
MAJESTY_ID         = int(os.getenv("MAJESTY_ID",         "778476921117343744"))
DRIDER_ID          = int(os.getenv("DRIDER_ID",          "1396150414549717207"))
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID", "1483987513575215207"))

if not TOKEN:
    print("[오류] DISCORD_TOKEN 환경변수가 설정되지 않았슴미댜!")
    print("  .env 파일에 DISCORD_TOKEN=<봇 토큰> 을 추가하셰요.")
    sys.exit(1)

# 먹을 수 있는 아이템 합산
EDIBLE_ITEMS = {**CONSUMABLES, **COOKED_DISHES}

# ─── Discord 봇 초기화 ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ─── 공유 객체 초기화 ─────────────────────────────────────────────────────
shared_player     = Player(name="츄라이더")
npc_manager       = VillageNPC(shared_player)
shop_manager      = ShopManager(shared_player)
battle_engine     = BattleEngine(shared_player, npc_manager)
fishing_engine    = FishingEngine(shared_player)
cooking_engine    = CookingEngine(shared_player)
metallurgy_engine = MetallurgyEngine(shared_player)
gathering_engine  = GatheringEngine(shared_player)
potion_engine     = PotionEngine(shared_player)
quest_manager     = QuestManager(shared_player)
affinity_manager  = AffinityManager(shared_player)
gacha_engine      = GachaEngine(shared_player)
music_engine      = MusicEngine(shared_player)
crafting_engine   = CraftingEngine(shared_player)
shared_player._affinity_manager = affinity_manager


# ─── 이벤트 ──────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[봇 시작] {bot.user} 로그인 완료")

    # DB 초기화
    init_db()

    # status.json 확보
    status_mod.ensure_status_json()

    # DB에서 플레이어 로드
    loaded = load_player_from_db(0)
    if loaded:
        shared_player.load_from_dict(loaded)
        print(f"[DB 로드] {shared_player.name} 데이터 복원 완료")
    else:
        print("[DB 로드] 저장 데이터 없음 — 기본 캐릭터로 시작")

    # 알람 설정
    alarm_loop = setup_alarms(bot, ALLOWED_CHANNEL_ID, DRIDER_ID, hyness_id=HYNESS_ID, majesty_id=MAJESTY_ID)
    if not alarm_loop.is_running():
        alarm_loop.start()

    print("[봇 준비] 모든 시스템 초기화 완료!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # 츄라이더 응답
    if "츄라이더" in content and message.author.id == DRIDER_ID:
        await message.channel.send(get_drider_response())
        return

    # 하이네스 응답
    if "하이네스" in content and message.author.id == HYNESS_ID:
        await message.channel.send(get_hyness_response())
        return

    # 마제스티 응답
    if "마제스티" in content and message.author.id == MAJESTY_ID:
        await message.channel.send(get_majesty_response())
        return

    await bot.process_commands(message)


# ─── 채널 검사 유틸 ───────────────────────────────────────────────────────
async def _check_channel(ctx) -> bool:
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 캐릭터 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="상태창")
async def status_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = status_window.create_status_embed(shared_player)
    await ctx.send(embed=embed)


@bot.command(name="장비")
async def equipment_cmd(ctx):
    if not await _check_channel(ctx):
        return
    ew = EquipmentWindow(shared_player)
    embed = ew.create_embed()
    await ctx.send(embed=embed)


@bot.command(name="스왑")
async def swap_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = shared_player.swap_weapons()
    await ctx.send(ansi(f"  {C.GREEN}✔{C.R} {msg}"))


@bot.command(name="치료")
async def heal_cmd(ctx):
    if not await _check_channel(ctx):
        return
    cost = 50
    if shared_player.gold < cost:
        await ctx.send(ansi(f"  {C.RED}✖ 골드 부족! 치료비: {cost}G{C.R}"))
        return
    shared_player.gold -= cost
    heal_hp = shared_player.max_hp - shared_player.hp
    heal_mp = shared_player.max_mp - shared_player.mp
    shared_player.hp = shared_player.max_hp
    shared_player.mp = shared_player.max_mp
    await ctx.send(ansi(
        f"  {C.GREEN}✔ 치료 완료!{C.R}\n"
        f"  {C.RED}HP +{heal_hp}{C.R}  {C.BLUE}MP +{heal_mp}{C.R}\n"
        f"  {C.GOLD}-{cost}G{C.R} (현재: {shared_player.gold:,}G)"
    ))


@bot.command(name="먹기")
async def eat_item(ctx, item_name: str = None):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /먹기 [아이템이름] 형식으로 입력하셰요!{C.R}"))
        return
    item_id = find_item_by_name(item_name)
    if not item_id or shared_player.inventory.get(item_id, 0) == 0:
        await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]가 없슴미댜!{C.R}"))
        return
    item = EDIBLE_ITEMS.get(item_id)
    if not item:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]은(는) 먹을 수 없는 아이템임미댜!{C.R}"))
        return

    shared_player.remove_item(item_id)

    hp_eff = item.get("hp", 0)
    mp_eff = item.get("mp", 0)
    en_eff = item.get("en", 0)

    if hp_eff:
        shared_player.hp = min(shared_player.max_hp, shared_player.hp + hp_eff)
    if mp_eff:
        shared_player.mp = min(shared_player.max_mp, shared_player.mp + mp_eff)
    if en_eff:
        shared_player.energy = min(shared_player.max_energy, shared_player.energy + en_eff)

    name = item.get("name", item_id)
    effects = []
    if hp_eff: effects.append(f"{C.RED}HP +{hp_eff}{C.R}")
    if mp_eff: effects.append(f"{C.BLUE}MP +{mp_eff}{C.R}")
    if en_eff: effects.append(f"{C.GREEN}EN +{en_eff}{C.R}")

    await ctx.send(ansi(
        f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} 섭취!\n"
        f"  {' / '.join(effects) if effects else '효과 없음'}"
    ))


# ═══════════════════════════════════════════════════════════════════════════
# 마을 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="공지")
async def notice_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await send_town_notice(ctx.channel)


@bot.command(name="마을")
async def village_cmd(ctx, name: str = None):
    if not await _check_channel(ctx):
        return
    if name:
        msg = npc_manager.talk_to_npc(name)
        await ctx.send(msg)
    else:
        msg = npc_manager.list_npcs()
        await ctx.send(msg)


@bot.command(name="대화")
async def talk_cmd(ctx, name: str = None):
    if not await _check_channel(ctx):
        return
    if not name:
        msg = npc_manager.list_npcs()
        await ctx.send(msg)
        return
    msg = npc_manager.talk_to_npc(name)
    await ctx.send(msg)


@bot.command(name="알바")
async def job_cmd(ctx, name: str = None):
    if not await _check_channel(ctx):
        return
    if not name:
        await ctx.send(ansi(f"  {C.RED}✖ /알바 [NPC이름] 형식으로 입력하셰요!{C.R}"))
        return
    await npc_manager.start_job_async(ctx, name)


# ═══════════════════════════════════════════════════════════════════════════
# 상점 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="구매목록")
async def buy_list_cmd(ctx, npc_name: str = None):
    if not await _check_channel(ctx):
        return
    if not npc_name:
        from shop import NPC_CATALOGS
        names = ", ".join(NPC_CATALOGS.keys())
        await ctx.send(ansi(f"  {C.GOLD}상점 NPC: {names}{C.R}\n  {C.GREEN}/구매목록 [NPC이름]{C.R} 으로 확인하셰요!"))
        return
    msg = shop_manager.show_buy_list(npc_name)
    await ctx.send(msg)


@bot.command(name="구매")
async def buy_cmd(ctx, npc_name: str = None, item_name: str = None):
    if not await _check_channel(ctx):
        return
    if not npc_name or not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /구매 [NPC이름] [아이템이름] 형식으로 입력하셰요!{C.R}"))
        return
    msg = shop_manager.execute_buy(npc_name, item_name)
    await ctx.send(msg)


@bot.command(name="판매목록")
async def sell_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = shop_manager.show_sell_list()
    await ctx.send(msg)


@bot.command(name="판매", aliases=["판매확정"])
async def sell_cmd(ctx, item_name: str = None):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /판매 [아이템이름] 형식으로 입력하셰요!{C.R}"))
        return
    msg = shop_manager.sell_item(item_name)
    await ctx.send(msg)


# ═══════════════════════════════════════════════════════════════════════════
# 전투 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="사냥터")
async def zone_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    zones = battle_engine.zone_list
    lines = ["  " + C.GOLD + "사냥터 목록" + C.R]
    from monsters_db import MONSTERS_DB
    for zone_name in zones:
        zone = MONSTERS_DB[zone_name]
        lvl_min, lvl_max = zone["level_range"]
        lines.append(f"  {C.WHITE}{zone_name}{C.R}  {C.DARK}(Lv.{lvl_min}~{lvl_max}){C.R}")
    lines.append(f"  {C.GREEN}/사냥 [사냥터이름]{C.R} 으로 출발!")
    await ctx.send(ansi("\n".join(lines)))


@bot.command(name="사냥")
async def hunt_cmd(ctx, *, zone: str = None):
    if not await _check_channel(ctx):
        return
    if not zone:
        await ctx.send(ansi(f"  {C.RED}✖ /사냥 [사냥터이름] 형식으로 입력하셰요!{C.R}"))
        return
    success, msg = battle_engine.start_encounter(zone)
    await ctx.send(ansi(msg) if not msg.startswith("```") else msg)


@bot.command(name="공격")
async def attack_cmd(ctx, skill_id: str = "smash"):
    if not await _check_channel(ctx):
        return
    if not battle_engine.in_battle:
        await ctx.send(ansi(f"  {C.RED}✖ 현재 전투 중이 아님미댜! /사냥 으로 전투 시작.{C.R}"))
        return

    was_in_battle = battle_engine.in_battle
    result = battle_engine.process_turn(skill_id)

    # 전투 종료 후 업적 체크 (승리 시)
    if was_in_battle and not battle_engine.in_battle and shared_player.hp > 0:
        newly_unlocked = achievement_manager.increment("battles_won", 1)
        diary_manager.increment("battles_won", 1)
        for ach_id in newly_unlocked:
            from achievements import ACHIEVEMENT_DEFS
            ach = ACHIEVEMENT_DEFS.get(ach_id, {})
            await ctx.send(
                f"🏆✨ **업적 달성!** [{ach.get('name', ach_id)}]\n"
                f"  {ach.get('desc', '')}\n"
                f"  🎀 타이틀 획득: **{ach.get('title', '')}**"
            )

    await ctx.send(result if result.startswith("```") else ansi(result))


@bot.command(name="도주")
async def flee_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = battle_engine.flee()
    await ctx.send(result if result.startswith("```") else ansi(result))


# ═══════════════════════════════════════════════════════════════════════════
# 낚시 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="낚시")
async def fishing_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await fishing_engine.fish(ctx)


@bot.command(name="낚시목록")
async def fish_guide_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = fishing_engine.show_fish_guide()
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 요리 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="요리")
async def cook_cmd(ctx, dish_id: str = None):
    if not await _check_channel(ctx):
        return
    if not dish_id:
        result = cooking_engine.show_recipe_list(method_filter="cook")
        await ctx.send(result)
        return
    result = cooking_engine.cook(dish_id, force_method="cook")
    await ctx.send(result)


@bot.command(name="레시피")
async def recipe_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = cooking_engine.show_recipe_list()
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 제련 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="제련")
async def smelt_cmd(ctx, ore_id: str = None):
    if not await _check_channel(ctx):
        return
    if not ore_id:
        result = metallurgy_engine.show_recipe_list()
        await ctx.send(result)
        return
    result = metallurgy_engine.smelt(ore_id)
    await ctx.send(result)


@bot.command(name="제련목록")
async def smelt_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = metallurgy_engine.show_recipe_list()
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 혼합 요리 명령어 (비가열)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="혼합", aliases=["믹스"])
async def mix_cmd(ctx, dish_id: str = None):
    if not await _check_channel(ctx):
        return
    if not dish_id:
        result = cooking_engine.show_recipe_list(method_filter="mix")
        await ctx.send(result)
        return
    result = cooking_engine.cook(dish_id, force_method="mix")
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 장비 제작 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="제작")
async def craft_item_cmd(ctx, result_id: str = None):
    if not await _check_channel(ctx):
        return
    if not result_id:
        result = crafting_engine.show_recipe_list()
        await ctx.send(result)
        return
    result = crafting_engine.craft(result_id)
    await ctx.send(result)


@bot.command(name="제작도감")
async def craft_guide_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = crafting_engine.show_recipe_list()
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 기타 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="주사위")
async def dice_cmd(ctx, sides: int = 6):
    if not await _check_channel(ctx):
        return
    sides = max(2, min(sides, 10000))
    result = random.randint(1, sides)
    await ctx.send(ansi(
        f"  🎲 {C.GOLD}{sides}면 주사위{C.R} 결과: {C.WHITE}{result}{C.R}!"
    ))


@bot.command(name="저장")
async def save_cmd(ctx):
    if not await _check_channel(ctx):
        return
    try:
        save_player_to_db(shared_player)
        await ctx.send(ansi(f"  {C.GREEN}✔ 데이터 저장 완료임미댜!{C.R}"))
    except Exception as e:
        await ctx.send(ansi(f"  {C.RED}✖ 저장 실패: {e}{C.R}"))


@bot.command(name="도움말")
async def help_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = discord.Embed(
        title="📖 비전 타운 봇 도움말",
        color=EMBED_COLOR["help"],
    )
    embed.add_field(
        name="👤 캐릭터 & 상태",
        value=(
            "`/상태창` — 캐릭터 상태 보기\n"
            "`/장비` — 장비창 보기\n"
            "`/스왑` — 주·보조 무기 교환\n"
            "`/치료` — HP/MP 회복 (50G)\n"
            "`/먹기 [아이템이름]` — 아이템 섭취\n"
            "`/휴식` — 기력 회복 (5분 쿨타임)\n"
            "`/쓰담` — 츄라이더를 쓰다듬기 💕"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏘 마을 & NPC",
        value=(
            "`/공지` — 마을 공지 보기\n"
            "`/마을 [NPC이름]` — NPC 목록 / 대화\n"
            "`/대화 [NPC이름]` — NPC와 대화\n"
            "`/알바 [NPC이름]` — 알바 진행\n"
            "`/마을상태` — 마을 레벨·기여도 확인\n"
            "`/치료` — 치료사 방문"
        ),
        inline=False,
    )
    embed.add_field(
        name="🛒 상점",
        value=(
            "`/구매목록 [NPC이름]` — NPC 판매 목록\n"
            "`/구매 [NPC이름] [아이템이름]` — 구매\n"
            "`/판매목록` — 인벤토리 판매 목록\n"
            "`/판매 [아이템이름]` — 아이템 판매"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚔ 전투",
        value=(
            "`/사냥터` — 사냥터 목록\n"
            "`/사냥 [사냥터이름]` — 전투 시작\n"
            "`/공격 [스킬ID]` — 공격 (기본: smash)\n"
            "`/도주` — 전투 이탈"
        ),
        inline=False,
    )
    embed.add_field(
        name="🌿 생활",
        value=(
            "`/낚시` — 낚시하기 (타이밍 게임)\n"
            "`/낚시도감` `/낚시터정보` — 낚시터·물고기 정보\n"
            "`/채집` — 채집 (기력 15)\n"
            "`/채광` — 채광 (기력 20)\n"
            "`/채집도감` — 채집 가능 아이템 목록\n"
            "`/요리 [레시피ID]` — 가열 요리\n"
            "`/혼합 [레시피ID]` — 혼합(비가열) 요리\n"
            "`/레시피` — 요리 레시피 목록\n"
            "`/제련 [광석ID]` — 제련하기\n"
            "`/제련목록` — 제련 목록\n"
            "`/제작 [장비ID]` — 장비 제작\n"
            "`/제작도감` — 제작 가능 장비 목록\n"
            "`/제조 [레시피ID]` — 포션 제조\n"
            "`/날씨` — 현재 날씨 확인"
        ),
        inline=False,
    )
    embed.add_field(
        name="📋 소셜",
        value=(
            "`/퀘스트` — 퀘스트 목록\n"
            "`/퀘스트수락 [ID]` — 퀘스트 수락\n"
            "`/퀘스트완료 [ID]` — 퀘스트 완료\n"
            "`/뽑기` — 가챠 1회 (500G)\n"
            "`/뽑기10` — 가챠 10회 (4500G)\n"
            "`/작곡` — 곡 선택\n"
            "`/연주 [곡ID]` — 연주 시작\n"
            "`/게시판` — 마을 게시판\n"
            "`/명예의전당` — 명예의 전당\n"
            "`/낚시순위` — 주간 낚시 순위"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎲 기타",
        value=(
            "`/주사위 [면수]` — 주사위 굴리기\n"
            "`/저장` — 데이터 저장\n"
            "`/공지` — 마을 공지\n"
            "`/도움말` — 이 도움말"
        ),
        inline=False,
    )
    embed.set_footer(text=FOOTERS["help"])
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 낚시터정보, 날씨, 채집, 채광, 제조
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="낚시터정보")
async def fish_spot_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = fishing_engine.show_fish_guide()
    await ctx.send(result)


@bot.command(name="낚시도감")
async def fish_guide_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = fishing_engine.show_fish_guide()
    await ctx.send(result)


@bot.command(name="채집도감")
async def gather_guide_cmd(ctx):
    if not await _check_channel(ctx):
        return
    from gathering import GATHER_ITEMS_BY_SEASON, MINE_ITEMS, get_current_season
    from ui_theme import header_box, divider, section, GRADE_ICON_PLAIN
    season = get_current_season()
    season_kr = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}.get(season, season)
    pool = GATHER_ITEMS_BY_SEASON.get(season, [])
    lines = [header_box("🌿 채집 도감"), section(f"현재 계절: {season_kr}")]
    for item in sorted(pool, key=lambda x: x["grade"]):
        grade = item["grade"]
        mark  = GRADE_ICON_PLAIN.get(grade, "⚬")
        pct   = int(item["rate"] * 100)
        lines.append(f"  {mark} {C.WHITE}{item['name']}{C.R}  {C.DARK}등급: {grade}  {pct}%{C.R}")
    lines.append(section("채광 아이템"))
    for item in MINE_ITEMS:
        grade = item["grade"]
        mark  = GRADE_ICON_PLAIN.get(grade, "⚬")
        lines.append(f"  {mark} {C.WHITE}{item['name']}{C.R}  {C.DARK}등급: {grade}  힘 {item['str_req']} 필요{C.R}")
    lines.append(divider())
    lines.append(f"  {C.GREEN}/채집{C.R} 또는 {C.GREEN}/채광{C.R} 으로 수집하셰요!")
    await ctx.send(ansi("\n".join(lines)))


@bot.command(name="날씨")
async def weather_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = weather_system.make_weather_embed()
    await ctx.send(embed=embed)


@bot.command(name="채집")
async def gather_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await gathering_engine.gather(ctx)


@bot.command(name="채광")
async def mine_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await gathering_engine.mine(ctx)


@bot.command(name="제조")
async def craft_cmd(ctx, recipe_id: str = None):
    if not await _check_channel(ctx):
        return
    if not recipe_id:
        result = potion_engine.show_recipe_list()
        await ctx.send(result)
        return
    result = potion_engine.craft(recipe_id)
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 퀘스트
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="퀘스트")
async def quest_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = quest_manager.list_quests()
    await ctx.send(result)


@bot.command(name="퀘스트수락")
async def quest_accept_cmd(ctx, quest_id: str = None):
    if not await _check_channel(ctx):
        return
    if not quest_id:
        await ctx.send(ansi(f"  {C.RED}✖ /퀘스트수락 [ID] 형식으로 입력하셰요!{C.R}"))
        return
    result = quest_manager.accept_quest(quest_id)
    await ctx.send(result)


@bot.command(name="퀘스트완료")
async def quest_complete_cmd(ctx, quest_id: str = None):
    if not await _check_channel(ctx):
        return
    if not quest_id:
        await ctx.send(ansi(f"  {C.RED}✖ /퀘스트완료 [ID] 형식으로 입력하셰요!{C.R}"))
        return
    result = quest_manager.complete_quest(quest_id)
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 가챠
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="뽑기")
async def gacha_cmd(ctx, count: int = 1):
    if not await _check_channel(ctx):
        return
    count   = max(1, min(count, 10))
    results = gacha_engine.do_gacha(count)
    embed   = gacha_engine.show_result(results)
    await ctx.send(embed=embed)


@bot.command(name="뽑기10")
async def gacha10_cmd(ctx):
    if not await _check_channel(ctx):
        return
    results = gacha_engine.do_gacha_10()
    embed   = gacha_engine.show_result(results)
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 음악
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="작곡")
async def compose_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await music_engine.compose(ctx)


@bot.command(name="연주")
async def perform_cmd(ctx, song_id: str = None):
    if not await _check_channel(ctx):
        return
    if not song_id:
        await music_engine.compose(ctx)
        return
    await music_engine.perform(ctx, song_id)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 게시판 & 마을
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="게시판")
async def board_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = bulletin_board.make_board_embed()
    await ctx.send(embed=embed)


@bot.command(name="명예의전당")
async def hall_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = bulletin_board.make_hall_of_fame_embed()
    await ctx.send(embed=embed)


@bot.command(name="낚시순위")
async def fishing_rank_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = weekly_fishing.make_rankings_embed()
    await ctx.send(embed=embed)


@bot.command(name="마을상태")
async def village_status_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = village_manager.make_status_embed()
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 쓰담
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="쓰담")
async def pat_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = get_pet_response()

    # 업적 & 일기 카운터 증가
    newly_unlocked = achievement_manager.increment("pet_count", 1)
    diary_manager.increment("pet_count", 1)

    embed = discord.Embed(
        title="🐱 쓰담쓰담...",
        description=msg,
        color=0xFFB6C1,
    )
    embed.set_footer(text="츄라이더는 언제나 쓰다듬어주면 좋아합니다! 💕")
    await ctx.send(embed=embed)

    # 새 업적 달성 알림
    for ach_id in newly_unlocked:
        from achievements import ACHIEVEMENT_DEFS
        ach = ACHIEVEMENT_DEFS.get(ach_id, {})
        await ctx.send(
            f"🏆✨ **업적 달성!** [{ach.get('name', ach_id)}]\n"
            f"  {ach.get('desc', '')}\n"
            f"  🎀 타이틀 획득: **{ach.get('title', '')}**"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 휴식
# ═══════════════════════════════════════════════════════════════════════════

_rest_cooldowns: dict[int, float] = {}
REST_COOLDOWN_SEC = 300  # 5분


@bot.command(name="휴식")
async def rest_cmd(ctx):
    if not await _check_channel(ctx):
        return

    user_id = ctx.author.id
    now = _time.time()

    last_used = _rest_cooldowns.get(user_id, 0)
    remaining = REST_COOLDOWN_SEC - (now - last_used)
    if remaining > 0:
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        await ctx.send(ansi(
            f"  {C.RED}💤 아직 쉴 수 없슴미댜! 남은 시간: {minutes}분 {seconds}초{C.R}"
        ))
        return

    if shared_player.energy >= shared_player.max_energy:
        await ctx.send(ansi(f"  {C.GREEN}💚 기력이 이미 가득 찼슴미댜!{C.R}"))
        return

    rest_engine = RestEngine(shared_player, channel=ctx.channel)

    _rest_cooldowns[user_id] = now

    embed = discord.Embed(
        title="💤 휴식 시작!",
        description=(
            f"기력을 회복하기 시작했슴미댜...\n"
            f"현재 기력: **{shared_player.energy}/{shared_player.max_energy}**\n\n"
            f"2초마다 **+{rest_engine.get_recovery_per_tick()}** 회복\n"
            "기력이 가득 차면 자동으로 완료됩니댜!"
        ),
        color=EMBED_COLOR["rest"],
    )
    embed.set_footer(text="💤 휴식 중에도 다른 활동이 가능합니댜!")
    await ctx.send(embed=embed)

    await rest_engine.start_rest()


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 일기
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="일기")
async def diary_cmd(ctx, date_str: str = None):
    if not await _check_channel(ctx):
        return
    diary_manager.set_player(shared_player)
    if date_str:
        msg = diary_manager.get_diary_detail(date_str)
    else:
        msg = diary_manager.get_diary_list()
    await ctx.send(msg)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 도감
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="도감")
async def collection_cmd(ctx, category: str = None):
    if not await _check_channel(ctx):
        return
    from collection import CATEGORY_ICONS
    if category and category in CATEGORY_ICONS:
        msg = collection_manager.show_collection(category)
    else:
        msg = collection_manager.show_all_categories()
    await ctx.send(msg)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 업적
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="업적")
async def achievements_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = achievement_manager.show_achievements()
    await ctx.send(msg)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 타이틀
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="타이틀")
async def title_cmd(ctx, *, title_name: str = None):
    if not await _check_channel(ctx):
        return
    owned_titles = achievement_manager.get_unlocked_titles()
    # 기본 타이틀도 항상 포함
    if shared_player.current_title not in owned_titles:
        owned_titles = [shared_player.current_title] + owned_titles

    if not title_name:
        # 목록 표시
        lines = [f"  {C.GOLD}🎀 보유 타이틀 목록{C.R}"]
        for t in owned_titles:
            marker = f"{C.GREEN}▶{C.R}" if t == shared_player.current_title else "  "
            lines.append(f"  {marker} {C.WHITE}{t}{C.R}")
        lines.append(f"\n  {C.GREEN}/타이틀 [이름]{C.R} 으로 장착!")
        await ctx.send(ansi("\n".join(lines)))
    else:
        # 장착
        if title_name in owned_titles:
            shared_player.current_title = title_name
            await ctx.send(ansi(
                f"  {C.GREEN}✔ [{title_name}] 타이틀을 장착했슴미댜! 🎀{C.R}"
            ))
        else:
            await ctx.send(ansi(
                f"  {C.RED}✖ [{title_name}] 타이틀을 보유하고 있지 않슴미댜!{C.R}"
            ))


# ─── 종료 시그널 핸들러 ───────────────────────────────────────────────────
def _shutdown_handler(sig, frame):
    print(f"\n[종료] 시그널 {sig} 수신 — 데이터 저장 중...")
    try:
        save_player_to_db(shared_player)
        print("[종료] 저장 완료.")
    except Exception as e:
        print(f"[종료] 저장 실패: {e}")
    sys.exit(0)


signal.signal(signal.SIGINT,  _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)

# ─── 봇 실행 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
