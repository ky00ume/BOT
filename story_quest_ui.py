"""story_quest_ui.py — 스토리 퀘스트 Discord UI 컴포넌트"""
import asyncio
import discord
from discord.ui import View, Button
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR
from story_quest_data import (
    STORY_CHAPTERS, CH1_QUESTS, CH2_QUESTS, CH3_QUESTS,
)


# ─── 유틸 ──────────────────────────────────────────────────────────────────

def _chapter_name(chapter: int) -> str:
    ch = STORY_CHAPTERS.get(chapter, {})
    return ch.get("title", f"챕터 {chapter}")


# ═══════════════════════════════════════════════════════════════════════════
# 챕터 1 Q4 — 그림자와의 공명 선택지 View
# ═══════════════════════════════════════════════════════════════════════════

class ShadowChoiceView(View):
    """shadow_sync 분기 선택 버튼 (챕터 1 Q4 / 챕터 2 Q3)."""

    STYLE_MAP = {
        "red":     discord.ButtonStyle.danger,
        "yellow":  discord.ButtonStyle.secondary,
        "blurple": discord.ButtonStyle.primary,
    }

    def __init__(self, choices: dict, sq_manager, player, *, timeout=120.0):
        super().__init__(timeout=timeout)
        self.sq_manager = sq_manager
        self.player     = player
        self.chosen     = False
        for key, data in choices.items():
            style = self.STYLE_MAP.get(data.get("style", "yellow"), discord.ButtonStyle.secondary)
            emoji = {"red": "🔴", "yellow": "🟡", "blurple": "🔵"}.get(data.get("style"), "⚫")
            btn = Button(
                label=f"{emoji} {data['label']}",
                style=style,
                custom_id=f"shadow_choice_{key}",
            )
            btn.callback = self._make_cb(key, data)
            self.add_item(btn)

    def _make_cb(self, key: str, data: dict):
        async def _cb(interaction: discord.Interaction):
            if self.chosen:
                await interaction.response.send_message(
                    ansi(f"  {C.DARK}이미 선택했슴미댜.{C.R}"), ephemeral=True
                )
                return
            self.chosen = True
            delta = data.get("shadow_sync", 0)
            self.sq_manager.add_shadow_sync(delta)
            result_hint = self.sq_manager.get_shadow_hint()
            sign = f"+{delta}" if delta > 0 else str(delta)
            lines = [
                header_box("🕷️  그림자의 응답"),
                f"  {C.WHITE}선택: {data['label']}{C.R}",
                divider(),
                f"  {C.DARK}\"{result_hint}\"{C.R}",
            ]
            if delta != 0:
                color = C.RED if delta > 0 else C.BLUE
                lines.append(f"  {color}(그림자 공명 {sign}){C.R}")
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(
                content=ansi("\n".join(lines)), view=self
            )
        return _cb


# ═══════════════════════════════════════════════════════════════════════════
# 챕터 3 Q4 — 강제 패배 전투 View
# ═══════════════════════════════════════════════════════════════════════════

BATTLE_TURN_EMOJIS = {
    "물기":       "🦷",
    "할퀴기":     "🐾",
    "거미줄 발사": "🕸️",
    "점프 공격":   "⬆️",
    "전력 도약":   "🦘",
}


class ForcedBattleView(View):
    """픽시 강제 패배 전투 (챕터 3 Q4)."""

    def __init__(self, turns: list, sq_manager, player, on_done_coro=None, *, timeout=180.0):
        super().__init__(timeout=timeout)
        self.turns         = turns
        self.current_turn  = 0
        self.sq_manager    = sq_manager
        self.player        = player
        self.on_done_coro  = on_done_coro
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        if self.current_turn >= len(self.turns):
            return
        turn = self.turns[self.current_turn]
        for action in turn["actions"]:
            emoji = BATTLE_TURN_EMOJIS.get(action, "⚔️")
            btn = Button(
                label=f"{emoji} {action}",
                style=discord.ButtonStyle.danger,
                custom_id=f"battle_action_{action}",
            )
            btn.callback = self._make_action_cb(action)
            self.add_item(btn)

    def _make_action_cb(self, action: str):
        async def _cb(interaction: discord.Interaction):
            turn = self.turns[self.current_turn]
            miss  = turn["miss_reason"]
            pixie = turn["pixie_attack"]
            dmg   = turn["hp_damage"]
            stun  = turn.get("stun", False)

            # HP 감소 (최소 1 유지)
            self.player.hp = max(1, self.player.hp - dmg)

            lines = [
                header_box(f"⚔️  턴 {self.current_turn + 1} — {action}"),
                f"  {C.RED}MISS!{C.R}  {C.DARK}{miss}{C.R}",
                divider(),
                f"  {C.GOLD}픽시의 반격: {pixie}{C.R}  {C.RED}HP -{dmg}{C.R}",
            ]
            if stun:
                lines.append(f"  {C.PINK}★ 기절!{C.R} {C.DARK}눈앞이 하얗게 번쩍인다...{C.R}")
            lines.append(f"  {C.RED}현재 HP: {self.player.hp}{C.R}")

            self.current_turn += 1
            if self.current_turn >= len(self.turns):
                # 전투 종료
                for item in self.children:
                    item.disabled = True
                lines.append(divider())
                lines.append(f"  {C.DARK}전투 종료 — 다음 장면으로 이어집니다...{C.R}")
                await interaction.response.edit_message(
                    content=ansi("\n".join(lines)), view=self
                )
                if self.on_done_coro:
                    await self.on_done_coro(interaction)
            else:
                self._build_buttons()
                await interaction.response.edit_message(
                    content=ansi("\n".join(lines)), view=self
                )
        return _cb


# ═══════════════════════════════════════════════════════════════════════════
# 챕터 3 Q2 — 늪지대 탐색 View (3단계)
# ═══════════════════════════════════════════════════════════════════════════

class ExploreView(View):
    """늪지대 탐색 단계 버튼 (챕터 3 Q2)."""

    def __init__(self, step_descs: list, sq_manager, player, on_done_coro=None, *, timeout=180.0):
        super().__init__(timeout=timeout)
        self.step_descs   = step_descs
        self.current_step = 0
        self.sq_manager   = sq_manager
        self.player       = player
        self.on_done_coro = on_done_coro
        self._build_button()

    def _build_button(self):
        self.clear_items()
        if self.current_step >= len(self.step_descs):
            return
        btn = Button(
            label=f"🔦 탐색 ({self.current_step + 1}/{len(self.step_descs)})",
            style=discord.ButtonStyle.primary,
            custom_id="explore_step",
        )
        btn.callback = self._explore_cb
        self.add_item(btn)

    async def _explore_cb(self, interaction: discord.Interaction):
        desc = self.step_descs[self.current_step]
        self.current_step += 1
        lines = [
            header_box(f"🌫️  탐색 {self.current_step}/{len(self.step_descs)}"),
            f"  {C.WHITE}{desc}{C.R}",
        ]
        if self.current_step >= len(self.step_descs):
            for item in self.children:
                item.disabled = True
            lines.append(divider())
            lines.append(f"  {C.GOLD}탐색 완료! 무언가 발견된 것 같다...{C.R}")
            await interaction.response.edit_message(
                content=ansi("\n".join(lines)), view=self
            )
            if self.on_done_coro:
                await self.on_done_coro(interaction)
        else:
            self._build_button()
            await interaction.response.edit_message(
                content=ansi("\n".join(lines)), view=self
            )


# ═══════════════════════════════════════════════════════════════════════════
# 컷신 자동 재생 (단계별 임베드)
# ═══════════════════════════════════════════════════════════════════════════

async def play_cutscene(ctx_or_interaction, lines_list: list, delay: float = 2.5):
    """
    lines_list: [str, str, ...] 형태의 장면 문자열 목록.
    각 장면을 delay 초 간격으로 순서대로 전송합니다.
    """
    channel = ctx_or_interaction.channel
    for scene in lines_list:
        await channel.send(ansi(scene))
        await asyncio.sleep(delay)


# ═══════════════════════════════════════════════════════════════════════════
# 퀘스트 저널 임베드 생성
# ═══════════════════════════════════════════════════════════════════════════

def make_story_journal_embed(sq_manager) -> discord.Embed:
    """현재 스토리 퀘스트 저널 임베드를 생성합니다."""
    game_time = sq_manager.get_game_time()
    color     = sq_manager.get_embed_theme(game_time)
    embed     = discord.Embed(
        title="📜 스토리 퀘스트 저널",
        color=color,
    )

    chapter = sq_manager.chapter
    quest   = sq_manager.quest

    for ch_num, ch_data in STORY_CHAPTERS.items():
        if ch_data.get("locked"):
            embed.add_field(
                name=f"🔒 챕터 {ch_num}: {ch_data['title']}",
                value="다음 이야기는 아직 쓰이지 않았습니다.",
                inline=False,
            )
            continue

        quests = ch_data["quests"]
        max_q  = ch_data["max_quest"]
        lines  = []
        for q_key in (list(range(1, max_q + 1)) + ch_data.get("extra_keys", [])):
            qdata = quests.get(q_key)
            if not qdata:
                continue
            done = sq_manager.is_quest_done(ch_num, q_key)
            if done:
                mark = "✅"
            elif ch_num == chapter and (
                (isinstance(q_key, int) and q_key == quest)
                or (isinstance(q_key, str) and ch_num == chapter)
            ):
                mark = "▶️"
            else:
                mark = "○"
            title_str = qdata.get("title", str(q_key))
            lines.append(f"{mark} {title_str}")

        ch_status = "진행 중" if ch_num == chapter else ("완료" if ch_num < chapter else "미해금")
        embed.add_field(
            name=f"📖 챕터 {ch_num}: {ch_data['title']}  [{ch_status}]",
            value="\n".join(lines) if lines else "—",
            inline=False,
        )

    # shadow_sync 힌트
    shadow_hint = sq_manager.get_shadow_hint()
    embed.add_field(name="🌑 그림자 상태", value=shadow_hint, inline=False)

    # 힌트 수
    hint_count = len(sq_manager.hints)
    embed.set_footer(text=f"수집한 힌트: {hint_count}개  |  {'🌙 밤' if game_time == 'night' else '☀️ 낮'}")
    return embed


def make_hints_embed(sq_manager) -> discord.Embed:
    """수집한 힌트 목록 임베드를 생성합니다."""
    color = sq_manager.get_embed_theme()
    embed = discord.Embed(title="📋 수집한 힌트 목록", color=color)
    if not sq_manager.hints:
        embed.description = "아직 수집한 힌트가 없습니다."
    else:
        for i, hint in enumerate(sq_manager.hints, 1):
            embed.add_field(name=f"힌트 #{i}", value=f"「{hint}」", inline=False)
    embed.set_footer(text=f"총 {len(sq_manager.hints)}개의 힌트")
    return embed
