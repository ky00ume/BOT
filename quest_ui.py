"""quest_ui.py — 마비노기식 PIL 이미지 퀘스트 창 UI"""
import discord
from discord.ui import View, Button, Select
from bg3_renderer import get_renderer
from quest import QUEST_DB


DIFFICULTY_LABEL = {"easy": "쉬움", "normal": "보통", "hard": "어려움"}
TYPE_LABEL = {"collect": "채집형", "kill": "처치형", "deliver": "전달형"}

MAX_SELECT_LABEL_LENGTH = 80  # Discord select menu label max length


def _make_quest_list_image(quest_manager) -> discord.File:
    """퀘스트 목록 메인 이미지 생성"""
    active = [(qid, QUEST_DB[qid]) for qid in quest_manager.active_quests if qid in QUEST_DB]
    completable = []
    for qid, q in active:
        info = quest_manager.active_quests[qid]
        tp = q["type"]
        if tp == "collect":
            have = quest_manager.player.inventory.get(q.get("target_item", ""), 0)
            if have >= q.get("target_count", 1):
                completable.append((qid, q))
        elif tp == "kill":
            if info["progress"] >= q.get("target_count", 1):
                completable.append((qid, q))
        elif tp == "deliver":
            if info.get("delivered"):
                completable.append((qid, q))

    completable_ids = {qid for qid, _ in completable}
    in_progress = [(qid, q) for qid, q in active if qid not in completable_ids]
    available = [(qid, QUEST_DB[qid]) for qid in QUEST_DB
                 if qid not in quest_manager.completed_quests and qid not in quest_manager.active_quests]

    rows = []

    # 완료 가능
    for _, q in completable:
        rows.append({"label": "완료 가능", "value": f"{q['name']} — {q['npc']}", "color": (100, 255, 100)})

    # 진행 중
    for qid, q in in_progress:
        info = quest_manager.active_quests[qid]
        tp = q["type"]
        if tp in ("collect", "kill"):
            prog = info["progress"]
            tot = q.get("target_count", 1)
            rows.append({"label": "진행 중", "value": f"{q['name']} ({prog}/{tot})", "color": (255, 220, 100)})
        elif tp == "deliver":
            state = "전달 완료" if info.get("delivered") else "전달 중"
            rows.append({"label": "진행 중", "value": f"{q['name']} [{state}]", "color": (255, 220, 100)})

    # 수락 가능
    for _, q in available[:10]:
        diff = DIFFICULTY_LABEL.get(q.get("difficulty", "easy"), "")
        rows.append({"label": "수락 가능", "value": f"{q['name']} — {q['npc']} | {diff}"})

    if len(available) > 10:
        rows.append({"label": "기타", "value": f"...외 {len(available) - 10}개"})

    if not rows:
        rows.append({"label": "안내", "value": "현재 퀘스트가 없습니다."})

    # 높이를 행 수에 맞춰 동적으로 계산
    h = max(260, 140 + len(rows) * 34)

    r = get_renderer()
    buf = r.render_card(
        title="퀘스트 목록",
        rows=rows,
        grade="Normal",
        system_key="quest",
        footer="셀렉트 메뉴에서 퀘스트를 선택하세요",
        w=600,
        h=h,
    )
    return discord.File(buf, filename="quest_list.png")


def _make_quest_detail_image(quest_id, quest_manager, player) -> discord.File:
    """퀘스트 상세 이미지 생성"""
    q = QUEST_DB.get(quest_id, {})
    info = quest_manager.active_quests.get(quest_id, {})
    is_active = quest_id in quest_manager.active_quests

    rows = [
        {"label": "설명", "value": q.get("desc", "")},
        {"label": "의뢰 NPC", "value": q.get("npc", "")},
        {"label": "타입", "value": TYPE_LABEL.get(q.get("type", ""), q.get("type", ""))},
        {"label": "난이도", "value": DIFFICULTY_LABEL.get(q.get("difficulty", "easy"), "")},
    ]

    tp = q.get("type", "")
    if is_active:
        prog = info.get("progress", 0)
        if tp == "collect":
            have = player.inventory.get(q.get("target_item", ""), 0)
            total = q.get("target_count", 1)
            rows.append({"label": "진행 상황", "value": f"{have}/{total}", "color": (100, 220, 255)})
        elif tp == "kill":
            total = q.get("target_count", 1)
            rows.append({"label": "진행 상황", "value": f"{prog}/{total}", "color": (100, 220, 255)})
        elif tp == "deliver":
            state = "전달 완료 — 의뢰자에게 귀환하세요" if info.get("delivered") else "목표 NPC에게 전달하세요"
            rows.append({"label": "진행 상황", "value": state, "color": (100, 220, 255)})

    # 보상
    reward_parts = []
    reward_parts.append(f"{q.get('reward_gold', 0):,}G")
    reward_parts.append(f"{q.get('reward_exp', 0)} EXP")
    if q.get("reward_item"):
        from items import ALL_ITEMS
        item_name = ALL_ITEMS.get(q["reward_item"], {}).get("name", q["reward_item"])
        reward_parts.append(item_name)
    rows.append({"label": "보상", "value": " | ".join(reward_parts), "color": (255, 215, 0)})

    h = max(300, 140 + len(rows) * 34)

    r = get_renderer()
    buf = r.render_card(
        title=q.get("name", quest_id),
        rows=rows,
        grade="Normal",
        subtitle=f"퀘스트 상세",
        system_key="quest",
        footer="✦ 비전 타운 ✦",
        w=600,
        h=h,
    )
    return discord.File(buf, filename="quest_detail.png")


def _make_result_image(title, quest_name, result_text) -> discord.File:
    """퀘스트 액션 결과 이미지 생성"""
    rows = [
        {"label": "퀘스트", "value": quest_name},
        {"label": "결과", "value": result_text, "color": (100, 255, 100)},
    ]
    r = get_renderer()
    buf = r.render_card(
        title=title,
        rows=rows,
        grade="Normal",
        subtitle=quest_name,
        system_key="quest",
        footer="✦ 비전 타운 ✦",
        w=560,
        h=260,
    )
    return discord.File(buf, filename="quest_result.png")


class QuestWindowView(View):
    """마비노기식 퀘스트 창 View"""

    def __init__(self, quest_manager, player):
        super().__init__(timeout=300.0)
        self.quest_manager = quest_manager
        self.player = player
        self._build_select()
        self._add_story_button()

    def _build_select(self):
        """퀘스트 Select Menu 구성"""
        self.clear_items()

        active = [(qid, QUEST_DB[qid]) for qid in self.quest_manager.active_quests if qid in QUEST_DB]
        available = [(qid, QUEST_DB[qid]) for qid in QUEST_DB
                     if qid not in self.quest_manager.completed_quests
                     and qid not in self.quest_manager.active_quests]

        options = []

        # 완료 가능 먼저
        for qid, q in active:
            info = self.quest_manager.active_quests[qid]
            tp = q["type"]
            ready = False
            if tp == "collect":
                ready = self.player.inventory.get(q.get("target_item", ""), 0) >= q.get("target_count", 1)
            elif tp == "kill":
                ready = info["progress"] >= q.get("target_count", 1)
            elif tp == "deliver":
                ready = info.get("delivered", False)
            emoji = "✅" if ready else "🔄"
            label = q["name"][:MAX_SELECT_LABEL_LENGTH]
            options.append(discord.SelectOption(
                label=label,
                value=qid,
                emoji=emoji,
                description=f"{q['npc']} | {TYPE_LABEL.get(q['type'], q['type'])}",
            ))

        # 수락 가능
        for qid, q in available[:15]:
            options.append(discord.SelectOption(
                label=q["name"][:MAX_SELECT_LABEL_LENGTH],
                value=qid,
                emoji="◽",
                description=f"{q['npc']} | {DIFFICULTY_LABEL.get(q.get('difficulty', 'easy'), '')}",
            ))

        if not options:
            options.append(discord.SelectOption(label="퀘스트 없음", value="_none", description="현재 퀘스트가 없습니다."))

        select = Select(
            placeholder="퀘스트를 선택하세요...",
            options=options[:25],
        )
        select.callback = self._on_select
        self.add_item(select)
        self._add_story_button()

    def _add_story_button(self):
        story_btn = Button(label="📖 메인 스토리", style=discord.ButtonStyle.secondary)
        story_btn.callback = self._story_callback
        self.add_item(story_btn)

    async def _on_select(self, interaction: discord.Interaction):
        qid = interaction.data["values"][0]
        if qid == "_none":
            await interaction.response.defer()
            return
        file = _make_quest_detail_image(qid, self.quest_manager, self.player)
        detail_view = QuestDetailView(qid, self.quest_manager, self.player)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=detail_view, content=None,
        )

    async def _story_callback(self, interaction: discord.Interaction):
        from story_quest_ui import make_story_journal_embed
        from main import story_quest_manager
        embed = make_story_journal_embed(story_quest_manager)
        back_view = StoryBackView(self.quest_manager, self.player)
        await interaction.response.edit_message(embed=embed, view=back_view, attachments=[])


class QuestDetailView(View):
    """퀘스트 상세 버튼 뷰"""

    def __init__(self, quest_id: str, quest_manager, player):
        super().__init__(timeout=300.0)
        self.quest_id = quest_id
        self.quest_manager = quest_manager
        self.player = player
        self._build()

    def _build(self):
        self.clear_items()
        q = QUEST_DB.get(self.quest_id, {})
        is_active = self.quest_id in self.quest_manager.active_quests

        if is_active:
            info = self.quest_manager.active_quests[self.quest_id]
            tp = q.get("type", "")
            ready = False
            if tp == "collect":
                ready = self.player.inventory.get(q.get("target_item", ""), 0) >= q.get("target_count", 1)
            elif tp == "kill":
                ready = info["progress"] >= q.get("target_count", 1)
            elif tp == "deliver":
                ready = info.get("delivered", False)

            if ready:
                complete_btn = Button(label="완료하기", style=discord.ButtonStyle.success, emoji="✅")
                complete_btn.callback = self._complete_callback
                self.add_item(complete_btn)

            abandon_btn = Button(label="포기하기", style=discord.ButtonStyle.danger, emoji="🚫")
            abandon_btn.callback = self._abandon_callback
            self.add_item(abandon_btn)
        else:
            accept_btn = Button(label="수락하기", style=discord.ButtonStyle.primary, emoji="📝")
            accept_btn.callback = self._accept_callback
            self.add_item(accept_btn)

        back_btn = Button(label="뒤로가기", style=discord.ButtonStyle.secondary, emoji="◀️")
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    async def _accept_callback(self, interaction: discord.Interaction):
        q = QUEST_DB.get(self.quest_id, {})
        result = self.quest_manager.accept_quest(self.quest_id)
        self._build()
        file = _make_result_image("퀘스트 수락", q.get("name", self.quest_id), result)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=self, content=None,
        )

    async def _complete_callback(self, interaction: discord.Interaction):
        q = QUEST_DB.get(self.quest_id, {})
        result = self.quest_manager.complete_quest(self.quest_id)
        file = _make_result_image("퀘스트 완료", q.get("name", self.quest_id), result)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=None, content=None,
        )

    async def _abandon_callback(self, interaction: discord.Interaction):
        q = QUEST_DB.get(self.quest_id, {})
        result = self.quest_manager.abandon_quest(self.quest_id)
        file = _make_result_image("퀘스트 포기", q.get("name", self.quest_id), result)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=None, content=None,
        )

    async def _back_callback(self, interaction: discord.Interaction):
        qw = QuestWindowView(self.quest_manager, self.player)
        file = _make_quest_list_image(self.quest_manager)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=qw, content=None,
        )


class StoryBackView(View):
    """메인 스토리에서 일반 퀘스트로 돌아가는 뷰"""

    def __init__(self, quest_manager, player):
        super().__init__(timeout=300.0)
        self.quest_manager = quest_manager
        self.player = player
        back_btn = Button(label="← 일반 퀘스트", style=discord.ButtonStyle.secondary)
        back_btn.callback = self._back_callback
        self.add_item(back_btn)

    async def _back_callback(self, interaction: discord.Interaction):
        qw = QuestWindowView(self.quest_manager, self.player)
        file = _make_quest_list_image(self.quest_manager)
        await interaction.response.edit_message(
            attachments=[file], embed=None, view=qw,
        )
