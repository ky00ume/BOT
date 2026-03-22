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
from equipment_window import EquipmentWindow, create_equipment_image
import status_window
from status_window import create_status_image
from town_ui import create_town_banner, create_hunting_banner, create_gathering_banner, create_fishing_banner
import status as status_mod
from ui_theme     import C, ansi, EMBED_COLOR, FOOTERS, divider
from town_notice  import send_town_notice, make_intro_embed, make_npc_embed, make_commands_embed
from fishing      import FishingEngine
from cooking_db   import CookingEngine
from metallurgy   import MetallurgyEngine
from alarms       import setup_alarms
from responses    import get_pet_response, get_scold_response, HYNESS_PET_RESPONSES, MAJESTY_PET_RESPONSES, DRIDER_PET_RESPONSES, HYNESS_SCOLD_RESPONSES, MAJESTY_SCOLD_RESPONSES, DRIDER_SCOLD_RESPONSES
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
from special_npc  import SpecialNPCEncounterManager

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

# 특수 NPC 인카운터 매니저 초기화
encounter_manager = SpecialNPCEncounterManager(shared_player)

# 스토리 퀘스트 매니저 초기화
from story_quest import StoryQuestManager
story_quest_manager = StoryQuestManager(shared_player)
shared_player._story_quest_manager = story_quest_manager

# 보관함 엔진 초기화
from storage import StorageEngine
storage_engine = StorageEngine(shared_player)

# 이동·훈련 시스템 초기화
from movement import MovementSystem
from training import TrainingSystem
movement_system  = MovementSystem(shared_player)
training_system  = TrainingSystem(shared_player)

# 전투 스킬 역방향 맵핑 (이름 → ID)
from skills_db import COMBAT_SKILLS as _CS, MAGIC_SKILLS as _MS, RECOVERY_SKILLS as _RS
_ALL_BATTLE_SKILLS     = {**_CS, **_MS, **_RS}
_SKILL_NAME_TO_ID: dict = {v["name"]: k for k, v in _ALL_BATTLE_SKILLS.items()}



# ─── BG3 UI 이미지 전송 헬퍼 ────────────────────────────────────────────
async def _send_image(ctx, buf, filename: str = "ui.png"):
    """BytesIO 버퍼를 discord.File로 전송"""
    import io
    buf.seek(0)
    await ctx.send(file=discord.File(fp=buf, filename=filename))


async def _send_image_with_text(ctx, buf, text: str = None, filename: str = "ui.png"):
    """이미지 + 텍스트 함께 전송"""
    import io
    buf.seek(0)
    await ctx.send(content=text,
                   file=discord.File(fp=buf, filename=filename))


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
        # 호감도 데이터 복원 (affinity_full에 to_dict() 전체 포함)
        aff_full = loaded.get("affinity_full", {})
        if not aff_full:
            # 구 버전 호환: affinity_data에 affinities만 있는 경우
            aff_full = {"affinities": loaded.get("affinity_data", {})}
        affinity_manager.from_dict(aff_full)
        # 스토리 퀘스트 데이터 복원
        sq_data = loaded.get("story_quest", {})
        if sq_data:
            story_quest_manager.from_dict(sq_data)
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
    try:
        buf = create_status_image(shared_player)
        await _send_image(ctx, buf, 'status.png')
    except Exception:
        embed = status_window.create_status_embed(shared_player)
        await ctx.send(embed=embed)


@bot.command(name="장비", aliases=["장비창"])
async def equipment_cmd(ctx):
    if not await _check_channel(ctx):
        return
    try:
        buf = create_equipment_image(shared_player)
        await _send_image(ctx, buf, 'equipment.png')
    except Exception:
        ew = EquipmentWindow(shared_player)
        embed = ew.create_embed()
        await ctx.send(embed=embed)


@bot.command(name="스왑")
async def swap_cmd(ctx):
    if not await _check_channel(ctx):
        return
    msg = shared_player.swap_weapons()
    await ctx.send(ansi(f"  {C.GREEN}✔{C.R} {msg}"))


@bot.command(name="장착")
async def equip_cmd(ctx, *, item_name: str = None):
    if not await _check_channel(ctx):
        return
    if not item_name:
        await ctx.send(ansi(f"  {C.RED}✖ /장착 [아이템이름] 형식으로 입력하셰요!{C.R}"))
        return
    item_id = find_item_by_name(item_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return
    if shared_player.inventory.get(item_id, 0) == 0:
        await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]가 없슴미댜!{C.R}"))
        return
    msg = shared_player.equip_item(item_id)
    await ctx.send(ansi(f"  {C.GREEN}✔{C.R} {msg}"))


@bot.command(name="벗기", aliases=["탈착", "장비해제"])
async def unequip_cmd(ctx, slot: str = None):
    if not await _check_channel(ctx):
        return
    if not slot:
        await ctx.send(ansi(
            f"  {C.RED}✖ /벗기 [슬롯] 형식으로 입력하셰요!{C.R}\n"
            f"  {C.DARK}슬롯: main(주무기) sub(보조) body(갑옷) head(투구) hands(장갑) feet(신발){C.R}"
        ))
        return
    msg = shared_player.unequip_item(slot.lower())
    if "올바른 슬롯" in msg or "비어있" in msg:
        await ctx.send(ansi(f"  {C.RED}✖ {msg}{C.R}"))
    else:
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
    """NPC에게 아이템을 선물합니다. 아이템 이름 생략 시 인벤토리 선택 UI 표시."""
    if not await _check_channel(ctx):
        return

    if not npc_name:
        await ctx.send(ansi(
            f"  {C.RED}✖ /선물 [NPC이름] 또는 /선물 [NPC이름] [아이템이름] 형식으로 입력하셰요!{C.R}\n"
            f"  예시: /선물 다몬   또는   /선물 다몬 철 주괴"
        ))
        return

    from database import NPC_DATA
    npc = NPC_DATA.get(npc_name)
    if not npc:
        await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return

    # 특수 NPC 처리
    special_npcs = {"라파엘", "카르니스", "루바토"}
    if npc_name in special_npcs:
        from npc_dialogue_db import NPC_GIFT_REACTIONS
        reactions = NPC_GIFT_REACTIONS.get(npc_name, {})
        msg = reactions.get("special", "선물은 필요 없어.")
        await ctx.send(ansi(
            f"  {C.GOLD}🎁 {npc['name']}{C.R}\n"
            f"  {C.DARK}─────────────────────────────{C.R}\n"
            f"  {C.WHITE}\"{msg}\"{C.R}"
        ))
        return

    # 아이템 이름이 직접 주어진 경우: 기존 처리
    if item_name:
        await _process_gift(ctx, npc_name, item_name)
        return

    # 아이템 이름 없으면 인벤토리 Select UI 표시
    inventory = shared_player.inventory
    if not inventory:
        await ctx.send(ansi(f"  {C.RED}✖ 인벤토리가 비어 있슴미댜!{C.R}"))
        return

    # 선물 가능 아이템 목록 (인벤토리 보유 아이템)
    options = []
    for item_id, count in list(inventory.items())[:25]:
        item_info = ALL_ITEMS.get(item_id, {})
        item_display = item_info.get("name", item_id)
        options.append(discord.SelectOption(
            label=f"{item_display} (x{count})",
            value=item_id,
            description=item_info.get("desc", "")[:100] if item_info.get("desc") else "",
        ))

    if not options:
        await ctx.send(ansi(f"  {C.RED}✖ 선물할 수 있는 아이템이 없슴미댜!{C.R}"))
        return

    select = discord.ui.Select(
        placeholder=f"{npc_name}에게 선물할 아이템을 선택하셰요",
        options=options,
    )

    async def select_callback(interaction: discord.Interaction):
        selected_item_id = select.values[0]
        item_info = ALL_ITEMS.get(selected_item_id, {})
        item_display = item_info.get("name", selected_item_id)
        await interaction.response.defer()
        await _process_gift_by_id(ctx, npc_name, selected_item_id, item_display)

    select.callback = select_callback
    view = discord.ui.View(timeout=60.0)
    view.add_item(select)

    await ctx.send(
        ansi(
            f"  {C.GOLD}🎁 {npc['name']}에게 선물{C.R}\n"
            f"  {C.DARK}아래에서 선물할 아이템을 선택하셰요.{C.R}"
        ),
        view=view,
    )


async def _process_gift(ctx, npc_name: str, item_name: str):
    """아이템 이름으로 선물을 처리합니다."""
    item_id = find_item_by_name(item_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return
    item_info = ALL_ITEMS.get(item_id, {})
    item_display = item_info.get("name", item_id)
    await _process_gift_by_id(ctx, npc_name, item_id, item_display)


async def _process_gift_by_id(ctx, npc_name: str, item_id: str, item_display: str):
    """아이템 ID로 선물을 처리합니다."""
    from database import NPC_DATA
    npc = NPC_DATA.get(npc_name)
    if not npc:
        await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
        return

    if shared_player.inventory.get(item_id, 0) == 0:
        await ctx.send(ansi(f"  {C.RED}✖ [{item_display}]이(가) 인벤토리에 없슴미댜!{C.R}"))
        return

    shared_player.remove_item(item_id, 1)
    result = affinity_manager.give_gift(npc_name, item_id)
    amount, reaction, leveled, lv_name, limit_exceeded = result

    if limit_exceeded:
        # 아이템은 이미 소비됨 — 환불
        shared_player.add_item(item_id, 1)
        await ctx.send(ansi(
            f"  {C.GOLD}🎁 {npc['name']}{C.R}\n"
            f"  {C.DARK}─────────────────────────────{C.R}\n"
            f"  {C.RED}\"{reaction}\"{C.R}"
        ))
        return

    pts = affinity_manager.affinities.get(npc_name, 0)
    lines = [
        f"  {C.GOLD}🎁 {npc['name']}에게 선물!{C.R}",
        f"  {C.WHITE}{item_display}{C.R} 을(를) {npc['name']}에게 선물했슴미댜!",
        f"  {C.DARK}─────────────────────────────{C.R}",
        f"  {C.WHITE}\"{reaction}\"{C.R}",
        f"  {C.DARK}─────────────────────────────{C.R}",
    ]
    if amount > 0:
        lines.append(f"  {C.PINK}💖 호감도 +{amount}{C.R}  (현재 {pts}pt)")
    elif amount < 0:
        lines.append(f"  {C.RED}💔 호감도 {amount}{C.R}  (현재 {pts}pt)")
    if leveled:
        lines.append(f"  {C.PINK}✦ 호감도 단계 상승! → [{lv_name}]{C.R}")

    await ctx.send(ansi("\n".join(lines)))


# ═══════════════════════════════════════════════════════════════════════════
# 마을 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="공지")
async def notice_cmd(ctx):
    if not await _check_channel(ctx):
        return
    await send_town_notice(ctx.channel)


@bot.command(name="비전타운", aliases=["마을"])
async def vision_town_cmd(ctx):
    if not await _check_channel(ctx):
        return
    from town_ui import VisionTownView, _make_town_embed
    # BG3 마을 배너
    try:
        _bnr = create_town_banner('비전타운')
        await _send_image(ctx, _bnr, 'banner_town.png')
    except Exception:
        pass
    embed = _make_town_embed(village_manager)
    view = VisionTownView(shared_player, affinity_manager, npc_manager, village_manager)
    await ctx.send(embed=embed, view=view)


@bot.command(name="대화")
async def talk_cmd(ctx, *, name: str = None):
    if not await _check_channel(ctx):
        return
    if name:
        await ctx.send(ansi(
            f"  {C.RED}✖ /대화 [NPC이름] 형식은 더 이상 지원하지 않슴미댜!\n"
            f"  {C.GREEN}/비전타운{C.R} 또는 {C.GREEN}/마을상태{C.R} 로 NPC에게 접근해주셰요."
        ))
        return
    msg = npc_manager.list_npcs()
    await ctx.send(msg)


@bot.command(name="특수키워드")
async def special_keyword_cmd(ctx, npc_name: str = None, *, keyword: str = None):
    """특수 NPC 인카운터 중 키워드 대화."""
    if not await _check_channel(ctx):
        return
    if not npc_name or not keyword:
        await ctx.send(ansi(f"  {C.RED}✖ /특수키워드 [NPC이름] [키워드] 형식으로 입력하셰요!{C.R}"))
        return
    from special_npc import SPECIAL_NPCS
    if npc_name not in SPECIAL_NPCS:
        await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]은(는) 특수 NPC가 아님미댜.{C.R}"))
        return
    active = encounter_manager.get_active_encounter()
    if active != npc_name:
        await ctx.send(ansi(
            f"  {C.RED}✖ 현재 {npc_name}(이)가 근처에 없슴미댜. 인카운터를 기다리셰요!{C.R}"
        ))
        return
    # 특수 NPC도 동일한 임베드+버튼 대화 시스템 활용
    from npc_conversation import ConversationManager
    aff_mgr = getattr(shared_player, "_affinity_manager", None)
    conv = ConversationManager(shared_player, aff_mgr, npc_manager)
    await conv.send_conversation(ctx, npc_name)


@bot.command(name="계약확인")
async def contract_check_cmd(ctx):
    """라파엘 계약 현황 확인."""
    if not await _check_channel(ctx):
        return
    result = encounter_manager.check_contract_status()
    await ctx.send(result)


@bot.command(name="계약수락")
async def contract_accept_cmd(ctx):
    """라파엘 계약 수락."""
    if not await _check_channel(ctx):
        return
    active = encounter_manager.get_active_encounter()
    if active != "라파엘":
        await ctx.send(ansi(f"  {C.RED}✖ 라파엘이 근처에 없슴미댜. 인카운터를 기다리셰요!{C.R}"))
        return
    result = encounter_manager.accept_contract()
    await ctx.send(result)


@bot.command(name="계약거절")
async def contract_reject_cmd(ctx):
    """라파엘 계약 거절."""
    if not await _check_channel(ctx):
        return
    result = encounter_manager.reject_contract()
    await ctx.send(result)


@bot.command(name="계약완료")
async def contract_complete_cmd(ctx):
    """라파엘 계약 완료 보상 수령."""
    if not await _check_channel(ctx):
        return
    result = encounter_manager.complete_contract()
    await ctx.send(result)


@bot.command(name="루바토버프")
async def lubato_buff_cmd(ctx):
    """루바토 인카운터 시 노래 버프 받기."""
    if not await _check_channel(ctx):
        return
    result = encounter_manager.apply_lubato_buff()
    await ctx.send(result)


@bot.command(name="알바")
async def job_cmd(ctx, *, name: str = None):
    if not await _check_channel(ctx):
        return
    if not name:
        await ctx.send(ansi(f"  {C.RED}✖ /알바 [NPC이름] 형식으로 입력하셰요!{C.R}"))
        return
    # 다른 행동 시 인카운터 NPC 퇴장 처리
    departure = encounter_manager.clear_encounter()
    if departure:
        await ctx.send(departure)
    await npc_manager.start_job_async(ctx, name)
    # 인카운터 체크
    enc_msg = encounter_manager.trigger_encounter()
    if enc_msg:
        await ctx.send(enc_msg)


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
    # 다른 행동 시 인카운터 NPC 퇴장 처리
    departure = encounter_manager.clear_encounter()
    if departure:
        await ctx.send(departure)
    success, result = battle_engine.start_encounter(zone)
    # BG3 배너: 사냥터 진입
    try:
        from monsters_db import MONSTERS_DB as _MDB
        _zd = _MDB.get(zone, {})
        banner_buf = create_hunting_banner(zone, _zd.get('name', zone), _zd.get('desc', ''))
        await _send_image(ctx, banner_buf, 'banner_hunting.png')
    except Exception:
        pass
    # 전투 시작 카드
    if success:
        try:
            _bimg = battle_engine.build_battle_image()
            if _bimg:
                await _send_image(ctx, _bimg, 'battle.png')
            else:
                raise Exception('no image')
        except Exception:
            if isinstance(result, discord.Embed):
                await ctx.send(embed=result)
            else:
                await ctx.send(ansi(result) if not str(result).startswith('```') else result)
    else:
        if isinstance(result, discord.Embed):
            await ctx.send(embed=result)
        else:
            await ctx.send(ansi(result) if not str(result).startswith('```') else result)
    # 인카운터 체크 (사냥 후)
    if success:
        enc_msg = encounter_manager.trigger_encounter()
        if enc_msg:
            await ctx.send(enc_msg)


@bot.command(name="공격")
async def attack_cmd(ctx, *, skill_input: str = "smash"):
    if not await _check_channel(ctx):
        return
    if not battle_engine.in_battle:
        await ctx.send(ansi(f"  {C.RED}✖ 현재 전투 중이 아님미댜! /사냥 으로 전투 시작.{C.R}"))
        return

    # 스킬 이름 → ID 변환 (모듈 레벨 캐시 사용)
    skill_id = skill_input.strip()
    if skill_id not in _ALL_BATTLE_SKILLS:
        skill_id = _SKILL_NAME_TO_ID.get(skill_id, skill_id)

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

    # BG3 전투 카드
    try:
        _sname = _ALL_BATTLE_SKILLS.get(skill_id, {}).get('name', skill_id)
        _bimg = battle_engine.build_battle_image(_sname)
        if _bimg:
            await _send_image(ctx, _bimg, 'battle.png')
        else:
            raise Exception('no image')
    except Exception:
        if isinstance(result, discord.Embed):
            await ctx.send(embed=result)
        else:
            await ctx.send(ansi(result) if not str(result).startswith('```') else result)
    # 전투 종료 텍스트 (승리/패배)
    if not battle_engine.in_battle:
        if isinstance(result, discord.Embed):
            await ctx.send(embed=result)
        else:
            await ctx.send(ansi(result) if not str(result).startswith('```') else result)


@bot.command(name="도주")
async def flee_cmd(ctx):
    if not await _check_channel(ctx):
        return
    result = battle_engine.flee()
    if isinstance(result, discord.Embed):
        await ctx.send(embed=result)
    else:
        await ctx.send(ansi(str(result)))


# ═══════════════════════════════════════════════════════════════════════════
# 낚시 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="낚시")
async def fishing_cmd(ctx):
    if not await _check_channel(ctx):
        return
    # BG3 낚시터 배너
    try:
        _loc = getattr(shared_player, 'current_location', '지하 강')
        from town_ui import create_fishing_banner
        _buf = create_fishing_banner(_loc, _loc, '')
        await _send_image(ctx, _buf, 'banner_fishing.png')
    except Exception:
        pass
    departure = encounter_manager.clear_encounter()
    if departure:
        await ctx.send(departure)
    await fishing_engine.fish(ctx)
    enc_msg = encounter_manager.trigger_encounter()
    if enc_msg:
        await ctx.send(enc_msg)


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
async def smelt_cmd(ctx, *, ore_input: str = None):
    if not await _check_channel(ctx):
        return
    if not ore_input:
        result = metallurgy_engine.show_recipe_list()
        await ctx.send(result)
        return
    result = metallurgy_engine.smelt(ore_input)
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
async def craft_item_cmd(ctx, *, result_id: str = None):
    if not await _check_channel(ctx):
        return
    if not result_id:
        embeds = crafting_engine.get_recipe_embeds()
        for emb in embeds:
            await ctx.send(embed=emb)
        return
    result = crafting_engine.craft(result_id)
    await ctx.send(result)


@bot.command(name="제작도감")
async def craft_guide_cmd(ctx):
    if not await _check_channel(ctx):
        return
    embeds = crafting_engine.get_recipe_embeds()
    for emb in embeds:
        await ctx.send(embed=emb)


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
            "`/장착 [아이템이름]` — 장비 장착\n"
            "`/벗기 [슬롯]` — 장비 탈착 (`/탈착` `/장비해제` 동일)\n"
            "`/스왑` — 주·보조 무기 교환\n"
            "`/치료` — HP/MP 회복 (50G)\n"
            "`/먹기 [아이템이름]` — 아이템 섭취\n"
            "`/휴식` — 기력 회복 (3분 쿨타임)\n"
            "`/쓰담` — 츄라이더를 쓰다듬기 💕 (`/복복` `/북북` `/쓰다듬` 등 동일)\n"
            "`/혼내기` — 츄라이더 혼내기 😤 (`/훈육` 동일)\n"
            "`/버리기 [아이템이름] [수량]` — 아이템 버리기\n"
            "`/타이틀 [이름]` — 보유 타이틀 목록/장착\n"
            "`/업적` — 업적 목록 보기\n"
            "`/도감 [카테고리]` — 도감 보기\n"
            "`/일기 [날짜]` — 일기 보기\n"
            "`/아이템목록` — 전체 아이템 목록(CSV)"
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
            "`/치료` — 치료사 방문\n"
            "`/이동 [장소]` — 맵 이동 (3분 쿨타임)"
        ),
        inline=False,
    )
    embed.add_field(
        name="🛒 상점",
        value=(
            "`/구매목록 [NPC이름]` — NPC 판매 목록\n"
            "`/구매 [NPC이름] [아이템이름]` — 구매\n"
            "`/판매목록` — 인벤토리 판매 목록\n"
            "`/판매 [아이템이름]` — 아이템 판매\n"
            "`/보관함` — 보관함 보기\n"
            "`/보관함넣기 [아이템이름] [수량]` — 보관함에 넣기\n"
            "`/보관함꺼내기 [아이템이름] [수량]` — 보관함에서 꺼내기\n"
            "`/보관함업그레이드` — 보관함 확장"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚔ 전투",
        value=(
            "`/사냥터` — 사냥터 목록\n"
            "`/사냥 [사냥터이름]` — 전투 시작\n"
            "`/공격 [스킬ID]` — 공격 (기본: smash)\n"
            "`/도주` — 전투 이탈\n"
            "`/스킬 [스킬이름]` — 스킬 설명·효과 조회 (`/스킬조회` 동일)"
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
            "`/물뜨기 [수량]` — 빈 병으로 물 뜨기\n"
            "`/날씨` — 현재 날씨 확인\n"
            "`/수련 [스탯]` — 훈련소 스탯 수련 (`/훈련소` `/학교` 동일)"
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
        name="📖 스토리",
        value=(
            "`/스토리` — 스토리 퀘스트 저널\n"
            "`/스토리퀘스트` — 다음 스토리 퀘스트 진행\n"
            "`/스토리탐색` — 늪지대 탐색 (챕터 3 Q2)\n"
            "`/스토리수집` — 재료 수집 (챕터 2 Q2)\n"
            "`/스토리힌트` — 수집한 힌트 목록\n"
            "`/그림자` — 그림자의 상태 확인"
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
    departure = encounter_manager.clear_encounter()
    if departure:
        await ctx.send(departure)
    await gathering_engine.gather(ctx)
    enc_msg = encounter_manager.trigger_encounter()
    if enc_msg:
        await ctx.send(enc_msg)


@bot.command(name="채광")
async def mine_cmd(ctx):
    if not await _check_channel(ctx):
        return
    departure = encounter_manager.clear_encounter()
    if departure:
        await ctx.send(departure)
    await gathering_engine.mine(ctx)
    enc_msg = encounter_manager.trigger_encounter()
    if enc_msg:
        await ctx.send(enc_msg)


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
    from quest_ui import QuestWindowView, make_quest_embed
    embed = make_quest_embed(quest_manager)
    view = QuestWindowView(quest_manager, shared_player)
    await ctx.send(embed=embed, view=view)


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
    uid = ctx.author.id
    if uid == HYNESS_ID:
        msg = random.choice(HYNESS_PET_RESPONSES)
    elif uid == MAJESTY_ID:
        msg = random.choice(MAJESTY_PET_RESPONSES)
    elif uid == DRIDER_ID:
        msg = random.choice(DRIDER_PET_RESPONSES)
    else:
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
REST_COOLDOWN_SEC = 180  # 3분


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

    # 퀘스트 아이템 버리기 차단
    from items import ALL_ITEMS as _ALL_ITEMS_CHECK
    if _ALL_ITEMS_CHECK.get(item_id, {}).get("quest_locked"):
        await ctx.send(ansi(f"  {C.RED}❌ 퀘스트 아이템은 버릴 수 없슴미댜!{C.R}"))
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
    uid = ctx.author.id
    if uid == HYNESS_ID:
        msg = random.choice(HYNESS_SCOLD_RESPONSES)
    elif uid == MAJESTY_ID:
        msg = random.choice(MAJESTY_SCOLD_RESPONSES)
    elif uid == DRIDER_ID:
        msg = random.choice(DRIDER_SCOLD_RESPONSES)
    else:
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
# 신규 명령어 — 스킬 습득 (스킬북 사용)
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="스킬습득", aliases=["스킬사용", "스킬배우기"])
async def learn_skill_cmd(ctx, *, book_name: str = None):
    if not await _check_channel(ctx):
        return
    if not book_name:
        await ctx.send(ansi(f"  {C.RED}✖ /스킬습득 [스킬북이름] 형식으로 입력하셰요!{C.R}"))
        return
    from items import ALL_ITEMS
    from shop import find_item_by_name
    item_id = find_item_by_name(book_name)
    if not item_id:
        await ctx.send(ansi(f"  {C.RED}✖ [{book_name}] 아이템을 찾을 수 없슴미댜!{C.R}"))
        return
    item = ALL_ITEMS.get(item_id, {})
    if item.get("type") != "skillbook":
        await ctx.send(ansi(f"  {C.RED}✖ [{item.get('name', item_id)}]은(는) 스킬북이 아님미댜!{C.R}"))
        return
    if shared_player.inventory.get(item_id, 0) < 1:
        await ctx.send(ansi(f"  {C.RED}✖ [{item.get('name', item_id)}]이(가) 인벤토리에 없슴미댜!{C.R}"))
        return
    skill_id = item.get("skill_id")
    if not skill_id:
        await ctx.send(ansi(f"  {C.RED}✖ 이 스킬북에 연결된 스킬이 없슴미댜!{C.R}"))
        return
    if skill_id in shared_player.skill_ranks:
        await ctx.send(ansi(f"  {C.GOLD}이미 [{item.get('name', item_id)}] 스킬을 보유하고 있슴미댜!{C.R}"))
        return
    shared_player.remove_item(item_id, 1)
    shared_player.skill_ranks[skill_id] = "연습"
    shared_player.skill_exp[skill_id] = 0.0
    from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS
    all_defs = {**COMBAT_SKILLS, **MAGIC_SKILLS, **RECOVERY_SKILLS, **OTHER_SKILLS}
    skill_name = all_defs.get(skill_id, {}).get("name", skill_id)
    await ctx.send(ansi(
        f"  {C.GREEN}✔ [{skill_name}] 스킬을 습득했슴미댜! [연습 랭크]{C.R}\n"
        f"  {C.DARK}/스킬 {skill_name} 으로 상세 확인{C.R}"
    ))

@bot.command(name="이동")
async def move_cmd(ctx, *, destination: str = None):
    if not await _check_channel(ctx):
        return
    if destination:
        result = movement_system.move_to(ctx.author.id, destination)
        # BG3 이동 배너
        try:
            from town_ui import create_location_banner
            from database import HUNTING_GROUNDS, GATHERING_SPOTS
            if destination in HUNTING_GROUNDS:
                _zd = HUNTING_GROUNDS[destination]
                _buf = create_location_banner(_zd.get('name',destination), _zd.get('desc',''), 'hunting', destination)
            else:
                _buf = create_location_banner(destination, '', 'town', destination)
            await _send_image(ctx, _buf, 'banner_move.png')
        except Exception:
            pass
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


# ═══════════════════════════════════════════════════════════════════════════
# 스토리 퀘스트 명령어
# ═══════════════════════════════════════════════════════════════════════════

@bot.command(name="스토리")
async def story_cmd(ctx):
    """현재 스토리 퀘스트 저널 표시 (챕터/퀘스트 진행도)."""
    if not await _check_channel(ctx):
        return
    from story_quest_ui import make_story_journal_embed
    embed = make_story_journal_embed(story_quest_manager)
    await ctx.send(embed=embed)


@bot.command(name="스토리퀘스트")
async def story_quest_cmd(ctx):
    """현재 챕터의 다음 스토리 퀘스트를 진행합니다."""
    if not await _check_channel(ctx):
        return
    from story_quest_data import STORY_CHAPTERS, CH1_QUESTS, CH2_QUESTS, CH3_QUESTS
    from story_quest_ui import ShadowChoiceView, ForcedBattleView, play_cutscene

    ch  = story_quest_manager.chapter
    q   = story_quest_manager.quest

    # 챕터 4는 미해금
    if ch >= 4:
        await ctx.send(ansi(
            f"  {C.DARK}🔒 챕터 4 《거미줄과 속박》 — 미해금{C.R}\n"
            f"  {C.DARK}다음 이야기는 아직 쓰이지 않았습니다.{C.R}"
        ))
        return

    ch_data = STORY_CHAPTERS.get(ch, {})
    if ch_data.get("locked"):
        await ctx.send(ansi(f"  {C.DARK}🔒 이 챕터는 아직 해금되지 않았슴미댜.{C.R}"))
        return

    quests_map = {1: CH1_QUESTS, 2: CH2_QUESTS, 3: CH3_QUESTS}
    quests = quests_map.get(ch, {})
    qdata  = quests.get(q)
    if not qdata:
        await ctx.send(ansi(f"  {C.GOLD}✔ 챕터 {ch}의 모든 퀘스트를 완료했슴미댜!{C.R}"))
        return

    already_done = story_quest_manager.is_quest_done(ch, q)

    # ── 챕터 1 퀘스트 처리 ─────────────────────────────────────────────
    if ch == 1:
        if q in (1, 2, 3):
            # NPC 대화 퀘스트
            if already_done:
                await ctx.send(ansi(
                    f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"
                ))
                return
            npc_name = qdata["npc"]
            hint     = qdata["hint"]
            dialogue = qdata["dialogue"]
            lines = [
                header_box(f"📜 챕터 1 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 {npc_name}{C.R}",
                divider(),
                f"  {C.WHITE}\"{dialogue}\"{C.R}",
                divider(),
                f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
            ]
            # 호감도 보상
            aff_rewards = qdata.get("rewards", {}).get("affinity", {})
            for npc, pts in aff_rewards.items():
                if affinity_manager:
                    affinity_manager.add_affinity(npc, pts)
                lines.append(f"  {C.PINK}💖 {npc} 호감도 +{pts}{C.R}")
            story_quest_manager.add_hint(hint)
            # 키워드 해금
            kw = qdata.get("keyword")
            if kw and kw not in shared_player.keywords:
                shared_player.keywords.append(kw)
                lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest = q + 1
            save_player_to_db(shared_player)
            await ctx.send(ansi("\n".join(lines)))

        elif q == 4:
            # 그림자와의 공명 — 선택지
            if already_done:
                await ctx.send(ansi(
                    f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"
                ))
                return
            lines = [
                header_box("🌑 그림자와의 공명"),
                divider(),
                f"  {C.WHITE}그림자 등불에 대한 이야기를 들은 후, 어둠이 속삭인다.{C.R}",
                f"  {C.DARK}...당신은 어떤 존재이고 싶은가?{C.R}",
                divider(),
            ]
            view = ShadowChoiceView(
                qdata["choices"], story_quest_manager, shared_player
            )
            msg = await ctx.send(ansi("\n".join(lines)), view=view)
            # 완료 처리 (선택 후 자동)
            await view.wait()
            if view.chosen:
                # 아이템 지급
                item_id = qdata.get("item")
                if item_id:
                    shared_player.add_item(item_id)
                # 칭호 지급
                title = qdata.get("title_reward")
                if title and title not in shared_player.titles:
                    shared_player.titles.append(title)
                story_quest_manager.complete_quest(ch, q)
                story_quest_manager.quest  = 1
                story_quest_manager.chapter = 2
                save_player_to_db(shared_player)
                await ctx.send(ansi(
                    f"  {C.GREEN}✔ 챕터 1 완료! 챕터 2 《픽시의 흔적》으로 진행합니다.{C.R}\n"
                    + (f"  {C.GOLD}🏅 칭호 획득: [{title}]{C.R}" if title else "")
                    + (f"\n  {C.CYAN}📦 아이템 획득: [{item_id}]{C.R}" if item_id else "")
                ))

    # ── 챕터 2 퀘스트 처리 ─────────────────────────────────────────────
    elif ch == 2:
        if q == 1:
            # 마법적 조언
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            hint = qdata["hint"]
            dialogue = qdata["dialogue"]
            lines = [
                header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 게일의 환영{C.R}",
                divider(),
                f"  {C.WHITE}\"{dialogue}\"{C.R}",
                divider(),
                f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
            ]
            story_quest_manager.add_hint(hint)
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest = 2
            save_player_to_db(shared_player)
            await ctx.send(ansi("\n".join(lines)))

        elif q == 2:
            # 갇힌 자의 노래 — 수집 미션 안내
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            lines = [
                header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 알피라{C.R}",
                divider(),
                f"  {C.WHITE}\"{qdata['dialogue_alpira']}\"{C.R}",
                divider(),
                f"  {C.GOLD}💬 아라벨라{C.R}",
                f"  {C.WHITE}\"{qdata['dialogue_arabella']}\"{C.R}",
                divider(),
                f"  {C.CYAN}📋 수집 미션: [{qdata['collect_item'].replace('sq_', '')}] × {qdata['collect_count']}{C.R}",
                f"  {C.DARK}→ 방울숲에서 그림자 몬스터를 사냥해 획득 (드롭률 {int(qdata['drop_rate']*100)}%){C.R}",
                f"  {C.DARK}→ /스토리수집 으로 사냥 시작{C.R}",
            ]
            await ctx.send(ansi("\n".join(lines)))

        elif q == 3:
            # 금기된 의식의 기록 — 선택지
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            hint = qdata["hint"]
            lines = [
                header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 엘레라신{C.R}",
                divider(),
                f"  {C.WHITE}\"{qdata['dialogue']}\"{C.R}",
                divider(),
                f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
                divider(),
                f"  {C.DARK}당신의 반응은?{C.R}",
            ]
            view = ShadowChoiceView(
                qdata["choices"], story_quest_manager, shared_player
            )
            await ctx.send(ansi("\n".join(lines)), view=view)
            await view.wait()
            if view.chosen:
                story_quest_manager.add_hint(hint)
                story_quest_manager.complete_quest(ch, q)
                story_quest_manager.quest = 4
                save_player_to_db(shared_player)

        elif q == 4:
            # 등불의 설계도
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            lines = [
                header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 다몬{C.R}",
                divider(),
                f"  {C.WHITE}\"{qdata['dialogue_damon']}\"{C.R}",
                divider(),
                f"  {C.GOLD}💬 오멜룸{C.R}",
                f"  {C.WHITE}\"{qdata['dialogue_omelum']}\"{C.R}",
                divider(),
            ]
            item_id = qdata.get("item_reward")
            title   = qdata.get("title_reward")
            if item_id:
                shared_player.add_item(item_id)
                lines.append(f"  {C.CYAN}📦 아이템 획득: [수리된 문랜턴 외형]{C.R}")
            if title and title not in shared_player.titles:
                shared_player.titles.append(title)
                lines.append(f"  {C.GOLD}🏅 칭호 획득: [{title}]{C.R}")
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest   = 1
            story_quest_manager.chapter = 3
            save_player_to_db(shared_player)
            lines.append(f"  {C.GREEN}✔ 챕터 2 완료! 챕터 3 《선택의 무게》로 진행합니다.{C.R}")
            await ctx.send(ansi("\n".join(lines)))

    # ── 챕터 3 퀘스트 처리 ─────────────────────────────────────────────
    elif ch == 3:
        if q == 1:
            # 마지막 재료
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            lines = [
                header_box(f"📜 챕터 3 Q{q}: {qdata['title']}"),
                f"  {C.GOLD}💬 몰{C.R}",
                divider(),
                f"  {C.WHITE}\"{qdata['dialogue']}\"{C.R}",
                divider(),
            ]
            item_id = qdata.get("item_reward")
            if item_id:
                shared_player.add_item(item_id)
                lines.append(f"  {C.CYAN}📦 아이템 획득: [몰의 지도 조각]{C.R}")
            # 늪지대 해금 플래그
            story_quest_manager.flags["늪지대_해금"] = True
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest = "gate"
            save_player_to_db(shared_player)
            lines.append(f"  {C.GREEN}🗺️ 늪지대 이동 가능! /이동 늪지대{C.R}")
            await ctx.send(ansi("\n".join(lines)))

        elif q == "gate" or story_quest_manager.flags.get("at_gate"):
            # 성문 통과
            gate_data = CH3_QUESTS.get("gate", {})
            if story_quest_manager.is_quest_done(ch, "gate"):
                await ctx.send(ansi(f"  {C.GOLD}✔ [성문 통과] 이미 완료했슴미댜!{C.R}"))
                return
            lines = [
                header_box("📜 챕터 3 — 성문 통과"),
                f"  {C.GOLD}💬 제블로어{C.R}",
                divider(),
                f"  {C.WHITE}\"{gate_data.get('dialogue', '...')}\"{C.R}",
                divider(),
                f"  {C.GREEN}늪지대 진입 허가!{C.R}",
            ]
            story_quest_manager.complete_quest(ch, "gate")
            story_quest_manager.quest = 2
            save_player_to_db(shared_player)
            await ctx.send(ansi("\n".join(lines)))

        elif q == 2:
            await ctx.send(ansi(
                f"  {C.CYAN}/스토리탐색{C.R} 명령어로 늪지대 탐색을 진행하세요!"
            ))

        elif q == 3:
            # 시끄러운 불청객 — 픽시 컷신
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            scenes = []
            for dlg in qdata["dialogues"]:
                scenes.append(
                    f"  {C.GOLD}✨ 픽시{C.R}\n"
                    f"  {C.WHITE}\"{dlg}\"{C.R}"
                )
            await play_cutscene(ctx, scenes, delay=3.0)

            # shadow_sync 자동 분기
            sync = story_quest_manager.shadow_sync
            reactions = qdata["auto_reactions"]
            if sync >= reactions["dark"]["threshold"]:
                result = reactions["dark"]
            elif sync <= reactions["light"]["threshold"]:
                result = reactions["light"]
            else:
                result = reactions["neutral"]

            story_quest_manager.add_shadow_sync(result["shadow_sync"])
            await ctx.send(ansi(
                f"  {C.DARK}─────────────────────────────{C.R}\n"
                f"  {C.WHITE}{result['text']}{C.R}"
            ))
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest = 4
            save_player_to_db(shared_player)

        elif q == 4:
            # 닿지 않는 전투
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return

            async def on_battle_done(interaction):
                story_quest_manager.complete_quest(ch, 4)
                story_quest_manager.quest = 5
                save_player_to_db(shared_player)
                await interaction.channel.send(ansi(
                    f"  {C.RED}★ 전투 종료 — 도달할 수 없었다.{C.R}\n"
                    f"  {C.DARK}/스토리퀘스트 로 다음 장면을 진행하세요.{C.R}"
                ))

            lines = [
                header_box("⚔️  닿지 않는 전투"),
                f"  {C.WHITE}픽시가 공중으로 솟구쳤다.{C.R}",
                divider(),
                f"  {C.DARK}공격 버튼을 눌러 전투를 진행하세요.{C.R}",
            ]
            view = ForcedBattleView(
                qdata["turns"], story_quest_manager, shared_player,
                on_done_coro=on_battle_done
            )
            await ctx.send(ansi("\n".join(lines)), view=view)

        elif q == 5:
            # 추락한 포식자 — 엔딩 컷신
            if already_done:
                await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                return
            ending = qdata["ending_text"]
            lines = [
                header_box("📜 챕터 3 엔딩 — 추락한 포식자"),
                divider(),
                f"  {C.WHITE}{ending}{C.R}",
                divider(),
            ]
            title = qdata.get("title_reward")
            item_id = qdata.get("item_reward")
            if title and title not in shared_player.titles:
                shared_player.titles.append(title)
                lines.append(f"  {C.GOLD}🏅 칭호 획득: [{title}] (원거리 명중률 +3%){C.R}")
            if item_id:
                shared_player.add_item(item_id)
                lines.append(f"  {C.CYAN}📦 아이템 획득: [한 줌의 픽시 가루]{C.R}")
            story_quest_manager.complete_quest(ch, q)
            story_quest_manager.quest   = 1
            story_quest_manager.chapter = 4
            save_player_to_db(shared_player)
            lines.append(divider())
            lines.append(f"  {C.DARK}🔒 챕터 4 《거미줄과 속박》 — 미해금{C.R}")
            lines.append(f"  {C.DARK}다음 이야기는 아직 쓰이지 않았습니다.{C.R}")
            await ctx.send(ansi("\n".join(lines)))


@bot.command(name="스토리탐색")
async def story_explore_cmd(ctx):
    """늪지대 탐색 퀘스트 실행 (챕터 3 Q2 전용, 3단계)."""
    if not await _check_channel(ctx):
        return
    from story_quest_data import CH3_QUESTS
    from story_quest_ui import ExploreView

    ch = story_quest_manager.chapter
    q  = story_quest_manager.quest
    if ch != 3 or q != 2:
        await ctx.send(ansi(
            f"  {C.RED}✖ 탐색은 챕터 3 Q2에서만 가능합미댜!{C.R}\n"
            f"  {C.DARK}현재: 챕터 {ch} Q{q}{C.R}"
        ))
        return

    if story_quest_manager.is_quest_done(3, 2):
        await ctx.send(ansi(f"  {C.GOLD}✔ 탐색을 이미 완료했슴미댜!{C.R}"))
        return

    if not story_quest_manager.flags.get("늪지대_해금"):
        await ctx.send(ansi(f"  {C.RED}✖ 아직 늪지대에 진입할 수 없슴미댜.{C.R}"))
        return

    qdata = CH3_QUESTS[2]

    async def on_explore_done(interaction):
        story_quest_manager.complete_quest(3, 2)
        story_quest_manager.quest = 3
        save_player_to_db(shared_player)
        await interaction.channel.send(ansi(
            f"  {C.GOLD}✔ 탐색 완료! 무언가 발견됐슴미댜...{C.R}\n"
            f"  {C.GREEN}/스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}"
        ))

    lines = [
        header_box("🌫️  늪지대 탐색"),
        f"  {C.DARK}안개와 진흙으로 뒤덮인 음습한 늪지대.{C.R}",
        divider(),
    ]
    view = ExploreView(
        qdata["step_descs"], story_quest_manager, shared_player,
        on_done_coro=on_explore_done
    )
    await ctx.send(ansi("\n".join(lines)), view=view)


@bot.command(name="스토리수집")
async def story_collect_cmd(ctx):
    """챕터 2 Q2 — 픽시의 날개 가루 수집 (방울숲 전용)."""
    if not await _check_channel(ctx):
        return
    import random
    import time as _t
    from story_quest_data import CH2_QUESTS

    ch = story_quest_manager.chapter
    q  = story_quest_manager.quest
    if ch != 2 or q != 2:
        await ctx.send(ansi(
            f"  {C.RED}✖ 수집은 챕터 2 Q2에서만 가능합미댜! (현재: 챕터 {ch} Q{q}){C.R}"
        ))
        return

    if story_quest_manager.is_quest_done(2, 2):
        await ctx.send(ansi(f"  {C.GOLD}✔ 이미 완료했슴미댜!{C.R}"))
        return

    # 위치 체크
    current_loc = getattr(shared_player, "current_location", "마을")
    if current_loc != "방울숲":
        await ctx.send(ansi(
            f"  {C.RED}✖ 방울숲에 있어야 합미댜! (현재 위치: {current_loc}){C.R}\n"
            f"  {C.DARK}/이동 방울숲 으로 이동하세요.{C.R}"
        ))
        return

    # 쿨다운 체크
    qdata    = CH2_QUESTS[2]
    cooldown = qdata["drop_cooldown"]
    last_collect = story_quest_manager.flags.get("_collect_last_time", 0)
    now = _t.time()
    if now - last_collect < cooldown:
        remain = int(cooldown - (now - last_collect))
        await ctx.send(ansi(f"  {C.RED}⏳ 수집 쿨다운: {remain}초 남음{C.R}"))
        return

    story_quest_manager.flags["_collect_last_time"] = now

    # 드롭 판정
    if random.random() < qdata["drop_rate"]:
        shared_player.add_item(qdata["collect_item"])
        have = shared_player.inventory.get(qdata["collect_item"], 0)
        lines = [
            f"  {C.GREEN}✔ 픽시의 날개 가루 획득!{C.R}  ({have}/{qdata['collect_count']})",
        ]
        if have >= qdata["collect_count"]:
            story_quest_manager.complete_quest(2, 2)
            story_quest_manager.quest = 3
            save_player_to_db(shared_player)
            lines.append(f"  {C.GOLD}✔ 수집 완료! /스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}")
        await ctx.send(ansi("\n".join(lines)))
    else:
        await ctx.send(ansi(
            f"  {C.DARK}그림자 몬스터를 쓰러뜨렸지만 가루가 떨어지지 않았슴미댜.{C.R}\n"
            f"  {C.DARK}({int(qdata['drop_rate']*100)}% 확률로 드롭){C.R}"
        ))


@bot.command(name="스토리힌트")
async def story_hints_cmd(ctx):
    """수집한 힌트 목록을 표시합니다."""
    if not await _check_channel(ctx):
        return
    from story_quest_ui import make_hints_embed
    embed = make_hints_embed(story_quest_manager)
    await ctx.send(embed=embed)


@bot.command(name="그림자")
async def shadow_cmd(ctx):
    """shadow_sync 암시 텍스트를 확인합니다."""
    if not await _check_channel(ctx):
        return
    hint = story_quest_manager.get_shadow_hint()
    game_time = story_quest_manager.get_game_time()
    color = story_quest_manager.get_embed_theme(game_time)
    embed = discord.Embed(
        title="🌑 그림자의 상태",
        description=hint,
        color=color,
    )
    embed.set_footer(text="✦ 수치는 비공개임미댜 ✦")
    await ctx.send(embed=embed)


# ─── 봇 실행 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
