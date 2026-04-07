"""cogs/system_cog.py — 시스템 명령어 Cog.

독립성이 높은 시스템/유틸리티 명령어들을 main.py 에서 분리합니다.

포함 명령어:
  /도움말   — 봇 도움말
  /저장     — 데이터 저장
  /주사위   — 주사위 굴리기
  /날씨     — 현재 날씨 확인
  /마을상태 — 마을 레벨·기여도
  /공지     — 마을 공지
  /게시판   — 마을 게시판
  /명예의전당 — 명예의 전당
  /낚시순위 — 주간 낚시 순위
"""
from __future__ import annotations

import random

import discord
from discord.ext import commands

from bg3_renderer import get_renderer
from bulletin import bulletin_board, weekly_fishing
from town_notice import send_town_notice
from ui_theme import C, ansi, EMBED_COLOR
from utils.logger import setup_logger
from village import village_manager
from weather import weather_system

logger = setup_logger('system_cog')


class SystemCog(commands.Cog, name="시스템"):
    """시스템/유틸리티 명령어 Cog."""

    def __init__(
        self,
        bot: commands.Bot,
        shared_player,
        save_manager,
        allowed_channel_id: int,
    ) -> None:
        self.bot = bot
        self.shared_player = shared_player
        self.save_manager = save_manager
        self.allowed_channel_id = allowed_channel_id

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────

    async def _check_channel(self, ctx) -> bool:
        """명령이 허용된 채널에서 실행되는지 확인합니다."""
        return ctx.channel.id == self.allowed_channel_id

    async def _send_msg_card(self, ctx, title: str, message: str,
                             system_key: str = "system",
                             grade: str = "Normal") -> None:
        """간단한 메시지를 BG3 스타일 이미지 카드로 전송합니다."""
        buf = get_renderer().render_result_card(
            title=title,
            rows=[{"label": "내용", "value": str(message)}],
            system_key=system_key,
            grade=grade,
        )
        buf.seek(0)
        await ctx.send(file=discord.File(fp=buf, filename="message.png"))

    # ── 명령어 ───────────────────────────────────────────────────────────

    @commands.command(name="도움말")
    async def help_cmd(self, ctx):
        """봇 도움말을 표시합니다."""
        if not await self._check_channel(ctx):
            return
        embed = discord.Embed(
            title="📖 비전 타운 봇 도움말 (v2.0 개편)",
            description="✨ 대부분의 기능이 임베드+드롭다운 UI로 전환되었습니다!",
            color=EMBED_COLOR["help"],
        )
        embed.add_field(
            name="👤 캐릭터 & 상태",
            value=(
                "`/상태` — 캐릭터 상태 보기\n"
                "`/장비` — 장비창 보기\n"
                "`/장착 [아이템이름]` — 장비 장착\n"
                "`/벗기 [슬롯]` — 장비 탈착\n"
                "`/스왑` — 주·보조 무기 교환\n"
                "`/치료` — HP/MP 회복 (50G)\n"
                "`/먹기 [아이템이름]` — 아이템 섭취\n"
                "`/휴식` — 기력 회복\n"
                "`/타이틀 [이름]` — 보유 타이틀 목록/장착 (타이틀 효과 표시)\n"
                "`/업적` — 업적 목록 보기\n"
                "`/도감 [카테고리]` — 도감 보기"
            ),
            inline=False,
        )
        embed.add_field(
            name="🏘 마을 & NPC",
            value=(
                "`/공지` — 마을 공지 보기\n"
                "`/비전타운` — 마을 입장 (NPC 목록/대화/구매 UI)\n"
                "  ↳ NPC 선택 → 대화 키워드 클릭 → [구매] 버튼으로 드롭다운 구매\n"
                "`/알바 [NPC이름]` — 알바 진행 (NPC당 9개, 3가지 유형)\n"
                "  ↳ 배달형: 아이템 수령 후 대상 NPC 방문 → 자동 완료\n"
                "`/마을상태` — 마을 레벨·기여도 확인\n"
                "`/이동 [장소]` — 맵 이동"
            ),
            inline=False,
        )
        embed.add_field(
            name="📚 스킬 창 (NEW)",
            value=(
                "`/스킬` — **스킬 창 UI** 열기\n"
                "  ↳ 카테고리 드롭다운: 전투 / 마법 / 생활\n"
                "  ↳ 생활 스킬 선택 → 레시피 드롭다운 → 재료 현황 확인 → [제작 실행]\n"
                "  ↳ 힐링(마법): 전투 밖에서도 [사용] 버튼으로 HP 회복 가능\n"
                "  ↳ **인벤토리에서 스킬북 옆 [읽기] 버튼**으로 스킬 습득"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎒 인벤토리",
            value=(
                "`/인벤토리` 또는 `/가방` — 인벤토리 보기\n"
                "  ↳ 미습득 스킬북 → **[{스킬북이름} 읽기] 버튼** 자동 표시\n"
                "  ↳ 이미 습득한 스킬북 → **(습득한 스킬)** 표시\n"
                "  ↳ **[판매] 버튼** — 드롭다운으로 아이템/수량 선택 후 판매\n"
                "`/버리기 [아이템이름] [수량]` — 아이템 버리기"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚔ 전투",
            value=(
                "`/사냥터` — 사냥터 목록\n"
                "`/사냥 [사냥터이름]` — 전투 시작\n"
                "`/공격 [스킬ID]` — 공격 (기본: smash)\n"
                "`/도주` — 전투 이탈"
            ),
            inline=False,
        )
        embed.add_field(
            name="🌿 생활",
            value=(
                "`/비전타운` — 생활 컨텐츠 입장 (낚시/채집/벌목/수련 등은 버튼 UI로 이용)\n"
                "  ↳ 채집 (기력 8), 벌목 (기력 9)\n"
                "`/날씨` — 현재 날씨 확인"
            ),
            inline=False,
        )
        embed.add_field(
            name="📋 소셜·기타",
            value=(
                "`/퀘스트` — 퀘스트 목록\n"
                "`/뽑기` / `/뽑기10` — 가챠\n"
                "`/작곡` / `/연주 [곡ID]` — 음악\n"
                "`/게시판` — 마을 게시판\n"
                "`/스토리` — 스토리 퀘스트\n"
                "`/주사위 [면수]` — 주사위 굴리기\n"
                "`/저장` — 데이터 저장\n"
                "`/공지` — 마을 공지\n"
                "`/도움말` — 이 도움말"
            ),
            inline=False,
        )
        embed.set_footer(
            text="🎉 v2.0 개편: 텍스트 명령어 최소화, 드롭다운+버튼 UI 중심으로 전환되었습니다!"
        )
        await ctx.send(embed=embed)

    @commands.command(name="저장")
    async def save_cmd(self, ctx):
        """플레이어 데이터를 저장합니다."""
        if not await self._check_channel(ctx):
            return
        try:
            self.save_manager.save(self.shared_player)
            await self._send_msg_card(ctx, "데이터 저장", "저장 완료임미댜!", system_key="system")
        except Exception as e:
            logger.error("[저장] 실패: %s", e, exc_info=True)
            await ctx.send(ansi(f"  {C.RED}✖ 저장 실패: {e}{C.R}"))

    @commands.command(name="주사위")
    async def dice_cmd(self, ctx, sides: int = 6):
        """주사위를 굴립니다."""
        if not await self._check_channel(ctx):
            return
        sides = max(2, min(sides, 10000))
        result = random.randint(1, sides)
        await self._send_msg_card(
            ctx, f"🎲 {sides}면 주사위", f"결과: {result}", system_key="system"
        )

    @commands.command(name="날씨")
    async def weather_cmd(self, ctx):
        """현재 날씨를 확인합니다."""
        if not await self._check_channel(ctx):
            return
        embed = weather_system.make_weather_embed()
        await ctx.send(embed=embed)

    @commands.command(name="마을상태")
    async def village_status_cmd(self, ctx):
        """마을 레벨과 기여도를 확인합니다."""
        if not await self._check_channel(ctx):
            return
        embed = village_manager.make_status_embed()
        await ctx.send(embed=embed)

    @commands.command(name="공지")
    async def notice_cmd(self, ctx):
        """마을 공지를 표시합니다."""
        if not await self._check_channel(ctx):
            return
        await send_town_notice(ctx.channel)

    @commands.command(name="게시판")
    async def board_cmd(self, ctx):
        """마을 게시판을 표시합니다."""
        if not await self._check_channel(ctx):
            return
        embed = bulletin_board.make_board_embed()
        await ctx.send(embed=embed)

    @commands.command(name="명예의전당")
    async def hall_cmd(self, ctx):
        """명예의 전당을 표시합니다."""
        if not await self._check_channel(ctx):
            return
        embed = bulletin_board.make_hall_of_fame_embed()
        await ctx.send(embed=embed)

    @commands.command(name="낚시순위")
    async def fishing_rank_cmd(self, ctx):
        """주간 낚시 순위를 표시합니다."""
        if not await self._check_channel(ctx):
            return
        embed = weekly_fishing.make_rankings_embed()
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot, **kwargs) -> None:
    """Cog 등록 진입점."""
    await bot.add_cog(SystemCog(bot, **kwargs))
