import discord
from discord.ext import commands, tasks
import signal
import sys

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
from database     import init_db, load_village_data
from save_manager import save_manager
import status as status_mod
from fishing      import FishingEngine
from cooking_db   import CookingEngine
from metallurgy   import MetallurgyEngine
from alarms       import setup_alarms
from items        import CONSUMABLES, COOKED_DISHES, GATHERING_ITEMS
from village      import village_manager
from gathering    import GatheringEngine
from potion       import PotionEngine
from quest        import QuestManager
from affinity     import AffinityManager
from gacha        import GachaEngine
from music        import MusicEngine
from restaurant   import RestaurantEngine
from crafting     import CraftingEngine
from collection   import collection_manager
from special_npc  import SpecialNPCEncounterManager
from care         import CareManager
from utils.logger import setup_logger

logger = setup_logger('main')

# ─── 상수 (환경변수로 관리) ────────────────────────────────────────────────
# REMEDIATION_PLAN 3-D: Discord 사용자 ID 를 소스에 하드코딩하지 않는다.
# 누락된 환경변수는 명확한 에러 메시지와 함께 즉시 실패하도록 한다.
from utils.env import (
    ConfigError as _EnvConfigError,
    load_discord_token,
    load_required_int,
)

try:
    TOKEN              = load_discord_token("DISCORD_TOKEN")
    HYNESS_ID          = load_required_int("HYNESS_ID")
    MAJESTY_ID         = load_required_int("MAJESTY_ID")
    DRIDER_ID          = load_required_int("DRIDER_ID")
    ALLOWED_CHANNEL_ID = load_required_int("ALLOWED_CHANNEL_ID")
except _EnvConfigError as _env_err:
    print(f"[오류] 환경변수 구성 실패: {_env_err}")
    print("  .env.example 을 참고해 .env 파일을 채워 주세요.")
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
care_manager      = CareManager()
shared_player._affinity_manager = affinity_manager

# 특수 NPC 인카운터 매니저 초기화
encounter_manager = SpecialNPCEncounterManager(shared_player)

# 퀘스트 매니저 플레이어에 주입 (저장/복원 연동)
shared_player._quest_manager = quest_manager

# 스토리 퀘스트 매니저 초기화
from story_quest import StoryQuestManager
story_quest_manager = StoryQuestManager(shared_player)
shared_player._story_quest_manager = story_quest_manager

# 도감 매니저 플레이어에 주입 (저장/복원 연동)
shared_player._collection_manager = collection_manager

# 보관함 엔진 초기화
from storage import StorageEngine
storage_engine = StorageEngine(shared_player)

# 이동·훈련 시스템 초기화
from movement import MovementSystem
from training import TrainingSystem
movement_system  = MovementSystem(shared_player)
training_system  = TrainingSystem(shared_player)

# 탐험 엔진 초기화
from adventure import AdventureEngine
adventure_engine = AdventureEngine(shared_player)

# 전투 스킬 역방향 맵핑 (이름 → ID)
from skills_db import COMBAT_SKILLS as _CS, MAGIC_SKILLS as _MS, RECOVERY_SKILLS as _RS
_ALL_BATTLE_SKILLS     = {**_CS, **_MS, **_RS}
_SKILL_NAME_TO_ID: dict = {v["name"]: k for k, v in _ALL_BATTLE_SKILLS.items()}

# ─── BotContext 구성 (Cog들이 공유 상태에 접근하는 컨테이너) ─────────────────
from utils.bot_context import BotContext
_bot_ctx = BotContext()
_bot_ctx.hyness_id          = HYNESS_ID
_bot_ctx.majesty_id         = MAJESTY_ID
_bot_ctx.drider_id          = DRIDER_ID
_bot_ctx.allowed_channel_id = ALLOWED_CHANNEL_ID
_bot_ctx.player             = shared_player
_bot_ctx.npc_manager        = npc_manager
_bot_ctx.shop_manager       = shop_manager
_bot_ctx.restaurant_engine  = restaurant_engine
_bot_ctx.battle_engine      = battle_engine
_bot_ctx.fishing_engine     = fishing_engine
_bot_ctx.cooking_engine     = cooking_engine
_bot_ctx.metallurgy_engine  = metallurgy_engine
_bot_ctx.gathering_engine   = gathering_engine
_bot_ctx.potion_engine      = potion_engine
_bot_ctx.quest_manager      = quest_manager
_bot_ctx.affinity_manager   = affinity_manager
_bot_ctx.gacha_engine       = gacha_engine
_bot_ctx.music_engine       = music_engine
_bot_ctx.crafting_engine    = crafting_engine
_bot_ctx.care_manager       = care_manager
_bot_ctx.encounter_manager  = encounter_manager
_bot_ctx.story_quest_manager = story_quest_manager
_bot_ctx.storage_engine     = storage_engine
_bot_ctx.movement_system    = movement_system
_bot_ctx.training_system    = training_system
_bot_ctx.adventure_engine   = adventure_engine
_bot_ctx.all_battle_skills  = _ALL_BATTLE_SKILLS
_bot_ctx.skill_name_to_id   = _SKILL_NAME_TO_ID
_bot_ctx.edible_items       = EDIBLE_ITEMS
bot.ctx = _bot_ctx


# ─── 자동 저장 루프 (2분마다) ────────────────────────────────────────────
@tasks.loop(minutes=2)
async def auto_save_loop():
    """2분마다 플레이어 데이터를 자동 저장합니다."""
    try:
        await save_manager.save_async(shared_player)
    except Exception as e:
        logger.error("[자동저장] 실패: %s", e, exc_info=True)


# ─── 이벤트 ──────────────────────────────────────────────────────────────
_bot_initialized = False  # 재접속 시 데이터 덮어쓰기 방지 가드

@bot.event
async def on_ready():
    global _bot_initialized
    print(f"[봇 시작] {bot.user} 로그인 완료")

    if _bot_initialized:
        # 재접속: 현재 인메모리 데이터를 보존하고 저장만 수행
        print("[재접속] 인메모리 데이터 보존, 강제 저장 실행")
        try:
            save_manager.save(shared_player)
        except Exception as e:
            print(f"[재접속 저장] 실패: {e}")
        return

    _bot_initialized = True

    # DB 초기화
    init_db()

    # status.json 확보
    status_mod.ensure_status_json()

    # DB에서 플레이어 로드
    loaded = save_manager.load(0)
    if loaded:
        shared_player.load_from_dict(loaded)
        # 호감도 데이터 복원 (affinity_full에 to_dict() 전체 포함)
        aff_full = loaded.get("affinity_full") or {}
        if aff_full and aff_full.get("affinities"):
            affinity_manager.from_dict(aff_full)
        # 스토리 퀘스트 데이터 복원
        sq_data = loaded.get("story_quest", {})
        if sq_data:
            story_quest_manager.from_dict(sq_data)
        # 도감 데이터 복원 (DB 우선, 없으면 파일에서)
        col_data = loaded.get("collection_data", {})
        if col_data:
            collection_manager.from_dict(col_data)
        print(f"[DB 로드] {shared_player.name} 데이터 복원 완료")
    else:
        print("[DB 로드] 저장 데이터 없음 — 기본 캐릭터로 시작")

    # 마을 기여도/레벨 DB에서 복원
    village_data = load_village_data()
    village_manager.from_dict(village_data)
    print(f"[DB 로드] 마을 기여도: {village_manager.contribution}pt, Lv.{village_manager.level}")

    # 알람 설정
    alarm_loop = setup_alarms(bot, ALLOWED_CHANNEL_ID, DRIDER_ID, hyness_id=HYNESS_ID, majesty_id=MAJESTY_ID)
    if not alarm_loop.is_running():
        alarm_loop.start()

    # ── 레벨업 사탕 1회성 지급 (츄라이더용) ─────────────────────────────────
    if not getattr(shared_player, "_flags", {}).get("levelup_potion_granted", False):
        if not hasattr(shared_player, "_flags"):
            shared_player._flags = {}
        shared_player._flags["levelup_potion_granted"] = True
        shared_player.add_item("levelup_potion", 1)
        print("[이벤트] 레벨업 사탕 1회 지급 완료")

    # 자동 저장 루프 시작
    if not auto_save_loop.is_running():
        auto_save_loop.start()

    # Cog 로드
    from cogs import COGS as _COGS
    for _cog_path in _COGS:
        try:
            await bot.load_extension(_cog_path)
            logger.info("Cog 로드 완료: %s", _cog_path)
        except Exception as _e:
            logger.error("Cog 로드 실패: %s — %s", _cog_path, _e, exc_info=True)

    print("[봇 준비] 모든 시스템 초기화 완료!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# ─── 종료 시그널 핸들러 ───────────────────────────────────────────────────
def _shutdown_handler(sig, frame):
    print(f"\n[종료] 시그널 {sig} 수신 — 데이터 저장 중...")
    try:
        save_manager.save(shared_player)
        print("[종료] 저장 완료.")
    except Exception as e:
        print(f"[종료] 저장 실패: {e}")
    sys.exit(0)


signal.signal(signal.SIGINT,  _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)


# ─── 종료 시 강제 저장 ────────────────────────────────────────────────────
import atexit


def _shutdown_save():
    """봇 종료 시 플레이어 데이터 강제 저장"""
    try:
        save_manager.save(shared_player)
        print("[종료 저장] 플레이어 데이터 저장 완료")
    except Exception as e:
        print(f"[종료 저장] 실패: {e}")


atexit.register(_shutdown_save)


# ─── 봇 실행 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
