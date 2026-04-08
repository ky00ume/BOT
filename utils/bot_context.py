# utils/bot_context.py
"""BotContext — Cog들이 공유하는 게임 상태 컨테이너."""


class BotContext:
    """모든 Cog에서 self.bot.ctx 로 접근하는 공유 상태 컨테이너."""

    def __init__(self):
        # 환경변수 ID
        self.hyness_id: int = 0
        self.majesty_id: int = 0
        self.drider_id: int = 0
        self.allowed_channel_id: int = 0

        # 핵심 객체
        self.player = None            # Player
        self.npc_manager = None       # VillageNPC
        self.shop_manager = None      # ShopManager
        self.restaurant_engine = None # RestaurantEngine
        self.battle_engine = None     # BattleEngine
        self.fishing_engine = None    # FishingEngine
        self.cooking_engine = None    # CookingEngine
        self.metallurgy_engine = None # MetallurgyEngine
        self.gathering_engine = None  # GatheringEngine
        self.potion_engine = None     # PotionEngine
        self.quest_manager = None     # QuestManager
        self.affinity_manager = None  # AffinityManager
        self.gacha_engine = None      # GachaEngine
        self.music_engine = None      # MusicEngine
        self.crafting_engine = None   # CraftingEngine
        self.care_manager = None      # CareManager
        self.encounter_manager = None # SpecialNPCEncounterManager
        self.story_quest_manager = None # StoryQuestManager
        self.storage_engine = None    # StorageEngine
        self.movement_system = None   # MovementSystem
        self.training_system = None   # TrainingSystem
        self.adventure_engine = None  # AdventureEngine

        # 전투 스킬 역방향 맵핑 (이름 → ID)
        self.all_battle_skills: dict = {}
        self.skill_name_to_id: dict = {}

        # 먹을 수 있는 아이템 합산
        self.edible_items: dict = {}
