"""npc_conversation.py — 마비노기식 NPC 키워드 대화 시스템 (PIL 이미지+버튼 UI)"""
import random
import io
import discord
from discord.ui import View, Button
from database import NPC_DATA
from npc_dialogue_db import NPC_KEYWORDS, DEFAULT_KEYWORDS, AFFINITY_UNLOCK_KEYWORDS
from bg3_renderer import get_renderer

# ── NPC 초상화 파일 ID 매핑 ─────────────────────────────────────────────────
# BG3 위키 매칭 NPC: 파일명은 static/portraits/npc/{portrait_id}.png
# 창작 캐릭터(카엘릭, 브룩샤, 실렌, 루바토)는 placeholder 유지
NPC_PORTRAIT_MAP: dict[str, str] = {
    "라파엘":    "라파엘",    # BG3 Raphael
    "카르니스":  "카르니스",  # BG3 Kar'niss (드라이더)
    "다몬":      "다몬",      # BG3 Dammon
    "오멜룸":    "오멜룸",    # BG3 Omeluum
    "몰":        "몰",        # BG3 Mol
    "아라벨라":  "아라벨라",  # BG3 Arabella
    "알피라":    "알피라",    # BG3 Alfira
    "엘레라신":  "엘레라신",  # BG3 Jaheira
    "게일의 환영": "게일의 환영",  # BG3 Gale
    # 창작 캐릭터 (placeholder)
    "카엘릭":    "카엘릭",    # 창작 캐릭터
    "브룩샤":    "브룩샤",    # 창작 캐릭터
    "실렌":      "실렌",      # 창작 캐릭터
    "루바토":    "루바토",    # 창작 캐릭터
}


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


def _render_greeting_image(npc_name: str, aff_manager, show_limit_warning: bool = False) -> io.BytesIO:
    """NPC 인사 이미지를 PIL로 생성합니다."""
    npc = NPC_DATA.get(npc_name, {})
    greeting = random.choice(npc.get("greetings", ["..."]))
    role = npc.get("role", "???")
    aff_pts = _get_affinity_points(aff_manager, npc_name)
    aff_lv = _get_affinity_level_name(aff_manager, npc_name)

    if show_limit_warning:
        greeting += f"\n(오늘의 최대 호감도 획득량을 달성했슴미댜! 현재 {aff_pts}pt)"

    return get_renderer().render_npc_dialogue(
        npc_name=npc.get("name", npc_name),
        npc_role=role,
        greeting=greeting,
        affinity_pts=aff_pts,
        affinity_level=aff_lv,
        portrait_type="npc",
        portrait_id=npc_name,
    )


def _render_keyword_response_image(
    npc_name: str,
    keyword: str,
    response_text: str,
    aff_manager,
    aff_gain: int,
    show_limit_warning: bool,
    unlocked: list,
    leveled: bool,
    lv_name: str,
) -> io.BytesIO:
    """키워드 응답 이미지를 PIL로 생성합니다."""
    npc = NPC_DATA.get(npc_name, {})
    aff_pts = _get_affinity_points(aff_manager, npc_name)
    aff_lv = _get_affinity_level_name(aff_manager, npc_name)

    rows = [
        {"label": "대사", "value": response_text},
        {"label": "호감도", "value": f"{aff_lv} ({aff_pts}pt)"},
    ]

    if not show_limit_warning and aff_gain > 0:
        rows.append({"label": "호감도 변화", "value": f"+{aff_gain}"})
    if leveled:
        rows.append({"label": "단계 상승", "value": f"→ [{lv_name}]"})
    if unlocked:
        rows.append({"label": "새 키워드", "value": ", ".join(f"[{k}]" for k in unlocked)})
    if show_limit_warning:
        rows.append({"label": "알림", "value": f"오늘의 최대 호감도 달성! (현재 {aff_pts}pt)"})

    return get_renderer().render_card(
        title=npc.get("name", npc_name),
        subtitle=f"[{keyword}]",
        rows=rows,
        system_key="npc",
    )


class NPCConversationView(View):
    """NPC 대화 이미지+버튼 View"""

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

        # 기능 버튼 수에 따라 키워드 버튼 최대 수 동적 계산 (Discord 한계: 25)
        extra_count = (
            (1 if npc.get("job") else 0) +
            (1 if self.npc_name in __import__("shop").NPC_CATALOGS else 0) +
            (1 if npc.get("train") else 0)
        )
        max_kw_buttons = max(0, 25 - extra_count)

        # 기본 키워드 버튼들 (마을, 날씨, 소문 및 해금된 키워드들)
        for kw in available[:max_kw_buttons]:
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

        # PIL 이미지로 응답 생성
        buf = _render_keyword_response_image(
            self.npc_name, keyword, response_text,
            self.aff_manager, aff_gain, show_limit_warning,
            unlocked, leveled, lv_name,
        )
        file = discord.File(buf, filename="npc_response.png")

        # 새 키워드가 해금됐으면 버튼 재구성
        if unlocked or leveled:
            self._build_buttons()

        # 친밀도/키워드 변경 시 저장
        if aff_gain or unlocked or leveled:
            try:
                from save_manager import save_manager
                save_manager.save(self.player)
            except Exception:
                pass

        await interaction.response.edit_message(attachments=[file], embed=None, view=self)

    async def _job_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.npc_manager_ref:
            class _FakeCtx:
                def __init__(self, inter):
                    self.channel = inter.channel
                    self.send = inter.channel.send
                    self.author = inter.user
            fake_ctx = _FakeCtx(interaction)
            await self.npc_manager_ref.start_job_async(fake_ctx, self.npc_name)
        else:
            await interaction.followup.send(f"**{self.npc_name}** 알바를 시작합미댜!", ephemeral=False)

    async def _buy_callback(self, interaction: discord.Interaction):
        from shop import NPC_CATALOGS
        from shop_ui import BuyView
        from database import NPC_DATA
        catalog = NPC_CATALOGS.get(self.npc_name)
        if not catalog:
            await interaction.response.send_message("이 NPC는 상점이 없슴미댜.", ephemeral=True)
            return
        npc = NPC_DATA.get(self.npc_name, {})
        embed = discord.Embed(
            title=f"🛒 {npc.get('name', self.npc_name)} 상점",
            description=f"💰 소지금: **{self.player.gold:,}G**",
            color=0xFFD700,
        )
        lines = []
        for item_id, item in list(catalog.items())[:20]:
            from ui_theme import GRADE_ICON_PLAIN
            grade = item.get("grade", "Normal")
            icon = GRADE_ICON_PLAIN.get(grade, "⚬")
            name = item.get("name", item_id)
            price = item.get("price", 0)
            extra = f" (+{item.get('slots',0)}칸)" if item.get("type") == "bag" else ""
            lines.append(f"{icon} **{name}**{extra} — {price:,}G")
        embed.add_field(name="📦 판매 상품", value="\n".join(lines) if lines else "상품이 없슴미댜.", inline=False)
        embed.set_footer(text="아래 드롭다운에서 상품과 수량을 선택하세요.")

        from shop import ShopManager
        shop_mgr = ShopManager(self.player)
        view = BuyView(self.player, shop_mgr, self.npc_name, catalog)
        msg = await interaction.response.send_message(embed=embed, view=view)
        view._message = msg

    async def _train_callback(self, interaction: discord.Interaction):
        npc = NPC_DATA.get(self.npc_name, {})
        train_info = npc.get("train", {})

        buf = get_renderer().render_card(
            title=f"{npc.get('name', self.npc_name)} 수련",
            rows=[{"label": "설명", "value": train_info.get("desc", "수련을 받을 수 있슴미댜.")}],
            system_key="battle",
        )
        file = discord.File(buf, filename="npc_train.png")
        await interaction.response.send_message(file=file, ephemeral=False)


class ConversationManager:
    """NPC 키워드 대화 관리 클래스"""

    def __init__(self, player, aff_manager=None, npc_manager_ref=None):
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref

    async def send_conversation(self, ctx, npc_name: str):
        """대화 명령어 실행 — BG3 스타일 PIL 이미지 + 버튼 전송"""
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(f"[{npc_name}]을(를) 찾을 수 없슴미댜.")
            return

        # deliver 타입 퀘스트: 목표 NPC 방문 시 자동 전달 처리
        try:
            from main import quest_manager
            deliver_msg = quest_manager.deliver_to_npc(npc_name)
            if deliver_msg:
                await ctx.send(deliver_msg)
        except Exception:
            pass

        # 일일 제한 확인 (차단 없음, 경고만)
        show_limit_warning = False
        if self.aff_manager and hasattr(self.aff_manager, "check_talk_limit"):
            allowed, _ = self.aff_manager.check_talk_limit(npc_name)
            if not allowed:
                show_limit_warning = True

        # BG3 대화 UI 이미지 (초상화 + 대사창)
        buf = _render_greeting_image(npc_name, self.aff_manager, show_limit_warning)
        file = discord.File(buf, filename="npc_dialogue.png")

        view = NPCConversationView(npc_name, self.player, self.aff_manager, self.npc_manager_ref)
        await ctx.send(file=file, view=view)
