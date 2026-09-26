# cogs/town_cog.py
import discord
from discord.ext import commands
from ui.ui_theme import C, ansi
from town_notice import send_town_notice
from village import village_manager
from core.events import GameEvent, event_store
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

    @commands.command(name="탑", aliases=["비전의탑"])
    async def tower_cmd(self, ctx):
        """비전의 탑 상층을 바로 연다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.care_ui import TowerUpperFloorView
        view = TowerUpperFloorView(self.ctx.player, self.ctx.care_manager, suspicious_actor_id=getattr(self.ctx, "drider_id", None))
        await ctx.send(embed=view.make_embed(), view=view)

    @commands.command(name="악기연주", aliases=["연주"])
    async def music_cmd(self, ctx):
        """장착한 악기와 악보로 리듬게임 연주를 시작한다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from music_system import ensure_music_skills
        ensure_music_skills(self.ctx.player)
        view = InstrumentPerformanceSetupView(
            self.ctx.player,
            suspicious_actor_id=getattr(self.ctx, "drider_id", None),
        )
        await ctx.send(embed=view.make_embed(), view=view)

    @commands.command(name="군락", aliases=["마이코니드", "마이코니드군락", "비전타운"])
    async def vision_town_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.town_ui import VisionTownView
        view = VisionTownView(self.ctx.player, self.ctx.affinity_manager, self.ctx.npc_manager, village_manager, care_manager=self.ctx.care_manager)
        await view.send(ctx)

    @commands.command(name="대화")
    async def talk_cmd(self, ctx, *, name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if name:
            await ctx.send(ansi(
                f"  {C.RED}✖ /대화 [NPC이름] 형식은 더 이상 지원하지 않슴미댜!\n"
                f"  {C.GREEN}/군락{C.R} 또는 {C.GREEN}/마을상태{C.R} 로 NPC에게 접근해주셰요."
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
            origin = self.ctx.movement_system._get_location()
            result = self.ctx.movement_system.move_to(ctx.author.id, destination)
            if self.ctx.movement_system._get_location() == destination and origin != destination:
                event_store.append(GameEvent(
                    event_type="world.moved", actor_id=ctx.author.id, subject="츄라이더",
                    location=destination, payload={"from": origin, "to": destination},
                ))
        else:
            result = self.ctx.movement_system.show_map(ctx.author.id)
        await send_msg_card(ctx, "이동", str(result), system_key="system")


class InstrumentPerformanceSetupView(discord.ui.View):
    """악기 + 악보를 장착한 뒤 외부 리듬게임 창으로 진입하는 준비 화면."""
    def __init__(self, player, *, suspicious_actor_id=None):
        from ui.view_timeouts import GAME_VIEW_TIMEOUT
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.player=player
        self.suspicious_actor_id=suspicious_actor_id
        self._rebuild()

    def _rebuild(self):
        from music_system import INSTRUMENTS, learned_melodies, FAITH_SONGS, equip_instrument, equip_score, music_loadout, can_start_instrument_performance
        self.clear_items()
        ld=music_loadout(self.player)
        for iid,data in INSTRUMENTS.items():
            b=discord.ui.Button(label=data["name"],emoji=data["emoji"],style=discord.ButtonStyle.success if ld.get("instrument")==iid else discord.ButtonStyle.secondary,row=0)
            async def pick(interaction, instrument_id=iid):
                equip_instrument(self.player,instrument_id);self._save();self._rebuild()
                await interaction.response.edit_message(embed=self.make_embed(),view=self)
            b.callback=pick;self.add_item(b)
        known=[mid for mid,_ in learned_melodies(self.player)]
        # 복원된 피아노 악보는 발견 플래그가 있으면 선택 가능. 구세이브 호환을 위해 관련 플래그가 없을 때는 노출하지 않는다.
        try:
            from tower_exhibition import piano_unlocked
            piano_ready=piano_unlocked(self.player)
        except Exception:
            piano_ready=False
        if piano_ready:
            known += [mid for mid in FAITH_SONGS if mid not in known]
        if known:
            opts=[]
            from music_system import song_title
            for mid in known[:25]:
                opts.append(discord.SelectOption(label=song_title(mid)[:100],value=mid,default=ld.get('score')==mid))
            sel=discord.ui.Select(placeholder='📜 악보 장착',options=opts,row=1)
            async def score_pick(interaction):
                equip_score(self.player,sel.values[0]);self._save();self._rebuild()
                await interaction.response.edit_message(embed=self.make_embed(),view=self)
            sel.callback=score_pick;self.add_item(sel)
        ok,_=can_start_instrument_performance(self.player)
        play=discord.ui.Button(label='악기 연주',emoji='▶️',style=discord.ButtonStyle.primary,disabled=not ok,row=2)
        play.callback=self._start
        self.add_item(play)

    def _save(self):
        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception:
            pass

    def make_embed(self):
        from music_system import INSTRUMENTS, music_loadout, song_title, can_start_instrument_performance
        ld=music_loadout(self.player)
        inst=INSTRUMENTS.get(ld.get('instrument') or '',{}).get('name','—')
        score=song_title(ld['score']) if ld.get('score') else '—'
        ok,reason=can_start_instrument_performance(self.player)
        desc=f"**악기**  {inst}\n**악보**  {score}\n\n악기와 악보를 맞춰 장착한 뒤 **악기 연주**를 누르면 리듬게임 창으로 들어갑니다."
        if not ok: desc += f"\n\n> {reason}"
        return discord.Embed(title='🎼 악기 연주 · 준비',description=desc,color=0x6B5578)

    async def _start(self, interaction):
        import os
        from urllib.parse import urlencode
        from music_system import music_loadout, can_start_instrument_performance
        ok,reason=can_start_instrument_performance(self.player)
        if not ok:
            await interaction.response.send_message(reason,ephemeral=True);return
        base=os.getenv('RHYTHM_ACTIVITY_URL','').strip()
        if not base:
            await interaction.response.send_message('리듬게임 Activity 주소가 아직 연결되지 않았슴미댜.',ephemeral=True);return
        ld=music_loadout(self.player)
        sep='&' if '?' in base else '?'
        url=base+sep+urlencode({'song':ld['score']})
        launch=discord.ui.View(timeout=300)
        launch.add_item(discord.ui.Button(label='리듬게임 열기',emoji='🎹',style=discord.ButtonStyle.link,url=url))
        await interaction.response.send_message('🎶 준비됐슴미댜. 아래 버튼으로 연주를 시작하셰요!',view=launch,ephemeral=True)


async def setup(bot):
    await bot.add_cog(TownCog(bot))
