import logging
import random
from database import NPC_DATA
from economy import Economy
from ui_theme import C, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS
from job_data import get_random_job, get_jobs_by_difficulty, DIFFICULTY_LABELS, NPC_JOB_POOL

logger = logging.getLogger(__name__)


class VillageNPC:
    def __init__(self, player):
        self.player = player

    def get_greeting(self, npc_name: str) -> str:
        npc = NPC_DATA.get(npc_name)
        if not npc:
            return f"{C.RED}✖ [{npc_name}]이라는 NPC를 찾을 수 없슴미댜.{C.R}"
        greetings = npc.get("greetings", ["..."])
        return random.choice(greetings)

    def talk_to_npc(self, npc_name: str) -> str:
        """기본 인사 텍스트를 반환합니다. (키워드 UI는 talk_to_npc_async 사용)"""
        npc = NPC_DATA.get(npc_name)
        if not npc:
            return ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}")

        greeting = self.get_greeting(npc_name)
        lines = [
            header_box(f"💬 {npc['name']}"),
            f"  {C.DARK}[{npc.get('role','???')}] {npc.get('location','???')}{C.R}",
            divider(),
            f"  {C.WHITE}\"{greeting}\"{C.R}",
            divider(),
            f"  {C.DARK}{npc.get('desc','')}{C.R}",
        ]

        # Fix #6: 알바 가능 여부만 표시 (구체적인 알바 1개를 고정하지 않음)
        if NPC_JOB_POOL.get(npc_name):
            lines.append(f"\n  {C.GOLD}▸ 알바 가능{C.R}: {C.WHITE}{npc['name']}{C.R}에게 알바를 받을 수 있슴미댜!")
            lines.append(f"  {C.GREEN}/알바 {npc['name']}{C.R} 으로 알바 선택 UI를 열 수 있슴미댜.")

        return ansi("\n".join(lines))

    async def talk_to_npc_async(self, ctx, npc_name: str):
        """키워드 대화 시스템으로 NPC 대화를 처리합니다."""
        # 특수 NPC는 직접 대화 불가 (인카운터 상태는 특수키워드 명령어로 대화)
        SPECIAL_NPCS = {"라파엘", "카르니스", "루바토"}
        if npc_name in SPECIAL_NPCS:
            await ctx.send(ansi(
                f"  {C.RED}✖ [{npc_name}]은(는) 직접 찾아갈 수 없슴미댜.\n"
                f"  만남은 운명에 맡기셰요! (랜덤 인카운터로만 만날 수 있어요)\n"
                f"  인카운터 중이라면 /특수키워드 {npc_name} [키워드] 를 사용하셰요.{C.R}"
            ))
            return
        from npc_conversation import ConversationManager
        aff_mgr = getattr(self.player, "_affinity_manager", None)
        conv = ConversationManager(self.player, aff_mgr)
        await conv.send_conversation(ctx, npc_name)

    def start_job(self, npc_name: str) -> str:
        """동기 알바 처리 (deprecated — start_job_async 사용 권장)."""
        npc = NPC_DATA.get(npc_name)
        if not npc:
            return ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}")

        job = get_random_job(npc_name, self.player)
        if not job:
            return ansi(f"  {C.RED}✖ {npc.get('name', npc_name)}은(는) 알바가 없슴미댜.{C.R}")

        energy_cost = job.get("energy_cost", 20)
        if not self.player.consume_energy(energy_cost):
            return ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            )

        reward_gold = job.get("reward_gold", 100)
        reward_exp  = job.get("reward_exp",  10)
        economy = Economy(self.player)
        economy.pay_reward(source=f"알바:{npc_name}", gold=reward_gold, exp=reward_exp)

        lines = [
            header_box(f"💼 {npc['name']} 알바"),
            f"  {C.WHITE}{job['name']}{C.R}",
            divider(),
            f"  {C.DARK}{job.get('desc','')}{C.R}",
            f"  {C.GOLD}+{reward_gold}G{C.R}  {C.GREEN}EXP +{reward_exp}{C.R}",
            f"  {C.RED}기력 -{energy_cost}{C.R}",
        ]
        return ansi("\n".join(lines))

    async def start_job_async(self, ctx, npc_name: str):
        """알바 선택 UI → 진행 → 결과를 전송합니다."""
        import asyncio
        import discord

        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}"))
            return

        # Fix #5: 난이도별 3개 알바 제시 (제작 가능 여부 체크 포함)
        jobs_by_diff = get_jobs_by_difficulty(npc_name, self.player)
        if not jobs_by_diff:
            await ctx.send(ansi(f"  {C.RED}✖ {npc.get('name', npc_name)}은(는) 알바가 없슴미댜.{C.R}"))
            return

        # ── 알바 선택 UI ──────────────────────────────────────────────────────
        diff_styles = {
            "easy":   discord.ButtonStyle.success,
            "normal": discord.ButtonStyle.primary,
            "hard":   discord.ButtonStyle.danger,
        }
        type_icons = {"gather": "🛒", "deliver": "📦", "hunt": "⚔️"}

        class JobSelectView(discord.ui.View):
            def __init__(self, jobs: dict, author_id: int):
                super().__init__(timeout=10)
                self.selected_job = None
                self.author_id = author_id

                for diff in ("easy", "normal", "hard"):
                    if diff not in jobs:
                        continue
                    j = jobs[diff]
                    diff_label = DIFFICULTY_LABELS.get(diff, diff)
                    icon = type_icons.get(j.get("type", "hunt"), "💼")
                    btn = discord.ui.Button(
                        label=f"{icon} [{diff_label}] {j['name']}  {j['reward_gold']}G / EXP+{j['reward_exp']}",
                        style=diff_styles.get(diff, discord.ButtonStyle.secondary),
                    )
                    btn.callback = self._make_cb(j)
                    self.add_item(btn)

                cancel_btn = discord.ui.Button(
                    label="취소", style=discord.ButtonStyle.secondary, row=1
                )
                cancel_btn.callback = self._on_cancel
                self.add_item(cancel_btn)

            def _make_cb(self, job: dict):
                async def cb(interaction: discord.Interaction):
                    if interaction.user.id != self.author_id:
                        await interaction.response.send_message(
                            "다른 플레이어의 알바 선택입니다!", ephemeral=True
                        )
                        return
                    self.selected_job = job
                    for child in self.children:
                        child.disabled = True
                    await interaction.response.edit_message(view=self)
                    self.stop()
                return cb

            async def _on_cancel(self, interaction: discord.Interaction):
                if interaction.user.id != self.author_id:
                    await interaction.response.send_message(
                        "다른 플레이어의 알바 선택입니다!", ephemeral=True
                    )
                    return
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(view=self)
                self.stop()

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True

        author_id = ctx.author.id if hasattr(ctx, "author") else 0
        view = JobSelectView(jobs_by_diff, author_id)
        select_msg = await ctx.send(
            ansi(
                f"  {C.GOLD}💼 {npc['name']} 알바 선택{C.R}\n"
                f"  {C.DARK}원하는 알바를 선택하셰요. (10초 안에 선택해야 합니다){C.R}"
            ),
            view=view,
        )
        await view.wait()

        job = view.selected_job
        if job is None:
            await select_msg.edit(
                content=ansi(f"  {C.RED}✖ 알바 선택이 취소되었슴미댜. (기력 소모 없음){C.R}"),
                view=None,
            )
            return

        # Fix #7: deliver 변수 기본값 초기화
        deliver_item      = ""
        deliver_item_name = ""
        target_npc        = ""

        energy_cost = job.get("energy_cost", 20)
        diff_label  = DIFFICULTY_LABELS.get(job.get("difficulty", "easy"), "쉬움")
        job_type    = job.get("type", "hunt")
        economy     = Economy(self.player)

        # Fix #3: gather 재료 확인을 기력 차감 전에 수행
        if job_type == "gather":
            target_item  = job.get("target_item", "")
            target_count = job.get("target_count", 1)
            have = self.player.inventory.get(target_item, 0)
            if have < target_count:
                from items import ALL_ITEMS
                item_name = ALL_ITEMS.get(target_item, {}).get("name", target_item)
                await ctx.send(ansi(
                    f"  {C.RED}✖ 재료가 부족함미댜! "
                    f"{item_name} {target_count}개 필요 (보유: {have}개){C.R}"
                ))
                return

        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        # gather: 아이템 차감
        if job_type == "gather":
            economy.remove_item(f"알바:{npc_name}", target_item, target_count)

        # deliver: 퀘스트 아이템 지급
        elif job_type == "deliver":
            deliver_item      = job.get("deliver_item", "")
            deliver_item_name = job.get("deliver_item_name", "")
            target_npc        = job.get("target_npc", "")
            if deliver_item and not deliver_item_name:
                from items import ALL_ITEMS as _AI
                deliver_item_name = _AI.get(deliver_item, {}).get("name", deliver_item)
            if not deliver_item_name:
                deliver_item_name = deliver_item
            if deliver_item:
                economy.add_item(f"알바:{npc_name}", deliver_item, 1)

        # deliver 타입: 배달 아이템 이름 안내 메시지 준비
        deliver_notice = ""
        if job_type == "deliver" and deliver_item:
            _dname = deliver_item_name if deliver_item_name else deliver_item
            _target = job.get("target_npc", "")
            deliver_notice = f"\n  {C.WHITE}📦 {_dname}을(를) {_target}에게 전달하셰요!{C.R}"

        await ctx.send(ansi(
            f"  {C.GOLD}💼 {npc['name']} 알바 시작! [{diff_label}]{C.R}\n"
            f"  {C.DARK}{job['name']} — {job.get('desc','')}{C.R}{deliver_notice}\n"
            f"  {C.RED}기력 -{energy_cost}{C.R}  ⏱ 잠시 기다려 주셰요..."
        ))

        await asyncio.sleep(3)

        reward_gold      = job.get("reward_gold", 100)
        reward_exp       = job.get("reward_exp", 10)
        reward_item      = job.get("reward_item")
        reward_skill_exp = job.get("reward_skill_exp", {})

        try:
            from village import village_manager
            village_manager.add_contribution(5, "job")
        except Exception as e:
            logger.error(f"[npcs] village contribution 실패: {e}")

        result_note = ""

        # Fix #2: hunt 유형 — 스탯 기반 성공/실패 판정
        if job_type == "hunt":
            difficulty  = job.get("difficulty", "easy")
            base_rates  = {"easy": 0.90, "normal": 0.70, "hard": 0.50}
            base_rate   = base_rates.get(difficulty, 0.70)
            str_val     = self.player.base_stats.get("str", 10)
            dex_val     = self.player.base_stats.get("dex", 10)
            final_rate  = min(0.95, base_rate + (str_val + dex_val) * 0.005)
            hunt_success = random.random() < final_rate
            if not hunt_success:
                reward_gold = max(1, int(reward_gold * 0.3))
                reward_exp  = max(1, int(reward_exp  * 0.3))
                result_note = "실패"
            economy.pay_reward(
                source=f"알바:{npc_name}",
                gold=reward_gold,
                exp=float(reward_exp),
            )

        elif job_type == "gather":
            economy.pay_reward(
                source=f"알바:{npc_name}",
                gold=reward_gold,
                exp=float(reward_exp),
            )

        else:  # Fix #1: deliver — 즉시 보상 지급 + 배달 아이템 제거
            economy.pay_reward(
                source=f"알바:{npc_name}",
                gold=reward_gold,
                exp=float(reward_exp),
            )
            if deliver_item:
                economy.remove_item(f"알바:{npc_name}", deliver_item, 1)

        # Fix #4: 스킬 경험치 보상 — train_skill() 사용 (미등록 스킬도 자동 초기화)
        if reward_skill_exp:
            for skill_id, amount in reward_skill_exp.items():
                self.player.train_skill(skill_id, amount)

        # ── 보상 아이템 지급 ──────────────────────────────────────────────────
        reward_item_line = ""
        if reward_item:
            economy.add_item(f"알바:{npc_name}", reward_item, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(reward_item, {}).get("name", reward_item)
            reward_item_line = f"\n  {C.WHITE}🎁 {item_name} x1{C.R}"

        # ── 결과 카드 / 텍스트 전송 ──────────────────────────────────────────
        completion_label = f"{'실패! ' if result_note == '실패' else '완료! '}[{diff_label}]"
        card_sent = False
        try:
            import fishing_card
            buf  = fishing_card.generate_job_card(
                job["name"], completion_label, reward_gold, f"EXP +{reward_exp}"
            )
            file = discord.File(buf, filename="job_result.png")
            embed = discord.Embed(
                title=f"💼 {npc['name']} 알바 {completion_label}",
                color=EMBED_COLOR.get("npc", 0x4A7856),
            )
            embed.set_image(url="attachment://job_result.png")
            await ctx.send(embed=embed, file=file)
            card_sent = True
        except Exception:
            pass

        if not card_sent:
            lines = [
                header_box(f"💼 {npc['name']} 알바 {completion_label}"),
                f"  {C.WHITE}{job['name']}{C.R}",
                divider(),
                f"  {C.GOLD}+{reward_gold}G{C.R}  {C.GREEN}EXP +{reward_exp}{C.R}",
            ]
            if result_note == "실패":
                lines.insert(2, f"  {C.RED}⚠ 사냥에 실패했슴미댜. 보상이 30%만 지급됩니다.{C.R}")
            if reward_item_line:
                lines.append(reward_item_line)
            await ctx.send(ansi("\n".join(lines)))

        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception:
            pass

    def list_npcs(self) -> str:
        lines = [header_box("🏘 마을 NPC 목록"), section("NPC 목록")]
        for npc_name, npc in NPC_DATA.items():
            role = npc.get("role", "???")
            loc  = npc.get("location", "???")
            lines.append(f"  {C.GOLD}{npc_name}{C.R}  {C.DARK}[{role}] {loc}{C.R}")
        lines.append(divider())
        lines.append(f"  {C.GREEN}/대화 [이름]{C.R} 으로 NPC와 대화하셰요!")
        return ansi("\n".join(lines))
