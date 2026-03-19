"""shop_ui.py — discord.ui.View 기반 인터랙티브 구매/판매 UI"""
import discord
from ui_theme import C, ansi, header_box, divider, GRADE_ICON_PLAIN
from items import ALL_ITEMS


class SellView(discord.ui.View):
    """인터랙티브 판매 UI."""

    def __init__(self, player, shop_manager):
        super().__init__(timeout=60)
        self.player       = player
        self.shop_manager = shop_manager
        self.selected_id  = None
        self.sell_count   = 1
        self._message     = None

        # 드롭다운: 인벤토리 아이템 (최대 25개)
        options = []
        for item_id, count in list(player.inventory.items())[:25]:
            item  = ALL_ITEMS.get(item_id, {})
            name  = item.get("name", item_id)
            price = item.get("price", 0)
            sell  = price // 2
            grade = item.get("grade", "Normal")
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            options.append(discord.SelectOption(
                label=f"{icon} {name} x{count}",
                value=item_id,
                description=f"판매가: {sell:,}G",
            ))

        if options:
            select = discord.ui.Select(
                placeholder="판매할 아이템을 선택하셰요...",
                options=options,
                custom_id="sell_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        # 수량 버튼
        for label, count in [("1개", 1), ("5개", 5), ("10개", 10), ("전부", -1)]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"cnt_{count}")
            btn.callback = self._make_count_cb(count)
            self.add_item(btn)

        # 판매 확정 / 취소
        confirm = discord.ui.Button(label="판매 확정", style=discord.ButtonStyle.danger, custom_id="sell_confirm")
        confirm.callback = self._on_confirm
        self.add_item(confirm)

        cancel = discord.ui.Button(label="취소", style=discord.ButtonStyle.secondary, custom_id="sell_cancel")
        cancel.callback = self._on_cancel
        self.add_item(cancel)

    def _make_count_cb(self, count: int):
        async def cb(interaction: discord.Interaction):
            if count == -1:
                # 전부
                if self.selected_id:
                    self.sell_count = self.player.inventory.get(self.selected_id, 1)
                else:
                    self.sell_count = -1
            else:
                self.sell_count = count
            await interaction.response.defer()
        return cb

    async def _on_select(self, interaction: discord.Interaction):
        self.selected_id = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self.selected_id:
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 아이템을 먼저 선택하셰요!{C.R}"), ephemeral=True
            )
            return
        count = self.sell_count
        if count == -1:
            count = self.player.inventory.get(self.selected_id, 1)
        item  = ALL_ITEMS.get(self.selected_id, {})
        name  = item.get("name", self.selected_id)
        msg   = self.shop_manager.sell_item(name, count)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=msg, view=self)
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=ansi(f"  {C.DARK}판매를 취소했슴미댜.{C.R}"), view=self
        )
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                await self._message.edit(
                    content=ansi(f"  {C.DARK}⏰ 판매 시간이 만료됐슴미댜.{C.R}"), view=self
                )
            except Exception:
                pass


class BuyView(discord.ui.View):
    """인터랙티브 구매 UI."""

    def __init__(self, player, shop_manager, npc_name: str, catalog: dict):
        super().__init__(timeout=60)
        self.player       = player
        self.shop_manager = shop_manager
        self.npc_name     = npc_name
        self.catalog      = catalog
        self.selected_id  = None
        self.buy_count    = 1
        self._message     = None

        # 드롭다운: NPC 카탈로그 아이템 (최대 25개)
        options = []
        for item_id, item in list(catalog.items())[:25]:
            name  = item.get("name", item_id)
            price = item.get("price", 0)
            grade = item.get("grade", "Normal")
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            options.append(discord.SelectOption(
                label=f"{icon} {name}",
                value=item_id,
                description=f"가격: {price:,}G",
            ))

        if options:
            select = discord.ui.Select(
                placeholder="구매할 아이템을 선택하셰요...",
                options=options,
                custom_id="buy_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        # 수량 버튼
        for label, count in [("1개", 1), ("5개", 5), ("10개", 10)]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"bcnt_{count}")
            btn.callback = self._make_count_cb(count)
            self.add_item(btn)

        # 구매 확정 / 취소
        confirm = discord.ui.Button(label="구매 확정", style=discord.ButtonStyle.success, custom_id="buy_confirm")
        confirm.callback = self._on_confirm
        self.add_item(confirm)

        cancel = discord.ui.Button(label="취소", style=discord.ButtonStyle.secondary, custom_id="buy_cancel")
        cancel.callback = self._on_cancel
        self.add_item(cancel)

    def _make_count_cb(self, count: int):
        async def cb(interaction: discord.Interaction):
            self.buy_count = count
            await interaction.response.defer()
        return cb

    async def _on_select(self, interaction: discord.Interaction):
        self.selected_id = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self.selected_id:
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 아이템을 먼저 선택하셰요!{C.R}"), ephemeral=True
            )
            return
        item = self.catalog.get(self.selected_id, {})
        name = item.get("name", self.selected_id)
        msg  = self.shop_manager.execute_buy(self.npc_name, name, self.buy_count)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=msg, view=self)
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=ansi(f"  {C.DARK}구매를 취소했슴미댜.{C.R}"), view=self
        )
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                await self._message.edit(
                    content=ansi(f"  {C.DARK}⏰ 구매 시간이 만료됐슴미댜.{C.R}"), view=self
                )
            except Exception:
                pass
