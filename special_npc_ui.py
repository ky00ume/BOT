"""special_npc_ui.py — 특수 NPC 인카운터 UI (버튼/셀렉트 방식)"""
import discord
from discord.ui import View, Button, Select
from special_npc import (
    SPECIAL_NPCS, ENCOUNTER_SHORT_GREETINGS, ENCOUNTER_NPC_ROLES,
    render_encounter_image,
)

# 특수 NPC 키워드 목록
SPECIAL_NPC_KEYWORDS = {
    "라파엘": ["계약", "거래", "보상", "소문", "악마"],
    "카르니스": ["마제스티", "어둠", "언더다크", "거미", "힘"],
    "루바토": ["모험", "소문", "음악", "동료", "여행"],
}

# 특수 NPC 키워드 응답
SPECIAL_NPC_RESPONSES = {
    "라파엘": {
        "계약": "\"계약이라는 건 말이지... 서로가 원하는 걸 얻는 가장 우아한 방법이야. 어때?\"",
        "거래": "\"거래는 공정해야 하지. 물론 내가 정하는 공정함이지만.\" *미소를 짓는다*",
        "보상": "\"보상이 필요하다고? 좋아. 하지만 대가도 있어. 항상 그렇듯이.\"",
        "소문": "\"소문이라면 나보다 많이 아는 자는 없지. 값을 치를 준비가 됐어?\"",
        "악마": "\"악마라고? 실망스럽군. 나는 그냥... 거래에 특화된 존재일 뿐이야.\"",
    },
    "카르니스": {
        "마제스티": "\"마제스티... 그 이름을 함부로 입에 올리지 마. 그 분의 이름은 경외로 불려야 해.\"",
        "어둠": "\"어둠은 두려워할 게 아니야. 어둠 속에서 사는 법을 배워라.\"",
        "언더다크": "\"이곳이 내 영역이다. 너 같은 것이 감히 발을 들이다니.\"",
        "거미": "\"거미는 완벽한 사냥꾼이야. 기다리고, 포착하고, 끝낸다.\"",
        "힘": "\"힘? 너 같은 미물이 힘을 논해? 웃기는군.\"",
    },
    "루바토": {
        "모험": "\"모험이라면 나도 빠질 수 없지! 하지만 항상 조심해야 한다고!\"",
        "소문": "\"소문이라면 내가 제일 잘 알지! 어디서 들었냐면요~\"",
        "음악": "\"음악은 영혼의 언어야! 들어볼래? ♪ 라라라~ ♫\"",
        "동료": "\"동료? 나야말로 최고의 동료가 될 수 있어! 믿어봐!\"",
        "여행": "\"여행이라면 내가 전문가지! 이 세상 구석구석 다 가봤거든.\"",
    },
}


def _get_aff_info(aff_manager, npc_name: str):
    """호감도 정보 반환 헬퍼."""
    if aff_manager is None:
        return 0, "낯선이"
    pts = aff_manager.affinities.get(npc_name, 0) if hasattr(aff_manager, "affinities") else 0
    lv = "낯선이"
    if hasattr(aff_manager, "get_level_name"):
        lv = aff_manager.get_level_name(npc_name)
    return pts, lv


class SpecialNPCView(View):
    """특수 NPC 인카운터 버튼 UI"""

    def __init__(self, npc_name: str, player, aff_manager, npc_manager_ref, encounter_manager):
        super().__init__(timeout=180.0)
        self.npc_name = npc_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self.encounter_manager = encounter_manager
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()

        # [대화] 버튼 — 키워드 셀렉트 드롭다운 열기
        talk_btn = Button(label="대화", style=discord.ButtonStyle.secondary, emoji="💬")
        talk_btn.callback = self._talk_callback
        self.add_item(talk_btn)

        # [버프 받기] 버튼
        buff_btn = Button(label="버프 받기", style=discord.ButtonStyle.success, emoji="✨")
        buff_btn.callback = self._buff_callback
        self.add_item(buff_btn)

        # [선물하기] 버튼
        gift_btn = Button(label="선물하기", style=discord.ButtonStyle.primary, emoji="🎁")
        gift_btn.callback = self._gift_callback
        self.add_item(gift_btn)

        # [계약] 버튼 (라파엘 전용)
        if self.npc_name == "라파엘":
            contract_btn = Button(label="계약", style=discord.ButtonStyle.danger, emoji="📜")
            contract_btn.callback = self._contract_callback
            self.add_item(contract_btn)

    async def _render_and_send(self, interaction: discord.Interaction, greeting: str):
        """NPC 응답 PIL 이미지를 렌더링하여 메시지를 업데이트합니다."""
        try:
            from bg3_renderer import get_renderer, render_async
            pts, lv = _get_aff_info(self.aff_manager, self.npc_name)
            buf = await render_async(
                get_renderer().render_npc_dialogue,
                npc_name=self.npc_name,
                npc_role=ENCOUNTER_NPC_ROLES.get(self.npc_name, "특수 NPC"),
                greeting=greeting,
                affinity_pts=pts,
                affinity_level=lv,
                portrait_type="npc",
                portrait_id=self.npc_name,
            )
            buf.seek(0)
            file = discord.File(fp=buf, filename="npc_response.png")
            await interaction.response.send_message(file=file, view=self, ephemeral=False)
        except Exception:
            await interaction.response.send_message(greeting, ephemeral=False)

    async def _talk_callback(self, interaction: discord.Interaction):
        """키워드 Select 드롭다운을 에페메랄 메시지로 표시합니다."""
        keywords = SPECIAL_NPC_KEYWORDS.get(self.npc_name, [])
        if not keywords:
            await interaction.response.send_message("대화할 키워드가 없슴미댜.", ephemeral=True)
            return
        options = [discord.SelectOption(label=kw, value=kw) for kw in keywords]
        kw_select = Select(
            placeholder="키워드를 선택하세요...",
            options=options,
            custom_id=f"special_kw_{self.npc_name}",
        )
        async def kw_callback(sel_interaction: discord.Interaction):
            keyword = kw_select.values[0]
            responses = SPECIAL_NPC_RESPONSES.get(self.npc_name, {})
            response_text = responses.get(keyword, f"\"{keyword}\"... 흠.")
            # 호감도 증가 (약간)
            if self.aff_manager and hasattr(self.aff_manager, "add_affinity"):
                self.aff_manager.add_affinity(self.npc_name, 2)
            try:
                from bg3_renderer import get_renderer, render_async
                pts, lv = _get_aff_info(self.aff_manager, self.npc_name)
                buf = await render_async(
                    get_renderer().render_npc_dialogue,
                    npc_name=self.npc_name,
                    npc_role=ENCOUNTER_NPC_ROLES.get(self.npc_name, "특수 NPC"),
                    greeting=f"[{keyword}] {response_text}",
                    affinity_pts=pts,
                    affinity_level=lv,
                    portrait_type="npc",
                    portrait_id=self.npc_name,
                )
                buf.seek(0)
                file = discord.File(fp=buf, filename="npc_response.png")
                await sel_interaction.response.send_message(file=file, ephemeral=False)
            except Exception:
                await sel_interaction.response.send_message(response_text, ephemeral=False)
        kw_select.callback = kw_callback
        kw_view = View(timeout=60.0)
        kw_view.add_item(kw_select)
        await interaction.response.send_message(
            f"**{self.npc_name}**에게 어떤 키워드로 말을 걸까요?",
            view=kw_view,
            ephemeral=True,
        )

    async def _buff_callback(self, interaction: discord.Interaction):
        """NPC 버프 적용 (NPC별 다른 효과)."""
        if self.npc_name == "루바토":
            result = self.encounter_manager.apply_lubato_buff()
            await interaction.response.send_message(result, ephemeral=False)
        elif self.npc_name == "카르니스":
            heal_hp = int(self.player.max_hp * 0.15)
            self.player.hp = min(self.player.hp + heal_hp, self.player.max_hp)
            msg = (
                f"🕷️ **카르니스**의 차가운 손길이 상처를 아물게 한다.\n"
                f"HP +{heal_hp} (→ {self.player.hp}/{self.player.max_hp})"
            )
            await interaction.response.send_message(msg, ephemeral=False)
        elif self.npc_name == "라파엘":
            heal_mp = int(self.player.max_mp * 0.25)
            self.player.mp = min(self.player.mp + heal_mp, self.player.max_mp)
            msg = (
                f"⚡ **라파엘**이 악마의 힘을 살짝 나눠준다.\n"
                f"MP +{heal_mp} (→ {self.player.mp}/{self.player.max_mp})"
            )
            await interaction.response.send_message(msg, ephemeral=False)
        else:
            await interaction.response.send_message("이 NPC는 버프를 줄 수 없슴미댜.", ephemeral=True)

    async def _gift_callback(self, interaction: discord.Interaction):
        """인벤토리 아이템 선물하기 셀렉트 드롭다운 표시."""
        from items import ALL_ITEMS
        inv = self.player.inventory
        if not inv:
            await interaction.response.send_message("선물할 아이템이 없슴미댜!", ephemeral=True)
            return
        options = []
        for iid, cnt in list(inv.items())[:25]:
            item = ALL_ITEMS.get(iid, {})
            if item.get("quest_locked"):
                continue
            name = item.get("name", iid)
            options.append(discord.SelectOption(
                label=f"{name} (×{cnt})",
                value=iid,
                description=item.get("desc", "")[:50],
            ))
        if not options:
            await interaction.response.send_message("선물 가능한 아이템이 없슴미댜!", ephemeral=True)
            return
        gift_select = Select(
            placeholder="선물할 아이템을 선택하세요...",
            options=options,
            custom_id=f"gift_select_{self.npc_name}",
        )
        async def gift_select_cb(sel_interaction: discord.Interaction):
            item_id = gift_select.values[0]
            from items import ALL_ITEMS as _AI
            item = _AI.get(item_id, {})
            item_name = item.get("name", item_id)
            if self.player.inventory.get(item_id, 0) < 1:
                await sel_interaction.response.send_message("아이템이 부족슴미댜!", ephemeral=True)
                return
            self.player.remove_item(item_id, 1)
            # 호감도 증가
            aff_gain = 5
            if self.aff_manager and hasattr(self.aff_manager, "add_affinity"):
                self.aff_manager.add_affinity(self.npc_name, aff_gain)
            pts, lv = _get_aff_info(self.aff_manager, self.npc_name)
            gift_responses = {
                "라파엘": f"\"오, 이건... 꽤 마음에 들어. 고마워, 라고 해두지.\" ({item_name} 수령)",
                "카르니스": f"\"...받아두지. 쓸모가 있을 것 같군.\" ({item_name} 수령)",
                "루바토": f"\"와! 정말?! 고마워!! 이런 거 처음이야~!\" ({item_name} 수령)",
            }
            response = gift_responses.get(self.npc_name, f"{item_name}을(를) 선물했슴미댜!")
            try:
                from bg3_renderer import get_renderer, render_async
                buf = await render_async(
                    get_renderer().render_npc_dialogue,
                    npc_name=self.npc_name,
                    npc_role=ENCOUNTER_NPC_ROLES.get(self.npc_name, "특수 NPC"),
                    greeting=f"[선물: {item_name}] {response}",
                    affinity_pts=pts,
                    affinity_level=lv,
                    portrait_type="npc",
                    portrait_id=self.npc_name,
                )
                buf.seek(0)
                file = discord.File(fp=buf, filename="npc_gift.png")
                await sel_interaction.response.send_message(
                    file=file,
                    ephemeral=False,
                )
            except Exception:
                await sel_interaction.response.send_message(response, ephemeral=False)
        gift_select.callback = gift_select_cb
        gift_view = View(timeout=60.0)
        gift_view.add_item(gift_select)
        await interaction.response.send_message(
            f"**{self.npc_name}**에게 무엇을 선물하시겠슴미꺄?",
            view=gift_view,
            ephemeral=True,
        )

    async def _contract_callback(self, interaction: discord.Interaction):
        """라파엘 계약 제안 (라파엘 전용)."""
        result = self.encounter_manager.propose_contract()
        confirm_view = View(timeout=60.0)
        accept_btn = Button(label="계약 수락", style=discord.ButtonStyle.success, emoji="✅")
        reject_btn = Button(label="계약 거절", style=discord.ButtonStyle.danger, emoji="❌")
        async def accept_cb(btn_interaction: discord.Interaction):
            msg = self.encounter_manager.accept_contract()
            await btn_interaction.response.send_message(msg, ephemeral=False)
        async def reject_cb(btn_interaction: discord.Interaction):
            msg = self.encounter_manager.reject_contract()
            await btn_interaction.response.send_message(msg, ephemeral=False)
        accept_btn.callback = accept_cb
        reject_btn.callback = reject_cb
        confirm_view.add_item(accept_btn)
        confirm_view.add_item(reject_btn)
        await interaction.response.send_message(result, view=confirm_view, ephemeral=False)
