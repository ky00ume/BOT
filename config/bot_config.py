# config/bot_config.py
"""봇 공유 객체 초기화 및 BotContext 조립.

main.py 가 `create_bot_context()` 를 호출하면
모든 엔진/매니저 인스턴스를 생성하고 BotContext 에 담아 반환한다.
"""

from player       import Player
from npcs         import VillageNPC
from shop         import ShopManager
from battle       import BattleEngine
from fishing      import FishingEngine
from cooking_db   import CookingEngine
from metallurgy   import MetallurgyEngine
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
from storage      import StorageEngine
from movement     import MovementSystem
from training     import TrainingSystem
from adventure    import AdventureEngine
from story_quest  import StoryQuestManager
from skills_db    import COMBAT_SKILLS as _CS, MAGIC_SKILLS as _MS, RECOVERY_SKILLS as _RS
from utils.bot_context import BotContext


def _build_edible_items() -> dict:
    """먹을 수 있는 아이템 합산 (CONSUMABLES + COOKED_DISHES + 효과 있는 GATHERING_ITEMS)."""
    edible: dict = {**CONSUMABLES, **COOKED_DISHES}
    for k, v in GATHERING_ITEMS.items():
        if any(v.get(stat, 0) > 0 for stat in ("hp", "mp", "en")):
            edible[k] = v
    return edible


def create_bot_context(
    hyness_id: int,
    majesty_id: int,
    drider_id: int,
    allowed_channel_id: int,
) -> BotContext:
    """모든 엔진/매니저를 생성하고 BotContext 에 조립하여 반환한다."""

    # ─── 핵심 플레이어 + 매니저 ─────────────────────────────────────────────
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
    encounter_manager = SpecialNPCEncounterManager(shared_player)
    story_quest_manager = StoryQuestManager(shared_player)
    storage_engine    = StorageEngine(shared_player)
    movement_system   = MovementSystem(shared_player)
    training_system   = TrainingSystem(shared_player)
    adventure_engine  = AdventureEngine(shared_player)

    # ─── 역방향 참조 주입 ────────────────────────────────────────────────────
    shared_player._affinity_manager     = affinity_manager
    shared_player._quest_manager        = quest_manager
    shared_player._story_quest_manager  = story_quest_manager
    shared_player._collection_manager   = collection_manager

    # ─── 전투 스킬 역방향 맵핑 ───────────────────────────────────────────────
    all_battle_skills: dict = {**_CS, **_MS, **_RS}
    skill_name_to_id: dict  = {v["name"]: k for k, v in all_battle_skills.items()}

    # ─── BotContext 조립 ─────────────────────────────────────────────────────
    ctx = BotContext()
    ctx.hyness_id           = hyness_id
    ctx.majesty_id          = majesty_id
    ctx.drider_id           = drider_id
    ctx.allowed_channel_id  = allowed_channel_id

    ctx.player              = shared_player
    ctx.npc_manager         = npc_manager
    ctx.shop_manager        = shop_manager
    ctx.restaurant_engine   = restaurant_engine
    ctx.battle_engine       = battle_engine
    ctx.fishing_engine      = fishing_engine
    ctx.cooking_engine      = cooking_engine
    ctx.metallurgy_engine   = metallurgy_engine
    ctx.gathering_engine    = gathering_engine
    ctx.potion_engine       = potion_engine
    ctx.quest_manager       = quest_manager
    ctx.affinity_manager    = affinity_manager
    ctx.gacha_engine        = gacha_engine
    ctx.music_engine        = music_engine
    ctx.crafting_engine     = crafting_engine
    ctx.care_manager        = care_manager
    ctx.encounter_manager   = encounter_manager
    ctx.story_quest_manager = story_quest_manager
    ctx.storage_engine      = storage_engine
    ctx.movement_system     = movement_system
    ctx.training_system     = training_system
    ctx.adventure_engine    = adventure_engine
    ctx.all_battle_skills   = all_battle_skills
    ctx.skill_name_to_id    = skill_name_to_id
    ctx.edible_items        = _build_edible_items()

    return ctx
