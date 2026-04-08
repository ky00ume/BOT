# cogs/inventory_cog.py
import discord
from discord.ext import commands
from items import ALL_ITEMS
from ui_theme import C, ansi
from save_manager import save_manager
from shop import find_item_by_name
from utils.discord_helpers import check_channel
from utils.logger import setup_logger

logger = setup_logger('inventory_cog')


class InventoryCog(commands.Cog, name="인벤토리"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="아이템목록")
    async def item_list_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from generate_item_list import generate_csv_buffer
        buf  = generate_csv_buffer()
        file = discord.File(buf, filename="item_list.csv")
        await ctx.send("📋 전체 아이템 목록이에요!", file=file)

    @commands.command(name="보관함")
    async def storage_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from storage_ui import StorageView
        view = StorageView(self.ctx.player, self.ctx.storage_engine)
        await view.send(ctx)

    @commands.command(name="보관함넣기")
    async def storage_deposit_cmd(self, ctx, *, _args: str = ""):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await ctx.send(ansi(f"  {C.YELLOW}ℹ 이 명령어는 `/보관함` 버튼 UI로 통합되었슴미댜! `/보관함`을 사용해 주셰요.{C.R}"))

    @commands.command(name="보관함꺼내기")
    async def storage_withdraw_cmd(self, ctx, *, _args: str = ""):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await ctx.send(ansi(f"  {C.YELLOW}ℹ 이 명령어는 `/보관함` 버튼 UI로 통합되었슴미댜! `/보관함`을 사용해 주셰요.{C.R}"))

    @commands.command(name="보관함업그레이드")
    async def storage_upgrade_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await ctx.send(ansi(f"  {C.YELLOW}ℹ 이 명령어는 `/보관함` 버튼 UI로 통합되었슴미댜! `/보관함`을 사용해 주셰요.{C.R}"))

    @commands.command(name="인벤토리", aliases=["가방", "소지품"])
    async def inventory_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from items import ALL_ITEMS, SKILL_BOOKS
        from shop import ShopManager
        from shop_ui import SellView
        from bg3_renderer import get_renderer, C as RC, render_async
        inventory = self.ctx.player.inventory
        used, max_slots = self.ctx.player.inventory_check()

        from database import BAGS
        bag_names = [BAGS.get(b, {}).get("name", b) for b in self.ctx.player.bags if b in BAGS]
        bag_label = ", ".join(bag_names) if bag_names else "기본"
        rows = [
            {"label": "소지금", "value": f"{self.ctx.player.gold:,}G", "color": RC.GOLD_HI},
            {"label": "장착 가방", "value": bag_label},
        ]

        if not inventory:
            rows.append({"label": "아이템", "value": "인벤토리가 비어있슴미댜."})
        else:
            for item_id, count in list(inventory.items())[:48]:
                item = ALL_ITEMS.get(item_id, {})
                name = item.get("name", item_id)
                grade = item.get("grade", "Normal")
                if item.get("type") == "skillbook":
                    skill_id = item.get("skill_id", "")
                    if skill_id in self.ctx.player.skill_ranks:
                        name = f"{name} (습득완료)"
                color = RC.RARITY.get(grade, RC.TXT_HI)
                rows.append({"label": name, "value": f"×{count}", "color": color})

        n_rows = len(rows)
        if n_rows > 26:
            _rh = 24
        elif n_rows > 14:
            _rh = 30
        else:
            _rh = 36
        card_h = max(380, 120 + n_rows * _rh)
        card_w = 520 if len(inventory) <= 12 else 640 if len(inventory) <= 24 else 760
        buf = await render_async(
            get_renderer().render_card,
            f"🎒 인벤토리 ({used}/{max_slots})",
            rows,
            grade="Normal",
            system_key="status",
            footer="✦ 비전 타운 ✦",
            h=card_h,
            w=card_w,
        )
        file = discord.File(fp=buf, filename="inventory.png")

        view = discord.ui.View(timeout=120.0)

        # 미습득 스킬북 [읽기] 버튼들
        for item_id, count in inventory.items():
            item = ALL_ITEMS.get(item_id, {})
            if item.get("type") != "skillbook":
                continue
            skill_id = item.get("skill_id", "")
            if skill_id in self.ctx.player.skill_ranks:
                continue
            book_name = item.get("name", item_id)

            async def make_read_callback(_item_id=item_id, _skill_id=skill_id, _book_name=book_name):
                async def callback(interaction: discord.Interaction):
                    if self.ctx.player.inventory.get(_item_id, 0) < 1:
                        await interaction.response.send_message(
                            f"❌ [{_book_name}]이(가) 인벤토리에 없슴미댜!", ephemeral=True
                        )
                        return
                    if _skill_id in self.ctx.player.skill_ranks:
                        await interaction.response.send_message(
                            f"✅ 이미 [{_book_name}] 스킬을 보유하고 있슴미댜!", ephemeral=True
                        )
                        return
                    self.ctx.player.remove_item(_item_id, 1)
                    self.ctx.player.skill_ranks[_skill_id] = "연습"
                    self.ctx.player.skill_exp[_skill_id] = 0.0
                    from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS
                    all_defs = {**COMBAT_SKILLS, **MAGIC_SKILLS, **RECOVERY_SKILLS, **OTHER_SKILLS}
                    skill_name = all_defs.get(_skill_id, {}).get("name", _skill_id)
                    try:
                        from save_manager import save_manager
                        save_manager.save(self.ctx.player)
                    except Exception:
                        logger.error('inventory_cog: 스킬북 학습 후 save_manager.save 실패', exc_info=True)
                    await interaction.response.send_message(
                        f"✅ [{skill_name}] 스킬을 습득했슴미댜! [연습 랭크]",
                        ephemeral=False,
                    )
                return callback

            btn = discord.ui.Button(
                label=f"{book_name} 읽기",
                style=discord.ButtonStyle.primary,
                emoji="📖",
            )
            btn.callback = await make_read_callback()
            view.add_item(btn)
            if len(view.children) >= 4:
                break

        # [판매] 버튼
        sell_btn = discord.ui.Button(label="판매", style=discord.ButtonStyle.danger, emoji="🏪")
        async def sell_callback(interaction: discord.Interaction):
            sm = ShopManager(self.ctx.player)
            sell_view = SellView(self.ctx.player, sm)
            sell_embed = discord.Embed(
                title="🏪 아이템 판매",
                description=f"💰 소지금: **{self.ctx.player.gold:,}G**\n판매할 아이템을 선택하세요.",
                color=0xFF6B35,
            )
            msg = await interaction.response.send_message(embed=sell_embed, view=sell_view, ephemeral=False)
            sell_view._message = msg
        sell_btn.callback = sell_callback
        view.add_item(sell_btn)

        # [🗑️ 버리기] 버튼
        discard_btn = discord.ui.Button(label="버리기", style=discord.ButtonStyle.secondary, emoji="🗑️")
        async def discard_btn_callback(interaction: discord.Interaction):
            from items import ALL_ITEMS as _AI
            inv = self.ctx.player.inventory
            if not inv:
                await interaction.response.send_message("인벤토리가 비어있슴미댜!", ephemeral=True)
                return
            options = []
            for iid, cnt in list(inv.items())[:25]:
                item = _AI.get(iid, {})
                if item.get("quest_locked"):
                    continue
                name = item.get("name", iid)
                options.append(discord.SelectOption(
                    label=f"{name} (×{cnt})",
                    value=iid,
                    description=item.get("desc", "")[:50],
                ))
            if not options:
                await interaction.response.send_message("버릴 수 있는 아이템이 없슴미댜!", ephemeral=True)
                return
            discard_select = discord.ui.Select(
                placeholder="버릴 아이템을 선택하세요...",
                options=options,
                custom_id="discard_item_select",
            )
            async def discard_select_callback(sel_interaction: discord.Interaction):
                item_id = discard_select.values[0]
                item = _AI.get(item_id, {})
                if item.get("quest_locked"):
                    await sel_interaction.response.send_message("❌ 퀘스트 아이템은 버릴 수 없슴미댜!", ephemeral=True)
                    return
                have = self.ctx.player.inventory.get(item_id, 0)
                if have == 0:
                    await sel_interaction.response.send_message("인벤토리에 해당 아이템이 없슴미댜!", ephemeral=True)
                    return
                item_name = item.get("name", item_id)
                qty_view = discord.ui.View(timeout=60.0)
                for qty_label, qty_val in [("1개", 1), ("5개", 5), ("10개", 10), ("전부", have)]:
                    actual = min(qty_val, have)
                    if actual <= 0:
                        continue
                    qty_btn = discord.ui.Button(label=qty_label, style=discord.ButtonStyle.secondary)
                    async def make_confirm_callback(_iid=item_id, _iname=item_name, _qty=actual):
                        async def confirm_cb(q_interaction: discord.Interaction):
                            confirm_view = discord.ui.View(timeout=30.0)
                            yes_btn = discord.ui.Button(label="✅ 네, 버립니다", style=discord.ButtonStyle.danger)
                            no_btn  = discord.ui.Button(label="❌ 취소",        style=discord.ButtonStyle.secondary)
                            async def yes_cb(y_interaction: discord.Interaction):
                                cur = self.ctx.player.inventory.get(_iid, 0)
                                drop = min(_qty, cur)
                                if drop > 0:
                                    self.ctx.player.remove_item(_iid, drop)
                                remaining = self.ctx.player.inventory
                                if not remaining:
                                    await y_interaction.response.edit_message(
                                        content=f"🗑️ **{_iname}** ×{drop}을(를) 버렸슴미댜!\n인벤토리가 비었슴미댜!",
                                        view=None,
                                    )
                                    return
                                new_opts = []
                                for r_iid, r_cnt in list(remaining.items())[:25]:
                                    r_item = _AI.get(r_iid, {})
                                    if r_item.get("quest_locked"):
                                        continue
                                    r_name = r_item.get("name", r_iid)
                                    new_opts.append(discord.SelectOption(
                                        label=f"{r_name} (×{r_cnt})",
                                        value=r_iid,
                                        description=r_item.get("desc", "")[:50],
                                    ))
                                if not new_opts:
                                    await y_interaction.response.edit_message(
                                        content=f"🗑️ **{_iname}** ×{drop}을(를) 버렸슴미댜!\n더 이상 버릴 아이템이 없슴미댜!",
                                        view=None,
                                    )
                                    return
                                new_select = discord.ui.Select(
                                    placeholder="버릴 아이템을 선택하세요...",
                                    options=new_opts,
                                    custom_id="discard_item_select_cont",
                                )
                                new_select.callback = discard_select_callback
                                new_view = discord.ui.View(timeout=60.0)
                                new_view.add_item(new_select)
                                await y_interaction.response.edit_message(
                                    content=f"🗑️ **{_iname}** ×{drop}을(를) 버렸슴미댜! 계속 버릴 아이템을 선택하세요:",
                                    view=new_view,
                                )
                            async def no_cb(n_interaction: discord.Interaction):
                                await n_interaction.response.edit_message(content="취소했슴미댜.", view=None)
                            yes_btn.callback = yes_cb
                            no_btn.callback  = no_cb
                            confirm_view.add_item(yes_btn)
                            confirm_view.add_item(no_btn)
                            await q_interaction.response.send_message(
                                f"정말 **{_iname}** ×{_qty}을(를) 버리시겠슴미꺄?",
                                view=confirm_view,
                                ephemeral=True,
                            )
                        return confirm_cb
                    qty_btn.callback = await make_confirm_callback()
                    qty_view.add_item(qty_btn)
                await sel_interaction.response.send_message(
                    f"**{item_name}** 몇 개를 버리시겠슴미꺄? (보유: ×{have})",
                    view=qty_view,
                    ephemeral=True,
                )
            discard_select.callback = discard_select_callback
            sel_view = discord.ui.View(timeout=60.0)
            sel_view.add_item(discard_select)
            await interaction.response.send_message("버릴 아이템을 선택하세요:", view=sel_view, ephemeral=True)
        discard_btn.callback = discard_btn_callback
        view.add_item(discard_btn)

        await ctx.send(file=file, view=view)

    @commands.command(name="버리기")
    async def discard_cmd(self, ctx, item_name: str = None, count_str: str = "1"):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not item_name:
            await ctx.send(ansi(f"  {C.RED}✖ /버리기 [아이템이름] [수량] 형식으로 입력하셰요!{C.R}"))
            return

        item_id = find_item_by_name(item_name)
        if not item_id:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return

        from items import ALL_ITEMS as _ALL_ITEMS_CHECK
        if _ALL_ITEMS_CHECK.get(item_id, {}).get("quest_locked"):
            await ctx.send(ansi(f"  {C.RED}❌ 퀘스트 아이템은 버릴 수 없슴미댜!{C.R}"))
            return

        have = self.ctx.player.inventory.get(item_id, 0)
        if have == 0:
            await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]이(가) 없슴미댜!{C.R}"))
            return

        count_str_lower = count_str.lower()
        if count_str_lower == "전부":
            count = have
        else:
            try:
                count = max(1, int(count_str))
            except ValueError:
                await ctx.send(ansi(f"  {C.RED}✖ 수량은 숫자 또는 '전부'로 입력하셰요!{C.R}"))
                return
        count = min(count, have)

        self.ctx.player.remove_item(item_id, count)
        item_display = ALL_ITEMS.get(item_id, {}).get("name", item_id)
        await ctx.send(ansi(
            f"  {C.GREEN}🗑️  {item_display}{C.R} x{count}을(를) 버렸슴미댜!"
        ))


async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
