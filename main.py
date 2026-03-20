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
from responses    import get_drider_response, get_hyness_response, get_majesty_response, get_pet_response, get_scold_response
from items        import CONSUMABLES, COOKED_DISHES, ALL_ITEMS, GATHERING_ITEMS
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
from restaurant   import RestaurantEngine
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
# 채집 아이템 중 hp, mp, en이 있는 것도 포함
for _k, _v in GATHERING_ITEMS.items():
    if any(_v.get(stat, 0) > 0 for stat in ("hp", "mp", "en")):
        EDIBLE_ITEMS[_k] = _v

# ─── Discord 봇 초기화 ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ─── 공유 객체 초기화 ─────────────────────────────────────────────────────
shared_player     = Player(name="츄라이더")
npc_manager       = VillageNPC(shared_player)
shop_manager      = ShopManager(shared_player)
restaurant_engine = RestaurantEngine(shared_player)
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

# 보관함 엔진 초기화
from storage import StorageEngine
storage_engine = StorageEngine(shared_player)

# 이동·훈련 시스템 초기화
from movement import MovementSystem
from training import TrainingSystem
movement_system  = MovementSystem(shared_player)
training_system  = TrainingSystem(shared_player)


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

@bot.command(name="상태", aliases=["상태창"])
async def status_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embed = status_window.create_status_embed(shared_player)
    await ctx.send(embed=embed)


@bot.command(name="장비", aliases=["장비창"])
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
async def eat_item(ctx, *, item_name: str = None):
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


@bot.command(name="납품")
async def deliver_cmd(ctx, *, item_name: str = None):
    """브룩샤 식당에 요리를 납품합니다."""
    if not await _check_channel(ctx):
        return
    await restaurant_engine.deliver_food(ctx, item_name)


@bot.command(name="선물")
async def gift_cmd(ctx, npc_name: str = None, *, item_name: str = None):
    """NPC에게 요리/아이템을 선물합니다."""
    if not await _check_channel(ctx):
        return
    await restaurant_engine.gift_food(ctx, npc_name, item_name)


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
async def buy_cmd(ctx, npc_name: str = None, item_name: str = None, count: int = 1):
    if not await _check_channel(ctx):
        return
    if not npc_name:
        await ctx.send(ansi(f"  {C.RED}✖ /구매 [NPC이름] [아이템이름] [수량] 형식으로 입력하셰요!{C.R}"))
        return
    if not item_name:
        # 인터랙티브 UI 표시
        from shop import NPC_CATALOGS
        from shop_ui import BuyView
        catalog = NPC_CATALOGS.get(npc_name)
        if not catalog:
            available = ", ".join(NPC_CATALOGS.keys())
            await ctx.send(ansi(
                f"  {C.RED}✖ [{npc_name}]은(는) 상점 NPC가 아님미댜!\n"
                f"  상점 NPC: {available}{C.R}"
            ))
            return
        view = BuyView(shared_player, shop_manager, npc_name, catalog)
        msg  = await ctx.send(
            ansi(f"  {C.GOLD}🛒 {npc_name} 상점{C.R}  —  아이템을 선택하셰요!"),
            view=view
        )
        view._message = msg
        return
    count = max(1, min(count, 999))
    msg = shop_manager.execute_buy(npc_name, item_name, count)
    await ctx.send(msg)


@bot.command(name="판매목록")
async def sell_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = shop_manager.show_sell_list()
    await ctx.send(msg)


@bot.command(name="판매", aliases=["판매확정"])
async def sell_cmd(ctx, *args):
    if not await _check_channel(ctx):
        return
    # 공백 포함 아이템명 지원: /판매 철 주괴 3 → item_name="철 주괴", count=3
    if not args:
        # 인터랙티브 판매 UI
        from shop_ui import SellView
        view = SellView(shared_player, shop_manager)
        msg  = await ctx.send(
            ansi(f"  {C.GOLD}🏪 판매 UI{C.R}  —  아이템을 선택하셰요!"),
            view=view
        )
        view._message = msg
        return
    # 마지막 인수가 숫자 또는 "전부"면 수량으로 처리
    if args[-1] in ("전부",) or (len(args) > 1 and args[-1].isdigit()):
        count_or_all = args[-1]
        item_name    = " ".join(args[:-1])
    else:
        count_or_all = "1"
        item_name    = " ".join(args)
    # 수량 파싱 ("전부" 또는 숫자)
    if count_or_all == "전부":
        item_id = find_item_by_name(item_name)
        count   = shared_player.inventory.get(item_id, 0) if item_id else 0
        if count == 0:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]이(가) 인벤토리에 없슴미댜!{C.R}"))
            return
    else:
        try:
            count = max(1, int(count_or_all))
        except ValueError:
            count = 1
    msg = shop_manager.sell_item(item_name, count)
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
            "`/상태` — 캐릭터 상태 보기\n"
            "`/장비` — 장비창 보기\n"
            "`/스왑` — 주·보조 무기 교환\n"
            "`/치료` — HP/MP 회복 (50G)\n"
            "`/먹기 [아이템이름]` — 아이템 섭취\n"
            "`/휴식` — 기력 회복 (5분 쿨타임)\n"
            "`/쓰담` — 츄라이더를 쓰다듬기 💕 (`/복복` `/북북` `/쓰다듬` 등 동일)\n"
            "`/혼내기` — 츄라이더 혼내기 😤 (`/훈육` 동일)\n"
            "`/버리기 [아이템이름] [수량]` — 아이템 버리기"
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
            "`/벌목` — 벌목 (기력 18, 나무 획득)\n"
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
            "`/이동 [장소]` — 맵 이동 (3분 쿨타임)\n"
            "`/수련 [스탯]` — 훈련소 스탯 수련 (`/훈련소` `/학교` 동일)\n"
            "`/스킬 [스킬이름]` — 스킬 설명·효과 조회\n"
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
async def compose_cmd(ctx, title: str = None, *, melody: str = None):
    if not await _check_channel(ctx):
        return
    if not title or not melody:
        await music_engine.compose(ctx)
        return
    await music_engine.save_composition(ctx, title, melody)


@bot.command(name="악보목록")
async def sheet_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await music_engine.show_sheet_list(ctx)


@bot.command(name="악보삭제")
async def sheet_delete_cmd(ctx, title: str = None):
    if not await _check_channel(ctx):
        return
    if not title:
        await ctx.send(ansi(f"  {C.RED}✖ /악보삭제 [곡이름] 형식으로 입력하셰요!{C.R}"))
        return
    await music_engine.delete_sheet(ctx, title)


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

@bot.command(name="쓰담", aliases=["복복", "북북", "쓰다듬", "북북박박", "복복복", "복복박박"])
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


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 물 뜨기
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="물뜨기")
async def draw_water_cmd(ctx, count: int = 1):
    if not await _check_channel(ctx):
        return
    count = max(1, min(count, 99))
    if shared_player.inventory.get("empty_bottle", 0) < count:
        await ctx.send(ansi(f"  {C.RED}✖ 빈 병이 부족함미댜! (필요: {count}개){C.R}"))
        return
    energy_cost = 5 * count
    if not shared_player.consume_energy(energy_cost):
        await ctx.send(ansi(f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}){C.R}"))
        return
    shared_player.remove_item("empty_bottle", count)
    shared_player.add_item("water", count)
    await ctx.send(ansi(
        f"  {C.GREEN}✔ 물을 떴슴미댜!{C.R}\n"
        f"  {C.WHITE}물{C.R} x{count} 획득!\n"
        f"  {C.RED}기력 -{energy_cost}{C.R}"
    ))


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 아이템 목록 CSV
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="아이템목록")
async def item_list_cmd(ctx):
    if not await _check_channel(ctx):
        return
    from generate_item_list import generate_csv_buffer
    buf  = generate_csv_buffer()
    file = discord.File(buf, filename="item_list.csv")
    await ctx.send("📋 전체 아이템 목록이에요!", file=file)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 보관함 시스템
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="보관함")
async def storage_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await ctx.send(storage_engine.show())


@bot.command(name="보관함넣기")
async def storage_deposit_cmd(ctx, item_name: str = None, count: int = 1):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /보관함넣기 [아이템이름] [수량] 형식으로 입력하셰요!{C.R}"))
        return
    item_id = find_item_by_name(item_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return
    count = max(1, count)
    await ctx.send(storage_engine.deposit(item_id, count))


@bot.command(name="보관함꺼내기")
async def storage_withdraw_cmd(ctx, item_name: str = None, count: int = 1):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /보관함꺼내기 [아이템이름] [수량] 형식으로 입력하셰요!{C.R}"))
        return
    item_id = find_item_by_name(item_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return
    count = max(1, count)
    await ctx.send(storage_engine.withdraw(item_id, count))


@bot.command(name="보관함업그레이드")
async def storage_upgrade_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await ctx.send(storage_engine.upgrade())


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 버리기 (인벤토리 아이템 삭제)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="버리기")
async def discard_cmd(ctx, item_name: str = None, count_str: str = "1"):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /버리기 [아이템이름] [수량] 형식으로 입력하셰요!{C.R}"))
        return

    item_id = find_item_by_name(item_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return

    have = shared_player.inventory.get(item_id, 0)
    if have == 0:
        await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]이(가) 없슴미댜!{C.R}"))
        return

    count_str_lower = count_str.lower()
    if count_str_lower == "전부":
        count = have
    else:
        try:
            count = max(1, int(count_str))
        except ValueError:
            await ctx.send(ansi(f"  {C.RED}✖ 수량은 숫자 또는 '전부'로 입력하셰요!{C.R}"))
            return
    count = min(count, have)

    shared_player.remove_item(item_id, count)
    item_display = ALL_ITEMS.get(item_id, {}).get("name", item_id)
    await ctx.send(ansi(
        f"  {C.GREEN}🗑️  {item_display}{C.R} x{count}을(를) 버렸슴미댜!"
    ))


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 혼내기 / 훈육 (츄라이더 사죄 반응)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="혼내기", aliases=["훈육"])
async def scold_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = get_scold_response()
    embed = discord.Embed(
        title="😤 혼내기!",
        description=msg,
        color=0xFF4500,
    )
    embed.set_footer(text="츄라이더는 진심으로 반성하고 있습니다... 🙏")
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 벌목
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="벌목")
async def woodcut_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await gathering_engine.woodcut(ctx)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 스킬 (스킬 설명/효과 조회)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="스킬", aliases=["스킬조회"])
async def skill_info_cmd(ctx, skill_name: str = None):
    if not await _check_channel(ctx):
        return

    from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS
    from ui_theme import header_box, divider

    ALL_SKILLS = {**COMBAT_SKILLS, **MAGIC_SKILLS, **RECOVERY_SKILLS, **OTHER_SKILLS}

    if not skill_name:
        # 전체 목록
        lines = [header_box("📖 스킬 목록")]
        for sid, sdata in ALL_SKILLS.items():
            rank = shared_player.skill_ranks.get(sid)
            mark = f"{C.GREEN}[{rank}]{C.R}" if rank else f"{C.DARK}[미습득]{C.R}"
            lines.append(f"  {C.WHITE}{sdata['name']}{C.R} {mark}  {C.DARK}{sdata.get('desc','')}{C.R}")
        lines.append(divider())
        lines.append(f"  {C.GREEN}/스킬 [스킬이름]{C.R} 으로 상세 조회")
        await ctx.send(ansi("\n".join(lines)))
        return

    # 이름으로 검색
    found_id   = None
    found_data = None
    for sid, sdata in ALL_SKILLS.items():
        if sdata["name"] == skill_name or sid == skill_name:
            found_id   = sid
            found_data = sdata
            break

    if not found_data:
        await ctx.send(ansi(f"  {C.RED}✖ [{skill_name}] 스킬을 찾을 수 없슴미댜!{C.R}"))
        return

    rank = shared_player.skill_ranks.get(found_id)
    lines = [
        header_box(f"📖 {found_data['name']}"),
        f"  {C.DARK}{found_data.get('desc','')}{C.R}",
        divider(),
        f"  내 랭크: {C.GREEN if rank else C.DARK}{rank or '미습득'}{C.R}",
    ]

    # 랭크별 수치 표시 (대표 수치)
    for key in ("damage_bonus", "damage_reduce", "damage", "counter_multiplier", "aoe_multiplier", "heal", "restore_mp"):
        table = found_data.get(key)
        if isinstance(table, dict) and table:
            lines.append(f"\n  {C.GOLD}◈ {key}{C.R}")
            pairs = list(table.items())
            # 현재 랭크 주변 3개만
            if rank and rank in table:
                idx = list(table.keys()).index(rank)
                start = max(0, idx - 1)
                pairs = list(table.items())[start:start+4]
            for r, v in pairs:
                marker = f"{C.GREEN}▶ {C.R}" if r == rank else "  "
                lines.append(f"  {marker}{C.DARK}[{r}]{C.R} {C.WHITE}{v}{C.R}")

    mp_cost = found_data.get("mp_cost")
    if isinstance(mp_cost, dict) and rank and rank in mp_cost:
        lines.append(f"\n  {C.BLUE}MP 소모: {mp_cost[rank]}{C.R} (현재 랭크)")
    elif isinstance(mp_cost, (int, float)):
        lines.append(f"\n  {C.BLUE}MP 소모: {mp_cost}{C.R}")

    await ctx.send(ansi("\n".join(lines)))


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 이동 시스템
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="이동")
async def move_cmd(ctx, *, destination: str = None):
    if not await _check_channel(ctx):
        return
    if destination:
        result = movement_system.move_to(ctx.author.id, destination)
    else:
        result = movement_system.show_map(ctx.author.id)
    await ctx.send(result)


# ═══════════════════════════════════════════════════════════════════════════
# 신규 명령어 — 훈련소 (수련 시스템)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="수련", aliases=["훈련소", "학교"])
async def train_cmd(ctx, *, stat: str = None):
    if not await _check_channel(ctx):
        return
    if stat:
        result = training_system.train(stat.strip())
    else:
        result = training_system.show_menu()
    await ctx.send(result)


# ─── 봇 실행 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
___BEGIN___COMMAND_DONE_MARKER___0
