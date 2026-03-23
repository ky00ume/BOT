import logging
import random
from database import NPC_DATA
from ui_theme import C, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS
from job_data import get_random_job, DIFFICULTY_LABELS

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

        job = get_random_job(npc_name)
        if job:
            diff_label = DIFFICULTY_LABELS.get(job.get("difficulty", "easy"), "쉬움")
            lines.append(f"\n  {C.GOLD}▸ 알바{C.R}: {C.WHITE}{job['name']}{C.R} [{diff_label}]")
            lines.append(f"    {C.DARK}보상: {job['reward_gold']}G / EXP+{job['reward_exp']} / 기력 -{job['energy_cost']}{C.R}")
            lines.append(f"  {C.GREEN}/알바 {npc['name']}{C.R} 으로 알바 가능")

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

        job = get_random_job(npc_name)
        if not job:
            return ansi(f"  {C.RED}✖ {npc.get('name', npc_name)}은(는) 알바가 없슴미댜.{C.R}")

        energy_cost = job.get("energy_cost", 20)
        if not self.player.consume_energy(energy_cost):
            return ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            )

        reward_gold = job.get("reward_gold", 100)
        reward_exp  = job.get("reward_exp",  10)
        from economy import Economy
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
        """알바 시작 메시지 전송 후 대기, 결과를 전송합니다."""
        import asyncio
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}"))
            return

        job = get_random_job(npc_name)
        if not job:
            await ctx.send(ansi(f"  {C.RED}✖ {npc.get('name', npc_name)}은(는) 알바가 없슴미댜.{C.R}"))
            return

        energy_cost = job.get("energy_cost", 20)
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        diff_label = DIFFICULTY_LABELS.get(job.get("difficulty", "easy"), "쉬움")
        job_type   = job.get("type", "hunt")

        from economy import Economy
        economy = Economy(self.player)

        # ── gather 유형: 인벤토리 아이템 확인 & 차감 ──────────────────
        if job_type == "gather":
            target_item  = job.get("target_item", "")
            target_count = job.get("target_count", 1)
            have = self.player.inventory.get(target_item, 0)
            if have < target_count:
                # 기력 환불
                self.player.energy = min(
                    getattr(self.player, "max_energy", 100),
                    self.player.energy + energy_cost,
                )
                from items import ALL_ITEMS
                item_name = ALL_ITEMS.get(target_item, {}).get("name", target_item)
                await ctx.send(ansi(
                    f"  {C.RED}✖ 재료가 부족함미댜! "
                    f"{item_name} {target_count}개 필요 (보유: {have}개)\n"
                    f"  기력이 환불되었슴미댜. {C.R}"
                ))
                return
            economy.remove_item(f"알바:{npc_name}", target_item, target_count)

        # ── deliver 유형: 퀘스트 아이템 인벤토리에 추가 ──────────────────
        elif job_type == "deliver":
            deliver_item      = job.get("deliver_item", "")
            deliver_item_name = job.get("deliver_item_name", deliver_item)
            target_npc        = job.get("target_npc", "")
            if deliver_item:
                economy.add_item(f"알바:{npc_name}", deliver_item, 1)

        await ctx.send(ansi(
            f"  {C.GOLD}💼 {npc['name']} 알바 시작! [{diff_label}]{C.R}\n"
            f"  {C.DARK}{job['name']} — {job.get('desc','')}{C.R}\n"
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

        # ── hunt/gather 유형: Economy를 통한 보상 지급 ─────────────────
        if job_type in ("hunt", "gather"):
            economy.pay_reward(
                source=f"알바:{npc_name}",
                gold=reward_gold,
                exp=float(reward_exp),
            )
            result_note = ""
        else:  # deliver
            # 전달형: 보상은 대상 NPC에게 전달 완료 후 지급 (여기선 안내만)
            await ctx.send(ansi(
                f"  {C.GOLD}📦 배달 아이템을 받았슴미댜!{C.R}\n"
                f"  {C.WHITE}[{deliver_item_name}]{C.R} — "
                f"**{target_npc}** 에게 전달해 주셰요.\n"
                f"  {C.DARK}전달 완료 시 보상: {reward_gold}G / EXP +{reward_exp}{C.R}"
            ))
            return

        # ── 스킬 경험치 보상 ─────────────────────────────────────────────
        if reward_skill_exp:
            skill_ranks_ref = getattr(self.player, "skill_ranks", {})
            skill_exp_ref   = getattr(self.player, "skill_exp", {})
            for skill_id, amount in reward_skill_exp.items():
                if skill_id in skill_ranks_ref:
                    skill_exp_ref[skill_id] = skill_exp_ref.get(skill_id, 0) + amount
            if not hasattr(self.player, "skill_exp"):
                self.player.skill_exp = skill_exp_ref

        # ── 보상 아이템 지급 ──────────────────────────────────────────────
        reward_item_line = ""
        if reward_item:
            economy.add_item(f"알바:{npc_name}", reward_item, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(reward_item, {}).get("name", reward_item)
            reward_item_line = f"\n  {C.WHITE}🎁 {item_name} x1{C.R}"

        # ── 결과 카드 / 텍스트 전송 ──────────────────────────────────────
        card_sent = False
        try:
            import fishing_card
            import discord
            buf  = fishing_card.generate_job_card(
                job["name"], f"완료! [{diff_label}]", reward_gold, f"EXP +{reward_exp}"
            )
            file = discord.File(buf, filename="job_result.png")
            embed = discord.Embed(
                title=f"💼 {npc['name']} 알바 완료! [{diff_label}]",
                color=EMBED_COLOR.get("npc", 0x4A7856),
            )
            embed.set_image(url="attachment://job_result.png")
            await ctx.send(embed=embed, file=file)
            card_sent = True
        except Exception:
            pass

        if not card_sent:
            lines = [
                header_box(f"💼 {npc['name']} 알바 완료! [{diff_label}]"),
                f"  {C.WHITE}{job['name']}{C.R}",
                divider(),
                f"  {C.GOLD}+{reward_gold}G{C.R}  {C.GREEN}EXP +{reward_exp}{C.R}",
            ]
            if reward_item_line:
                lines.append(reward_item_line)
            await ctx.send(ansi("\n".join(lines)))

    def list_npcs(self) -> str:
        lines = [header_box("🏘 마을 NPC 목록"), section("NPC 목록")]
        for npc_name, npc in NPC_DATA.items():
            role = npc.get("role", "???")
            loc  = npc.get("location", "???")
            lines.append(f"  {C.GOLD}{npc_name}{C.R}  {C.DARK}[{role}] {loc}{C.R}")
        lines.append(divider())
        lines.append(f"  {C.GREEN}/대화 [이름]{C.R} 으로 NPC와 대화하셰요!")
        return ansi("\n".join(lines))
