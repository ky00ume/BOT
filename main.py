import discord
from discord.ext import commands
import signal
import sys
import atexit

# .env 파일 지원 (python-dotenv 설치 시 자동 로드)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── 환경변수 로드 ────────────────────────────────────────────────────────────
from utils.env import (
    ConfigError as _EnvConfigError,
    load_discord_token,
    load_required_int,
)

try:
    TOKEN              = load_discord_token("DISCORD_TOKEN")
    HYNESS_ID          = load_required_int("HYNESS_ID")
    MAJESTY_ID         = load_required_int("MAJESTY_ID")
    DRIDER_ID          = load_required_int("DRIDER_ID")
    ALLOWED_CHANNEL_ID = load_required_int("ALLOWED_CHANNEL_ID")
except _EnvConfigError as _env_err:
    print(f"[오류] 환경변수 구성 실패: {_env_err}")
    print("  .env.example 을 참고해 .env 파일을 채워 주세요.")
    sys.exit(1)

# ─── Discord 봇 초기화 ────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ─── 공유 객체 초기화 및 BotContext 조립 ─────────────────────────────────────
from config.bot_config import create_bot_context
bot.ctx = create_bot_context(
    hyness_id=HYNESS_ID,
    majesty_id=MAJESTY_ID,
    drider_id=DRIDER_ID,
    allowed_channel_id=ALLOWED_CHANNEL_ID,
)

# ─── 종료 시그널 핸들러 ───────────────────────────────────────────────────────
from save_manager import save_manager


def _shutdown_handler(sig, frame):
    print(f"\n[종료] 시그널 {sig} 수신 — 데이터 저장 중...")
    try:
        save_manager.save(bot.ctx.player)
        print("[종료] 저장 완료.")
    except Exception as e:
        print(f"[종료] 저장 실패: {e}")
    sys.exit(0)


signal.signal(signal.SIGINT,  _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)


def _shutdown_save():
    """봇 종료 시 플레이어 데이터 강제 저장"""
    try:
        save_manager.save(bot.ctx.player)
        print("[종료 저장] 플레이어 데이터 저장 완료")
    except Exception as e:
        print(f"[종료 저장] 실패: {e}")


atexit.register(_shutdown_save)

# ─── EventsCog 로드 후 봇 실행 ────────────────────────────────────────────────
import asyncio


async def _main():
    async with bot:
        await bot.load_extension("cogs.events_cog")
        await bot.start(TOKEN)


# ─── 봇 실행 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(_main())

