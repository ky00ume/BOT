# cogs/social_cog.py
import discord
from discord.ext import commands
import random
import time as _time
from items import ALL_ITEMS
from ui_theme import C, ansi
from bg3_renderer import get_renderer
from save_manager import save_manager
from shop import find_item_by_name
from achievements import achievement_manager
from diary import diary_manager
from responses import (
    get_pet_response, get_scold_response,
    HYNESS_PET_RESPONSES, MAJESTY_PET_RESPONSES, DRIDER_PET_RESPONSES,
    HYNESS_SCOLD_RESPONSES, MAJESTY_SCOLD_RESPONSES, DRIDER_SCOLD_RESPONSES,
)
from care_ui import CareRoomView, _make_room_card
from utils.discord_helpers import send_image, check_channel
from utils.player_lock import get_player_lock


class SocialCog(commands.Cog, name="소셜"):
    _scold_last_used: float = 0.0
    SCOLD_COOLDOWN_SEC = 30

    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="납품")
    async def deliver_cmd(self, ctx, *, item_name: str = None):
        """브룩샤 식당에 요리를 납품합니다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await self.ctx.restaurant_engine.deliver_food(ctx, item_name)

    @commands.command(name="선물")
    async def gift_cmd(self, ctx, npc_name: str = None, *, item_name: str = None):
        """NPC에게 아이템을 선물합니다. 아이템 이름 생략 시 인벤토리 선택 UI 표시."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return

        if not npc_name:
            await ctx.send(ansi(
                f"  {C.RED}✖ /선물 [NPC이름] 또는 /선물 [NPC이름] [아이템이름] 형식으로 입력하셰요!{C.R}\n"
                f"  예시: /선물 다몬   또는   /선물 다몬 철 주괴"
            ))
            return

        from database import NPC_DATA
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return

        special_npcs = {"라파엘", "카르니스", "루바토"}
        if npc_name in special_npcs:
            from npc_dialogue_db import NPC_GIFT_REACTIONS
            reactions = NPC_GIFT_REACTIONS.get(npc_name, {})
            msg = reactions.get("special", "선물은 필요 없어.")
            await ctx.send(ansi(
                f"  {C.GOLD}🎁 {npc['name']}{C.R}\n"
                f"  {C.DARK}─────────────────────────────{C.R}\n"
                f"  {C.WHITE}\"{msg}\"{C.R}"
            ))
            return

        if item_name:
            await self._process_gift(ctx, npc_name, item_name)
            return

        inventory = self.ctx.player.inventory
        if not inventory:
            await ctx.send(ansi(f"  {C.RED}✖ 인벤토리가 비어 있슴미댜!{C.R}"))
            return

        options = []
        for item_id, count in list(inventory.items())[:25]:
            item_info = ALL_ITEMS.get(item_id, {})
            item_display = item_info.get("name", item_id)
            options.append(discord.SelectOption(
                label=f"{item_display} (x{count})",
                value=item_id,
                description=item_info.get("desc", "")[:100] if item_info.get("desc") else "",
            ))

        if not options:
            await ctx.send(ansi(f"  {C.RED}✖ 선물할 수 있는 아이템이 없슴미댜!{C.R}"))
            return

        select = discord.ui.Select(
            placeholder=f"{npc_name}에게 선물할 아이템을 선택하셰요",
            options=options,
        )

        async def select_callback(interaction: discord.Interaction):
            selected_item_id = select.values[0]
            item_info = ALL_ITEMS.get(selected_item_id, {})
            item_display = item_info.get("name", selected_item_id)
            await interaction.response.defer()
            await self._process_gift_by_id(ctx, npc_name, selected_item_id, item_display)

        select.callback = select_callback
        view = discord.ui.View(timeout=60.0)
        view.add_item(select)

        await ctx.send(
            ansi(
                f"  {C.GOLD}🎁 {npc['name']}에게 선물{C.R}\n"
                f"  {C.DARK}아래에서 선물할 아이템을 선택하셰요.{C.R}"
            ),
            view=view,
        )

    async def _process_gift(self, ctx, npc_name: str, item_name: str):
        """아이템 이름으로 선물을 처리합니다."""
        item_id = find_item_by_name(item_name)
        if not item_id:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return
        item_info = ALL_ITEMS.get(item_id, {})
        item_display = item_info.get("name", item_id)
        await self._process_gift_by_id(ctx, npc_name, item_id, item_display)

    async def _process_gift_by_id(self, ctx, npc_name: str, item_id: str, item_display: str):
        """아이템 ID로 선물을 처리합니다."""
        from database import NPC_DATA
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return

        if self.ctx.player.inventory.get(item_id, 0) == 0:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_display}]이(가) 인벤토리에 없슴미댜!{C.R}"))
            return

        self.ctx.player.remove_item(item_id, 1)
        result = self.ctx.affinity_manager.give_gift(npc_name, item_id)
        amount, reaction, leveled, lv_name, limit_exceeded = result

        if limit_exceeded:
            self.ctx.player.add_item(item_id, 1)
            await ctx.send(ansi(
                f"  {C.GOLD}🎁 {npc['name']}{C.R}\n"
                f"  {C.DARK}─────────────────────────────{C.R}\n"
                f"  {C.RED}\"{reaction}\"{C.R}"
            ))
            return

        pts = self.ctx.affinity_manager.affinities.get(npc_name, 0)
        affinity_str = f"{'+' if amount >= 0 else ''}{amount} (현재 {pts}pt)"
        rows = [
            {"label": "반응",   "value": (reaction or "...")[:50]},
            {"label": "호감도", "value": affinity_str},
        ]
        if leveled:
            rows.append({"label": "호감 단계", "value": f"↑ [{lv_name}]"})
        buf = get_renderer().render_card(
            f"🎁 {npc.get('name', npc_name)}에게 선물",
            rows=rows,
            subtitle=f"{item_display} 을(를) 선물했슴미댜!",
            system_key="system",
            footer="선물 완료",
        )
        await send_image(ctx, buf, "gift.png")
        save_manager.save(self.ctx.player)

    @commands.command(name="방", aliases=["하이네스의방", "돌봄"])
    async def room_command(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            view = CareRoomView(self.ctx.player, self.ctx.care_manager)
            file = _make_room_card(self.ctx.player)
            msg  = await ctx.send(file=file, view=view)
            view._message = msg

    @commands.command(name="쓰담", aliases=["복복", "북북", "쓰다듬", "북북박박", "복복복", "복복박박"])
    async def pat_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return

        uid = ctx.author.id
        if uid == self.ctx.hyness_id:
            msg = random.choice(HYNESS_PET_RESPONSES)
        elif uid == self.ctx.majesty_id:
            msg = random.choice(MAJESTY_PET_RESPONSES)
        elif uid == self.ctx.drider_id:
            msg = random.choice(DRIDER_PET_RESPONSES)
        else:
            msg = get_pet_response()

        newly_unlocked = achievement_manager.increment("pet_count", 1)
        diary_manager.increment("pet_count", 1)

        embed = discord.Embed(
            title="🐱 쓰담쓰담...",
            description=msg,
            color=0xFFB6C1,
        )
        embed.set_footer(text="츄라이더는 언제나 쓰다듬어주면 좋아합니다! 💕")
        await ctx.send(embed=embed)

        for ach_id in newly_unlocked:
            from achievements import ACHIEVEMENT_DEFS
            ach = ACHIEVEMENT_DEFS.get(ach_id, {})
            await ctx.send(
                f"🏆✨ **업적 달성!** [{ach.get('name', ach_id)}]\n"
                f"  {ach.get('desc', '')}\n"
                f"  🎀 타이틀 획득: **{ach.get('title', '')}**"
            )

    @commands.command(name="혼내기", aliases=["훈육"])
    async def scold_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return

        now = _time.time()
        remaining = SocialCog.SCOLD_COOLDOWN_SEC - (now - SocialCog._scold_last_used)
        if remaining > 0:
            await ctx.send(ansi(
                f"  {C.RED}😤 아직 혼낼 수 없슴미댜! {int(remaining)}초 남음{C.R}"
            ))
            return

        SocialCog._scold_last_used = now

        uid = ctx.author.id
        if uid == self.ctx.hyness_id:
            msg = random.choice(HYNESS_SCOLD_RESPONSES)
        elif uid == self.ctx.majesty_id:
            msg = random.choice(MAJESTY_SCOLD_RESPONSES)
        elif uid == self.ctx.drider_id:
            msg = random.choice(DRIDER_SCOLD_RESPONSES)
        else:
            msg = get_scold_response()
        embed = discord.Embed(
            title="😤 혼내기!",
            description=msg,
            color=0xFF4500,
        )
        embed.set_footer(text="츄라이더는 진심으로 반성하고 있습니다... 🙏")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SocialCog(bot))
