# cogs/quest_cog.py
import discord
from discord.ext import commands
from ui.ui_theme import C, ansi, header_box, divider
from save_manager import save_manager
from utils.discord_helpers import check_channel


class QuestCog(commands.Cog, name="퀘스트"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="퀘스트")
    async def quest_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.quest_ui import QuestWindowView, _make_quest_list_image
        file = _make_quest_list_image(self.ctx.quest_manager)
        view = QuestWindowView(self.ctx.quest_manager, self.ctx.player)
        await ctx.send(file=file, view=view)

    @commands.command(name="퀘스트수락")
    async def quest_accept_cmd(self, ctx, quest_id: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not quest_id:
            await ctx.send(ansi(f"  {C.RED}✖ /퀘스트수락 [ID] 형식으로 입력하셰요!{C.R}"))
            return
        result = self.ctx.quest_manager.accept_quest(quest_id)
        await ctx.send(result)
        save_manager.save(self.ctx.player)

    @commands.command(name="퀘스트완료")
    async def quest_complete_cmd(self, ctx, quest_id: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not quest_id:
            await ctx.send(ansi(f"  {C.RED}✖ /퀘스트완료 [ID] 형식으로 입력하셰요!{C.R}"))
            return
        result = self.ctx.quest_manager.complete_quest(quest_id)
        await ctx.send(result)
        save_manager.save(self.ctx.player)

    @commands.command(name="스토리")
    async def story_cmd(self, ctx):
        """현재 스토리 퀘스트 저널 표시 (챕터/퀘스트 진행도)."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.story_quest_ui import make_story_journal_image
        file = make_story_journal_image(self.ctx.story_quest_manager)
        await ctx.send(file=file)

    @commands.command(name="스토리퀘스트")
    async def story_quest_cmd(self, ctx):
        """현재 챕터의 다음 스토리 퀘스트를 진행합니다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from story_quest_data import STORY_CHAPTERS, CH1_QUESTS, CH2_QUESTS, CH3_QUESTS, CH4_QUESTS
        from ui.story_quest_ui import ShadowChoiceView, ForcedBattleView, play_cutscene

        ch  = self.ctx.story_quest_manager.chapter
        q   = self.ctx.story_quest_manager.quest

        if ch >= 5:
            await ctx.send(ansi(
                f"  {C.DARK}🔒 챕터 5 《등불이 비추는 것》 — 미해금{C.R}\n"
                f"  {C.DARK}다음 이야기는 아직 쓰이지 않았습니다.{C.R}"
            ))
            return

        ch_data = STORY_CHAPTERS.get(ch, {})
        if ch_data.get("locked"):
            await ctx.send(ansi(f"  {C.DARK}🔒 이 챕터는 아직 해금되지 않았슴미댜.{C.R}"))
            return

        quests_map = {1: CH1_QUESTS, 2: CH2_QUESTS, 3: CH3_QUESTS, 4: CH4_QUESTS}
        quests = quests_map.get(ch, {})
        qdata  = quests.get(q)
        if not qdata:
            await ctx.send(ansi(f"  {C.GOLD}✔ 챕터 {ch}의 모든 퀘스트를 완료했슴미댜!{C.R}"))
            return

        already_done = self.ctx.story_quest_manager.is_quest_done(ch, q)

        # ── 챕터 1 퀘스트 처리 ─────────────────────────────────────────────
        if ch == 1:
            if q in (1, 2, 3):
                if already_done:
                    await ctx.send(ansi(
                        f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"
                    ))
                    return
                npc_name = qdata["npc"]
                hint     = qdata["hint"]
                dialogue = qdata["dialogue"]
                lines = [
                    header_box(f"📜 챕터 1 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 {npc_name}{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{dialogue}\"{C.R}",
                    divider(),
                    f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
                ]
                aff_rewards = qdata.get("rewards", {}).get("affinity", {})
                for npc, pts in aff_rewards.items():
                    if self.ctx.affinity_manager:
                        self.ctx.affinity_manager.add_affinity(npc, pts)
                    lines.append(f"  {C.PINK}💖 {npc} 호감도 +{pts}{C.R}")
                self.ctx.story_quest_manager.add_hint(hint)
                kw = qdata.get("keyword")
                if kw and kw not in self.ctx.player.keywords:
                    self.ctx.player.keywords.append(kw)
                    lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = q + 1
                save_manager.save(self.ctx.player)
                await ctx.send(ansi("\n".join(lines)))

            elif q == 4:
                if already_done:
                    await ctx.send(ansi(
                        f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"
                    ))
                    return
                lines = [
                    header_box("🌑 그림자와의 공명"),
                    divider(),
                    f"  {C.WHITE}그림자 등불에 대한 이야기를 들은 후, 어둠이 속삭인다.{C.R}",
                    f"  {C.DARK}...당신은 어떤 존재이고 싶은가?{C.R}",
                    divider(),
                ]
                view = ShadowChoiceView(
                    qdata["choices"], self.ctx.story_quest_manager, self.ctx.player
                )
                msg = await ctx.send(ansi("\n".join(lines)), view=view)
                await view.wait()
                if view.chosen:
                    item_id = qdata.get("item")
                    if item_id:
                        self.ctx.player.add_item(item_id)
                    title = qdata.get("title_reward")
                    if title and title not in self.ctx.player.titles:
                        self.ctx.player.titles.append(title)
                    self.ctx.story_quest_manager.complete_quest(ch, q)
                    self.ctx.story_quest_manager.quest  = 1
                    self.ctx.story_quest_manager.chapter = 2
                    save_manager.save(self.ctx.player)
                    await ctx.send(ansi(
                        f"  {C.GREEN}✔ 챕터 1 완료! 챕터 2 《팅커 벨의 흔적》으로 진행합니다.{C.R}\n"
                        + (f"  {C.GOLD}🏅 칭호 획득: [{title}]{C.R}" if title else "")
                        + (f"\n  {C.CYAN}📦 아이템 획득: [{item_id}]{C.R}" if item_id else "")
                    ))

        # ── 챕터 2 퀘스트 처리 ─────────────────────────────────────────────
        elif ch == 2:
            if q == 1:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                hint = qdata["hint"]
                dialogue = qdata["dialogue"]
                lines = [
                    header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 게일의 환영{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{dialogue}\"{C.R}",
                    divider(),
                    f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
                ]
                self.ctx.story_quest_manager.add_hint(hint)
                kw = qdata.get("keyword")
                if kw and kw not in self.ctx.player.keywords:
                    self.ctx.player.keywords.append(kw)
                    lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = 2
                save_manager.save(self.ctx.player)
                await ctx.send(ansi("\n".join(lines)))

            elif q == 2:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                lines = [
                    header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 알피라{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{qdata['dialogue_alpira']}\"{C.R}",
                    divider(),
                    f"  {C.GOLD}💬 아라벨라{C.R}",
                    f"  {C.WHITE}\"{qdata['dialogue_arabella']}\"{C.R}",
                    divider(),
                    f"  {C.CYAN}📋 수집 미션: [{qdata['collect_item'].replace('sq_', '')}] × {qdata['collect_count']}{C.R}",
                    f"  {C.DARK}→ 방울숲에서 그림자 몬스터를 사냥해 획득 (드롭률 {int(qdata['drop_rate']*100)}%){C.R}",
                    f"  {C.DARK}→ /스토리수집 으로 사냥 시작{C.R}",
                ]
                await ctx.send(ansi("\n".join(lines)))

            elif q == 3:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                hint = qdata["hint"]
                lines = [
                    header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 엘레라신{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{qdata['dialogue']}\"{C.R}",
                    divider(),
                    f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
                    divider(),
                    f"  {C.DARK}당신의 반응은?{C.R}",
                ]
                view = ShadowChoiceView(
                    qdata["choices"], self.ctx.story_quest_manager, self.ctx.player
                )
                await ctx.send(ansi("\n".join(lines)), view=view)
                await view.wait()
                if view.chosen:
                    self.ctx.story_quest_manager.add_hint(hint)
                    kw = qdata.get("keyword")
                    if kw and kw not in self.ctx.player.keywords:
                        self.ctx.player.keywords.append(kw)
                    self.ctx.story_quest_manager.complete_quest(ch, q)
                    self.ctx.story_quest_manager.quest = 4
                    save_manager.save(self.ctx.player)

            elif q == 4:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                lines = [
                    header_box(f"📜 챕터 2 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 다몬{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{qdata['dialogue_damon']}\"{C.R}",
                    divider(),
                    f"  {C.GOLD}💬 오멜룸{C.R}",
                    f"  {C.WHITE}\"{qdata['dialogue_omelum']}\"{C.R}",
                    divider(),
                ]
                item_id = qdata.get("item_reward")
                title   = qdata.get("title_reward")
                if item_id:
                    self.ctx.player.add_item(item_id)
                    lines.append(f"  {C.CYAN}📦 아이템 획득: [수리된 문랜턴 외형]{C.R}")
                if title and title not in self.ctx.player.titles:
                    self.ctx.player.titles.append(title)
                    lines.append(f"  {C.GOLD}🏅 칭호 획득: [{title}]{C.R}")
                keywords = qdata.get("keyword", [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                for kw in keywords:
                    if kw and kw not in self.ctx.player.keywords:
                        self.ctx.player.keywords.append(kw)
                        lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest   = 1
                self.ctx.story_quest_manager.chapter = 3
                save_manager.save(self.ctx.player)
                lines.append(f"  {C.GREEN}✔ 챕터 2 완료! 챕터 3 《선택의 무게》로 진행합니다.{C.R}")
                await ctx.send(ansi("\n".join(lines)))

        # ── 챕터 3 퀘스트 처리 ─────────────────────────────────────────────
        elif ch == 3:
            if q == 1:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                lines = [
                    header_box(f"📜 챕터 3 Q{q}: {qdata['title']}"),
                    f"  {C.GOLD}💬 몰{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{qdata['dialogue']}\"{C.R}",
                    divider(),
                ]
                item_id = qdata.get("item_reward")
                if item_id:
                    self.ctx.player.add_item(item_id)
                    lines.append(f"  {C.CYAN}📦 아이템 획득: [몰의 지도 조각]{C.R}")
                kw = qdata.get("keyword")
                if kw and kw not in self.ctx.player.keywords:
                    self.ctx.player.keywords.append(kw)
                    lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.flags["늪지대_해금"] = True
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = "gate"
                save_manager.save(self.ctx.player)
                lines.append(f"  {C.GREEN}🗺️ 늪지대 이동 가능! /이동 늪지대{C.R}")
                await ctx.send(ansi("\n".join(lines)))

            elif q == "gate" or self.ctx.story_quest_manager.flags.get("at_gate"):
                gate_data = CH3_QUESTS.get("gate", {})
                if self.ctx.story_quest_manager.is_quest_done(ch, "gate"):
                    await ctx.send(ansi(f"  {C.GOLD}✔ [성문 통과] 이미 완료했슴미댜!{C.R}"))
                    return
                lines = [
                    header_box("📜 챕터 3 — 성문 통과"),
                    f"  {C.GOLD}💬 제블로어{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{gate_data.get('dialogue', '...')}\"{C.R}",
                    divider(),
                    f"  {C.GREEN}늪지대 진입 허가!{C.R}",
                ]
                self.ctx.story_quest_manager.complete_quest(ch, "gate")
                self.ctx.story_quest_manager.quest = 2
                save_manager.save(self.ctx.player)
                await ctx.send(ansi("\n".join(lines)))

            elif q == 2:
                await ctx.send(ansi(
                    f"  {C.CYAN}/스토리탐색{C.R} 명령어로 늪지대 탐색을 진행하세요!"
                ))

            elif q == 3:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                scenes = []
                for dlg in qdata["dialogues"]:
                    scenes.append(
                        f"  {C.GOLD}✨ 팅커 벨{C.R}\n"
                        f"  {C.WHITE}\"{dlg}\"{C.R}"
                    )
                await play_cutscene(ctx, scenes, delay=3.0)

                sync = self.ctx.story_quest_manager.shadow_sync
                reactions = qdata["auto_reactions"]
                if sync >= reactions["dark"]["threshold"]:
                    result = reactions["dark"]
                elif sync <= reactions["light"]["threshold"]:
                    result = reactions["light"]
                else:
                    result = reactions["neutral"]

                self.ctx.story_quest_manager.add_shadow_sync(result["shadow_sync"])
                await ctx.send(ansi(
                    f"  {C.DARK}─────────────────────────────{C.R}\n"
                    f"  {C.WHITE}{result['text']}{C.R}"
                ))
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = 4
                save_manager.save(self.ctx.player)

            elif q == 4:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return

                async def on_battle_done(interaction):
                    self.ctx.story_quest_manager.complete_quest(ch, 4)
                    self.ctx.story_quest_manager.quest = 5
                    save_manager.save(self.ctx.player)
                    await interaction.channel.send(ansi(
                        f"  {C.RED}★ 전투 종료 — 도달할 수 없었다.{C.R}\n"
                        f"  {C.DARK}/스토리퀘스트 로 다음 장면을 진행하세요.{C.R}"
                    ))

                lines = [
                    header_box("⚔️  닿지 않는 전투"),
                    f"  {C.WHITE}팅커 벨이 공중으로 솟구쳤다.{C.R}",
                    divider(),
                    f"  {C.DARK}공격 버튼을 눌러 전투를 진행하세요.{C.R}",
                ]
                view = ForcedBattleView(
                    qdata["turns"], self.ctx.story_quest_manager, self.ctx.player,
                    on_done_coro=on_battle_done
                )
                await ctx.send(ansi("\n".join(lines)), view=view)

            elif q == 5:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                ending = qdata["ending_text"]
                lines = [
                    header_box("📜 챕터 3 엔딩 — 추락한 포식자"),
                    divider(),
                    f"  {C.WHITE}{ending}{C.R}",
                    divider(),
                ]
                title = qdata.get("title_reward")
                item_id = qdata.get("item_reward")
                if title and title not in self.ctx.player.titles:
                    self.ctx.player.titles.append(title)
                    lines.append(f"  {C.GOLD}🏅 칭호 획득: [{title}] (원거리 명중률 +3%){C.R}")
                if item_id:
                    self.ctx.player.add_item(item_id)
                    lines.append(f"  {C.CYAN}📦 아이템 획득: [한 줌의 팅커 벨 가루]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest   = 1
                self.ctx.story_quest_manager.chapter = 4
                save_manager.save(self.ctx.player)
                lines.append(divider())
                lines.append(f"  {C.GREEN}📖 챕터 4 《거미줄과 속박》 해금!{C.R}")
                lines.append(f"  {C.DARK}/스토리퀘스트 로 다음 이야기를 진행하세요.{C.R}")
                await ctx.send(ansi("\n".join(lines)))

        # ── 챕터 4 퀘스트 처리 ─────────────────────────────────────────────
        elif ch == 4:
            if q == 1:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return
                npc_name = qdata["npc"]
                hint     = qdata["hint"]
                dialogue = qdata["dialogue"]
                lines = [
                    header_box(f"📜 챕터 4 Q1: {qdata['title']}"),
                    f"  {C.GOLD}💬 {npc_name}{C.R}",
                    divider(),
                    f"  {C.WHITE}\"{dialogue}\"{C.R}",
                    divider(),
                    f"  {C.GREEN}[힌트 획득]: 「{hint}」{C.R}",
                ]
                aff_rewards = qdata.get("rewards", {}).get("affinity", {})
                for npc, pts in aff_rewards.items():
                    if self.ctx.affinity_manager:
                        self.ctx.affinity_manager.add_affinity(npc, pts)
                    lines.append(f"  {C.PINK}💖 {npc} 호감도 +{pts}{C.R}")
                self.ctx.story_quest_manager.add_hint(hint)
                kw = qdata.get("keyword")
                if kw and kw not in self.ctx.player.keywords:
                    self.ctx.player.keywords.append(kw)
                    lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = 2
                save_manager.save(self.ctx.player)
                await ctx.send(ansi("\n".join(lines)))

            elif q == 2:
                await ctx.send(ansi(
                    f"  {C.WHITE}📜 챕터 4 Q2: {qdata['title']}{C.R}\n"
                    f"  {C.DARK}방울숲에서 비정상적인 소리가 들린다.{C.R}\n"
                    f"  {C.GREEN}/스토리탐색4 명령어로 탐색을 진행하세요.{C.R}"
                ))

            elif q == 3:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return

                await play_cutscene(ctx, qdata["dialogues"])

                sync = self.ctx.story_quest_manager.shadow_sync
                reactions = qdata["auto_reactions"]
                if sync >= reactions["dark"]["threshold"]:
                    result = reactions["dark"]
                elif sync <= reactions["light"]["threshold"]:
                    result = reactions["light"]
                else:
                    result = reactions["neutral"]

                self.ctx.story_quest_manager.add_shadow_sync(result["shadow_sync"])
                lines = [
                    header_box("🕷️  내면의 반응"),
                    divider(),
                    f"  {C.WHITE}{result['text']}{C.R}",
                    divider(),
                ]
                if result["shadow_sync"] != 0:
                    sign = f"+{result['shadow_sync']}" if result['shadow_sync'] > 0 else str(result['shadow_sync'])
                    lines.append(f"  {C.DARK}(그림자 공명 {sign}){C.R}")

                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = 4
                save_manager.save(self.ctx.player)
                lines.append(f"  {C.GREEN}/스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}")
                await ctx.send(ansi("\n".join(lines)))

            elif q == 4:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return

                lines = [
                    header_box("⚖️  빛의 무게"),
                    f"  {C.WHITE}날개가 찢어진 팅커 벨이 눈앞에 있다.{C.R}",
                    f"  {C.WHITE}등불은 차갑게 기다리고 있다.{C.R}",
                    divider(),
                    f"  {C.DARK}선택하세요.{C.R}",
                ]

                from ui.story_quest_ui import ShadowChoiceWithFlagView
                view = ShadowChoiceWithFlagView(
                    qdata["choices"], self.ctx.story_quest_manager, self.ctx.player,
                    choice_results=qdata["choice_results"],
                    author_id=ctx.author.id,
                )
                await ctx.send(ansi("\n".join(lines)), view=view)
                await view.wait()

                if not getattr(view, "chosen", False):
                    await ctx.send(ansi(
                        f"  {C.YELLOW}⏰ 선택 시간이 만료되었거나 아무도 버튼을 누르지 않았슴미댜.{C.R}\n"
                        f"  {C.DARK}다시 `/스토리퀘스트` 명령어로 이 퀘스트를 열어서 선택을 완료해 주세요!{C.R}"
                    ))
                    return
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest = 5
                save_manager.save(self.ctx.player)

            elif q == 5:
                if already_done:
                    await ctx.send(ansi(f"  {C.GOLD}✔ [{qdata['title']}] 이미 완료했슴미댜!{C.R}"))
                    return

                if self.ctx.story_quest_manager.flags.get("pixie_captured"):
                    route_key = "pixie_captured"
                elif self.ctx.story_quest_manager.flags.get("pixie_pact"):
                    route_key = "pixie_pact"
                elif self.ctx.story_quest_manager.flags.get("pixie_healed"):
                    route_key = "pixie_healed"
                else:
                    route_key = "pixie_pact"

                ending = qdata["ending_texts"][route_key]
                lines = [
                    header_box("📜 챕터 4 엔딩 — 속박과 해방 사이"),
                    divider(),
                    f"  {C.WHITE}{ending}{C.R}",
                    divider(),
                ]
                title_rw = qdata.get("title_reward")
                if title_rw and title_rw not in self.ctx.player.titles:
                    self.ctx.player.titles.append(title_rw)
                    lines.append(f"  {C.GOLD}🏅 칭호 획득: [{title_rw}]{C.R}")
                item_id = qdata.get("item_rewards", {}).get(route_key)
                if item_id:
                    self.ctx.player.add_item(item_id)
                    from items import ALL_ITEMS
                    item_name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                    lines.append(f"  {C.CYAN}📦 아이템 획득: [{item_name}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(ch, q)
                self.ctx.story_quest_manager.quest   = 1
                self.ctx.story_quest_manager.chapter = 5
                save_manager.save(self.ctx.player)
                lines.append(divider())
                lines.append(f"  {C.DARK}🔒 챕터 5 《등불이 비추는 것》 — 미해금{C.R}")
                lines.append(f"  {C.DARK}다음 이야기는 아직 쓰이지 않았습니다.{C.R}")
                await ctx.send(ansi("\n".join(lines)))

    @commands.command(name="스토리탐색")
    async def story_explore_cmd(self, ctx):
        """늪지대 탐색 퀘스트 실행 (챕터 3 Q2 전용, 3단계)."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from story_quest_data import CH3_QUESTS
        from ui.story_quest_ui import ExploreView

        ch = self.ctx.story_quest_manager.chapter
        q  = self.ctx.story_quest_manager.quest
        if ch != 3 or q != 2:
            await ctx.send(ansi(
                f"  {C.RED}✖ 탐색은 챕터 3 Q2에서만 가능합미댜!{C.R}\n"
                f"  {C.DARK}현재: 챕터 {ch} Q{q}{C.R}"
            ))
            return

        if self.ctx.story_quest_manager.is_quest_done(3, 2):
            await ctx.send(ansi(f"  {C.GOLD}✔ 탐색을 이미 완료했슴미댜!{C.R}"))
            return

        if not self.ctx.story_quest_manager.flags.get("늪지대_해금"):
            await ctx.send(ansi(f"  {C.RED}✖ 아직 늪지대에 진입할 수 없슴미댜.{C.R}"))
            return

        qdata = CH3_QUESTS[2]

        async def on_explore_done(interaction):
            self.ctx.story_quest_manager.complete_quest(3, 2)
            self.ctx.story_quest_manager.quest = 3
            save_manager.save(self.ctx.player)
            await interaction.channel.send(ansi(
                f"  {C.GOLD}✔ 탐색 완료! 무언가 발견됐슴미댜...{C.R}\n"
                f"  {C.GREEN}/스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}"
            ))

        lines = [
            header_box("🌫️  늪지대 탐색"),
            f"  {C.DARK}안개와 진흙으로 뒤덮인 음습한 늪지대.{C.R}",
            divider(),
        ]
        view = ExploreView(
            qdata["step_descs"], self.ctx.story_quest_manager, self.ctx.player,
            on_done_coro=on_explore_done
        )
        await ctx.send(ansi("\n".join(lines)), view=view)

    @commands.command(name="스토리탐색4")
    async def story_explore4_cmd(self, ctx):
        """방울숲 탐색 퀘스트 실행 (챕터 4 Q2 전용, 3단계)."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from story_quest_data import CH4_QUESTS
        from ui.story_quest_ui import ExploreView

        ch = self.ctx.story_quest_manager.chapter
        q  = self.ctx.story_quest_manager.quest
        if ch != 4 or q != 2:
            await ctx.send(ansi(
                f"  {C.RED}✖ 이 탐색은 챕터 4 Q2에서만 가능합미댜!{C.R}\n"
                f"  {C.DARK}현재: 챕터 {ch} Q{q}{C.R}"
            ))
            return

        if self.ctx.story_quest_manager.is_quest_done(4, 2):
            await ctx.send(ansi(f"  {C.GOLD}✔ 탐색을 이미 완료했슴미댜!{C.R}"))
            return

        qdata = CH4_QUESTS[2]

        async def on_explore_done(interaction):
            self.ctx.story_quest_manager.complete_quest(4, 2)
            self.ctx.story_quest_manager.quest = 3
            save_manager.save(self.ctx.player)
            await interaction.channel.send(ansi(
                f"  {C.GOLD}✔ 탐색 완료! 가시덤불 사이에 무언가가...{C.R}\n"
                f"  {C.GREEN}/스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}"
            ))

        lines = [
            header_box("🌿  방울숲 탐색"),
            f"  {C.DARK}이전과 다른 소리가 숲에서 흘러나온다.{C.R}",
            divider(),
        ]
        view = ExploreView(
            qdata["step_descs"], self.ctx.story_quest_manager, self.ctx.player,
            on_done_coro=on_explore_done
        )
        await ctx.send(ansi("\n".join(lines)), view=view)

    @commands.command(name="스토리수집")
    async def story_collect_cmd(self, ctx):
        """챕터 2 Q2 — 팅커 벨의 날개 가루 수집 (방울숲 전용)."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        import random
        import time as _t
        from story_quest_data import CH2_QUESTS

        ch = self.ctx.story_quest_manager.chapter
        q  = self.ctx.story_quest_manager.quest
        if ch != 2 or q != 2:
            await ctx.send(ansi(
                f"  {C.RED}✖ 수집은 챕터 2 Q2에서만 가능합미댜! (현재: 챕터 {ch} Q{q}){C.R}"
            ))
            return

        if self.ctx.story_quest_manager.is_quest_done(2, 2):
            await ctx.send(ansi(f"  {C.GOLD}✔ 이미 완료했슴미댜!{C.R}"))
            return

        current_loc = getattr(self.ctx.player, "current_location", "마을")
        if current_loc != "방울숲":
            await ctx.send(ansi(
                f"  {C.RED}✖ 방울숲에 있어야 합미댜! (현재 위치: {current_loc}){C.R}\n"
                f"  {C.DARK}/이동 방울숲 으로 이동하세요.{C.R}"
            ))
            return

        qdata    = CH2_QUESTS[2]
        cooldown = qdata["drop_cooldown"]
        last_collect = self.ctx.story_quest_manager.flags.get("_collect_last_time", 0)
        now = _t.time()
        if now - last_collect < cooldown:
            remain = int(cooldown - (now - last_collect))
            await ctx.send(ansi(f"  {C.RED}⏳ 수집 쿨다운: {remain}초 남음{C.R}"))
            return

        self.ctx.story_quest_manager.flags["_collect_last_time"] = now

        if random.random() < qdata["drop_rate"]:
            self.ctx.player.add_item(qdata["collect_item"])
            have = self.ctx.player.inventory.get(qdata["collect_item"], 0)
            lines = [
                f"  {C.GREEN}✔ 팅커 벨의 날개 가루 획득!{C.R}  ({have}/{qdata['collect_count']})",
            ]
            if have >= qdata["collect_count"]:
                keywords = qdata.get("keyword", [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                for kw in keywords:
                    if kw and kw not in self.ctx.player.keywords:
                        self.ctx.player.keywords.append(kw)
                        lines.append(f"  {C.CYAN}🔓 새 키워드: [{kw}]{C.R}")
                self.ctx.story_quest_manager.complete_quest(2, 2)
                self.ctx.story_quest_manager.quest = 3
                save_manager.save(self.ctx.player)
                lines.append(f"  {C.GOLD}✔ 수집 완료! /스토리퀘스트 로 다음 퀘스트를 진행하세요.{C.R}")
            await ctx.send(ansi("\n".join(lines)))
        else:
            await ctx.send(ansi(
                f"  {C.DARK}그림자 몬스터를 쓰러뜨렸지만 가루가 떨어지지 않았슴미댜.{C.R}\n"
                f"  {C.DARK}({int(qdata['drop_rate']*100)}% 확률로 드롭){C.R}"
            ))

    @commands.command(name="스토리힌트")
    async def story_hints_cmd(self, ctx):
        """수집한 힌트 목록을 표시합니다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from ui.story_quest_ui import make_hints_image
        file = make_hints_image(self.ctx.story_quest_manager)
        await ctx.send(file=file)

    @commands.command(name="그림자")
    async def shadow_cmd(self, ctx):
        """shadow_sync 암시 텍스트를 확인합니다."""
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        hint = self.ctx.story_quest_manager.get_shadow_hint()
        game_time = self.ctx.story_quest_manager.get_game_time()
        color = self.ctx.story_quest_manager.get_embed_theme(game_time)
        embed = discord.Embed(
            title="🌑 그림자의 상태",
            description=hint,
            color=color,
        )
        embed.set_footer(text="✦ 수치는 비공개임미댜 ✦")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(QuestCog(bot))
