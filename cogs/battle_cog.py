# cogs/battle_cog.py
import io
import discord
from discord.ext import commands
from ui.ui_theme import C, ansi
from bg3_renderer import get_renderer
from save_manager import save_manager
from achievements import achievement_manager
from diary import diary_manager
from utils.discord_helpers import send_image, send_msg_card, send_encounter, check_channel
from utils.player_lock import get_player_lock


class BattleCog(commands.Cog, name="전투"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="사냥터")
    async def zone_list_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        zones = self.ctx.battle_engine.zone_list
        from monsters_db import MONSTERS_DB
        rows = []
        for zone_name in zones:
            zone = MONSTERS_DB[zone_name]
            lvl_min, lvl_max = zone["level_range"]
            rows.append({"label": zone_name, "value": f"Lv.{lvl_min} ~ {lvl_max}"})
        buf = get_renderer().render_card(
            "사냥터 목록",
            rows=rows,
            subtitle="/사냥 [사냥터이름] 으로 출발!",
            system_key="battle",
            footer="⚔ 전투 시스템",
        )
        await send_image(ctx, buf, "zones.png")

    @commands.command(name="사냥")
    async def hunt_cmd(self, ctx, *, zone: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            if not zone:
                await ctx.send(ansi(f"  {C.RED}✖ /사냥 [사냥터이름] 형식으로 입력하셰요!{C.R}"))
                return
            departure = self.ctx.encounter_manager.clear_encounter()
            if departure:
                await ctx.send(departure)
            success, result = self.ctx.battle_engine.start_encounter(zone)
            if success:
                _bimg = self.ctx.battle_engine.build_battle_image()

                async def _on_battle_end(won: bool):
                    if won:
                        newly_unlocked = achievement_manager.increment("battles_won", 1)
                        diary_manager.increment("battles_won", 1)
                        _killed_zone    = self.ctx.battle_engine.current_zone
                        _killed_monster = self.ctx.battle_engine.current_monster.get("id", "") if self.ctx.battle_engine.current_monster else ""
                        self.ctx.quest_manager.update_kill_count(1, zone=_killed_zone, monster_id=_killed_monster)
                        _hunt_completed = self.ctx.npc_manager.update_hunt_kill(monster_id=_killed_monster, count=1)
                        if _hunt_completed:
                            await self.ctx.npc_manager.complete_pending_hunts(ctx, _hunt_completed)
                        for ach_id in newly_unlocked:
                            from achievements import ACHIEVEMENT_DEFS
                            ach = ACHIEVEMENT_DEFS.get(ach_id, {})
                            await ctx.send(
                                f"🏆✨ **업적 달성!** [{ach.get('name', ach_id)}]\n"
                                f"  {ach.get('desc', '')}\n"
                                f"  🎀 타이틀 획득: **{ach.get('title', '')}**"
                            )
                    save_manager.save(self.ctx.player)

                from ui.battle_view import BattleView
                view = BattleView(self.ctx.battle_engine, ctx, on_battle_end=_on_battle_end)
                if _bimg:
                    _bimg.seek(0)
                    await ctx.send(file=discord.File(fp=_bimg, filename='battle.png'), view=view)
                elif isinstance(result, io.BytesIO):
                    result.seek(0)
                    await ctx.send(file=discord.File(fp=result, filename='battle.png'), view=view)
                else:
                    await ctx.send(str(result), view=view)
            else:
                if isinstance(result, io.BytesIO):
                    await send_image(ctx, result, 'battle.png')
                else:
                    await send_msg_card(ctx, "전투 오류", str(result), system_key="battle", grade="Fail")
            if success:
                enc_msg = self.ctx.encounter_manager.trigger_encounter()
                if enc_msg:
                    await send_encounter(ctx, enc_msg, self.ctx)

    @commands.command(name="공격")
    async def attack_cmd(self, ctx, *, skill_input: str = "smash"):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            if not self.ctx.battle_engine.in_battle:
                await send_msg_card(ctx, "오류", "현재 전투 중이 아님미댜! /사냥 으로 전투 시작.", system_key="battle", grade="Fail")
                return

            skill_id = skill_input.strip()
            if skill_id not in self.ctx.all_battle_skills:
                skill_id = self.ctx.skill_name_to_id.get(skill_id, skill_id)

            was_in_battle = self.ctx.battle_engine.in_battle
            result = self.ctx.battle_engine.process_turn(skill_id)

            if was_in_battle and not self.ctx.battle_engine.in_battle and self.ctx.player.hp > 0:
                newly_unlocked = achievement_manager.increment("battles_won", 1)
                diary_manager.increment("battles_won", 1)
                _killed_zone = self.ctx.battle_engine.current_zone
                _killed_monster = self.ctx.battle_engine.current_monster.get("id", "") if self.ctx.battle_engine.current_monster else ""
                self.ctx.quest_manager.update_kill_count(1, zone=_killed_zone, monster_id=_killed_monster)
                _hunt_completed = self.ctx.npc_manager.update_hunt_kill(monster_id=_killed_monster, count=1)
                if _hunt_completed:
                    await self.ctx.npc_manager.complete_pending_hunts(ctx, _hunt_completed)
                for ach_id in newly_unlocked:
                    from achievements import ACHIEVEMENT_DEFS
                    ach = ACHIEVEMENT_DEFS.get(ach_id, {})
                    await ctx.send(
                        f"🏆✨ **업적 달성!** [{ach.get('name', ach_id)}]\n"
                        f"  {ach.get('desc', '')}\n"
                        f"  🎀 타이틀 획득: **{ach.get('title', '')}**"
                    )

            _sname = self.ctx.all_battle_skills.get(skill_id, {}).get('name', skill_id)
            if self.ctx.battle_engine.in_battle:
                _bimg = self.ctx.battle_engine.build_battle_image(_sname)
                if _bimg:
                    await send_image(ctx, _bimg, 'battle.png')
                elif isinstance(result, io.BytesIO):
                    await send_image(ctx, result, 'battle.png')
                else:
                    await send_msg_card(ctx, "전투", str(result), system_key="battle")
            if not self.ctx.battle_engine.in_battle:
                if isinstance(result, io.BytesIO):
                    await send_image(ctx, result, 'battle_result.png')
                else:
                    await send_msg_card(ctx, "전투 결과", str(result), system_key="battle")
                save_manager.save(self.ctx.player)

    @commands.command(name="도주")
    async def flee_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            result = self.ctx.battle_engine.flee()
            if isinstance(result, io.BytesIO):
                await send_image(ctx, result, 'flee.png')
            else:
                await send_msg_card(ctx, "도주", str(result), system_key="battle")
            if not self.ctx.battle_engine.in_battle:
                save_manager.save(self.ctx.player)

    @commands.command(name="탐험")
    async def adventure_cmd(self, ctx, *, zone: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        lock = get_player_lock(ctx.author.id)
        if lock.locked():
            await ctx.send("⏳ 이전 명령을 처리 중입니다. 잠시 기다려주세요!")
            return
        async with lock:
            if not zone:
                from adventure_data import ADVENTURE_SCENARIOS
                avail_zones = list(ADVENTURE_SCENARIOS.keys())
                await ctx.send(ansi(
                    f"  {C.GOLD}탐험 가능한 지역{C.R}\n"
                    + "\n".join(f"  {C.GREEN}/탐험 {z}{C.R}" for z in avail_zones)
                ))
                return

            departure = self.ctx.encounter_manager.clear_encounter()
            if departure:
                await ctx.send(departure)

            result = self.ctx.adventure_engine.start_adventure(zone)
            if not result["ok"]:
                await send_msg_card(ctx, "탐험 오류", result["error"], system_key="battle", grade="Fail")
                return

            if result.get("hidden"):
                hidden = result["hidden"]
                event  = hidden.get("event", {})
                reward = event.get("reward", {})
                rparts = []
                if reward.get("gold"):   rparts.append(f"+{reward['gold']}G")
                if reward.get("exp"):    rparts.append(f"+{reward['exp']} EXP")
                if reward.get("item"):
                    from items import ALL_ITEMS
                    iname = ALL_ITEMS.get(reward["item"], {}).get("name", reward["item"])
                    rparts.append(f"{iname} 획득")
                await send_msg_card(
                    ctx,
                    f"✨ {event.get('title', '숨겨진 이벤트')}",
                    f"{event.get('desc', '')}\n\n🎁 {', '.join(rparts)}",
                    system_key="battle",
                )
                return

            if result.get("npc"):
                npc = result["npc"]
                from adventure import NPCInteractionView
                view = NPCInteractionView(self.ctx.adventure_engine, npc)
                embed = discord.Embed(
                    title=f"👤 {npc['race']} — {npc['name']} ({npc['type']})",
                    description=f"{npc['desc']}\n\n{npc.get('greeting', '')}",
                    color=0x8B4513,
                )
                await ctx.send(embed=embed, view=view)
                return

            scenario  = result["scenario"]
            step_data = result["step_data"]
            if not scenario or not step_data:
                await send_msg_card(ctx, "탐험", "이 지역에는 탐험할 것이 없슴미댜.", system_key="battle")
                return

            from adventure import AdventureView

            async def _on_adv_end(adv_result: dict):
                post_evt = self.ctx.adventure_engine.post_adventure_event(zone)
                if post_evt:
                    await ctx.send(f"📬 {post_evt.get('text', '')}")
                save_manager.save(self.ctx.player)

            view = AdventureView(
                adventure_engine=self.ctx.adventure_engine,
                step_data=step_data,
                scenario_title=scenario.get("title", "탐험"),
                on_end=_on_adv_end,
                zone_name=zone,
            )
            await ctx.send(
                f"📖 **[{scenario.get('title', '탐험')}]** — {zone}\n\n{step_data['desc']}",
                view=view,
            )


async def setup(bot):
    await bot.add_cog(BattleCog(bot))
