# cogs/misc_cog.py
import random
import discord
from discord.ext import commands
from ui_theme import C, ansi, EMBED_COLOR
from bg3_renderer import get_renderer
from save_manager import save_manager
from bulletin import bulletin_board, weekly_fishing
from diary import diary_manager
from collection import collection_manager
from achievements import achievement_manager
from utils.discord_helpers import send_msg_card, check_channel


class MiscCog(commands.Cog, name="기타"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="주사위")
    async def dice_cmd(self, ctx, sides: int = 6):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        sides = max(2, min(sides, 10000))
        result = random.randint(1, sides)
        await send_msg_card(ctx, f"🎲 {sides}면 주사위", f"결과: {result}", system_key="system")

    @commands.command(name="저장")
    async def save_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        try:
            save_manager.save(self.ctx.player)
            await send_msg_card(ctx, "데이터 저장", "저장 완료임미댜!", system_key="system")
        except Exception as e:
            await ctx.send(ansi(f"  {C.RED}✖ 저장 실패: {e}{C.R}"))

    @commands.command(name="도움말")
    async def help_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
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
        embed.set_footer(text="🎉 v2.0 개편: 텍스트 명령어 최소화, 드롭다운+버튼 UI 중심으로 전환되었습니다!")
        await ctx.send(embed=embed)

    @commands.command(name="뽑기")
    async def gacha_cmd(self, ctx, count: int = 1):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        count   = max(1, min(count, 10))
        results = self.ctx.gacha_engine.do_gacha(count)
        embed   = self.ctx.gacha_engine.show_result(results)
        await ctx.send(embed=embed)
        save_manager.save(self.ctx.player)

    @commands.command(name="뽑기10")
    async def gacha10_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        results = self.ctx.gacha_engine.do_gacha_10()
        embed   = self.ctx.gacha_engine.show_result(results)
        await ctx.send(embed=embed)
        save_manager.save(self.ctx.player)

    @commands.command(name="작곡")
    async def compose_cmd(self, ctx, title: str = None, *, melody: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not title or not melody:
            await self.ctx.music_engine.compose(ctx)
            return
        await self.ctx.music_engine.save_composition(ctx, title, melody)

    @commands.command(name="악보목록")
    async def sheet_list_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        await self.ctx.music_engine.show_sheet_list(ctx)

    @commands.command(name="악보삭제")
    async def sheet_delete_cmd(self, ctx, title: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not title:
            await ctx.send(ansi(f"  {C.RED}✖ /악보삭제 [곡이름] 형식으로 입력하셰요!{C.R}"))
            return
        await self.ctx.music_engine.delete_sheet(ctx, title)

    @commands.command(name="게시판")
    async def board_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        embed = bulletin_board.make_board_embed()
        await ctx.send(embed=embed)

    @commands.command(name="명예의전당")
    async def hall_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        embed = bulletin_board.make_hall_of_fame_embed()
        await ctx.send(embed=embed)

    @commands.command(name="낚시순위")
    async def fishing_rank_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        embed = weekly_fishing.make_rankings_embed()
        await ctx.send(embed=embed)

    @commands.command(name="일기")
    async def diary_cmd(self, ctx, date_str: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        diary_manager.set_player(self.ctx.player)
        if date_str:
            msg = diary_manager.get_diary_detail(date_str)
        else:
            msg = diary_manager.get_diary_list()
        await ctx.send(msg)

    @commands.command(name="도감")
    async def collection_cmd(self, ctx, category: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from collection import CATEGORY_ICONS
        if category and category in CATEGORY_ICONS:
            msg = collection_manager.show_collection(category)
        else:
            msg = collection_manager.show_all_categories()
        await ctx.send(msg)

    @commands.command(name="업적")
    async def achievements_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        msg = achievement_manager.show_achievements()
        await ctx.send(msg)

    @commands.command(name="스킬", aliases=["스킬창"])
    async def skill_ui_cmd(self, ctx):
        """스킬 창 UI — 임베드+드롭다운으로 전투/마법/생활 스킬 관리."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from skill_ui import SkillMainView, make_skill_main_embed
        embed = make_skill_main_embed(self.ctx.player)
        view = SkillMainView(
            self.ctx.player,
            potion_engine=self.ctx.potion_engine,
            crafting_engine=self.ctx.crafting_engine,
            cooking_engine=self.ctx.cooking_engine,
            metallurgy_engine=self.ctx.metallurgy_engine,
        )
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(MiscCog(bot))
