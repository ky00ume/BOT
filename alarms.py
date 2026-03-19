from discord.ext import tasks
import discord
from datetime import datetime

MORNING_HOUR   = 9   # 오전 9시
AFTERNOON_HOUR = 14  # 오후 2시
EVENING_HOUR   = 19  # 오후 7시
NIGHT_HOUR     = 23  # 오후 11시


def setup_alarms(bot, channel_id: int, drider_id: int):
    """알람 루프를 설정하고 반환합니다."""

    @tasks.loop(minutes=1)
    async def alarm_loop():
        now  = datetime.now()
        hour = now.hour
        minute = now.minute

        if minute != 0:
            return

        channel = bot.get_channel(channel_id)
        if not channel:
            return

        user_mention = f"<@{drider_id}>"

        if hour == MORNING_HOUR:
            await channel.send(
                f"🌅 {user_mention} 좋은 아침임미댜~! 오늘도 비전 타운에서 열심히 모험하셰요! ✨"
            )
        elif hour == AFTERNOON_HOUR:
            await channel.send(
                f"☀️ {user_mention} 점심 시간임미댜! 밥 잘 챙겨드셨슴미댜~? 🍽️"
            )
        elif hour == EVENING_HOUR:
            await channel.send(
                f"🌆 {user_mention} 저녁이 됐슴미댜! 오늘 하루도 수고하셨슴미댜~ 🌸"
            )
        elif hour == NIGHT_HOUR:
            await channel.send(
                f"🌙 {user_mention} 오늘도 늦게까지 수고하셨슴미댜! 건강 챙기셰요~ 💤"
            )

    return alarm_loop
