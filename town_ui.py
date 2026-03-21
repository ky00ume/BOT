"""town_ui.py — 비전타운 / 비전의 땅 임베드+버튼 UI 시스템"""
import discord
from discord.ui import View, Button
from ui_theme import EMBED_COLOR


# ── 비전타운 묘사 ────────────────────────────────────────────────────────────
VISION_TOWN_DESC = (
    "언더다크의 깊은 곳에 자리한 작은 마을. 천장 낮은 석굴을 따라 불빛이 흔들리며, "
    "버섯 포자와 광석 가루가 뒤섞인 공기 속에서 사람들이 분주히 오간다. "
    "지상에서 보면 존재조차 모를 이곳은, 그럼에도 제 나름의 온기를 품고 있다."
)

# ── 비전의 땅 묘사 ────────────────────────────────────────────────────────────
UNDERDARK_DESC = (
    "돌과 어둠의 세계. 거대한 석순이 천장에서 내려오고, "
    "발광버섯이 길을 희미하게 밝힌다. 먼 곳에서 지하 강물 소리가 울려 퍼지며, "
    "공기는 차고 눅눅하다. 이 광대한 지하 세계에는 위험과 보물이 함께 숨어 있다."
)

# ── 사냥터 데이터 (database.py HUNTING_GROUNDS 키와 일치) ──────────────────
HUNTING_ZONE_DATA = {
    "방울숲": {
        "name": "방울숲",
        "level_range": (1, 5),
        "desc": "초보 모험가들이 자주 찾는 작은 숲. 방울꽃이 피어 있고 소형 몬스터들이 서식한다.",
        "monsters": ["슬라임", "작은 박쥐", "고블린"],
        "emoji": "🌿",
    },
    "고블린동굴": {
        "name": "고블린 동굴",
        "level_range": (5, 15),
        "desc": "고블린 무리가 점령한 어두운 동굴. 보물을 숨겨 놓은 것 같다.",
        "monsters": ["고블린", "고블린 대장", "동굴 박쥐"],
        "emoji": "🗝️",
    },
    "소금광산": {
        "name": "소금 광산",
        "level_range": (10, 25),
        "desc": "소금 결정이 빛나는 광산. 언데드 광부들이 배회한다.",
        "monsters": ["해골 광부", "좀비 광부", "암흑 결정"],
        "emoji": "⛏️",
    },
}

# ── 채집터 데이터 ─────────────────────────────────────────────────────────────
GATHERING_ZONE_DATA = {
    "방울숲 외곽": {
        "name": "방울숲 외곽",
        "desc": "방울숲 주변의 초지. 약초와 야생 꽃이 풍부하다.",
        "items": ["약초", "들꽃", "버섯", "야생 열매"],
        "emoji": "🌸",
    },
    "지하 광맥": {
        "name": "지하 광맥",
        "desc": "비전타운 근처의 광맥. 다양한 광석을 채굴할 수 있다.",
        "items": ["구리 광석", "철광석", "석탄", "은 광석"],
        "emoji": "🪨",
    },
    "버섯 군락지": {
        "name": "버섯 군락지",
        "desc": "형형색색의 버섯이 자라는 언더다크 특유의 지역.",
        "items": ["버섯", "발광버섯", "독버섯", "표고버섯"],
        "emoji": "🍄",
    },
}

# ── 낚시터 데이터 ─────────────────────────────────────────────────────────────
FISHING_ZONE_DATA = {
    "지하 강": {
        "name": "지하 강",
        "desc": "언더다크를 흐르는 신비로운 지하 강. 어두운 물속에 희귀한 물고기가 산다.",
        "fish": ["장어", "메기", "지하 붕어"],
        "has_silen": False,
        "emoji": "🎣",
    },
    "실렌의 낚시터": {
        "name": "실렌의 낚시터",
        "desc": "드로우 낚시꾼 실렌이 자주 앉아있는 조용한 강가. 황금 잉어가 나온다는 소문이 있다.",
        "fish": ["황금잉어", "잉어", "붕어"],
        "has_silen": True,
        "emoji": "🌊",
    },
}


def _make_town_embed(village_manager=None) -> discord.Embed:
    """비전타운 메인 임베드"""
    embed = discord.Embed(
        title="🏘️ 비전타운 — [언더다크] 시작의 마을",
        description=VISION_TOWN_DESC,
        color=EMBED_COLOR.get("npc", 0x4A7856),
    )
    if village_manager:
        lv = getattr(village_manager, "level", 1)
        contrib = getattr(village_manager, "contribution", 0)
        embed.add_field(name="🏙️ 마을 정보", value=f"레벨: **{lv}** | 기여도: **{contrib}**", inline=False)
    embed.set_footer(text="건물 버튼을 눌러 NPC를 만나보세요!")
    return embed


def _make_worldmap_embed() -> discord.Embed:
    """비전의 땅 임베드"""
    embed = discord.Embed(
        title="🗺️ 비전의 땅 — [언더다크] 돌의 세계",
        description=UNDERDARK_DESC,
        color=EMBED_COLOR.get("help", 0x2F4F4F),
    )
    embed.add_field(
        name="⚔️ 사냥터",
        value=" · ".join(f"{v['emoji']} {k}" for k, v in HUNTING_ZONE_DATA.items()),
        inline=False,
    )
    embed.add_field(
        name="🌿 채집터",
        value=" · ".join(f"{v['emoji']} {k}" for k, v in GATHERING_ZONE_DATA.items()),
        inline=False,
    )
    embed.add_field(
        name="🎣 낚시터",
        value=" · ".join(f"{v['emoji']} {k}" for k, v in FISHING_ZONE_DATA.items()),
        inline=False,
    )
    embed.set_footer(text="버튼을 눌러 이동하세요!")
    return embed


def _make_hunting_zone_embed(zone_name: str) -> discord.Embed:
    zone = HUNTING_ZONE_DATA.get(zone_name, {})
    lv_min, lv_max = zone.get("level_range", (1, 10))
    embed = discord.Embed(
        title=f"{zone.get('emoji', '⚔️')} {zone.get('name', zone_name)} — 사냥터",
        description=zone.get("desc", ""),
        color=EMBED_COLOR.get("battle", 0xFF4500),
    )
    embed.add_field(name="⚔️ 레벨 범위", value=f"Lv.{lv_min} ~ {lv_max}", inline=True)
    monsters = zone.get("monsters", [])
    if monsters:
        embed.add_field(name="👾 출몰 몬스터", value=" · ".join(monsters), inline=False)
    embed.set_footer(text="[사냥] 버튼으로 전투 시작 | [돌아간다]로 복귀")
    return embed


def _make_gathering_zone_embed(zone_name: str) -> discord.Embed:
    zone = GATHERING_ZONE_DATA.get(zone_name, {})
    embed = discord.Embed(
        title=f"{zone.get('emoji', '🌿')} {zone.get('name', zone_name)} — 채집터",
        description=zone.get("desc", ""),
        color=0x228833,
    )
    items = zone.get("items", [])
    if items:
        embed.add_field(name="🌿 획득 가능 아이템", value=" · ".join(items), inline=False)
    embed.set_footer(text="[채집] 또는 [채광] 버튼으로 수집 | [돌아간다]로 복귀")
    return embed


def _make_fishing_zone_embed(zone_name: str) -> discord.Embed:
    zone = FISHING_ZONE_DATA.get(zone_name, {})
    embed = discord.Embed(
        title=f"{zone.get('emoji', '🎣')} {zone.get('name', zone_name)} — 낚시터",
        description=zone.get("desc", ""),
        color=0x1E90FF,
    )
    fish = zone.get("fish", [])
    if fish:
        embed.add_field(name="🐟 획득 가능 어종", value=" · ".join(fish), inline=False)
    if zone.get("has_silen"):
        embed.add_field(name="👤 특수", value="🌊 실렌이 낚시터를 지키고 있다.", inline=False)
    embed.set_footer(text="[낚시] 버튼으로 낚시 시작 | [돌아간다]로 복귀")
    return embed


class VisionTownView(View):
    """비전타운 메인 뷰"""

    def __init__(self, player, aff_manager, npc_manager_ref, village_manager=None):
        super().__init__(timeout=300.0)
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self.village_manager = village_manager
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        from database import NPC_DATA
        locations_seen = set()
        for npc_name, npc in NPC_DATA.items():
            loc = npc.get("location", "")
            if loc and loc not in locations_seen:
                locations_seen.add(loc)
                btn = Button(
                    label=loc[:20],
                    style=discord.ButtonStyle.secondary,
                    emoji="🏠",
                )
                btn.callback = self._make_location_callback(loc)
                self.add_item(btn)

        leave_btn = Button(label="마을을 나간다", style=discord.ButtonStyle.danger, emoji="🗺️")
        leave_btn.callback = self._leave_callback
        self.add_item(leave_btn)

    def _make_location_callback(self, location: str):
        async def callback(interaction: discord.Interaction):
            from database import NPC_DATA
            npcs_here = [n for n, d in NPC_DATA.items() if d.get("location") == location]
            if not npcs_here:
                await interaction.response.send_message("이 장소에는 아무도 없슴미댜.", ephemeral=True)
                return
            if len(npcs_here) == 1:
                npc_name = npcs_here[0]
                from npc_conversation import ConversationManager
                conv = ConversationManager(self.player, self.aff_manager, self.npc_manager_ref)
                await interaction.response.defer()
                await conv.send_conversation(interaction.channel, npc_name)
            else:
                npc_list = "\n".join(f"• {n}" for n in npcs_here)
                await interaction.response.send_message(
                    f"**{location}**에 있는 NPC:\n{npc_list}\n`/대화 [NPC이름]`으로 대화하세요.",
                    ephemeral=True,
                )
        return callback

    async def _leave_callback(self, interaction: discord.Interaction):
        embed = _make_worldmap_embed()
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.edit_message(embed=embed, view=view)


class WorldMapView(View):
    """비전의 땅 세계지도 뷰"""

    def __init__(self, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=300.0)
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        town_btn = Button(label="비전타운", style=discord.ButtonStyle.secondary, emoji="🏘️")
        town_btn.callback = self._back_to_town
        self.add_item(town_btn)

        for zone_name, zone in HUNTING_ZONE_DATA.items():
            btn = Button(label=zone_name, style=discord.ButtonStyle.danger, emoji=zone["emoji"])
            btn.callback = self._make_hunting_callback(zone_name)
            self.add_item(btn)

        for zone_name, zone in GATHERING_ZONE_DATA.items():
            btn = Button(label=zone_name, style=discord.ButtonStyle.success, emoji=zone["emoji"])
            btn.callback = self._make_gather_callback(zone_name)
            self.add_item(btn)

        for zone_name, zone in FISHING_ZONE_DATA.items():
            btn = Button(label=zone_name, style=discord.ButtonStyle.primary, emoji=zone["emoji"])
            btn.callback = self._make_fishing_callback(zone_name)
            self.add_item(btn)

    async def _back_to_town(self, interaction: discord.Interaction):
        from village import village_manager as vm
        embed = _make_town_embed(vm)
        view = VisionTownView(self.player, self.aff_manager, self.npc_manager_ref, vm)
        await interaction.response.edit_message(embed=embed, view=view)

    def _make_hunting_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            embed = _make_hunting_zone_embed(zone_name)
            view = HuntingZoneView(zone_name, self.player, self.aff_manager, self.npc_manager_ref)
            await interaction.response.edit_message(embed=embed, view=view)
        return callback

    def _make_gather_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            embed = _make_gathering_zone_embed(zone_name)
            view = GatheringZoneView(zone_name, self.player, self.aff_manager, self.npc_manager_ref)
            await interaction.response.edit_message(embed=embed, view=view)
        return callback

    def _make_fishing_callback(self, zone_name: str):
        async def callback(interaction: discord.Interaction):
            embed = _make_fishing_zone_embed(zone_name)
            zone = FISHING_ZONE_DATA.get(zone_name, {})
            view = FishingZoneView(
                zone_name, zone.get("has_silen", False),
                self.player, self.aff_manager, self.npc_manager_ref,
            )
            await interaction.response.edit_message(embed=embed, view=view)
        return callback


class HuntingZoneView(View):
    """사냥터 상세 뷰"""

    def __init__(self, zone_name: str, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=300.0)
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

    async def _hunt_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from main import battle_engine, encounter_manager
        departure = encounter_manager.clear_encounter()
        if departure:
            await interaction.channel.send(departure)
        success, result = battle_engine.start_encounter(self.zone_name)
        if isinstance(result, discord.Embed):
            await interaction.channel.send(embed=result)
        else:
            await interaction.channel.send(str(result))
        if success:
            enc_msg = encounter_manager.trigger_encounter()
            if enc_msg:
                await interaction.channel.send(enc_msg)

    async def _back_callback(self, interaction: discord.Interaction):
        embed = _make_worldmap_embed()
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.edit_message(embed=embed, view=view)


class GatheringZoneView(View):
    """채집터 상세 뷰"""

    def __init__(self, zone_name: str, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=300.0)
        self.zone_name = zone_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        gather_btn = Button(label="채집", style=discord.ButtonStyle.success, emoji="🌿")
        gather_btn.callback = self._gather_callback
        self.add_item(gather_btn)

        mine_btn = Button(label="채광", style=discord.ButtonStyle.success, emoji="⛏️")
        mine_btn.callback = self._mine_callback
        self.add_item(mine_btn)

        back_btn = Button(label="돌아간다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    async def _gather_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from main import gathering_engine
        await gathering_engine.gather(interaction.channel)

    async def _mine_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from main import gathering_engine
        await gathering_engine.mine(interaction.channel)

    async def _back_callback(self, interaction: discord.Interaction):
        embed = _make_worldmap_embed()
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.edit_message(embed=embed, view=view)


class FishingZoneView(View):
    """낚시터 상세 뷰"""

    def __init__(self, zone_name: str, has_silen: bool, player, aff_manager, npc_manager_ref):
        super().__init__(timeout=300.0)
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

        if self.has_silen:
            silen_btn = Button(label="실렌", style=discord.ButtonStyle.secondary, emoji="🌊")
            silen_btn.callback = self._silen_callback
            self.add_item(silen_btn)

        back_btn = Button(label="돌아간다", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    async def _fish_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from main import fishing_engine, encounter_manager
        departure = encounter_manager.clear_encounter()
        if departure:
            await interaction.channel.send(departure)
        await fishing_engine.fish(interaction.channel)
        enc_msg = encounter_manager.trigger_encounter()
        if enc_msg:
            await interaction.channel.send(enc_msg)

    async def _silen_callback(self, interaction: discord.Interaction):
        from npc_conversation import ConversationManager
        conv = ConversationManager(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.defer()
        await conv.send_conversation(interaction.channel, "실렌")

    async def _back_callback(self, interaction: discord.Interaction):
        embed = _make_worldmap_embed()
        view = WorldMapView(self.player, self.aff_manager, self.npc_manager_ref)
        await interaction.response.edit_message(embed=embed, view=view)
