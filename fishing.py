"""fishing.py — 이프 스타일 낚시 타이밍 게임"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, rank_badge, FOOTERS, GRADE_EMBED_COLOR

FISH_DB = {
    "붕어":     {"id": "fs_carp_01",     "grade": "Normal",    "price": 5,   "size": (10, 30),  "rate": 0.45, "rank_req": "연습", "cookable": True},
    "잉어":     {"id": "fs_carp_02",     "grade": "Normal",    "price": 15,  "size": (20, 50),  "rate": 0.25, "rank_req": "연습", "cookable": True},
    "연어":     {"id": "fs_salmon_01",   "grade": "Rare",      "price": 40,  "size": (40, 80),  "rate": 0.18, "rank_req": "F",    "cookable": True},
    "장어":     {"id": "fs_eel_01",      "grade": "Rare",      "price": 60,  "size": (30, 70),  "rate": 0.08, "rank_req": "E",    "cookable": True},
    "황금장어": {"id": "fs_gold_eel_01", "grade": "Legendary", "price": 300, "size": (60, 120), "rate": 0.02, "rank_req": "B",    "cookable": True},
    "폐타이어": {"id": "trash_tire_01",  "grade": "Normal",    "price": 1,   "size": (0, 0),    "rate": 0.02, "rank_req": "연습", "cookable": False},
}

FISH_GUIDE = {
    "방울숲 강": {
        "desc": "조용한 방울숲 근처의 작은 강.",
        "fish": ["붕어", "잉어", "연어"],
        "energy_cost": 10,
        "fee_rate": 0.20,
    },
    "소금광산 지하호수": {
        "desc": "소금 광산 깊은 곳의 지하호수.",
        "fish": ["잉어", "연어", "장어", "황금장어"],
        "energy_cost": 20,
        "fee_rate": 0.15,
    },
}

RANK_ORDER_FISH = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    if rank_a not in RANK_ORDER_FISH or rank_b not in RANK_ORDER_FISH:
        return False
    return RANK_ORDER_FISH.index(rank_a) >= RANK_ORDER_FISH.index(rank_b)


class FishingView(discord.ui.View):
    def __init__(self, player, spot_name: str, spot_data: dict, fish_db_filtered: dict):
        super().__init__(timeout=70)
        self.player           = player
        self.spot_name        = spot_name
        self.spot_data        = spot_data
        self.fish_db_filtered = fish_db_filtered
        self.state            = "waiting"   # "waiting" | "bite" | "done"
        self.result           = None
        self._bite_task       = None
        self._message         = None

    def _disable_buttons(self):
        for child in self.children:
            child.disabled = True

    async def start(self, channel_or_ctx):
        embed = discord.Embed(
            title="🎣 낚시 시작!",
            description=(
                f"**{self.spot_name}** 에 낚싯줄을 던졌슴미댜!\n\n"
                "찌가 움직이면 **낚싯줄 당기기** 버튼을 누르셰요!"
            ),
            color=0x1a6ba0,
        )
        embed.set_footer(text="⏱ 70초 안에 반응하셰요!")
        msg = await channel_or_ctx.send(embed=embed, view=self)
        self._message = msg
        self._bite_task = asyncio.create_task(self._wait_and_bite())

    async def _wait_and_bite(self):
        try:
            await asyncio.sleep(random.uniform(5, 15))

            fake_count = random.randint(0, 2)
            for _ in range(fake_count):
                if self.state != "waiting":
                    return
                embed = discord.Embed(
                    title="🎣 낚시 중...",
                    description="찌가 살짝 움직인 것 같슴미댜...\n아직 아닌 것 같슴미댜.",
                    color=0x888888,
                )
                if self._message:
                    await self._message.edit(embed=embed, view=self)
                await asyncio.sleep(random.uniform(3, 8))

            if self.state != "waiting":
                return

            self.state = "bite"
            embed = discord.Embed(
                title="❗❗❗ 앗!! 찌에 느낌이!!!",
                description="**지금이다!! 낚싯줄 당기기!!**",
                color=0xff2200,
            )
            embed.set_footer(text="⚡ 10초 안에 버튼을 눌러야 함미댜!")
            if self._message:
                await self._message.edit(embed=embed, view=self)

            await asyncio.sleep(10)
            if self.state == "bite":
                self.state = "done"
                self._disable_buttons()
                embed = discord.Embed(
                    title="🎣 낚시 실패",
                    description="물고기를 놓쳤슴미댜! 다음엔 빠르게 반응하셰요~",
                    color=0x884444,
                )
                if self._message:
                    await self._message.edit(embed=embed, view=self)
                self.stop()
        except asyncio.CancelledError:
            pass

    @discord.ui.button(label="🎣 낚싯줄 당기기", style=discord.ButtonStyle.primary)
    async def pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.state == "waiting":
            await interaction.response.send_message(
                "아무것도 없슴미댜... 조금 더 기다려 보셰요!", ephemeral=True
            )
            return

        if self.state == "bite":
            self.state = "done"
            if self._bite_task and not self._bite_task.done():
                self._bite_task.cancel()
            self._disable_buttons()

            player   = self.player
            spot     = self.spot_data
            fee_rate = spot.get("fee_rate", 0.20)

            total_rate = sum(f["rate"] for f in self.fish_db_filtered.values())
            roll = random.uniform(0, total_rate)
            cumulative  = 0.0
            caught_name = None
            caught_data = None
            for name, data in self.fish_db_filtered.items():
                cumulative += data["rate"]
                if roll <= cumulative:
                    caught_name = name
                    caught_data = data
                    break
            if not caught_name:
                caught_name, caught_data = list(self.fish_db_filtered.items())[-1]

            fish_id  = caught_data["id"]
            grade    = caught_data["grade"]
            lo, hi   = caught_data.get("size", (10, 30))
            size_cm  = round(random.uniform(lo, hi), 1) if hi > 0 else 0.0
            price    = caught_data["price"]
            fee      = int(price * fee_rate)
            net      = price - fee

            added    = player.add_item(fish_id)
            rank_msg = player.train_skill("fishing", 15.0)

            try:
                from village import village_manager
                village_manager.add_contribution(1, "fishing")
            except Exception:
                pass

            try:
                from bulletin import weekly_fishing
                weekly_fishing.add_catch(player.name, caught_name, size_cm)
            except Exception:
                pass

            # PIL 카드
            card_sent = False
            if added and hi > 0:
                try:
                    import fishing_card
                    buf  = fishing_card.generate_fishing_card(
                        caught_name, size_cm, price, fee, 0, net, grade=grade
                    )
                    file = discord.File(buf, filename="fishing_result.png")
                    embed = discord.Embed(
                        title=f"🎣 와! {caught_name}을(를) 낚았슴미댜!!",
                        color=GRADE_EMBED_COLOR.get(grade, 0x00aa44),
                    )
                    embed.set_image(url="attachment://fishing_result.png")
                    footer_parts = [f"📍 {self.spot_name}", f"{grade} 등급"]
                    if rank_msg:
                        footer_parts.append(rank_msg)
                    embed.set_footer(text="  |  ".join(footer_parts))
                    await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
                    card_sent = True
                except Exception:
                    pass

            if not card_sent:
                grade_mark = {"Normal": "⚬", "Rare": "◆", "Epic": "❖", "Legendary": "✦"}.get(grade, "⚬")
                embed_color = GRADE_EMBED_COLOR.get(grade, 0x00aa44)
                if added:
                    desc = (
                        f"**{grade_mark} {caught_name}** 을(를) 낚았슴미댜!\n\n"
                        f"📏 크기: **{size_cm} cm**\n"
                        f"💰 {price:,}G  수수료 -{fee:,}G  순수익 {net:,}G"
                    )
                    if rank_msg:
                        desc += f"\n\n{rank_msg}"
                    embed = discord.Embed(
                        title=f"🎣 와! {caught_name}을(를) 낚았슴미댜!!",
                        description=desc,
                        color=embed_color,
                    )
                    embed.set_footer(text=f"📍 {self.spot_name}  |  {grade} 등급")
                else:
                    embed = discord.Embed(
                        title="🎣 낚시 성공... but",
                        description=f"**{caught_name}** 을(를) 낚았지만 인벤토리가 가득 차서 놓쳤슴미댜!",
                        color=GRADE_EMBED_COLOR.get(grade, 0xaa6600),
                    )
                await interaction.response.edit_message(embed=embed, view=self)

            self.stop()
            return

        if self.state == "done":
            await interaction.response.send_message("이미 끝났슴미댜!", ephemeral=True)

    @discord.ui.button(label="🚫 그만하기", style=discord.ButtonStyle.secondary)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.state == "done":
            await interaction.response.send_message("이미 끝났슴미댜!", ephemeral=True)
            return

        self.state = "done"
        if self._bite_task and not self._bite_task.done():
            self._bite_task.cancel()
        self._disable_buttons()

        refund = self.spot_data.get("energy_cost", 10) // 2
        self.player.energy = min(self.player.max_energy, self.player.energy + refund)

        embed = discord.Embed(
            title="🎣 낚시 종료",
            description=f"낚시를 그만했슴미댜.\n기력 **+{refund}** 일부 환불됐슴미댜.",
            color=0x888888,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        if self.state != "done":
            self.state = "done"
            self._disable_buttons()
            if self._message:
                try:
                    embed = discord.Embed(
                        title="⏰ 시간 초과",
                        description="낚시 시간이 끝났슴미댜!",
                        color=0x555555,
                    )
                    await self._message.edit(embed=embed, view=self)
                except Exception:
                    pass


class FishingEngine:
    def __init__(self, player):
        self.player       = player
        self.current_spot = "방울숲 강"

    def set_spot(self, spot_name: str):
        if spot_name in FISH_GUIDE:
            self.current_spot = spot_name

    async def fish(self, ctx):
        spot_name   = self.current_spot
        spot        = FISH_GUIDE.get(spot_name, list(FISH_GUIDE.values())[0])
        energy_cost = spot.get("energy_cost", 10)

        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            ))
            return

        rank = self.player.skill_ranks.get("fishing", "연습")
        fish_names = spot.get("fish", [])
        fish_db_filtered = {
            name: FISH_DB[name]
            for name in fish_names
            if name in FISH_DB and _rank_gte(rank, FISH_DB[name].get("rank_req", "연습"))
        }
        if not fish_db_filtered:
            fish_db_filtered = {name: FISH_DB[name] for name in fish_names if name in FISH_DB}

        view = FishingView(self.player, spot_name, spot, fish_db_filtered)
        await view.start(ctx)

    def show_fish_guide(self) -> str:
        rank  = self.player.skill_ranks.get("fishing", "연습")
        lines = [header_box("🎣 낚시 도감"), "  낚시터 & 물고기"]

        for spot_name, spot in FISH_GUIDE.items():
            lines.append(f"\n  {C.GOLD}[{spot_name}]{C.R}")
            lines.append(f"    {C.DARK}{spot['desc']}{C.R}")
            lines.append(f"    {C.RED}기력 -{spot['energy_cost']}{C.R}  수수료 {int(spot['fee_rate']*100)}%")
            for fish_name in spot.get("fish", []):
                data = FISH_DB.get(fish_name)
                if not data:
                    continue
                rr       = data.get("rank_req", "연습")
                unlocked = _rank_gte(rank, rr)
                badge    = rank_badge(rr)
                avail    = f"{C.GREEN}[가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"
                pct      = int(data["rate"] * 100)
                grade_m  = {"Normal": "⚬", "Rare": "◆", "Epic": "❖", "Legendary": "✦"}.get(data["grade"], "⚬")
                lines.append(
                    f"    {avail} {badge} {grade_m} {C.WHITE}{fish_name}{C.R}  "
                    f"{C.DARK}확률 {pct}%  {data['price']}G{C.R}"
                )

        lines.append(divider())
        lines.append(f"  {C.GREEN}/낚시{C.R} 로 낚시하셰요!")
        return ansi("\n".join(lines))
