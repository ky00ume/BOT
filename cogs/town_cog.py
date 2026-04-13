# cogs/town_cog.py
import discord
from discord.ext import commands
from ui.ui_theme import C, ansi
from town_notice import send_town_notice
from village import village_manager
from utils.discord_helpers import send_msg_card, send_encounter, check_channel
from utils.player_lock import get_player_lock


class TownCog(commands.Cog, name="마을"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="공지")
    async def notice_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await send_town_notice(ctx.channel)

    @commands.command(name="비전타운")
    async def vision_town_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.town_ui import VisionTownView
        view = VisionTownView(self.ctx.player, self.ctx.affinity_manager, self.ctx.npc_manager, village_manager)
        await view.send(ctx)

    @commands.command(name="대화")
    async def talk_cmd(self, ctx, *, name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if name:
            await ctx.send(ansi(
                f"  {C.RED}✖ /대화 [NPC이름] 형식은 더 이상 지원하지 않슴미댜!\n"
                f"  {C.GREEN}/비전타운{C.R} 또는 {C.GREEN}/마을상태{C.R} 로 NPC에게 접근해주셰요."
            ))
            return
        msg = self.ctx.npc_manager.list_npcs()
        await ctx.send(msg)

    @commands.command(name="특수키워드")
    async def special_keyword_cmd(self, ctx, npc_name: str = None, *, keyword: str = None):
        """특수 NPC 인카운터 중 키워드 대화."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not npc_name or not keyword:
            await ctx.send(ansi(f"  {C.RED}✖ /특수키워드 [NPC이름] [키워드] 형식으로 입력하셰요!{C.R}"))
            return
        from special_npc import SPECIAL_NPCS
        if npc_name not in SPECIAL_NPCS:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]은(는) 특수 NPC가 아님미댜.{C.R}"))
            return
        active = self.ctx.encounter_manager.get_active_encounter()
        if active != npc_name:
            await ctx.send(ansi(
                f"  {C.RED}✖ 현재 {npc_name}(이)가 근처에 없슴미댜. 인카운터를 기다리셰요!{C.R}"
            ))
            return
        from npc_conversation import ConversationManager
        aff_mgr = getattr(self.ctx.player, "_affinity_manager", None)
        conv = ConversationManager(self.ctx.player, aff_mgr, self.ctx.npc_manager)
        await conv.send_conversation(ctx, npc_name)

    @commands.command(name="계약확인")
    async def contract_check_cmd(self, ctx):
        """라파엘 계약 현황 확인."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.encounter_manager.check_contract_status()
        await ctx.send(result)

    @commands.command(name="계약수락")
    async def contract_accept_cmd(self, ctx):
        """라파엘 계약 수락."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        active = self.ctx.encounter_manager.get_active_encounter()
        if active != "라파엘":
            await ctx.send(ansi(f"  {C.RED}✖ 라파엘이 근처에 없슴미댜. 인카운터를 기다리셰요!{C.R}"))
            return
        result = self.ctx.encounter_manager.accept_contract()
        await ctx.send(result)

    @commands.command(name="계약거절")
    async def contract_reject_cmd(self, ctx):
        """라파엘 계약 거절."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.encounter_manager.reject_contract()
        await ctx.send(result)

    @commands.command(name="계약완료")
    async def contract_complete_cmd(self, ctx):
        """라파엘 계약 완료 보상 수령."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.encounter_manager.complete_contract()
        await ctx.send(result)

    @commands.command(name="루바토버프")
    async def lubato_buff_cmd(self, ctx):
        """루바토 인카운터 시 노래 버프 받기."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.encounter_manager.apply_lubato_buff()
        await ctx.send(result)

    @commands.command(name="알바")
    async def job_cmd(self, ctx, *, name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            if not name:
                await ctx.send(ansi(f"  {C.RED}✖ /알바 [NPC이름] 형식으로 입력하셰요!{C.R}"))
                return
            departure = self.ctx.encounter_manager.clear_encounter()
            if departure:
                await ctx.send(departure)
            await self.ctx.npc_manager.start_job_async(ctx, name)
            enc_msg = self.ctx.encounter_manager.trigger_encounter()
            if enc_msg:
                await send_encounter(ctx, enc_msg, self.ctx)

    @commands.command(name="마을상태")
    async def village_status_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        embed = village_manager.make_status_embed()
        await ctx.send(embed=embed)

    @commands.command(name="이동")
    async def move_cmd(self, ctx, *, destination: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if destination:
            result = self.ctx.movement_system.move_to(ctx.author.id, destination)
        else:
            result = self.ctx.movement_system.show_map(ctx.author.id)
        await send_msg_card(ctx, "이동", str(result), system_key="system")


async def setup(bot):
    await bot.add_cog(TownCog(bot))
