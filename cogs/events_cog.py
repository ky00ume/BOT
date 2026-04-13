# cogs/events_cog.py
"""EventsCog — on_ready, on_message, auto_save_loop 이벤트 핸들러 모음.

기존 main.py 의 이벤트/초기화 로직을 Cog 로 분리한 것이다.
"""

import discord
from discord.ext import commands, tasks

from database     import init_db, load_village_data
from save_manager import save_manager
from village      import village_manager
from alarms       import setup_alarms
import status as status_mod
from cogs import COGS
from utils.logger import setup_logger

logger = setup_logger('events_cog')


class EventsCog(commands.Cog, name="이벤트"):
    """봇 생명주기 이벤트 및 자동 저장 루프."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._initialized = False  # 재접속 시 데이터 덮어쓰기 방지 가드

    # ─── 자동 저장 루프 (2분마다) ─────────────────────────────────────────────
    @tasks.loop(minutes=2)
    async def auto_save_loop(self) -> None:
        """2분마다 플레이어 데이터를 자동 저장합니다."""
        try:
            await save_manager.save_async(self.bot.ctx.player)
        except Exception as e:
            logger.error("[자동저장] 실패: %s", e, exc_info=True)

    # ─── on_ready ─────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        ctx = self.bot.ctx
        print(f"[봇 시작] {self.bot.user} 로그인 완료")

        if self._initialized:
            # 재접속: 현재 인메모리 데이터를 보존하고 저장만 수행
            print("[재접속] 인메모리 데이터 보존, 강제 저장 실행")
            try:
                save_manager.save(ctx.player)
            except Exception as e:
                print(f"[재접속 저장] 실패: {e}")
            return

        self._initialized = True

        # DB 초기화
        init_db()

        # status.json 확보
        status_mod.ensure_status_json()

        # DB에서 플레이어 로드
        loaded = save_manager.load(0)
        if loaded:
            ctx.player.load_from_dict(loaded)
            # 호감도 데이터 복원 (affinity_full에 to_dict() 전체 포함)
            aff_full = loaded.get("affinity_full") or {}
            if aff_full and aff_full.get("affinities"):
                ctx.affinity_manager.from_dict(aff_full)
            # 스토리 퀘스트 데이터 복원
            sq_data = loaded.get("story_quest", {})
            if sq_data:
                ctx.story_quest_manager.from_dict(sq_data)
            # 도감 데이터 복원 (DB 우선, 없으면 파일에서)
            col_data = loaded.get("collection_data", {})
            if col_data:
                ctx.player._collection_manager.from_dict(col_data)
            print(f"[DB 로드] {ctx.player.name} 데이터 복원 완료")
        else:
            print("[DB 로드] 저장 데이터 없음 — 기본 캐릭터로 시작")

        # 마을 기여도/레벨 DB에서 복원
        village_data = load_village_data()
        village_manager.from_dict(village_data)
        print(f"[DB 로드] 마을 기여도: {village_manager.contribution}pt, Lv.{village_manager.level}")

        # 알람 설정
        alarm_loop = setup_alarms(
            self.bot,
            ctx.allowed_channel_id,
            ctx.drider_id,
            hyness_id=ctx.hyness_id,
            majesty_id=ctx.majesty_id,
        )
        if not alarm_loop.is_running():
            alarm_loop.start()

        # ── 레벨업 사탕 1회성 지급 (츄라이더용) ─────────────────────────────
        if not getattr(ctx.player, "_flags", {}).get("levelup_potion_granted", False):
            if not hasattr(ctx.player, "_flags"):
                ctx.player._flags = {}
            ctx.player._flags["levelup_potion_granted"] = True
            ctx.player.add_item("levelup_potion", 1)
            print("[이벤트] 레벨업 사탕 1회 지급 완료")

        # 자동 저장 루프 시작
        if not self.auto_save_loop.is_running():
            self.auto_save_loop.start()

        # Cog 로드
        for cog_path in COGS:
            try:
                await self.bot.load_extension(cog_path)
                logger.info("Cog 로드 완료: %s", cog_path)
            except Exception as e:
                logger.error("Cog 로드 실패: %s — %s", cog_path, e, exc_info=True)

        print("[봇 준비] 모든 시스템 초기화 완료!")

    # ─── on_message ──────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        await self.bot.process_commands(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))
