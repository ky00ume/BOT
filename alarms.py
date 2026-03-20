"""alarms.py — 츄라이더 BOT 알람 및 랜덤 이벤트 시스템"""
import random
from discord.ext import tasks
from datetime import datetime

MORNING_HOUR   = 8
LUNCH_HOUR     = 12
EVENING_HOUR   = 18
NIGHT_HOUR     = 23
DIARY_HOUR     = 22

_RANDOM_EVENTS = [
    "🕷️ 츄라이더가 마을을 산책하다가 **10골드**를 주웠슴미댜!",
    "🕷️ 츄라이더가 지금 **목공을 연습**하고 있슴미댜...",
    "🕷️ 츄라이더가 강가에서 **돌멩이를 던지며** 놀고 있슴미댜~",
    "🕷️ 츄라이더가 **거미줄을 새로 짰슴미댜**! 반짝반짝임미댜~",
    "🕷️ 츄라이더가 마을 게시판 앞에서 **공지를 읽고** 있슴미댜.",
    "🕷️ 츄라이더가 **버섯을 채집**하다가 예쁜 꽃도 발견했슴미댜! 🌸",
    "🕷️ 츄라이더가 **낮잠을 자다** 깼슴미댜... 기분이 좋슴미댜~",
    "🕷️ 츄라이더가 하늘을 보며 **구름 모양을 세고** 있슴미댜... 🌤",
    "🕷️ 츄라이더가 **새로운 레시피를 연습** 중임미댜! 맛있게 만들 수 있을까~",
    "🕷️ 츄라이더가 모험가 길드 앞에서 **게시물을 구경**하고 있슴미댜.",
    "🕷️ 츄라이더가 **광산 근처를 탐험**하다가 돌아왔슴미댜! 돌멩이가 예쁘슴미댜~",
    "🕷️ 츄라이더가 **일지를 쓰고** 있슴미댜... 오늘 뭘 했는지 기록 중임미댜.",
    "🕷️ 츄라이더가 **거미줄 해먹에 누워** 바람을 즐기고 있슴미댜~ 🍃",
    "🕷️ 츄라이더가 **귀엽게 스트레칭** 중임미댜! 다리가 여덟 개라 시간이 걸리슴미댜;;",
    "🕷️ 츄라이더가 **별자리를 공부**하고 있슴미댜... 오늘은 쌍둥이자리네요~ ✨",
    "🕷️ 츄라이더가 냇가에서 **발(?)을 담그고** 쉬는 중임미댜~ 🌊",
    "🕷️ 츄라이더가 **친구에게 편지를 쓰고** 있슴미댜! (친구가 있는지는 모르겠슴미댜;;)",
    "🕷️ 츄라이더가 마을 도서관에서 **책을 빌려왔슴미댜**! 어떤 책인지 궁금하슴미댜~",
]

_DAILY_SCENES = [
    (
        "```\n"
        "    🌙 ✨         ✦\n"
        "  🌲  🕷️  🌲\n"
        "  ～ ～🕸️～ ～\n"
        " 🍃     🍃    🍃\n"
        "```\n"
        "🕷️ 츄라이더가 **별빛 아래 숲속**에서 거미줄을 다듬고 있슴미댜..."
    ),
    (
        "```\n"
        "  🏠 ～～～\n"
        "   🕷️💤  ☕\n"
        "  ═══🕸️═══\n"
        "   (쉬는 중임미댜...)\n"
        "```\n"
        "🕷️ 츄라이더가 **방에서 따뜻하게 쉬고** 있슴미댜~ ☕"
    ),
    (
        "```\n"
        "  🌿🕷️🌿\n"
        "   ✂️ 슥슥\n"
        "  🕸️～～🕸️\n"
        "```\n"
        "🕷️ 츄라이더가 **풀밭에서 약초를 채집**하고 있슴미댜! 🌿"
    ),
    (
        "```\n"
        "  🕷️🎣        🌊\n"
        "  ｜         〰️\n"
        " 🪨～～～～～～🐟?\n"
        "```\n"
        "🕷️ 츄라이더가 **강가에서 낚시** 중임미댜~ 찌가 움직일 것 같슴미댜...?"
    ),
    (
        "```\n"
        "   ✨ 🎉 ✨\n"
        "    \\🕷️/\n"
        "  ～🕸️🎶🕸️～\n"
        "    💕💕\n"
        "```\n"
        "🕷️ 츄라이더가 **신나게 춤을 추고** 있슴미댜!! 오늘 기분이 좋은가봐요~ 🎶"
    ),
]

_last_random_minute: int = -1
_daily_scene_sent_date: str = ""


def setup_alarms(bot, channel_id: int, drider_id: int, hyness_id: int = None, majesty_id: int = None):
    """알람 루프를 설정하고 반환합니다."""

    @tasks.loop(minutes=1)
    async def alarm_loop():
        global _last_random_minute, _daily_scene_sent_date

        now    = datetime.now()
        hour   = now.hour
        minute = now.minute
        today  = now.strftime("%Y-%m-%d")

        channel = bot.get_channel(channel_id)
        if not channel:
            return

        drider_mention  = f"<@{drider_id}>"
        hyness_mention  = f"<@{hyness_id}>"  if hyness_id  else ""
        majesty_mention = f"<@{majesty_id}>" if majesty_id else ""

        all_mentions = " ".join(m for m in [drider_mention, hyness_mention, majesty_mention] if m)

        if minute == 0:
            if hour == MORNING_HOUR:
                await channel.send(
                    f"🌅 {all_mentions}\n"
                    "```\n"
                    "    🌅 좋은 아침임미댜~! ✨\n"
                    "     🕷️ (기지개 켜는 중~)\n"
                    "   ～～🕸️～～🕸️～～\n"
                    "```\n"
                    "오늘도 비전 타운에서 열심히 모험하셰요! 화이팅임미댜! 🕸️"
                )
            elif hour == LUNCH_HOUR:
                await channel.send(
                    f"☀️ {all_mentions}\n"
                    "```\n"
                    "  🕷️🍱 냠냠~\n"
                    "  🔥🔥🔥\n"
                    "  ═══🕸️═══\n"
                    "```\n"
                    "점심 시간임미댜! 🍽️ 밥 꼭 챙겨드셰요~ 배가 불러야 모험도 할 수 있슴미댜!"
                )
            elif hour == EVENING_HOUR:
                await channel.send(
                    f"🌆 {all_mentions}\n"
                    "```\n"
                    "  🌆 저녁이 됐슴미댜~\n"
                    "   🕷️ 🌸\n"
                    "  ～🕸️～🕸️～\n"
                    "```\n"
                    "오늘 하루도 정말 수고하셨슴미댜! 🌸 맛있는 저녁 드셰요~"
                )
            elif hour == NIGHT_HOUR:
                await channel.send(
                    f"🌙 {hyness_mention}\n"
                    "```\n"
                    "   🌙  ⭐  ✨\n"
                    "     💤🕷️💤\n"
                    "  ～～🕸️～～\n"
                    "   (새근새근...)\n"
                    "```\n"
                    "하이네스, 영약 복용하셰요! 저희도 가치 잠미댜...zzz 💤"
                )
            elif hour == DIARY_HOUR:
                try:
                    from diary import diary_manager
                    await diary_manager.write_and_send(channel)
                except Exception as e:
                    import traceback
                    print(f"[일기] 작성 중 오류 발생: {e}")
                    traceback.print_exc()

        if minute in (0, 30) and minute != _last_random_minute:
            _last_random_minute = minute
            if random.random() < 0.60:
                msg = random.choice(_RANDOM_EVENTS)
                await channel.send(msg)

        if hour == 15 and minute == 0 and today != _daily_scene_sent_date:
            _daily_scene_sent_date = today
            scene = random.choice(_DAILY_SCENES)
            await channel.send(scene)

    return alarm_loop
