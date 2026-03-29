"""care_ui.py — "하이네스의 방" discord.ui.View 기반 돌봄 UI"""
import discord
import random
import time as _time
from bg3_renderer import get_renderer
from costume_data import (
    COSTUME_ITEMS, SNACK_ITEMS, SNACK_RECIPES, COSTUME_RECIPES,
    GRADE_EMOJI, GRADE_LABELS,
)
from database import save_player_to_db


# ── 헬퍼: stat bar ──────────────────────────────────────────────────────────
def _bar(value: int, max_val: int = 100, length: int = 10) -> str:
    filled = round(value / max_val * length)
    return "█" * filled + "░" * (length - filled)


def _make_room_card(player):
    """하이네스의 방 현황 카드 이미지 생성."""
    cond = player.condition
    stab = player.stability
    fati = player.fatigue

    rows = [
        {"label": "💛 컨디션", "value": f"{_bar(cond)}  {cond}"},
        {"label": "💙 안정감", "value": f"{_bar(stab)}  {stab}"},
        {"label": "🔥 피로도", "value": f"{_bar(fati)}  {fati}"},
    ]
    buf = get_renderer().render_card(
        title="🏠 하이네스의 방",
        rows=rows,
        system_key="system",
        grade="Normal",
        footer="돌봄 시스템",
    )
    return discord.File(buf, filename="care_room.png")


def _result_card(title, rows, grade="Normal"):
    buf = get_renderer().render_card(
        title=title,
        rows=rows,
        system_key="system",
        grade=grade,
        footer="돌봄 시스템",
    )
    return discord.File(buf, filename="care_result.png")


# ── 의장 관리 서브 View ──────────────────────────────────────────────────────
class CostumeManageView(discord.ui.View):
    SLOT_LABELS = {
        "toy":       "🪄 장난감",
        "hat":       "🎀 모자",
        "outfit":    "👗 의상",
        "shoes":     "👢 신발",
        "accessory": "💎 악세사리",
    }

    def __init__(self, player, parent_view):
        super().__init__(timeout=60)
        self.player      = player
        self.parent_view = parent_view
        self._message    = None
        self._equip_slot = None   # 장착할 때 선택된 슬롯
        self._selected_item = None

        # 장착 버튼 (슬롯별)
        for slot, label in self.SLOT_LABELS.items():
            btn = discord.ui.Button(
                label=f"{label} 장착",
                style=discord.ButtonStyle.primary,
                custom_id=f"equip_{slot}",
                row=0 if slot in ("toy", "hat") else 1 if slot in ("outfit", "shoes") else 2,
            )
            btn.callback = self._make_equip_cb(slot)
            self.add_item(btn)

        # 해제 버튼
        unequip_btn = discord.ui.Button(
            label="🗑️ 해제",
            style=discord.ButtonStyle.danger,
            custom_id="unequip_costume",
            row=2,
        )
        unequip_btn.callback = self._on_unequip_select
        self.add_item(unequip_btn)

        # 뒤로 가기
        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_costume",
            row=3,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    def _make_equip_cb(self, slot: str):
        async def cb(interaction: discord.Interaction):
            self._equip_slot = slot
            # 해당 슬롯 의장 아이템 목록을 인벤에서 검색
            from items import ALL_ITEMS
            options = []
            for item_id, count in self.player.inventory.items():
                item = ALL_ITEMS.get(item_id, {})
                if item.get("type") == "costume" and item.get("slot") == slot:
                    grade = item.get("grade", "일반")
                    icon  = GRADE_EMOJI.get(grade, "⚬")
                    options.append(discord.SelectOption(
                        label=f"{icon} {item.get('name', item_id)} x{count}",
                        value=item_id,
                        description=item.get("description", "")[:50],
                    ))

            if not options:
                slot_label = self.SLOT_LABELS.get(slot, slot)
                file = _result_card(
                    "의장 장착",
                    [{"label": "안내", "value": f"{slot_label}에 장착 가능한 의장 아이템이 없슴미댜."}],
                    grade="Fail",
                )
                await interaction.response.send_message(file=file, ephemeral=True)
                return

            select = discord.ui.Select(
                placeholder=f"{self.SLOT_LABELS.get(slot, slot)} 슬롯에 장착할 의장 선택...",
                options=options[:25],
                custom_id=f"equip_item_select_{slot}",
            )
            select_view = _ItemSelectView(select, self._on_equip_confirm)
            await interaction.response.send_message(
                content=f"**{self.SLOT_LABELS.get(slot, slot)} 슬롯 장착**\n장착할 의장을 선택하셰요.",
                view=select_view,
                ephemeral=True,
            )
        return cb

    async def _on_equip_confirm(self, interaction: discord.Interaction, item_id: str):
        msg = self.player.equip_costume(item_id)
        from items import ALL_ITEMS
        item = ALL_ITEMS.get(item_id, {})
        grade_key = item.get("grade", "일반")
        grade_eng = GRADE_LABELS.get(grade_key, "Normal")
        try:
            save_player_to_db(self.player)
        except Exception:
            pass
        file = _result_card(
            "의장 장착",
            [{"label": "결과", "value": msg}],
            grade=grade_eng,
        )
        await interaction.response.edit_message(content=None, attachments=[file], view=None)

    async def _on_unequip_select(self, interaction: discord.Interaction):
        # 장착된 의장 슬롯 목록 표시
        options = []
        for slot, label in self.SLOT_LABELS.items():
            equipped_id = self.player.costume.get(slot)
            if equipped_id:
                from items import ALL_ITEMS
                item = ALL_ITEMS.get(equipped_id, {})
                options.append(discord.SelectOption(
                    label=f"{label}: {item.get('name', equipped_id)}",
                    value=slot,
                ))

        if not options:
            file = _result_card(
                "의장 해제",
                [{"label": "안내", "value": "장착된 의장이 없슴미댜."}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        async def unequip_confirm(inter: discord.Interaction, slot_chosen: str):
            msg = self.player.unequip_costume(slot_chosen)
            try:
                save_player_to_db(self.player)
            except Exception:
                pass
            file = _result_card("의장 해제", [{"label": "결과", "value": msg}])
            await inter.response.edit_message(content=None, attachments=[file], view=None)

        select = discord.ui.Select(
            placeholder="해제할 의장 슬롯 선택...",
            options=options,
            custom_id="unequip_slot_select",
        )
        select_view = _ItemSelectView(select, unequip_confirm)
        await interaction.response.send_message(
            content="해제할 의장 슬롯을 선택하셰요.",
            view=select_view,
            ephemeral=True,
        )

    async def _on_back(self, interaction: discord.Interaction):
        file = _make_room_card(self.player)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self.parent_view
        )

    def _build_status_rows(self):
        rows = []
        for slot, label in self.SLOT_LABELS.items():
            equipped_id = self.player.costume.get(slot)
            if equipped_id:
                from items import ALL_ITEMS
                item = ALL_ITEMS.get(equipped_id, {})
                rows.append({"label": label, "value": item.get("name", equipped_id)})
            else:
                rows.append({"label": label, "value": "(없음)"})
        return rows


# ── 간식 주기 서브 View ──────────────────────────────────────────────────────
class SnackFeedView(discord.ui.View):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=60)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view

        from items import ALL_ITEMS
        options = []
        for item_id, count in player.inventory.items():
            item = ALL_ITEMS.get(item_id, {})
            if item.get("type") == "snack":
                grade = item.get("grade", "일반")
                icon  = GRADE_EMOJI.get(grade, "⚬")
                eff   = item.get("effect", {})
                eff_str = " ".join(
                    f"{k[0].upper()}{'+'if v>0 else ''}{v}"
                    for k, v in eff.items()
                )
                options.append(discord.SelectOption(
                    label=f"{icon} {item.get('name', item_id)} x{count}",
                    value=item_id,
                    description=eff_str[:50],
                ))

        if options:
            select = discord.ui.Select(
                placeholder="줄 간식을 선택하셰요...",
                options=options[:25],
                custom_id="snack_select",
            )
            select.callback = self._on_snack_select
            self.add_item(select)
        else:
            # 간식 없음 안내 버튼 (비활성화)
            btn = discord.ui.Button(
                label="보유한 간식이 없슴미댜",
                style=discord.ButtonStyle.secondary,
                disabled=True,
            )
            self.add_item(btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_snack",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_snack_select(self, interaction: discord.Interaction):
        snack_id = interaction.data["values"][0]
        result = self.care_manager.feed_snack(self.player, snack_id)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("changes"):
            for k, v in result["changes"].items():
                labels = {"condition": "💛 컨디션", "stability": "💙 안정감", "fatigue": "🔥 피로도"}
                sign = "+" if v >= 0 else ""
                rows.append({"label": labels.get(k, k), "value": f"{sign}{v}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception:
                pass
        file = _result_card("🍪 간식 주기", rows, grade=grade)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self
        )

    async def _on_back(self, interaction: discord.Interaction):
        file = _make_room_card(self.player)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self.parent_view
        )


# ── 가위바위보 서브 View ─────────────────────────────────────────────────────
class RockPaperScissorsView(discord.ui.View):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=30)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view

        for label, choice in [("✊ 바위", "rock"), ("✌️ 가위", "scissors"), ("✋ 보", "paper")]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = self._make_cb(choice)
            self.add_item(btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    def _make_cb(self, choice: str):
        async def cb(interaction: discord.Interaction):
            result = self.care_manager.play_result(self.player, choice)
            rows = [
                {"label": "내 선택", "value": result.get("player_choice", "?")},
                {"label": "상대 선택", "value": result.get("bot_choice", "?")},
                {"label": "결과", "value": result["message"]},
            ]
            if result.get("stability_gain"):
                rows.append({"label": "💙 안정감", "value": f"+{result['stability_gain']}"})
            if result.get("fatigue_gain"):
                rows.append({"label": "🔥 피로도", "value": f"+{result['fatigue_gain']}"})

            result_label = result.get("result", "")
            grade = "Normal" if result.get("success") else "Fail"
            if result_label == "win":
                grade = "Legendary"
            elif result_label == "lose":
                grade = "Fail"

            for child in self.children:
                if child.label != "◀ 돌아가기":
                    child.disabled = True

            if result.get("success"):
                try:
                    save_player_to_db(self.player)
                except Exception:
                    pass

            file = _result_card("🎮 놀아주기 결과", rows, grade=grade)
            await interaction.response.edit_message(
                content=None, attachments=[file], view=self
            )
        return cb

    async def _on_back(self, interaction: discord.Interaction):
        file = _make_room_card(self.player)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self.parent_view
        )


# ── 간식 제작 서브 View ──────────────────────────────────────────────────────
class SnackCraftView(discord.ui.View):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=60)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view
        self._selected    = None

        options = []
        for snack_id, recipe in SNACK_RECIPES.items():
            snack = SNACK_ITEMS.get(snack_id, {})
            name  = snack.get("name", snack_id)
            grade = snack.get("grade", "일반")
            icon  = GRADE_EMOJI.get(grade, "⚬")
            can_craft = all(
                player.inventory.get(m, 0) >= n
                for m, n in recipe["materials"].items()
            )
            craft_icon = "✅" if can_craft else "❌"
            options.append(discord.SelectOption(
                label=f"{craft_icon} {icon} {name}",
                value=snack_id,
                description=recipe.get("desc", "")[:50],
            ))

        if options:
            select = discord.ui.Select(
                placeholder="제작할 간식을 선택하셰요...",
                options=options[:25],
                custom_id="snack_craft_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        confirm_btn = discord.ui.Button(
            label="✅ 제작 확정",
            style=discord.ButtonStyle.success,
            custom_id="snack_craft_confirm",
            row=1,
        )
        confirm_btn.callback = self._on_confirm
        self.add_item(confirm_btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_snack_craft",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        self._selected = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self._selected:
            await interaction.response.send_message(
                "먼저 제작할 간식을 선택하셰요!", ephemeral=True
            )
            return
        result = self.care_manager.craft_snack(self.player, self._selected)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("success") and result.get("item_id"):
            snack = SNACK_ITEMS.get(result["item_id"], {})
            recipe = SNACK_RECIPES.get(result["item_id"], {})
            mats_used = ", ".join(
                f"{mid} x{cnt}" for mid, cnt in recipe.get("materials", {}).items()
            )
            rows.append({"label": "재료 소모", "value": mats_used[:60]})
            rows.append({"label": "획득", "value": f"{snack.get('name', '')} x{result.get('count',1)}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception:
                pass
        file = _result_card("🍳 간식 제작", rows, grade=grade)
        await interaction.response.edit_message(content=None, attachments=[file], view=self)

    async def _on_back(self, interaction: discord.Interaction):
        file = _make_room_card(self.player)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self.parent_view
        )


# ── 의장 제작 서브 View ──────────────────────────────────────────────────────
class CostumeCraftView(discord.ui.View):
    SLOT_LABEL = {
        "toy":       "🪄 장난감",
        "hat":       "🎀 모자",
        "outfit":    "👗 의상",
        "shoes":     "👢 신발",
        "accessory": "💎 악세사리",
    }

    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=60)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view
        self._selected    = None

        options = []
        for costume_id, recipe in COSTUME_RECIPES.items():
            costume = COSTUME_ITEMS.get(costume_id, {})
            name    = costume.get("name", costume_id)
            grade   = costume.get("grade", "일반")
            icon    = GRADE_EMOJI.get(grade, "⚬")
            slot    = costume.get("slot", "")
            slot_label = self.SLOT_LABEL.get(slot, slot)
            can_craft = all(
                player.inventory.get(m, 0) >= n
                for m, n in recipe["materials"].items()
            )
            craft_icon = "✅" if can_craft else "❌"
            options.append(discord.SelectOption(
                label=f"{craft_icon} {icon} {name} ({slot_label})",
                value=costume_id,
                description=recipe.get("desc", "")[:50],
            ))

        if options:
            select = discord.ui.Select(
                placeholder="제작할 의장을 선택하셰요...",
                options=options[:25],
                custom_id="costume_craft_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        confirm_btn = discord.ui.Button(
            label="✅ 제작 확정",
            style=discord.ButtonStyle.success,
            custom_id="costume_craft_confirm",
            row=1,
        )
        confirm_btn.callback = self._on_confirm
        self.add_item(confirm_btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_costume_craft",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        self._selected = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self._selected:
            await interaction.response.send_message(
                "먼저 제작할 의장을 선택하셰요!", ephemeral=True
            )
            return
        result = self.care_manager.craft_costume(self.player, self._selected)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("success") and result.get("item_id"):
            costume = COSTUME_ITEMS.get(result["item_id"], {})
            recipe  = COSTUME_RECIPES.get(result["item_id"], {})
            mats_used = ", ".join(
                f"{mid} x{cnt}" for mid, cnt in recipe.get("materials", {}).items()
            )
            rows.append({"label": "재료 소모", "value": mats_used[:60]})
            rows.append({"label": "획득", "value": f"{costume.get('name','')} x{result.get('count',1)}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception:
                pass
        file = _result_card("✂️ 의장 제작", rows, grade=grade)
        await interaction.response.edit_message(content=None, attachments=[file], view=self)

    async def _on_back(self, interaction: discord.Interaction):
        file = _make_room_card(self.player)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=self.parent_view
        )


# ── 아이템 선택 헬퍼 View ───────────────────────────────────────────────────
class _ItemSelectView(discord.ui.View):
    """Select 메뉴 하나만 가지는 임시 뷰 (ephemeral 사용용)."""
    def __init__(self, select: discord.ui.Select, confirm_cb):
        super().__init__(timeout=30)
        self._confirm_cb = confirm_cb
        select.callback  = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        chosen = interaction.data["values"][0]
        await self._confirm_cb(interaction, chosen)


# ── 메인 하이네스의 방 View ──────────────────────────────────────────────────
class CareRoomView(discord.ui.View):
    def __init__(self, player, care_manager):
        super().__init__(timeout=120)
        self.player       = player
        self.care_manager = care_manager
        self._message     = None

        # Row 0: 쓰담쓰담, 간식주기
        pet_btn = discord.ui.Button(
            label="🐾 쓰담쓰담",
            style=discord.ButtonStyle.primary,
            custom_id="care_pet",
            row=0,
        )
        pet_btn.callback = self._on_pet
        self.add_item(pet_btn)

        snack_btn = discord.ui.Button(
            label="🍪 간식주기",
            style=discord.ButtonStyle.primary,
            custom_id="care_snack",
            row=0,
        )
        snack_btn.callback = self._on_snack
        self.add_item(snack_btn)

        # Row 1: 놀아주기, 의장관리
        play_btn = discord.ui.Button(
            label="🎮 놀아주기",
            style=discord.ButtonStyle.primary,
            custom_id="care_play",
            row=1,
        )
        play_btn.callback = self._on_play
        self.add_item(play_btn)

        costume_btn = discord.ui.Button(
            label="👗 의장관리",
            style=discord.ButtonStyle.secondary,
            custom_id="care_costume",
            row=1,
        )
        costume_btn.callback = self._on_costume
        self.add_item(costume_btn)

        # Row 2: 간식제작, 의장제작
        craft_snack_btn = discord.ui.Button(
            label="🍳 간식제작",
            style=discord.ButtonStyle.secondary,
            custom_id="care_craft_snack",
            row=2,
        )
        craft_snack_btn.callback = self._on_craft_snack
        self.add_item(craft_snack_btn)

        craft_costume_btn = discord.ui.Button(
            label="✂️ 의장제작",
            style=discord.ButtonStyle.secondary,
            custom_id="care_craft_costume",
            row=2,
        )
        craft_costume_btn.callback = self._on_craft_costume
        self.add_item(craft_costume_btn)

        # Row 3: 산책
        walk_btn = discord.ui.Button(
            label="🚶 산책",
            style=discord.ButtonStyle.secondary,
            custom_id="care_walk",
            row=3,
        )
        walk_btn.callback = self._on_walk
        self.add_item(walk_btn)

    # ── 쓰담쓰담 ──────────────────────────────────────────────────────────
    async def _on_pet(self, interaction: discord.Interaction):
        result = self.care_manager.pet(self.player)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("condition_gain"):
            rows.append({"label": "💛 컨디션", "value": f"+{result['condition_gain']}"})
        if result.get("stability_gain"):
            rows.append({"label": "💙 안정감", "value": f"+{result['stability_gain']}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception:
                pass
            try:
                import main as _main
                _main.diary_manager.increment("pet_count", 1)
            except Exception:
                pass
        file = _result_card("🐾 쓰담쓰담", rows, grade=grade)
        await interaction.response.edit_message(content=None, attachments=[file], view=self)

    # ── 산책 ──────────────────────────────────────────────────────────────
    WALK_COOLDOWN = 180  # 3분
    WALK_ITEMS = [
        # (아이템ID, 가중치)  — 장난감/의상 제작 재료
        ("mat_wood_scrap",    20),
        ("mat_feather",       18),
        ("mat_flower_petal",  18),
        ("mat_silk_thread",   12),
        ("mat_ribbon_scrap",  12),
        ("mat_soft_cotton",   10),
        ("mat_leather_piece",  8),
        ("mat_shiny_button",   8),
        ("mat_honey",         10),
        ("mat_fruit",         10),
        ("mat_magic_thread",   3),
        ("mat_magic_dust",     2),
    ]

    async def _on_walk(self, interaction: discord.Interaction):
        if not hasattr(self.player, "_flags") or self.player._flags is None:
            self.player._flags = {}

        # 쿨타임 체크
        now = _time.time()
        last_walk = self.player._flags.get("last_walk_time", 0)
        remaining = self.WALK_COOLDOWN - (now - last_walk)
        if remaining > 0:
            mins, secs = divmod(int(remaining), 60)
            file = _result_card("🚶 산책", [
                {"label": "⏱ 쿨타임", "value": f"아직 산책할 수 없슴미댜! {mins}분 {secs}초 남음"},
            ])
            await interaction.response.edit_message(content=None, attachments=[file], view=self)
            return

        # 쿨타임 갱신
        self.player._flags["last_walk_time"] = now

        # 랜덤 아이템 1~2개 획득
        items_found = []
        num_items = random.choices([1, 2], weights=[70, 30])[0]
        pool_ids, pool_weights = zip(*self.WALK_ITEMS)
        for _ in range(num_items):
            chosen_id = random.choices(pool_ids, weights=pool_weights)[0]
            self.player.add_item(chosen_id, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(chosen_id, {}).get("name", chosen_id)
            items_found.append(item_name)

        # 컨디션/안정감 소량 변화
        cond_gain = random.randint(2, 5)
        stab_gain = random.randint(1, 3)
        self.player.condition = min(100, self.player.condition + cond_gain)
        self.player.stability = min(100, self.player.stability + stab_gain)

        rows = [
            {"label": "🐾 상태", "value": "츄라이더가 신나게 산책하고 돌아왔슴미댜~!"},
            {"label": "🎁 획득", "value": ", ".join(items_found)},
            {"label": "💛 컨디션", "value": f"+{cond_gain} → {self.player.condition}"},
            {"label": "💙 안정감", "value": f"+{stab_gain} → {self.player.stability}"},
        ]

        try:
            save_player_to_db(self.player)
        except Exception:
            pass
        file = _result_card("🚶 산책 결과", rows)
        await interaction.response.edit_message(content=None, attachments=[file], view=self)

    # ── 간식주기 ──────────────────────────────────────────────────────────
    async def _on_snack(self, interaction: discord.Interaction):
        sub_view = SnackFeedView(self.player, self.care_manager, self)
        file = _result_card(
            "🍪 간식주기",
            [{"label": "안내", "value": "줄 간식을 선택하셰요!"}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 놀아주기 ──────────────────────────────────────────────────────────
    async def _on_play(self, interaction: discord.Interaction):
        # 쿨타임 체크
        remaining = self.care_manager.get_play_cooldown_remaining(self.player)
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            file = _result_card(
                "🎮 놀아주기",
                [{"label": "안내", "value": f"아직 쿨타임임미댜... ({mins}분 {secs}초 남음)"}],
                grade="Fail",
            )
            await interaction.response.edit_message(
                content=None, attachments=[file], view=self
            )
            return

        sub_view = RockPaperScissorsView(self.player, self.care_manager, self)
        file = _result_card(
            "🎮 놀아주기 — 가위바위보",
            [{"label": "안내", "value": "✊ 바위 / ✌️ 가위 / ✋ 보 중 선택하셰요!"}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 의장관리 ──────────────────────────────────────────────────────────
    async def _on_costume(self, interaction: discord.Interaction):
        sub_view = CostumeManageView(self.player, self)
        rows = sub_view._build_status_rows()
        file = _result_card("👗 의장관리", rows)
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 간식제작 ──────────────────────────────────────────────────────────
    async def _on_craft_snack(self, interaction: discord.Interaction):
        sub_view = SnackCraftView(self.player, self.care_manager, self)
        file = _result_card(
            "🍳 간식제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 간식을 선택하셰요."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 의장제작 ──────────────────────────────────────────────────────────
    async def _on_craft_costume(self, interaction: discord.Interaction):
        sub_view = CostumeCraftView(self.player, self.care_manager, self)
        file = _result_card(
            "✂️ 의장제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 의장을 선택하셰요."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                await self._message.edit(view=self)
            except Exception:
                pass
