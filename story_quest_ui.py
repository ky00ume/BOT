"""story_quest_ui.py — 스토리 퀘스트 Discord UI 컴포넌트 (PIL 이미지 기반)"""
import asyncio
import discord
from discord.ui import View, Button
from bg3_renderer import get_renderer
from story_quest_data import (
    STORY_CHAPTERS, CH1_QUESTS, CH2_QUESTS, CH3_QUESTS,
)


# ─── 유틸 ──────────────────────────────────────────────────────────────────

def _chapter_name(chapter: int) -> str:
    ch = STORY_CHAPTERS.get(chapter, {})
    return ch.get("title", f"챕터 {chapter}")


def _render_text_card(title: str, lines: list[str], system_key: str = "quest") -> discord.File:
    """여러 줄의 텍스트를 render_card rows로 변환하여 이미지 파일로 반환."""
    renderer = get_renderer()
    rows = [{"label": "", "value": line} for line in lines]
    row_count = max(len(rows), 1)
    h = max(340, 100 + row_count * 34)
    buf = renderer.render_card(
        title=title,
        rows=rows,
        system_key=system_key,
        h=h,
    )
    return discord.File(buf, filename="story.png")


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
                err_file = _render_text_card(
                    "알림", ["이미 선택했슴미댜."], system_key="quest"
                )
                await interaction.response.send_message(
                    file=err_file, ephemeral=True
                )
                return
            self.chosen = True
            delta = data.get("shadow_sync", 0)
            self.sq_manager.add_shadow_sync(delta)
            result_hint = self.sq_manager.get_shadow_hint()
            sign = f"+{delta}" if delta > 0 else str(delta)

            lines = [
                f"선택: {data['label']}",
                f"\"{result_hint}\"",
            ]
            if delta != 0:
                lines.append(f"(그림자 공명 {sign})")

            file = _render_text_card("🕷️  그림자의 응답", lines, system_key="quest")
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(
                attachments=[file], content=None, view=self
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
                f"MISS!  {miss}",
                f"픽시의 반격: {pixie}  HP -{dmg}",
            ]
            if stun:
                lines.append("★ 기절! 눈앞이 하얗게 번쩍인다...")
            lines.append(f"현재 HP: {self.player.hp}")

            self.current_turn += 1
            if self.current_turn >= len(self.turns):
                # 전투 종료
                for item in self.children:
                    item.disabled = True
                lines.append("전투 종료 — 다음 장면으로 이어집니다...")
                file = _render_text_card(
                    f"⚔️  턴 {self.current_turn} — {action}", lines, system_key="quest"
                )
                await interaction.response.edit_message(
                    attachments=[file], content=None, view=self
                )
                if self.on_done_coro:
                    await self.on_done_coro(interaction)
            else:
                file = _render_text_card(
                    f"⚔️  턴 {self.current_turn} — {action}", lines, system_key="quest"
                )
                self._build_buttons()
                await interaction.response.edit_message(
                    attachments=[file], content=None, view=self
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

        lines = [desc]

        if self.current_step >= len(self.step_descs):
            for item in self.children:
                item.disabled = True
            lines.append("탐색 완료! 무언가 발견된 것 같다...")
            file = _render_text_card(
                f"🌫️  탐색 {self.current_step}/{len(self.step_descs)}", lines, system_key="quest"
            )
            await interaction.response.edit_message(
                attachments=[file], content=None, view=self
            )
            if self.on_done_coro:
                await self.on_done_coro(interaction)
        else:
            file = _render_text_card(
                f"🌫️  탐색 {self.current_step}/{len(self.step_descs)}", lines, system_key="quest"
            )
            self._build_button()
            await interaction.response.edit_message(
                attachments=[file], content=None, view=self
            )


# ═══════════════════════════════════════════════════════════════════════════
# 컷신 자동 재생 (단계별 이미지 카드)
# ═══════════════════════════════════════════════════════════════════════════

async def play_cutscene(ctx_or_interaction, lines_list: list, delay: float = 2.5):
    """
    lines_list: [str, str, ...] 형태의 장면 문자열 목록.
    각 장면을 delay 초 간격으로 순서대로 이미지 카드로 전송합니다.
    """
    channel = ctx_or_interaction.channel
    for scene in lines_list:
        file = _render_text_card("📜 컷신", [scene], system_key="quest")
        await channel.send(file=file)
        await asyncio.sleep(delay)


# ═══════════════════════════════════════════════════════════════════════════
# 퀘스트 저널 이미지 생성
# ═══════════════════════════════════════════════════════════════════════════

def make_story_journal_image(sq_manager) -> discord.File:
    """현재 스토리 퀘스트 저널 이미지를 생성합니다."""
    chapter = sq_manager.chapter
    quest   = sq_manager.quest
    rows    = []

    for ch_num, ch_data in STORY_CHAPTERS.items():
        if ch_data.get("locked"):
            rows.append({
                "label": f"🔒 챕터 {ch_num}: {ch_data['title']}",
                "value": "다음 이야기는 아직 쓰이지 않았습니다.",
            })
            continue

        quests = ch_data["quests"]
        max_q  = ch_data["max_quest"]
        quest_lines = []
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
            quest_lines.append(f"{mark} {title_str}")

        ch_status = "진행 중" if ch_num == chapter else ("완료" if ch_num < chapter else "미해금")
        rows.append({
            "label": f"📖 챕터 {ch_num}: {ch_data['title']}",
            "value": f"[{ch_status}] " + " / ".join(quest_lines) if quest_lines else "—",
        })

    # shadow_sync 힌트
    shadow_hint = sq_manager.get_shadow_hint()
    rows.append({"label": "🌑 그림자 상태", "value": shadow_hint})

    # 힌트 수
    game_time = sq_manager.get_game_time()
    hint_count = len(sq_manager.hints)
    rows.append({
        "label": "수집한 힌트",
        "value": f"{hint_count}개  |  {'🌙 밤' if game_time == 'night' else '☀️ 낮'}",
    })

    renderer = get_renderer()
    row_count = max(len(rows), 1)
    h = max(340, 100 + row_count * 34)
    buf = renderer.render_card(
        title="📜 스토리 퀘스트 저널",
        rows=rows,
        system_key="quest",
        h=h,
    )
    return discord.File(buf, filename="story_journal.png")


def make_hints_image(sq_manager) -> discord.File:
    """수집한 힌트 목록 이미지를 생성합니다."""
    renderer = get_renderer()
    if not sq_manager.hints:
        rows = [{"label": "—", "value": "아직 수집한 힌트가 없습니다."}]
    else:
        rows = [
            {"label": f"힌트 #{i}", "value": f"「{hint}」"}
            for i, hint in enumerate(sq_manager.hints, 1)
        ]
    row_count = max(len(rows), 1)
    h = max(340, 100 + row_count * 34)
    buf = renderer.render_card(
        title="📋 수집한 힌트 목록",
        rows=rows,
        system_key="quest",
        footer=f"총 {len(sq_manager.hints)}개의 힌트",
        h=h,
    )
    return discord.File(buf, filename="hints.png")
