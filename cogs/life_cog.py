# cogs/life_cog.py
import discord
from discord.ext import commands
import time as _time
from ui_theme import C, ansi, EMBED_COLOR
from save_manager import save_manager
from utils.discord_helpers import send_encounter, check_channel
from utils.player_lock import get_player_lock


class LifeCog(commands.Cog, name="생활"):
    _rest_last_used: float = 0.0
    REST_COOLDOWN_SEC = 180  # 3분

    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="낚시목록")
    async def fish_guide_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.fishing_engine.show_fish_guide()
        await ctx.send(result)

    @commands.command(name="낚시터정보")
    async def fish_spot_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.fishing_engine.show_fish_guide()
        await ctx.send(result)

    @commands.command(name="낚시도감")
    async def fish_catalog_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        result = self.ctx.fishing_engine.show_fish_guide()
        await ctx.send(result)

    @commands.command(name="채집도감")
    async def gather_guide_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from gathering import GATHER_ITEMS_BY_SEASON, MINE_ITEMS, get_current_season
        from ui_theme import header_box, divider, section, GRADE_ICON_PLAIN
        season = get_current_season()
        season_kr = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}.get(season, season)
        pool = GATHER_ITEMS_BY_SEASON.get(season, [])
        lines = [header_box("🌿 채집 도감"), section(f"현재 계절: {season_kr}")]
        for item in sorted(pool, key=lambda x: x["grade"]):
            grade = item["grade"]
            mark  = GRADE_ICON_PLAIN.get(grade, "⚬")
            pct   = int(item["rate"] * 100)
            lines.append(f"  {mark} {C.WHITE}{item['name']}{C.R}  {C.DARK}등급: {grade}  {pct}%{C.R}")
        lines.append(section("채광 아이템"))
        for item in MINE_ITEMS:
            grade = item["grade"]
            mark  = GRADE_ICON_PLAIN.get(grade, "⚬")
            lines.append(f"  {mark} {C.WHITE}{item['name']}{C.R}  {C.DARK}등급: {grade}  힘 {item['str_req']} 필요{C.R}")
        from ui_theme import divider
        lines.append(divider())
        lines.append(f"  {C.GREEN}/채집{C.R} 으로 수집하셰요!")
        await ctx.send(ansi("\n".join(lines)))

    @commands.command(name="날씨")
    async def weather_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from weather import weather_system
        embed = weather_system.make_weather_embed()
        await ctx.send(embed=embed)

    @commands.command(name="채집")
    async def gather_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            departure = self.ctx.encounter_manager.clear_encounter()
            if departure:
                await ctx.send(departure)
            await self.ctx.gathering_engine.gather(ctx)
            save_manager.save(self.ctx.player)
            enc_msg = self.ctx.encounter_manager.trigger_encounter()
            if enc_msg:
                await send_encounter(ctx, enc_msg, self.ctx)

    @commands.command(name="벌목")
    async def woodcut_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            await self.ctx.gathering_engine.woodcut(ctx)
            save_manager.save(self.ctx.player)

    @commands.command(name="휴식")
    async def rest_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return

        now = _time.time()
        remaining = LifeCog.REST_COOLDOWN_SEC - (now - LifeCog._rest_last_used)
        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            await ctx.send(ansi(
                f"  {C.RED}💤 아직 쉴 수 없슴미댜! 남은 시간: {minutes}분 {seconds}초{C.R}"
            ))
            return

        if self.ctx.player.energy >= self.ctx.player.max_energy:
            await ctx.send(ansi(f"  {C.GREEN}💚 기력이 이미 가득 찼슴미댜!{C.R}"))
            return

        from rest import RestEngine
        rest_engine = RestEngine(self.ctx.player, channel=ctx.channel)

        LifeCog._rest_last_used = now

        embed = discord.Embed(
            title="💤 휴식 시작!",
            description=(
                f"기력을 회복하기 시작했슴미댜...\n"
                f"현재 기력: **{self.ctx.player.energy}/{self.ctx.player.max_energy}**\n\n"
                f"2초마다 **+{rest_engine.get_recovery_per_tick()}** 회복\n"
                "기력이 가득 차면 자동으로 완료됩니댜!"
            ),
            color=EMBED_COLOR["rest"],
        )
        embed.set_footer(text="💤 휴식 중에도 다른 활동이 가능합니댜!")
        await ctx.send(embed=embed)

        await rest_engine.start_rest()


async def setup(bot):
    await bot.add_cog(LifeCog(bot))
