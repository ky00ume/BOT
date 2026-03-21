"""npc_conversation.py — 마비노기식 NPC 키워드 대화 시스템 (임베드+버튼 UI)"""
import random
import discord
from discord.ui import View, Button
from database import NPC_DATA
from npc_dialogue_db import NPC_KEYWORDS, DEFAULT_KEYWORDS, AFFINITY_UNLOCK_KEYWORDS
from ui_theme import C, ansi, EMBED_COLOR


def _get_affinity_level_name(aff_manager, npc_name: str) -> str:
    if aff_manager is None:
        return "낯선이"
    return aff_manager.get_level_name(npc_name)


def _get_affinity_points(aff_manager, npc_name: str) -> int:
    if aff_manager is None:
        return 0
    return aff_manager.affinities.get(npc_name, 0)


def _level_index(level_name: str) -> int:
    order = ["낯선이", "지인", "친구", "절친", "영혼의 동반자"]
    try:
        return order.index(level_name)
    except ValueError:
        return 0


def _get_response(keyword_data: dict, level_name: str) -> str:
    """호감도 단계에 맞는 응답을 반환. 값이 list이면 랜덤 선택."""
    order = ["영혼의 동반자", "절친", "친구", "지인", "default"]
    lv_idx = _level_index(level_name)
    for key in order:
        if key == "default":
            val = keyword_data.get("default", "...")
        else:
            key_idx = _level_index(key)
            if lv_idx < key_idx or key not in keyword_data:
                continue
            val = keyword_data[key]
        if isinstance(val, list):
            return random.choice(val)
        return val
    return keyword_data.get("default", "...")


def get_available_keywords(npc_name: str, player_keywords: list) -> list:
    npc_keywords = NPC_KEYWORDS.get(npc_name, {})
    result = []
    for kw in player_keywords:
        kw_data = npc_keywords.get(kw)
        if kw_data is None:
            continue
        req = kw_data.get("required_keyword")
        if req:
            if isinstance(req, list):
                if not all(r in player_keywords for r in req):
                    continue
            else:
                if req not in player_keywords:
                    continue
        result.append(kw)
    return result


def _build_affinity_bar(aff_manager, npc_name: str) -> str:
    aff_points = _get_affinity_points(aff_manager, npc_name)
    lv_name = _get_affinity_level_name(aff_manager, npc_name)
    from affinity import AFFINITY_LEVELS
    next_lv = None
    for al in AFFINITY_LEVELS:
        if al["threshold"] > aff_points:
            next_lv = al
            break
    bar_max = next_lv["threshold"] if next_lv else max(aff_points + 1, 1)
    bar_filled = min(10, int(aff_points / max(bar_max, 1) * 10))
    bar_str = "█" * bar_filled + "░" * (10 - bar_filled)
    return f"`{bar_str}` **{lv_name}** ({aff_points}pt)"


def _build_greeting_embed(npc_name: str, aff_manager, show_limit_warning: bool = False) -> discord.Embed:
    """NPC 인사 임베드를 생성합니다."""
    npc = NPC_DATA.get(npc_name, {})
    greeting = random.choice(npc.get("greetings", ["..."]))
    aff_bar = _build_affinity_bar(aff_manager, npc_name)

    embed = discord.Embed(
        title=f"💬 {npc.get('name', npc_name)} — [{npc.get('role', '???')}] {npc.get('location', '???')}",
        color=EMBED_COLOR.get("npc", 0x4A7856),
    )
    appearance = npc.get("appearance")
    if appearance:
        embed.description = f"*{appearance}*"
    embed.add_field(name="💬 인사", value=f'"{greeting}"', inline=False)
    embed.add_field(name="💖 호감도", value=aff_bar, inline=False)
    if show_limit_warning:
        pts = _get_affinity_points(aff_manager, npc_name)
        embed.add_field(
            name="⚠️ 알림",
            value=f"⚠️ 오늘의 최대 호감도 획득량을 달성했슴미댜! (현재 {pts}pt)",
            inline=False,
        )
    return embed


def _build_keyword_response_embed(
    npc_name: str,
    keyword: str,
    response_text: str,
    aff_manager,
    aff_gain: int,
    show_limit_warning: bool,
    unlocked: list,
    leveled: bool,
    lv_name: str,
) -> discord.Embed:
    """키워드 응답 임베드를 생성합니다."""
    npc = NPC_DATA.get(npc_name, {})
    aff_bar = _build_affinity_bar(aff_manager, npc_name)

    embed = discord.Embed(
        title=f"💬 {npc.get('name', npc_name)} — [{npc.get('role', '???')}] {npc.get('location', '???')}",
        color=EMBED_COLOR.get("npc", 0x4A7856),
    )
    embed.add_field(
        name=f"[{keyword}]",
        value=f'"{response_text}"',
        inline=False,
    )
    embed.add_field(name="💖 호감도", value=aff_bar, inline=False)

    extras = []
    if not show_limit_warning and aff_gain > 0:
        extras.append(f"💖 호감도 +{aff_gain}")
    if leveled:
        extras.append(f"✦ 호감도 단계 상승! → [{lv_name}]")
    if unlocked:
        extras.append(f"🔓 새 키워드 획득: {', '.join(f'[{k}]' for k in unlocked)}")
    if extras:
        embed.add_field(name="📢", value="  |  ".join(extras), inline=False)
    if show_limit_warning:
        pts = _get_affinity_points(aff_manager, npc_name)
        embed.add_field(
            name="⚠️ 알림",
            value=f"⚠️ 오늘의 최대 호감도 획득량을 달성했슴미댜! (현재 {pts}pt)",
            inline=False,
        )
    return embed


class NPCConversationView(View):
    """NPC 대화 임베드+버튼 View"""

    def __init__(self, npc_name: str, player, aff_manager, npc_manager_ref=None):
        super().__init__(timeout=180.0)
        self.npc_name = npc_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        """현재 키워드 목록과 NPC 기능에 따라 버튼을 구성합니다."""
        self.clear_items()
        npc = NPC_DATA.get(self.npc_name, {})
        player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
        available = get_available_keywords(self.npc_name, player_kws)

        # 기본 키워드 버튼들 (마을, 날씨, 소문 및 해금된 키워드들)
        for kw in available[:20]:  # Discord 버튼 한계 고려
            btn = Button(
                label=kw,
                style=discord.ButtonStyle.secondary,
                custom_id=f"kw_{self.npc_name}_{kw}",
            )
            btn.callback = self._make_keyword_callback(kw)
            self.add_item(btn)

        # 아르바이트 버튼 (NPC에 job이 있으면)
        if npc.get("job"):
            job_btn = Button(
                label="아르바이트",
                style=discord.ButtonStyle.primary,
                emoji="💼",
            )
            job_btn.callback = self._job_callback
            self.add_item(job_btn)

        # 구매 버튼 (NPC_CATALOGS에 있으면)
        from shop import NPC_CATALOGS
        if self.npc_name in NPC_CATALOGS:
            buy_btn = Button(
                label="구매",
                style=discord.ButtonStyle.success,
                emoji="🛒",
            )
            buy_btn.callback = self._buy_callback
            self.add_item(buy_btn)

        # 수련 버튼 (NPC에 train이 있으면)
        if npc.get("train"):
            train_btn = Button(
                label="수련",
                style=discord.ButtonStyle.success,
                emoji="⚔️",
            )
            train_btn.callback = self._train_callback
            self.add_item(train_btn)

    def _make_keyword_callback(self, keyword: str):
        async def callback(interaction: discord.Interaction):
            await self._handle_keyword(interaction, keyword)
        return callback

    async def _handle_keyword(self, interaction: discord.Interaction, keyword: str):
        npc = NPC_DATA.get(self.npc_name)
        if not npc:
            await interaction.response.send_message("NPC를 찾을 수 없슴미댜.", ephemeral=True)
            return

        npc_kws = NPC_KEYWORDS.get(self.npc_name, {})
        kw_data = npc_kws.get(keyword)
        if not kw_data:
            await interaction.response.send_message("이 키워드에 대한 응답이 없슴미댜.", ephemeral=True)
            return

        level_name = _get_affinity_level_name(self.aff_manager, self.npc_name)

        # 일일 제한 체크 (차단하지 않고 경고만)
        show_limit_warning = False
        if self.aff_manager and hasattr(self.aff_manager, "check_talk_limit"):
            allowed, _ = self.aff_manager.check_talk_limit(self.npc_name)
            if not allowed:
                show_limit_warning = True

        response_text = _get_response(kw_data, level_name)
        aff_gain = kw_data.get("affinity_points", 2)

        leveled = False
        lv_name = level_name
        if self.aff_manager and not show_limit_warning:
            self.aff_manager.record_talk(self.npc_name)
            _, leveled, lv_name = self.aff_manager.add_affinity(self.npc_name, aff_gain)

        # 새 키워드 해금
        unlocked = []
        unlock_raw = kw_data.get("unlock_keyword")
        if unlock_raw:
            to_unlock = unlock_raw if isinstance(unlock_raw, list) else [unlock_raw]
            player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
            for new_kw in to_unlock:
                if new_kw not in player_kws:
                    player_kws.append(new_kw)
                    unlocked.append(new_kw)
            if not hasattr(self.player, "keywords"):
                self.player.keywords = player_kws

        # 레벨업 시 추가 키워드 해금
        if leveled and self.aff_manager:
            level_unlocks = AFFINITY_UNLOCK_KEYWORDS.get(self.npc_name, {}).get(lv_name, [])
            player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
            for new_kw in level_unlocks:
                if new_kw not in player_kws:
                    player_kws.append(new_kw)
                    unlocked.append(new_kw)

        # 임베드 갱신
        embed = _build_keyword_response_embed(
            self.npc_name, keyword, response_text,
            self.aff_manager, aff_gain, show_limit_warning,
            unlocked, leveled, lv_name,
        )

        # 새 키워드가 해금됐으면 버튼 재구성
        if unlocked or leveled:
            self._build_buttons()

        await interaction.response.edit_message(embed=embed, view=self)

    async def _job_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.npc_manager_ref:
            class _FakeCtx:
                def __init__(self, inter):
                    self.channel = inter.channel
                    self.send = inter.channel.send
            fake_ctx = _FakeCtx(interaction)
            await self.npc_manager_ref.start_job_async(fake_ctx, self.npc_name)
        else:
            await interaction.followup.send(f"**{self.npc_name}** 알바를 시작합미댜!", ephemeral=False)

    async def _buy_callback(self, interaction: discord.Interaction):
        from shop import NPC_CATALOGS
        from ui_theme import GRADE_ICON_PLAIN, EMBED_COLOR as _EC
        catalog = NPC_CATALOGS.get(self.npc_name)
        if not catalog:
            await interaction.response.send_message("이 NPC는 상점이 없슴미댜.", ephemeral=True)
            return
        npc = NPC_DATA.get(self.npc_name, {})
        embed = discord.Embed(
            title=f"🛒 {npc.get('name', self.npc_name)} 상점",
            color=_EC.get("shop", 0xFFD700),
        )
        lines = []
        for item_id, item in list(catalog.items())[:20]:
            grade = item.get("grade", "Normal")
            icon = GRADE_ICON_PLAIN.get(grade, "⚬")
            name = item.get("name", item_id)
            price = item.get("price", 0)
            extra = f" (+{item.get('slots',0)}칸)" if item.get("type") == "bag" else ""
            lines.append(f"{icon} **{name}**{extra} — {price:,}G")
        embed.description = "\n".join(lines) if lines else "상품이 없슴미댜."
        embed.set_footer(text="/구매 [NPC이름] [아이템이름] 으로 구매하셰요!")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def _train_callback(self, interaction: discord.Interaction):
        npc = NPC_DATA.get(self.npc_name, {})
        train_info = npc.get("train", {})
        embed = discord.Embed(
            title=f"⚔️ {npc.get('name', self.npc_name)} 수련",
            description=train_info.get("desc", "수련을 받을 수 있슴미댜."),
            color=EMBED_COLOR.get("battle", 0xFF4500),
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)


class ConversationManager:
    """NPC 키워드 대화 관리 클래스"""

    def __init__(self, player, aff_manager=None, npc_manager_ref=None):
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref

    async def send_conversation(self, ctx, npc_name: str):
        """대화 명령어 실행 — 임베드 + 버튼 전송"""
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}"))
            return

        # 일일 제한 확인 (차단 없음, 경고만)
        show_limit_warning = False
        if self.aff_manager and hasattr(self.aff_manager, "check_talk_limit"):
            allowed, _ = self.aff_manager.check_talk_limit(npc_name)
            if not allowed:
                show_limit_warning = True

        embed = _build_greeting_embed(npc_name, self.aff_manager, show_limit_warning)
        view = NPCConversationView(npc_name, self.player, self.aff_manager, self.npc_manager_ref)
        await ctx.send(embed=embed, view=view)
