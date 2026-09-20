"""Opt-in Discord voice controls for Churider life/crafting sound effects."""
from __future__ import annotations

from discord.ext import commands

from core.sound_director import sound_director
from utils.discord_helpers import check_channel


class SoundCog(commands.Cog, name="효과음"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="소리")
    async def sound_cmd(self, ctx, mode: str = ""):
        if not await check_channel(ctx, self.bot.ctx.allowed_channel_id):
            return
        mode = mode.strip().lower()
        if mode in {"켜기", "켜", "on"}:
            voice = getattr(ctx.author, "voice", None)
            channel = getattr(voice, "channel", None)
            if channel is None:
                await ctx.send("먼저 음성 채널에 들어가 있으면 츄라이더가 따라감미댜.")
                return
            await sound_director.join(channel)
            await ctx.send(f"🔊 **{channel.name}**에 들어왔슴미댜. 이제 생활/제작 소리가 남미댜.")
            return
        if mode in {"끄기", "꺼", "off"}:
            await sound_director.leave()
            await ctx.send("🔇 생활 효과음을 껐슴미댜.")
            return
        state = "켜져 있음" if sound_director.enabled else "꺼져 있음"
        await ctx.send(f"효과음: **{state}** · `/소리 켜기` / `/소리 끄기`")


async def setup(bot):
    await bot.add_cog(SoundCog(bot))
