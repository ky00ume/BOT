"""shop_ui.py — discord.ui.View 기반 인터랙티브 구매/판매 UI (PIL 이미지 출력)"""
import discord
from items import ALL_ITEMS
from bg3_renderer import get_renderer
from utils.logger import setup_logger

logger = setup_logger('shop_ui')

GRADE_ICON_PLAIN = {
    "Normal":    "⚬",
    "Rare":      "◆",
    "Epic":      "❖",
    "Legendary": "✦",
}


def _result_card(title, rows, grade="Normal"):
    """render_card wrapper for shop result feedback."""
    buf = get_renderer().render_card(
        title=title,
        rows=rows,
        system_key="shop",
        grade=grade,
    )
    return discord.File(buf, filename="shop_result.png")


class SellView(discord.ui.View):
    def __init__(self, player, shop_manager):
        super().__init__(timeout=60)
        self.player       = player
        self.shop_manager = shop_manager
        self.selected_id  = None
        self.sell_count   = 1
        self._message     = None

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

        for label, count in [("1개", 1), ("5개", 5), ("10개", 10), ("전부", -1)]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"cnt_{count}")
            btn.callback = self._make_count_cb(count)
            self.add_item(btn)

        confirm = discord.ui.Button(label="판매 확정", style=discord.ButtonStyle.danger, custom_id="sell_confirm")
        confirm.callback = self._on_confirm
        self.add_item(confirm)

        cancel = discord.ui.Button(label="취소", style=discord.ButtonStyle.secondary, custom_id="sell_cancel")
        cancel.callback = self._on_cancel
        self.add_item(cancel)

    def _make_count_cb(self, count: int):
        async def cb(interaction: discord.Interaction):
            if count == -1:
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
            file = _result_card(
                "오류",
                [{"label": "안내", "value": "아이템을 먼저 선택하셰요!"}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        count = self.sell_count
        if count == -1:
            count = self.player.inventory.get(self.selected_id, 1)

        item = ALL_ITEMS.get(self.selected_id, {})
        name = item.get("name", self.selected_id)
        have = self.player.inventory.get(self.selected_id, 0)

        if have < count:
            file = _result_card(
                "오류",
                [{"label": "아이템", "value": name},
                 {"label": "안내", "value": "수량이 부족하거나 없슴미댜!"}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        price = item.get("price", 0)
        sell_total = (price // 2) * count

        # Execute the actual sell operation (ID로 직접 전달하여 동명 아이템 혼동 방지)
        self.shop_manager.sell_item(self.selected_id, count)

        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception:
            logger.error('shop_ui: SellView 판매 후 save_manager.save 실패', exc_info=True)

        for child in self.children:
            child.disabled = True

        file = _result_card(
            "판매 완료",
            [{"label": "아이템", "value": name},
             {"label": "수량", "value": str(count)},
             {"label": "획득", "value": f"+{sell_total:,}G"},
             {"label": "소지금", "value": f"{self.player.gold:,}G"}],
            grade="Normal",
        )
        await interaction.response.edit_message(content=None, attachments=[file], view=self)
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        file = _result_card(
            "취소",
            [{"label": "안내", "value": "판매를 취소했슴미댜."}],
            grade="Normal",
        )
        await interaction.response.edit_message(content=None, attachments=[file], view=self)
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                file = _result_card(
                    "시간 만료",
                    [{"label": "안내", "value": "판매 시간이 만료됐슴미댜."}],
                    grade="Fail",
                )
                await self._message.edit(content=None, attachments=[file], view=self)
            except Exception:
                logger.warning('shop_ui: SellView.on_timeout 메시지 편집 실패', exc_info=True)
    def __init__(self, player, shop_manager, npc_name: str, catalog: dict):
        super().__init__(timeout=60)
        self.player       = player
        self.shop_manager = shop_manager
        self.npc_name     = npc_name
        self.catalog      = catalog
        self.selected_id  = None
        self.buy_count    = 1
        self._message     = None

        options = []
        SLOT_NAMES = {
            "main": "주무기", "sub": "보조", "body": "갑옷", "head": "투구",
            "glove": "장갑", "boot": "신발", "hands": "장갑", "feet": "신발",
        }
        for item_id, item in list(catalog.items())[:25]:
            name  = item.get("name", item_id)
            price = item.get("price", 0)
            grade = item.get("grade", "Normal")
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            # 상세 정보 조합
            desc_parts = [f"{price:,}G"]
            if item.get("attack"):
                desc_parts.append(f"공격+{item['attack']}")
            if item.get("magic_attack"):
                desc_parts.append(f"마공+{item['magic_attack']}")
            if item.get("defense"):
                desc_parts.append(f"방어+{item['defense']}")
            slot = item.get("slot")
            if slot:
                desc_parts.append(f"[{SLOT_NAMES.get(slot, slot)}]")
            # 소비/스킬북 효과
            eff = item.get("effect", {})
            if eff:
                for ek, ev in list(eff.items())[:3]:
                    sign = "+" if ev > 0 else ""
                    desc_parts.append(f"{ek}{sign}{ev}")
            if item.get("type") == "skillbook":
                desc_parts.append("스킬북")
            desc_str = " | ".join(desc_parts)[:100]
            options.append(discord.SelectOption(
                label=f"{icon} {name}",
                value=item_id,
                description=desc_str,
            ))

        if options:
            select = discord.ui.Select(
                placeholder="구매할 아이템을 선택하셰요...",
                options=options,
                custom_id="buy_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        for label, count in [("1개", 1), ("5개", 5), ("10개", 10)]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"bcnt_{count}")
            btn.callback = self._make_count_cb(count)
            self.add_item(btn)

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
            file = _result_card(
                "오류",
                [{"label": "안내", "value": "아이템을 먼저 선택하셰요!"}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        item = self.catalog.get(self.selected_id, {})
        name = item.get("name", self.selected_id)
        price = item.get("price", 0)
        grade = item.get("grade", "Normal")

        # Calculate discount
        discount = 0
        if hasattr(self.player, "_affinity_manager") and self.player._affinity_manager:
            aff = self.player._affinity_manager
            discount = getattr(aff, "get_shop_discount_pct", lambda n: 0)(self.npc_name)
        final_price = int(price * self.buy_count * (1 - discount / 100))

        # Gold check
        if self.player.gold < final_price:
            file = _result_card(
                "오류",
                [{"label": "안내", "value": "골드가 부족함미댜!"},
                 {"label": "필요", "value": f"{final_price:,}G"},
                 {"label": "보유", "value": f"{self.player.gold:,}G"}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        # Execute the actual buy operation
        self.shop_manager.execute_buy(self.npc_name, name, self.buy_count)

        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception:
            logger.error('shop_ui: BuyView 구매 후 save_manager.save 실패', exc_info=True)

        for child in self.children:
            child.disabled = True

        rows = [
            {"label": "아이템", "value": name},
            {"label": "수량", "value": str(self.buy_count)},
            {"label": "금액", "value": f"-{final_price:,}G"},
            {"label": "소지금", "value": f"{self.player.gold:,}G"},
        ]
        if discount:
            rows.insert(2, {"label": "할인", "value": f"{discount}%"})

        file = _result_card("구매 완료", rows, grade=grade)
        await interaction.response.edit_message(content=None, attachments=[file], view=self)
        self.stop()

    async def _on_cancel(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        file = _result_card(
            "취소",
            [{"label": "안내", "value": "구매를 취소했슴미댜."}],
            grade="Normal",
        )
        await interaction.response.edit_message(content=None, attachments=[file], view=self)
        self.stop()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                file = _result_card(
                    "시간 만료",
                    [{"label": "안내", "value": "구매 시간이 만료됐슴미댜."}],
                    grade="Fail",
                )
                await self._message.edit(content=None, attachments=[file], view=self)
            except Exception:
                logger.warning('shop_ui: BuyView.on_timeout 메시지 편집 실패', exc_info=True)