"""storage_ui.py — 보관함 인터랙티브 UI (넣기/꺼내기 버튼+셀렉트)"""
import discord
from discord.ui import View, Button, Select
from items import ALL_ITEMS
from ui_theme import C, ansi


class StorageView(View):
    """보관함 메인 뷰 — 넣기/꺼내기/업그레이드 버튼."""

    def __init__(self, player, storage_engine):
        super().__init__(timeout=180.0)
        self.player = player
        self.engine = storage_engine

    @discord.ui.button(label="넣기", style=discord.ButtonStyle.success, emoji="📥")
    async def deposit_btn(self, interaction: discord.Interaction, button: Button):
        inv = self.player.inventory
        if not inv:
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 인벤토리가 비어 있슴미댜!{C.R}"), ephemeral=True,
            )
            return
        items_list = list(inv.items())
        options = []
        for item_id, count in items_list[:25]:
            item = ALL_ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            options.append(discord.SelectOption(
                label=f"{name} (x{count})",
                value=item_id,
                description=f"보관함에 넣기",
            ))
        msg = "📥 넣을 아이템을 선택하세요:"
        if len(items_list) > 25:
            msg += f" (총 {len(items_list)}종 중 25개까지 표시)"
        view = _DepositSelectView(self.player, self.engine, self)
        view.add_item(_ItemSelect(options, mode="deposit", player=self.player, engine=self.engine, parent=self))
        await interaction.response.send_message(msg, view=view, ephemeral=True)

    @discord.ui.button(label="꺼내기", style=discord.ButtonStyle.primary, emoji="📤")
    async def withdraw_btn(self, interaction: discord.Interaction, button: Button):
        if not self.engine.items:
            await interaction.response.send_message(
                ansi(f"  {C.RED}✖ 보관함이 비어 있슴미댜!{C.R}"), ephemeral=True,
            )
            return
        items_list = list(self.engine.items.items())
        options = []
        for item_id, count in items_list[:25]:
            item = ALL_ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            options.append(discord.SelectOption(
                label=f"{name} (x{count})",
                value=item_id,
                description=f"보관함에서 꺼내기",
            ))
        msg = "📤 꺼낼 아이템을 선택하세요:"
        if len(items_list) > 25:
            msg += f" (총 {len(items_list)}종 중 25개까지 표시)"
        view = _DepositSelectView(self.player, self.engine, self)
        view.add_item(_ItemSelect(options, mode="withdraw", player=self.player, engine=self.engine, parent=self))
        await interaction.response.send_message(msg, view=view, ephemeral=True)

    @discord.ui.button(label="업그레이드", style=discord.ButtonStyle.secondary, emoji="⬆️")
    async def upgrade_btn(self, interaction: discord.Interaction, button: Button):
        result = self.engine.upgrade()
        from main import save_manager, shared_player
        save_manager.save(shared_player)
        await interaction.response.send_message(result)

    async def send(self, ctx):
        text = self.engine.show()
        await ctx.send(text, view=self)


class _DepositSelectView(View):
    """아이템 선택용 임시 뷰."""
    def __init__(self, player, engine, parent):
        super().__init__(timeout=60.0)
        self.player = player
        self.engine = engine
        self.parent = parent


class _ItemSelect(Select):
    """아이템 셀렉트 메뉴."""
    def __init__(self, options, mode, player, engine, parent):
        super().__init__(placeholder="아이템 선택...", options=options, min_values=1, max_values=1)
        self.mode = mode
        self.player = player
        self.engine = engine
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        try:
            if self.mode == "deposit":
                result = self.engine.deposit(item_id, 1)
            else:
                result = self.engine.withdraw(item_id, 1)
            from main import save_manager, shared_player
            save_manager.save(shared_player)
            await interaction.response.send_message(result)
        except Exception:
            await interaction.response.send_message(
                "보관함 작업 중 오류가 발생했슴미댜. 다시 시도해 주세요!", ephemeral=True
            )
