"""Discord presentation loop for the server-owned world clock."""
from __future__ import annotations

from datetime import datetime
from discord.ext import tasks

from core.world_clock import world_clock

MORNING_HOUR = 8
LUNCH_HOUR = 12
EVENING_HOUR = 18
NIGHT_HOUR = 23
DIARY_HOUR = 22

_last_daily_hour: dict[int, str] = {}


def setup_alarms(bot, channel_id: int, drider_id: int | None, hyness_id: int = None, majesty_id: int = None):
    """Present world changes and fixed daily rituals to Discord.

    Random activity is no longer invented by this module. WorldClock owns time,
    state changes, and durable history; this loop only renders what happened.
    """

    @tasks.loop(minutes=1)
    async def alarm_loop():
        now = datetime.now()
        hour, minute = now.hour, now.minute
        today = now.strftime("%Y-%m-%d")
        channel = bot.get_channel(channel_id)
        if not channel:
            return

        ctx = bot.ctx
        if minute in (0, 30):
            result = world_clock.advance(ctx.player)
            if result.changed_state:
                from save_manager import save_manager
                await save_manager.save_async(ctx.player)
            if result.message:
                await channel.send(result.message)

        if minute != 0 or _last_daily_hour.get(hour) == today:
            return

        drider = f"<@{drider_id}>" if drider_id else ""
        hyness = f"<@{hyness_id}>" if hyness_id else ""
        majesty = f"<@{majesty_id}>" if majesty_id else ""
        everyone = " ".join(x for x in (drider, hyness, majesty) if x)

        messages = {
            MORNING_HOUR: f"🌅 {everyone}\n🕷️ 좋은 아침임미댜. 츄라이더도 슬슬 일어났슴미댜~",
            LUNCH_HOUR: f"☀️ {everyone}\n🕷️ 점심 시간임미댜! 밥 꼭 챙겨드셰요~ 🍽️",
            EVENING_HOUR: f"🌆 {everyone}\n🕷️ 저녁이 됐슴미댜. 오늘 하루도 수고 많으셨슴미댜. 🌸",
            NIGHT_HOUR: f"🌙 {hyness}\n🕷️ 하이네스, 영약 복용하셰요. 츄라이더도 슬슬 잘 준비를 함미댜... 💤",
        }
        if hour == DIARY_HOUR:
            from diary import diary_manager
            await diary_manager.write_and_send(channel)
            _last_daily_hour[hour] = today
        elif hour in messages:
            await channel.send(messages[hour])
            _last_daily_hour[hour] = today

    return alarm_loop
