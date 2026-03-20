"""npc_conversation.py — 마비노기식 NPC 키워드 대화 시스템"""
import discord
from discord.ui import View, Button
from database import NPC_DATA
from npc_dialogue_db import NPC_KEYWORDS, DEFAULT_KEYWORDS, AFFINITY_UNLOCK_KEYWORDS
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR


def _get_affinity_level_name(aff_manager, npc_name: str) -> str:
    """호감도 매니저에서 현재 레벨 이름을 반환합니다."""
    if aff_manager is None:
        return "낯선이"
    return aff_manager.get_level_name(npc_name)


def _get_affinity_points(aff_manager, npc_name: str) -> int:
    """호감도 포인트를 반환합니다."""
    if aff_manager is None:
        return 0
    return aff_manager.affinities.get(npc_name, 0)


def _level_index(level_name: str) -> int:
    """호감도 레벨 이름을 숫자 인덱스로 변환합니다."""
    order = ["낯선이", "지인", "친구", "절친", "영혼의 동반자"]
    try:
        return order.index(level_name)
    except ValueError:
        return 0


def _get_response(keyword_data: dict, level_name: str) -> str:
    """호감도 단계에 맞는 응답을 반환합니다."""
    order = ["영혼의 동반자", "절친", "친구", "지인", "default"]
    lv_idx = _level_index(level_name)
    for key in order:
        if key == "default":
            return keyword_data.get("default", "...")
        key_idx = _level_index(key)
        if lv_idx >= key_idx and key in keyword_data:
            return keyword_data[key]
    return keyword_data.get("default", "...")


def get_available_keywords(npc_name: str, player_keywords: list) -> list:
    """
    플레이어가 보유한 키워드 중 해당 NPC가 응답 가능하고
    required_keyword 조건을 충족한 키워드 목록을 반환합니다.
    해금되지 않은 키워드(required_keyword 미충족)는 완전히 숨깁니다.
    """
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




async def handle_keyword_click(
    interaction: discord.Interaction,
    npc_name: str,
    keyword: str,
    player,
    aff_manager,
):
    """키워드 버튼 클릭 처리"""
    npc = NPC_DATA.get(npc_name)
    if not npc:
        await interaction.response.send_message(
            ansi(f"  {C.RED}✖ NPC를 찾을 수 없슴미댜.{C.R}"), ephemeral=True
        )
        return

    npc_kws = NPC_KEYWORDS.get(npc_name, {})
    kw_data = npc_kws.get(keyword)
    if not kw_data:
        await interaction.response.send_message(
            ansi(f"  {C.RED}✖ 이 키워드에 대한 응답이 없슴미댜.{C.R}"), ephemeral=True
        )
        return

    level_name = _get_affinity_level_name(aff_manager, npc_name)

    # 일일 제한 체크
    if aff_manager and hasattr(aff_manager, "check_talk_limit"):
        allowed, remaining = aff_manager.check_talk_limit(npc_name)
        if not allowed:
            await interaction.response.send_message(
                ansi(
                    f"  {C.GOLD}💬 {npc['name']}{C.R}\n"
                    f"  {C.DARK}─────────────────────────────{C.R}\n"
                    f"  {C.RED}오늘은 더 이야기하기 어려울 것 같아요. 내일 또 와요.{C.R}"
                ),
                ephemeral=True,
            )
            return

    response_text = _get_response(kw_data, level_name)
    aff_gain = kw_data.get("affinity_points", 2)

    # 호감도 증가
    pts = 0
    leveled = False
    lv_name = level_name
    if aff_manager:
        aff_manager.record_talk(npc_name)
        pts, leveled, lv_name = aff_manager.add_affinity(npc_name, aff_gain)

    # 새 키워드 해금
    unlocked = []
    unlock_raw = kw_data.get("unlock_keyword")
    if unlock_raw:
        if isinstance(unlock_raw, list):
            to_unlock = unlock_raw
        else:
            to_unlock = [unlock_raw]
        player_kws = getattr(player, "keywords", list(DEFAULT_KEYWORDS))
        for new_kw in to_unlock:
            if new_kw not in player_kws:
                player_kws.append(new_kw)
                unlocked.append(new_kw)
        if not hasattr(player, "keywords"):
            player.keywords = player_kws

    # 레벨업 시 추가 키워드 해금
    if leveled and aff_manager:
        level_unlocks = AFFINITY_UNLOCK_KEYWORDS.get(npc_name, {}).get(lv_name, [])
        player_kws = getattr(player, "keywords", list(DEFAULT_KEYWORDS))
        for new_kw in level_unlocks:
            if new_kw not in player_kws:
                player_kws.append(new_kw)
                unlocked.append(new_kw)
        if not hasattr(player, "keywords"):
            player.keywords = player_kws

    # 응답 임베드 구성
    lines = [
        f"  {C.GOLD}💬 {npc['name']}{C.R} — \"{keyword}\"에 대해",
        f"  {C.DARK}─────────────────────────────{C.R}",
        f"  {C.WHITE}\"{response_text}\"{C.R}",
        f"  {C.DARK}─────────────────────────────{C.R}",
    ]
    if unlocked:
        kw_str = "  ".join(f"[{k}]" for k in unlocked)
        lines.append(f"  {C.GREEN}🔓 새 키워드 획득: {kw_str}{C.R}")
    if leveled:
        lines.append(f"  {C.PINK}✦ 호감도 단계 상승! → [{lv_name}]{C.R}")
    lines.append(f"  {C.PINK}💖 호감도 +{aff_gain}{C.R}")

    msg = ansi("\n".join(lines))

    # 새로운 키워드 버튼 View 업데이트
    new_view = _build_keyword_view(npc_name, player, aff_manager)

    await interaction.response.send_message(msg)
    # 원래 메시지의 View도 업데이트
    try:
        await interaction.message.edit(view=new_view)
    except Exception:
        pass


def _build_keyword_view(npc_name: str, player, aff_manager) -> View:
    """npc_name, player, aff_manager를 이용해 KeywordView를 빌드합니다."""
    view = View(timeout=120.0)
    available = get_available_keywords(
        npc_name,
        getattr(player, "keywords", list(DEFAULT_KEYWORDS)),
    )

    def _cb_factory(kword):
        async def _cb(inter: discord.Interaction):
            await handle_keyword_click(inter, npc_name, kword, player, aff_manager)
        return _cb

    for kw in available[:25]:
        btn = Button(
            label=kw,
            style=discord.ButtonStyle.secondary,
            custom_id=f"kw_{npc_name}_{kw}",
        )
        btn.callback = _cb_factory(kw)
        view.add_item(btn)
    return view


class ConversationManager:
    """NPC 키워드 대화 관리 클래스"""

    def __init__(self, player, aff_manager=None):
        self.player = player
        self.aff_manager = aff_manager

    def build_initial_view(self, npc_name: str) -> tuple:
        """
        초기 대화 메시지 텍스트와 View를 반환합니다.
        Returns: (message_text: str, view: View)
        """
        npc = NPC_DATA.get(npc_name)
        if not npc:
            return ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}"), None

        import random
        greeting = random.choice(npc.get("greetings", ["..."]))

        aff_points = _get_affinity_points(self.aff_manager, npc_name)
        lv_name = _get_affinity_level_name(self.aff_manager, npc_name)

        # 호감도 바
        from affinity import AFFINITY_LEVELS, _calc_level
        current_lv = _calc_level(aff_points)
        next_lv = None
        for al in AFFINITY_LEVELS:
            if al["threshold"] > aff_points:
                next_lv = al
                break
        bar_max = next_lv["threshold"] if next_lv else max(aff_points + 1, 1)
        bar_filled = min(10, int(aff_points / max(bar_max, 1) * 10))
        bar_str = "█" * bar_filled + "░" * (10 - bar_filled)

        lines = [
            header_box(f"💬 {npc['name']}"),
            f"  {C.DARK}[{npc.get('role','???')}] {npc.get('location','???')}{C.R}",
            divider(),
            f"  {C.WHITE}\"{greeting}\"{C.R}",
            divider(),
            f"  {C.PINK}💖 호감도: {bar_str} {lv_name} ({aff_points}pt){C.R}",
            divider(),
        ]

        msg = ansi("\n".join(lines))
        view = _build_keyword_view(npc_name, self.player, self.aff_manager)
        return msg, view

    async def send_conversation(self, ctx, npc_name: str):
        """대화 명령어 실행 — 인사 메시지 + 키워드 버튼 전송"""
        msg, view = self.build_initial_view(npc_name)
        if view is None:
            await ctx.send(msg)
        else:
            await ctx.send(msg, view=view)
