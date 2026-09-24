"""town_ui.py — 마이코니드 군락 / 언더다크 이미지+버튼 UI 시스템 (임베드 제거, PIL 이미지 전용)"""
import discord
from ui.view_timeouts import GAME_VIEW_TIMEOUT
import io
from discord.ui import View, Button
from bg3_renderer import get_renderer
from utils.logger import setup_logger

logger = setup_logger('town_ui')


# ── 마이코니드 군락 묘사 ────────────────────────────────────────────────────────────
VISION_TOWN_DESC = (
    "에본레이크 곁 거대한 버섯 숲에 자리한 마이코니드들의 군락. "
    "발광버섯과 포자가 어둠을 은은하게 밝히고, 상인과 여행자들이 잠시 숨을 고른다. "
    "비전의 탑에서 길을 따라 건너오면 닿는 츄라이더의 가장 가까운 생활 거점이다."
)

# ── 언더다크 묘사 ────────────────────────────────────────────────────────────
UNDERDARK_DESC = (
    "돌과 어둠의 세계. 거대한 석순이 천장에서 내려오고, "
    "발광버섯이 길을 희미하게 밝힌다. 먼 곳에서 에본레이크물 소리가 울려 퍼지며, "
    "공기는 차고 눅눅하다. 이 광대한 지하 세계에는 위험과 보물이 함께 숨어 있다."
)

# ── 사냥터 데이터 (database.py HUNTING_GROUNDS 키와 일치) ──────────────────
HUNTING_ZONE_DATA = {
    "드레드 할로우": {
        "name": "드레드 할로우",
        "level_range": (1, 5),
        "desc": "거대한 수서 나무와 발광 식물이 뒤엉킨 숲. 초급 몬스터가 자주 모습을 드러낸다.",
        "monsters": ["슬라임", "작은 박쥐", "고블린"],
        "emoji": "🌿",
    },
    "폐허가 된 마을": {
        "name": "폐허가 된 마을",
        "level_range": (5, 15),
        "desc": "에본레이크 가장자리의 버려진 정착지. 무너진 건물 사이로 위험한 무리가 숨어든다.",
        "monsters": ["고블린", "고블린 대장", "동굴 박쥐"],
        "emoji": "🏚️",
    },
    "그림포지": {
        "name": "그림포지",
        "level_range": (10, 25),
        "desc": "듀에르가 유적과 오래된 작업장이 이어진 위험 지역. 광맥 주변에도 적이 배회한다.",
        "monsters": ["해골 광부", "좀비 광부", "암흑 결정"],
        "emoji": "⛏️",
    },
}

# ── 채집터 데이터 ─────────────────────────────────────────────────────────────
GATHERING_ZONE_DATA = {
    "마이코니드 군락 외곽": {
        "name": "마이코니드 군락 외곽",
        "desc": "군락 바로 바깥의 안전한 버섯숲. 식용 버섯부터 희귀 균류까지 포자 사이에서 찾을 수 있다.",
        "items": ["버섯", "표고버섯", "발광버섯", "독버섯", "나이트라이트 버섯", "팀마스크", "블루캡", "비버뱅", "토치스톡", "서서 꽃"],
        "activities": ("gather",),
        "emoji": "🍄",
    },
    "수서 나무 숲": {
        "name": "수서 나무 숲",
        "desc": "드레드 할로우를 감싼 거대한 수서 나무 숲. 약초와 야생 식물, 목재를 얻기 좋다.",
        "items": ["약초", "들꽃", "버섯", "야생 열매"],
        "activities": ("gather", "woodcut"),
        "emoji": "🌿",
    },
    "그림포지 광맥": {
        "name": "그림포지 광맥",
        "desc": "그림포지 작업장 아래로 이어지는 오래된 광맥. 철과 귀금속, 드물게 미스릴이 섞여 나온다.",
        "items": ["구리 광석", "철광석", "석탄", "은 광석", "금 광석", "미스릴 광석"],
        "activities": ("mine",),
        "emoji": "⛏️",
    },
    "아다만틴 심층 광맥": {
        "name": "아다만틴 심층 광맥", "desc": "아다만틴 대장간 아래의 고열 광맥. 희귀 광석이 나온다.",
        "items": ["미스릴 광석", "오리할콘 광석", "아다만티움 광석"], "activities": ("mine",), "emoji": "💎",
    },
    "비버뱅 군락지": {
        "name": "비버뱅 군락지", "desc": "건드리면 터질 듯 부푼 균류가 빽빽한 위험 지역.",
        "items": ["비버뱅", "팀마스크", "토치스톡", "나이트라이트 버섯", "공작버섯(희귀 사건)"], "activities": ("gather",), "emoji": "💥",
    },
    "셀루네 수정지": {
        "name": "셀루네 수정지", "desc": "전초기지 주변의 희미한 달빛 결정과 약초가 남은 곳.",
        "items": ["약초", "발광버섯", "은 광석"], "activities": ("gather",), "emoji": "🌙",
    },
    "샤의 잔해 채집지": {
        "name": "샤의 잔해 채집지", "desc": "고대 사원 잔해에서 의식 재료와 오래된 조각을 찾는다.",
        "items": ["고대의 조각", "마법의 돌", "검은 진주"], "activities": ("gather",), "emoji": "🕯️",
    },
}

# ── 낚시터 데이터 ─────────────────────────────────────────────────────────────
FISHING_ZONE_DATA = {
    "에본레이크 북안": {
        "name": "에본레이크 북안",
        "desc": "검은 호수의 비교적 잔잔한 북쪽 물가. 입문 낚시에 알맞다.",
        "has_silen": False,
        "emoji": "🎣",
    },
    "에본레이크 얕은 물가": {
        "name": "에본레이크 얕은 물가",
        "desc": "돌과 수초가 드러난 얕은 물가. 작은 물고기와 가재가 자주 걸린다.",
        "has_silen": False,
        "emoji": "🐟",
    },
    "에본레이크 선착장": {
        "name": "에본레이크 선착장",
        "desc": "폐허가 된 정착지로 오가는 낡은 선착장. 깊은 물의 큰 어종까지 노릴 수 있다.",
        "has_silen": False,
        "emoji": "⚓",
    },
    "곪아가는 만": {
        "name": "곪아가는 만",
        "desc": "절벽 아래 숨은 쿠오토아의 만. 희귀하고 기묘한 어종이 올라온다.",
        "has_silen": False,
        "emoji": "🌊",
    },
    "그림포지 용암지대": {
        "name": "그림포지 용암지대",
        "desc": "열기와 광물이 스며든 그림포지의 특수 수역. 평범한 호수와 전혀 다른 생물이 산다.",
        "has_silen": False,
        "emoji": "🌋",
    },
}


# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────

def _strip_town_prefix(label: str) -> str:
    """군락 내부 버튼에서는 정착지 접두사를 생략한다."""
    for prefix in ("마이코니드 군락 ", "비전 타운 "):
        if label.startswith(prefix):
            return label[len(prefix):]
    return label


def _render_banner(location_name: str, description: str,
                   zone_type: str = "town", zone_id: str = None) -> discord.File:
    """bg3_renderer를 호출하여 배너 이미지를 discord.File로 반환한다."""
    buf = get_renderer().render_location_banner(
        location_name=location_name,
        description=description,
        zone_type=zone_type,
        zone_id=zone_id,
    )
    return discord.File(buf, filename="banner.png")


# ── Views ─────────────────────────────────────────────────────────────────────

class ColonyPlaceView(View):
    """군락 내부 장소 자체를 보여주는 뷰. NPC는 장소 안 상호작용 중 하나다."""
    PLACE_INFO = {
        "마이코니드 군락 서쪽 입구": ("서쪽 입구", "외부에서 들어온 상인과 여행자가 먼저 닿는 군락의 가장자리."),
        "마이코니드 군락 광명회 야영지": ("광명회 야영지", "연구 도구와 표본이 놓인 광명회의 작은 야영지."),
        "마이코니드 군락 군주의 터": ("군주의 터", "포자와 감각이 이어지는 군락의 중심. 군주의 의지가 가장 선명하게 닿는다."),
        "마이코니드 군락 서쪽 통로": ("서쪽 통로", "군락 바깥으로 이어지는 그늘진 통로."),
    }
    PLACE_ACTIONS = {
        "마이코니드 군락 서쪽 입구": [
            ("상인의 짐을 살핀다", "📦", "데리스의 상자와 자루가 길 가장자리에 가지런히 쌓여 있다. 말린 버섯과 연금술 재료 냄새가 희미하게 섞인다."),
            ("군락 바깥을 살핀다", "👁️", "입구 너머로 언더다크의 어둠이 이어진다. 오가는 발자국과 수레 자국 사이로 최근 지나간 흔적이 남아 있다."),
        ],
        "마이코니드 군락 광명회 야영지": [
            ("연구 장비를 살핀다", "🔬", "유리병과 기록지, 생물 표본이 작은 작업대 위를 빼곡히 채운다. 몇몇 표본은 아직 희미하게 빛난다."),
            ("표본 선반을 살핀다", "🧪", "언더다크에서 모은 균류와 광물이 이름표와 함께 정리되어 있다. 손대기보다는 눈으로 보는 편이 안전해 보인다."),
        ],
        "마이코니드 군락 군주의 터": [
            ("포자 군락을 느낀다", "✨", "공기 속 포자가 느리게 떠다닌다. 가까이 서자 말이 아닌 감각과 오래된 기억의 잔향이 잠깐 스쳐 간다."),
            ("의식 공간을 살핀다", "🍄", "균사와 발광버섯이 원을 이루고 있다. 군락의 마이코니드들이 지나간 자리마다 포자가 얇은 길처럼 남아 있다."),
        ],
        "마이코니드 군락 서쪽 통로": [
            ("통로의 흔적을 살핀다", "🔎", "바위 틈의 균사가 여러 번 짓밟혀 있다. 군락 안쪽보다 바깥을 향한 발자국이 더 선명하다."),
            ("바깥 기척을 듣는다", "👂", "멀리서 물 떨어지는 소리와 돌이 긁히는 소리가 번갈아 들린다. 바로 앞에 무언가 있는 기척은 아니다."),
        ],
    }

    def __init__(self, location, player, aff_manager, npc_manager_ref, village_manager=None):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.location, self.player = location, player
        self.aff_manager, self.npc_manager_ref = aff_manager, npc_manager_ref
        self.village_manager = village_manager
        self._build_buttons()

    def _npcs_here(self):
        from database import NPC_DATA
        return [name for name, data in NPC_DATA.items() if data.get("location") == self.location]

    def _build_buttons(self):
        self.clear_items()
        for npc_name in self._npcs_here():
            btn = Button(label=npc_name, style=discord.ButtonStyle.primary)
            btn.callback = self._make_npc_callback(npc_name)
            self.add_item(btn)
        for label, emoji, observation in self.PLACE_ACTIONS.get(self.location, []):
            btn = Button(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
            btn.callback = self._make_observation_callback(label, observation)
            self.add_item(btn)
        back = Button(label="군락을 둘러본다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back.callback = self._back_callback
        self.add_item(back)

    def _make_observation_callback(self, label, observation):
        async def callback(interaction):
            title, desc = self.PLACE_INFO.get(self.location, (_strip_town_prefix(self.location), "주변을 천천히 둘러본다."))
            embed = discord.Embed(title=title, description=desc, color=0x6E6246)
            embed.add_field(name=label, value=observation, inline=False)
            await interaction.response.edit_message(attachments=[], embed=embed, view=self)
        return callback

    def _make_npc_callback(self, npc_name):
        async def callback(interaction):
            from npc_conversation import ConversationManager
            await interaction.response.defer()
            conv = ConversationManager(self.player, self.aff_manager, self.npc_manager_ref)
            await conv.send_conversation(interaction.channel, npc_name)
            try:
                await interaction.delete_original_response()
            except Exception:
                pass
        return callback

    async def _back_callback(self, interaction):
        view = VisionTownView(self.player, self.aff_manager, self.npc_manager_ref, self.village_manager)
        await view.send(interaction, edit=True)

    async def send(self, interaction, edit=True):
        title, desc = self.PLACE_INFO.get(self.location, (_strip_town_prefix(self.location), "주변을 천천히 둘러본다."))
        embed = discord.Embed(title=title, description=desc, color=0x6E6246)
        if edit:
            await interaction.response.edit_message(attachments=[], embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed, view=self)


class VisionTownView(View):
    """마이코니드 군락 메인 뷰. 클래스명은 저장/호출 호환을 위해 유지한다."""

    def __init__(self, player, aff_manager, npc_manager_ref, village_manager=None, care_manager=None):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self.village_manager = village_manager
        self.care_manager = care_manager
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        places = [
            ("서쪽 입구 · 데리스", "마이코니드 군락 서쪽 입구", "🛒"),
            ("광명회 야영지", "마이코니드 군락 광명회 야영지", "🔬"),
            ("군주의 터", "마이코니드 군락 군주의 터", "🍄"),
            ("서쪽 통로 · 글럿", "마이코니드 군락 서쪽 통로", "⚔️"),
        ]
        for label, location, emoji in places:
            btn = Button(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
            btn.callback = self._make_location_callback(location)
            self.add_item(btn)

        notice_btn = Button(label="군락 의뢰", style=discord.ButtonStyle.primary, emoji="📜")
        notice_btn.callback = self._quest_callback
        self.add_item(notice_btn)

        cook_btn = Button(label="취사장", style=discord.ButtonStyle.success, emoji="🍲")
        cook_btn.callback = self._cooking_callback
        self.add_item(cook_btn)

        tower_btn = Button(label="비전의 탑으로 가는 길", style=discord.ButtonStyle.success, emoji="🏰")
        tower_btn.callback = self._tower_road_callback
        self.add_item(tower_btn)

        leave_btn = Button(label="언더다크로 나간다", style=discord.ButtonStyle.danger, emoji="🗺️")
        leave_btn.callback = self._leave_callback
        self.add_item(leave_btn)

    def _make_banner_file(self) -> discord.File:
        """마이코니드 군락 배너 이미지를 생성한다."""
        return _render_banner(
            location_name="마이코니드 군락",
            description=VISION_TOWN_DESC,
            zone_type="town",
            zone_id="마이코니드군락",
        )

    async def send(self, channel_or_interaction, edit=False):
        """뷰를 전송하거나 기존 메시지를 편집한다."""
        file = self._make_banner_file()
        # 마을 기여도·레벨 임베드
        embed = None
        if self.village_manager is not None:
            embed = self.village_manager.make_status_embed()
        if edit and isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.edit_message(
                attachments=[file], embed=embed, view=self,
            )
        elif isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(
                file=file, embed=embed, view=self,
            )
        else:
            await channel_or_interaction.send(file=file, embed=embed, view=self)

    def _make_location_callback(self, location: str):
        async def callback(interaction: discord.Interaction):
            view = ColonyPlaceView(location, self.player, self.aff_manager, self.npc_manager_ref, self.village_manager)
            await view.send(interaction, edit=True)
        return callback

    async def _quest_callback(self, interaction: discord.Interaction):
        import app_context
        from ui.quest_ui import QuestWindowView, _make_quest_list_image
        qm = app_context.get_quest_manager()
        file = _make_quest_list_image(qm)
        view = QuestWindowView(qm, self.player)
        await interaction.response.send_message(file=file, view=view)

    async def _cooking_callback(self, interaction: discord.Interaction):
        import app_context
        from ui.skill_ui import SkillMainView, make_life_hub_embed
        def _back():
            return VisionTownView(self.player, self.aff_manager, self.npc_manager_ref, self.village_manager)
        view = SkillMainView(
            self.player, potion_engine=app_context.get_potion_engine(), crafting_engine=app_context.get_crafting_engine(),
            cooking_engine=app_context.get_cooking_engine(), metallurgy_engine=app_context.get_metallurgy_engine(), back_factory=_back,
        )
        # 취사장에서는 곧바로 생활 스킬 화면으로 들어간다.
        view.current_category = "life"
        view._build_life_hub()
        await interaction.response.edit_message(attachments=[], embed=make_life_hub_embed(self.player), view=view)

    async def _tower_road_callback(self, interaction: discord.Interaction):
        from ui.care_ui import TowerColonyRoadView
        if self.care_manager is None:
            import app_context
            care_manager = app_context.get("care_manager")
        else:
            care_manager = self.care_manager
        if care_manager is None:
            from care import CareManager
            care_manager = CareManager()
        view = TowerColonyRoadView(self.player, care_manager, direction="to_tower")
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

    async def _leave_callback(self, interaction: discord.Interaction):
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await view.send(interaction, edit=True)


class WorldMapView(View):
    """언더다크 세계지도 뷰 (이미지 + 버튼)"""

    def __init__(self, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        from movement import MAP_NODES
        from world_activities import activities_for

        current = getattr(self.player, "current_location", "마이코니드 군락")
        if current == "마이코니드 군락":
            town_btn = Button(label="군락 안으로", style=discord.ButtonStyle.secondary, emoji="🏘️")
            town_btn.callback = self._back_to_town
            self.add_item(town_btn)

        for activity in activities_for(current):
            kind = activity["kind"]
            style = {
                "hunt": discord.ButtonStyle.danger,
                "gather": discord.ButtonStyle.success,
                "mine": discord.ButtonStyle.success,
                "fish": discord.ButtonStyle.primary,
            }[kind]
            btn = Button(label=activity["label"], style=style, emoji=activity["emoji"])
            if kind == "hunt":
                btn.callback = self._make_hunting_callback(activity["zone"])
            elif kind in ("gather", "mine"):
                btn.callback = self._make_gather_callback(activity["zone"])
            else:
                btn.callback = self._make_fishing_callback(activity["zone"])
            self.add_item(btn)

        node = MAP_NODES.get(current)
        if node:
            for destination in node.get("adjacent", []):
                # 탑↔군락은 전용 생활 이동로가 있으므로 월드맵 순간 이동 버튼과 중복하지 않는다.
                if {current, destination} == {"비전의 탑", "마이코니드 군락"}:
                    continue
                dest = MAP_NODES[destination]
                btn = Button(label=f"{destination}로 이동", style=discord.ButtonStyle.secondary, emoji=dest["icon"])
                btn.callback = self._make_travel_callback(destination)
                self.add_item(btn)

    def _make_banner_file(self) -> discord.File:
        """현재 월드 위치와 그곳에서 할 수 있는 활동을 보여준다."""
        from movement import MAP_NODES
        current = getattr(self.player, "current_location", "마이코니드 군락")
        node = MAP_NODES.get(current, {"name": current, "desc": UNDERDARK_DESC})
        return _render_banner(
            location_name=node.get("name", current),
            description=node.get("desc", UNDERDARK_DESC),
            zone_type="town",
            zone_id=current,
        )

    async def send(self, channel_or_interaction, edit=False):
        """뷰를 전송하거나 기존 메시지를 편집한다."""
        file = self._make_banner_file()
        if edit and isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.edit_message(
                attachments=[file], embed=None, view=self,
            )
        elif isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(
                file=file, view=self,
            )
        else:
            await channel_or_interaction.send(file=file, view=self)

    async def _back_to_town(self, interaction: discord.Interaction):
        from village import village_manager as vm
        view = VisionTownView(self.player, self.aff_manager, self.npc_manager_ref, vm)
        await view.send(interaction, edit=True)

    def _make_travel_callback(self, destination: str):
        async def callback(interaction: discord.Interaction):
            import app_context
            movement = app_context.get("movement_system")
            if movement is None:
                movement = getattr(getattr(interaction.client, "ctx", None), "movement_system", None)
            if movement is None:
                await interaction.response.send_message("이동 시스템을 찾을 수 없습니다.", ephemeral=True)
                return
            before = movement._get_location()
            result = movement.move_to(interaction.user.id, destination)
            after = movement._get_location()
            if after != destination or before == after:
                await interaction.response.send_message(str(result), ephemeral=True)
                return
            try:
                app_context.get_save_manager().save(self.player)
            except Exception:
                logger.warning("town_ui: 월드 이동 저장 실패", exc_info=True)
            view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
            await view.send(interaction, edit=True)
        return callback

    def _make_hunting_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            view = HuntingZoneView(zone_name, self.player, self.aff_manager, self.npc_manager_ref)
            await view.send(interaction, edit=True)
        return callback

    def _make_gather_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            view = GatheringZoneView(zone_name, self.player, self.aff_manager, self.npc_manager_ref)
            await view.send(interaction, edit=True)
        return callback

    def _make_fishing_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            zone = FISHING_ZONE_DATA.get(zone_name, {})
            view = FishingZoneView(
                zone_name, zone.get("has_silen", False),
                self.player, self.aff_manager, self.npc_manager_ref,
            )
            await view.send(interaction, edit=True)
        return callback


class AdventureEventView(View):
    def __init__(self, event, player, continue_hunt):
        super().__init__(timeout=GAME_VIEW_TIMEOUT); self.event=event; self.player=player; self.continue_hunt=continue_hunt
        for key,label in event["choices"]:
            b=Button(label=label,style=discord.ButtonStyle.primary if key!="leave" else discord.ButtonStyle.secondary)
            async def cb(interaction, choice=key):
                from adventure_events import resolve_adventure_event
                result=resolve_adventure_event(self.player,self.event["id"],choice)
                for child in self.children: child.disabled=True
                await interaction.response.edit_message(embed=discord.Embed(title=self.event["title"],description=result["text"]),view=self)
                if result.get("battle"):
                    await self.continue_hunt(interaction, advantage=result.get("advantage",False))
                else:
                    import app_context; app_context.get_save_manager().save(self.player)
            b.callback=cb; self.add_item(b)

class HuntingZoneView(View):
    """사냥터 상세 뷰 (이미지 + 버튼)"""

    def __init__(self, zone_name: str, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.zone_name = zone_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        hunt_btn = Button(label="사냥", style=discord.ButtonStyle.danger, emoji="⚔️")
        hunt_btn.callback = self._hunt_callback
        self.add_item(hunt_btn)

        back_btn = Button(label="돌아간다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    def _make_banner_file(self) -> discord.File:
        zone = HUNTING_ZONE_DATA.get(self.zone_name, {})
        return _render_banner(
            location_name=zone.get("name", self.zone_name),
            description=zone.get("desc", ""),
            zone_type="hunting",
            zone_id=self.zone_name,
        )

    async def send(self, channel_or_interaction, edit=False):
        file = self._make_banner_file()
        if edit and isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.edit_message(
                attachments=[file], embed=None, view=self,
            )
        elif isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(
                file=file, view=self,
            )
        else:
            await channel_or_interaction.send(file=file, view=self)

    async def _hunt_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import app_context
        battle_engine = app_context.get_battle_engine()
        encounter_manager = app_context.get_encounter_manager()
        quest_manager = app_context.get_quest_manager()
        achievement_manager = app_context.get_achievement_manager()
        diary_manager = app_context.get_diary_manager()
        departure = encounter_manager.clear_encounter()
        if departure:
            await interaction.channel.send(departure)
        from adventure_events import roll_adventure_event
        event = roll_adventure_event(self.zone_name)
        if event:
            embed=discord.Embed(title=event["title"],description=event["text"])
            async def _continue(inter, advantage=False):
                if advantage:
                    battle_engine._cheer_active=True
                await self._start_hunt(interaction.channel, battle_engine, encounter_manager, quest_manager, achievement_manager, diary_manager)
            await interaction.channel.send(embed=embed,view=AdventureEventView(event,self.player,_continue))
            return
        await self._start_hunt(interaction.channel, battle_engine, encounter_manager, quest_manager, achievement_manager, diary_manager)

    async def _start_hunt(self, channel, battle_engine, encounter_manager, quest_manager, achievement_manager, diary_manager):
        success, result = battle_engine.start_encounter(self.zone_name)
        if success:
            _bimg = battle_engine.build_battle_image()

            async def _on_battle_end(won: bool):
                if won:
                    achievement_manager.increment("battles_won", 1)
                    diary_manager.increment("battles_won", 1)
                    _killed_zone = battle_engine.current_zone
                    _killed_monster = battle_engine.current_monster.get("id", "") if battle_engine.current_monster else ""
                    quest_manager.update_kill_count(1, zone=_killed_zone, monster_id=_killed_monster)
                    # 알바 hunt 킬 카운트 추적
                    npc_manager = app_context.get_npc_manager()
                    _hunt_completed = npc_manager.update_hunt_kill(monster_id=_killed_monster, count=1)
                    if _hunt_completed:
                        await npc_manager.complete_pending_hunts(channel, _hunt_completed)
                app_context.get_save_manager().save(app_context.get_player())

            from ui.battle_view import BattleView
            view = BattleView(battle_engine, channel, on_battle_end=_on_battle_end)
            if _bimg:
                _bimg.seek(0)
                await channel.send(file=discord.File(fp=_bimg, filename="battle.png"), view=view)
            elif isinstance(result, io.BytesIO):
                result.seek(0)
                await channel.send(file=discord.File(fp=result, filename="battle.png"), view=view)
            else:
                await channel.send(str(result), view=view)
        else:
            if isinstance(result, io.BytesIO):
                result.seek(0)
                await channel.send(file=discord.File(fp=result, filename="battle.png"))
            elif isinstance(result, discord.Embed):
                await channel.send(embed=result)
            else:
                await channel.send(str(result))
        if success:
            enc_msg = encounter_manager.trigger_encounter()
            if enc_msg:
                from special_npc import render_encounter_image
                npc_name = encounter_manager.get_active_encounter()
                buf = render_encounter_image(npc_name, enc_msg)
                if buf:
                    buf.seek(0)
                    from ui.special_npc_ui import SpecialNPCView
                    view = SpecialNPCView(npc_name, encounter_manager.player,
                                         getattr(encounter_manager, '_aff_manager', None),
                                         getattr(encounter_manager, '_npc_manager_ref', None),
                                         encounter_manager)
                    enc_file = discord.File(fp=buf, filename="encounter.png")
                    await channel.send(file=enc_file, view=view)
                else:
                    await channel.send(enc_msg)

    async def _back_callback(self, interaction: discord.Interaction):
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await view.send(interaction, edit=True)


class BibberbangNoblestalkView(View):
    def __init__(self, player):
        super().__init__(timeout=GAME_VIEW_TIMEOUT); self.player=player
        from bibberbang_event import event_payload
        self.event=event_payload()
        styles={"careful":discord.ButtonStyle.success,"dash":discord.ButtonStyle.primary,"burn":discord.ButtonStyle.danger,"leave":discord.ButtonStyle.secondary}
        for key,label in self.event["choices"]:
            b=Button(label=label,style=styles[key])
            async def cb(interaction, choice=key):
                import random, app_context
                from bibberbang_event import resolve
                result=resolve(self.player,choice,rng=random.random)
                if result.get("resolved"):
                    for child in self.children: child.disabled=True
                await interaction.response.edit_message(embed=discord.Embed(title=self.event["title"],description=result["text"]),view=self)
                app_context.get_save_manager().save(self.player)
            b.callback=cb; self.add_item(b)

class RareDiscoveryView(View):
    def __init__(self, zone_name, player):
        super().__init__(timeout=GAME_VIEW_TIMEOUT); self.zone_name=zone_name; self.player=player
        from rare_discovery_events import EVENTS
        self.event=EVENTS[zone_name]
        for key,label in self.event["choices"]:
            b=Button(label=label,style=discord.ButtonStyle.secondary if key=="leave" else discord.ButtonStyle.primary)
            async def cb(interaction,choice=key):
                import random,app_context
                from rare_discovery_events import resolve
                result=resolve(self.player,self.zone_name,choice,rng=random.random)
                if result.get("resolved"):
                    for child in self.children: child.disabled=True
                await interaction.response.edit_message(embed=discord.Embed(title=self.event["title"],description=result["text"]),view=self)
                app_context.get_save_manager().save(self.player)
            b.callback=cb;self.add_item(b)

class GatheringZoneView(View):
    """채집터 상세 뷰 (이미지 + 버튼)"""

    def __init__(self, zone_name: str, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.zone_name = zone_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        zone = GATHERING_ZONE_DATA.get(self.zone_name, {})
        activities = zone.get("activities", ("gather", "mine"))
        if "gather" in activities:
            gather_btn = Button(label="채집", style=discord.ButtonStyle.success, emoji="🌿")
            gather_btn.callback = self._gather_callback
            self.add_item(gather_btn)
        if self.zone_name == "비버뱅 군락지":
            from bibberbang_event import event_available
            if event_available(self.player):
                event_btn=Button(label="공작버섯 흔적",style=discord.ButtonStyle.primary,emoji="🍄")
                event_btn.callback=self._noblestalk_callback
                self.add_item(event_btn)
        from rare_discovery_events import EVENTS, available as rare_available
        if self.zone_name in EVENTS and rare_available(self.player,self.zone_name):
            rare_btn=Button(label="희귀한 흔적",style=discord.ButtonStyle.primary,emoji="✨")
            rare_btn.callback=self._rare_discovery_callback
            self.add_item(rare_btn)
        if "woodcut" in activities:
            wood_btn = Button(label="벌목", style=discord.ButtonStyle.success, emoji="🪓")
            wood_btn.callback = self._woodcut_callback
            self.add_item(wood_btn)
        if "mine" in activities:
            mine_btn = Button(label="채광", style=discord.ButtonStyle.success, emoji="⛏️")
            mine_btn.callback = self._mine_callback
            self.add_item(mine_btn)

        back_btn = Button(label="돌아간다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    def _make_banner_file(self) -> discord.File:
        zone = GATHERING_ZONE_DATA.get(self.zone_name, {})
        return _render_banner(
            location_name=zone.get("name", self.zone_name),
            description=zone.get("desc", ""),
            zone_type="gathering",
            zone_id=self.zone_name,
        )

    async def send(self, channel_or_interaction, edit=False):
        file = self._make_banner_file()
        if edit and isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.edit_message(
                attachments=[file], embed=None, view=self,
            )
        elif isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(
                file=file, view=self,
            )
        else:
            await channel_or_interaction.send(file=file, view=self)

    async def _rare_discovery_callback(self, interaction: discord.Interaction):
        from rare_discovery_events import EVENTS
        event=EVENTS[self.zone_name]
        await interaction.response.send_message(embed=discord.Embed(title=event["title"],description=event["text"]),view=RareDiscoveryView(self.zone_name,self.player))

    async def _noblestalk_callback(self, interaction: discord.Interaction):
        from bibberbang_event import event_payload
        event=event_payload()
        await interaction.response.send_message(embed=discord.Embed(title=event["title"],description=event["text"]),view=BibberbangNoblestalkView(self.player))

    async def _gather_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import app_context
        await app_context.get_gathering_engine().gather(interaction.channel, zone_name=self.zone_name)
        app_context.get_save_manager().save(app_context.get_player())
        # 채집 후 같은 채집터 뷰를 다시 전송하여 재접근 편의 제공
        new_view = GatheringZoneView(self.zone_name, self.player, self.aff_manager, self.npc_manager_ref)
        await new_view.send(interaction.channel)
        try:
            await interaction.delete_original_response()
        except Exception:
            logger.warning('town_ui: GatheringZoneView._gather_callback delete_original_response 실패', exc_info=True)

    async def _woodcut_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import app_context
        await app_context.get_gathering_engine().woodcut(interaction.channel)
        app_context.get_save_manager().save(app_context.get_player())
        new_view = GatheringZoneView(self.zone_name, self.player, self.aff_manager, self.npc_manager_ref)
        await new_view.send(interaction.channel)
        try:
            await interaction.delete_original_response()
        except Exception:
            logger.warning('town_ui: GatheringZoneView._woodcut_callback delete_original_response 실패', exc_info=True)

    async def _mine_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import app_context
        await app_context.get_gathering_engine().mine(interaction.channel, zone_name=self.zone_name)
        app_context.get_save_manager().save(app_context.get_player())
        new_view = GatheringZoneView(self.zone_name, self.player, self.aff_manager, self.npc_manager_ref)
        await new_view.send(interaction.channel)
        try:
            await interaction.delete_original_response()
        except Exception:
            logger.warning('town_ui: GatheringZoneView._mine_callback delete_original_response 실패', exc_info=True)

    async def _back_callback(self, interaction: discord.Interaction):
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await view.send(interaction, edit=True)


class FishingZoneView(View):
    """낚시터 상세 뷰 (이미지 + 버튼)"""

    def __init__(self, zone_name: str, has_silen: bool, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.zone_name = zone_name
        self.has_silen = has_silen
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        fish_btn = Button(label="낚시", style=discord.ButtonStyle.primary, emoji="🎣")
        fish_btn.callback = self._fish_callback
        self.add_item(fish_btn)

        water_btn = Button(label="물뜨기", style=discord.ButtonStyle.success, emoji="🫗")
        water_btn.callback = self._water_callback
        self.add_item(water_btn)

        if self.has_silen:
            silen_btn = Button(label="툴라", style=discord.ButtonStyle.secondary, emoji="🌊")
            silen_btn.callback = self._silen_callback
            self.add_item(silen_btn)

        back_btn = Button(label="돌아간다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    def _make_banner_file(self) -> discord.File:
        zone = FISHING_ZONE_DATA.get(self.zone_name, {})
        return _render_banner(
            location_name=zone.get("name", self.zone_name),
            description=zone.get("desc", ""),
            zone_type="fishing",
            zone_id=self.zone_name,
        )

    async def send(self, channel_or_interaction, edit=False):
        file = self._make_banner_file()
        if edit and isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.edit_message(
                attachments=[file], embed=None, view=self,
            )
        elif isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(
                file=file, view=self,
            )
        else:
            await channel_or_interaction.send(file=file, view=self)

    async def _fish_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import app_context
        departure = app_context.get_encounter_manager().clear_encounter()
        if departure:
            await interaction.channel.send(departure)
        # C-1 fix: 현재 낚시터 이름을 fishing_engine에 전달
        app_context.get_fishing_engine().set_spot(self.zone_name)
        await app_context.get_fishing_engine().fish(interaction.channel, actor_id=interaction.user.id)
        app_context.get_save_manager().save(app_context.get_player())
        enc_msg = app_context.get_encounter_manager().trigger_encounter()
        if enc_msg:
            from special_npc import render_encounter_image
            encounter_manager = app_context.get_encounter_manager()
            npc_name = encounter_manager.get_active_encounter()
            buf = render_encounter_image(npc_name, enc_msg)
            if buf:
                buf.seek(0)
                from ui.special_npc_ui import SpecialNPCView
                view = SpecialNPCView(npc_name, encounter_manager.player,
                                     getattr(encounter_manager, '_aff_manager', None),
                                     getattr(encounter_manager, '_npc_manager_ref', None),
                                     encounter_manager)
                enc_file = discord.File(fp=buf, filename="encounter.png")
                await interaction.channel.send(file=enc_file, view=view)
            else:
                await interaction.channel.send(enc_msg)
        # 낚시가 끝나기 전에는 낚시터 버튼을 중복으로 다시 띄우지 않는다.
        # FishingView의 결과/종료가 현재 흐름을 책임지고, 다음 행동은 기존 낚시터 메시지에서 선택한다.

    async def _water_callback(self, interaction: discord.Interaction):
        """물뜨기 — 빈 병 1개를 물 1개로 전환 (기력 5 소모)."""
        import app_context
        from ui.ui_theme import C, ansi
        p = self.player
        if p.inventory.get("empty_bottle", 0) < 1:
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 빈 병이 없슴미댜!{C.R}"), ephemeral=True,
            )
            return
        energy_cost = 5
        if not p.consume_energy(energy_cost):
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}){C.R}"), ephemeral=True,
            )
            return
        p.remove_item("empty_bottle", 1)
        p.add_item("water", 1)
        app_context.get_save_manager().save(app_context.get_player())
        await interaction.response.send_message(
            ansi(
                f"  {C.GREEN}✔ 물을 떴슴미댜!{C.R}\n"
                f"  {C.WHITE}물{C.R} x1 획득!  {C.RED}기력 -{energy_cost}{C.R}"
            ),
        )

    async def _silen_callback(self, interaction: discord.Interaction):
        from npc_conversation import ConversationManager
        conv = ConversationManager(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.defer()
        await conv.send_conversation(interaction.channel, "툴라")
        await interaction.delete_original_response()

    async def _back_callback(self, interaction: discord.Interaction):
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await view.send(interaction, edit=True)


# ── 하위 호환 배너 생성 함수 ─────────────────────────────────────────────────

def create_location_banner(location_name: str, description: str,
                            zone_type: str = "town",
                            zone_id: str = None) -> io.BytesIO:
    """
    장소 배너 이미지 (BG3 스타일). 하위 호환용.
    zone_type: 'town' | 'hunting' | 'gathering' | 'fishing'
    zone_id:   static/banners/{zone_type}/{zone_id}.png 파일명
    """
    return get_renderer().render_location_banner(
        location_name=location_name,
        description=description,
        zone_type=zone_type,
        zone_id=zone_id,
    )


def create_town_banner(zone_id: str = "비전타운") -> io.BytesIO:
    """비전타운 배너 단축 함수 (하위 호환용)"""
    return get_renderer().render_location_banner(
        location_name="마이코니드 군락",
        description=(
            "언더다크의 깊은 곳에 자리한 작은 마을. "
            "버섯 포자와 광석 가루가 뒤섞인 공기 속에서 사람들이 분주히 오간다."
        ),
        zone_type="town",
        zone_id=zone_id,
    )


def create_hunting_banner(zone_key: str, zone_name: str,
                           zone_desc: str) -> io.BytesIO:
    """사냥터 배너 단축 함수 (하위 호환용)"""
    return get_renderer().render_location_banner(
        location_name=zone_name,
        description=zone_desc,
        zone_type="hunting",
        zone_id=zone_key,
    )


def create_gathering_banner(zone_key: str, zone_name: str,
                             zone_desc: str) -> io.BytesIO:
    """채집터 배너 단축 함수 (하위 호환용)"""
    return get_renderer().render_location_banner(
        location_name=zone_name,
        description=zone_desc,
        zone_type="gathering",
        zone_id=zone_key,
    )


def create_fishing_banner(zone_key: str, zone_name: str,
                           zone_desc: str) -> io.BytesIO:
    """낚시터 배너 단축 함수 (하위 호환용)"""
    return get_renderer().render_location_banner(
        location_name=zone_name,
        description=zone_desc,
        zone_type="fishing",
        zone_id=zone_key,
    )
