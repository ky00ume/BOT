import random
from database import NPC_DATA
from ui_theme import C, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS


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

        job = npc.get("job")
        if job:
            lines.append(f"\n  {C.GOLD}▸ 알바{C.R}: {C.WHITE}{job['name']}{C.R}")
            lines.append(f"    {C.DARK}보상: {job['reward_gold']}G / EXP+{job['reward_exp']} / 기력 -{job['energy_cost']}{C.R}")
            lines.append(f"  {C.GREEN}/알바 {npc['name']}{C.R} 으로 알바 가능")

        return ansi("\n".join(lines))

    def start_job(self, npc_name: str) -> str:
        npc = NPC_DATA.get(npc_name)
        if not npc:
            return ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜.{C.R}")

        job = npc.get("job")
        if not job:
            return ansi(f"  {C.RED}✖ {npc['name']}은(는) 알바가 없슴미댜.{C.R}")

        energy_cost = job.get("energy_cost", 20)
        if not self.player.consume_energy(energy_cost):
            return ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            )

        reward_gold = job.get("reward_gold", 100)
        reward_exp  = job.get("reward_exp",  10)
        self.player.gold += reward_gold
        self.player.exp = getattr(self.player, "exp", 0.0) + reward_exp

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

        job = npc.get("job")
        if not job:
            await ctx.send(ansi(f"  {C.RED}✖ {npc['name']}은(는) 알바가 없슴미댜.{C.R}"))
            return

        energy_cost = job.get("energy_cost", 20)
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        await ctx.send(ansi(
            f"  {C.GOLD}💼 {npc['name']} 알바 시작!{C.R}\n"
            f"  {C.DARK}{job['name']} — {job.get('desc','')}{C.R}\n"
            f"  {C.RED}기력 -{energy_cost}{C.R}  ⏱ 잠시 기다려 주셰요..."
        ))

        await asyncio.sleep(3)

        reward_gold = job.get("reward_gold", 100)
        reward_exp  = job.get("reward_exp",  10)

        # 마을 기여도
        try:
            from village import village_manager
            village_manager.add_contribution(5, "job")
        except Exception:
            pass

        self.player.gold += reward_gold
        self.player.exp = getattr(self.player, "exp", 0.0) + reward_exp

        # PIL 카드 시도
        card_sent = False
        try:
            import fishing_card
            import discord
            buf  = fishing_card.generate_job_card(
                job["name"], "완료!", reward_gold, f"EXP +{reward_exp}"
            )
            file = discord.File(buf, filename="job_result.png")
            embed = discord.Embed(title=f"💼 {npc['name']} 알바 완료!", color=EMBED_COLOR.get("npc", 0x4A7856))
            embed.set_image(url="attachment://job_result.png")
            await ctx.send(embed=embed, file=file)
            card_sent = True
        except Exception:
            pass

        if not card_sent:
            lines = [
                header_box(f"💼 {npc['name']} 알바 완료!"),
                f"  {C.WHITE}{job['name']}{C.R}",
                divider(),
                f"  {C.GOLD}+{reward_gold}G{C.R}  {C.GREEN}EXP +{reward_exp}{C.R}",
            ]
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
