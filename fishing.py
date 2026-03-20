"""fishing.py — 이프 스타일 낚시 타이밍 게임"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, rank_badge, FOOTERS, GRADE_EMBED_COLOR

FISH_DB = {
    # ── Normal ──────────────────────────────────────────────────────────────
    "붕어":       {"id": "fs_carp_01",      "grade": "Normal",    "price": 5,    "size": (10, 30),   "rate": 0.45, "rank_req": "연습", "cookable": True},
    "잉어":       {"id": "fs_carp_02",      "grade": "Normal",    "price": 15,   "size": (20, 50),   "rate": 0.25, "rank_req": "연습", "cookable": True},
    "미꾸라지":   {"id": "fs_loach_01",     "grade": "Normal",    "price": 8,    "size": (8, 20),    "rate": 0.40, "rank_req": "연습", "cookable": True},
    "피라미":     {"id": "fs_minnow_01",    "grade": "Normal",    "price": 6,    "size": (5, 15),    "rate": 0.38, "rank_req": "연습", "cookable": True},
    "메기":       {"id": "fs_catfish_01",   "grade": "Normal",    "price": 20,   "size": (25, 60),   "rate": 0.22, "rank_req": "연습", "cookable": True},
    "가재":       {"id": "fs_crayfish_01",  "grade": "Normal",    "price": 12,   "size": (5, 15),    "rate": 0.30, "rank_req": "연습", "cookable": True},
    "폐타이어":   {"id": "trash_tire_01",   "grade": "Normal",    "price": 1,    "size": (0, 0),     "rate": 0.02, "rank_req": "연습", "cookable": False},
    # ── Rare ────────────────────────────────────────────────────────────────
    "연어":       {"id": "fs_salmon_01",    "grade": "Rare",      "price": 40,   "size": (40, 80),   "rate": 0.18, "rank_req": "F",    "cookable": True},
    "장어":       {"id": "fs_eel_01",       "grade": "Rare",      "price": 60,   "size": (30, 70),   "rate": 0.08, "rank_req": "E",    "cookable": True},
    "참치":       {"id": "fs_tuna_01",      "grade": "Rare",      "price": 80,   "size": (60, 200),  "rate": 0.12, "rank_req": "D",    "cookable": True},
    "광어":       {"id": "fs_flatfish_01",  "grade": "Rare",      "price": 70,   "size": (30, 80),   "rate": 0.14, "rank_req": "D",    "cookable": True},
    "고등어":     {"id": "fs_mackerel_01",  "grade": "Rare",      "price": 50,   "size": (25, 50),   "rate": 0.16, "rank_req": "E",    "cookable": True},
    "꽃게":       {"id": "fs_crab_01",      "grade": "Rare",      "price": 65,   "size": (10, 25),   "rate": 0.10, "rank_req": "D",    "cookable": True},
    "문어":       {"id": "fs_octopus_01",   "grade": "Rare",      "price": 90,   "size": (20, 80),   "rate": 0.08, "rank_req": "C",    "cookable": True},
    # ── Epic ────────────────────────────────────────────────────────────────
    "복어":       {"id": "fs_puffer_01",    "grade": "Epic",      "price": 200,  "size": (15, 40),   "rate": 0.04, "rank_req": "B",    "cookable": True},
    "상어":       {"id": "fs_shark_01",     "grade": "Epic",      "price": 350,  "size": (100, 400), "rate": 0.02, "rank_req": "A",    "cookable": True},
    "대왕오징어": {"id": "fs_squid_01",     "grade": "Epic",      "price": 280,  "size": (50, 300),  "rate": 0.03, "rank_req": "9",    "cookable": True},
    # ── Legendary ───────────────────────────────────────────────────────────
    "황금잉어":   {"id": "fs_gold_carp_01", "grade": "Legendary", "price": 500,  "size": (30, 80),   "rate": 0.008,"rank_req": "8",    "cookable": True},
    "황금장어":   {"id": "fs_gold_eel_01",  "grade": "Legendary", "price": 300,  "size": (60, 120),  "rate": 0.02, "rank_req": "B",    "cookable": True},
    "용의 물고기":{"id": "fs_dragon_01",    "grade": "Legendary", "price": 2000, "size": (80, 200),  "rate": 0.003,"rank_req": "5",    "cookable": True},
    "심해어":     {"id": "fs_deep_01",      "grade": "Legendary", "price": 1500, "size": (40, 150),  "rate": 0.005,"rank_req": "7",    "cookable": True},
}

FISH_GUIDE = {
    "방울숲 강": {
        "desc": "조용한 방울숲 근처의 작은 강.",
        "fish": ["붕어", "잉어", "연어", "미꾸라지", "피라미"],
        "energy_cost": 10,
        "fee_rate": 0.20,
    },
    "소금광산 지하호수": {
        "desc": "소금 광산 깊은 곳의 지하호수.",
        "fish": ["잉어", "연어", "장어", "황금장어", "메기"],
        "energy_cost": 20,
        "fee_rate": 0.15,
    },
    "고요한 연못": {
        "desc": "마을 근처의 고요하고 얕은 연못. 초보자 낚시터.",
        "fish": ["붕어", "잉어", "미꾸라지", "피라미", "가재", "폐타이어"],
        "energy_cost": 8,
        "fee_rate": 0.25,
    },
    "은빛 해안": {
        "desc": "은빛 파도가 치는 바닷가 낚시터. 바다 물고기가 많다.",
        "fish": ["참치", "광어", "고등어", "꽃게", "문어", "가재"],
        "energy_cost": 25,
        "fee_rate": 0.18,
    },
    "용암 호수": {
        "desc": "화산지대 근처의 뜨거운 용암 호수. 특이한 물고기가 서식한다.",
        "fish": ["복어", "상어", "심해어", "장어", "문어"],
        "energy_cost": 35,
        "fee_rate": 0.12,
    },
    "요정의 샘": {
        "desc": "요정들이 사는 신비로운 샘. 전설 등급 물고기가 출현한다.",
        "fish": ["황금잉어", "용의 물고기", "황금장어", "복어"],
        "energy_cost": 40,
        "fee_rate": 0.10,
    },
    "폭풍 부두": {
        "desc": "거센 폭풍이 몰아치는 부두. 위험하지만 Epic 물고기가 풍부하다.",
        "fish": ["상어", "대왕오징어", "복어", "참치", "광어"],
        "energy_cost": 30,
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
        from ui_theme import spider_scene
        embed = discord.Embed(
            title="🎣 낚시 시작!",
            description=(
                f"{spider_scene('fishing_wait')}\n"
                f"**{self.spot_name}** 에 낚싯줄을 던졌슴미댜!\n\n"
                "찌가 움직이면 **낚싯줄 당기기** 버튼을 누르셰요!"
            ),
            color=0x1a6ba0,
        )
        embed.set_footer(text="⏱ 70초 안에 반응하셰요!")
        msg = await channel_or_ctx.send(embed=embed, view=self)
        self._message = msg
        self._bite_task = asyncio.create_task(self._schedule_bite())

    async def _schedule_bite(self):
        """다양한 낚시 패턴을 랜덤으로 실행"""
        try:
            patterns = ["normal", "normal", "slow", "fake_then_real", "fake_then_real", "double_fake", "instant"]
            pattern = random.choice(patterns)

            if pattern == "normal":
                await asyncio.sleep(random.uniform(3.0, 7.0))
                await self._trigger_bite()
            elif pattern == "slow":
                await asyncio.sleep(random.uniform(8.0, 14.0))
                await self._trigger_bite()
            elif pattern == "fake_then_real":
                await asyncio.sleep(random.uniform(2.0, 5.0))
                if self.state != "waiting":
                    return
                fake_msgs = [
                    "🕷️ ...! 찌가 살짝 움직인 것 같슴미댜...? 아닌가...?",
                    "🕷️ 물결이 일었슴미댜...! ...아, 바람이었슴미댜.",
                    "🕷️ 뭔가 스친 느낌...! ...물풀이었슴미댜 ㅠ",
                    "🕷️ 철썩! ...돌멩이가 떨어진 것 같슴미댜...",
                ]
                if self._message:
                    fake_embed = discord.Embed(
                        title="🎣 낚시 중...",
                        description=random.choice(fake_msgs),
                        color=0x1a6ba0,
                    )
                    fake_embed.set_footer(text="⏱ 70초 안에 반응하셰요!")
                    await self._message.edit(embed=fake_embed)
                await asyncio.sleep(random.uniform(3.0, 8.0))
                await self._trigger_bite()
            elif pattern == "double_fake":
                for _ in range(2):
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    if self.state != "waiting":
                        return
                    fake_msgs = ["🕷️ ...찌가! ...아, 아니었슴미댜;;", "🕷️ 또 움직...인 줄 알았슴미댜..."]
                    if self._message:
                        fake_embed = discord.Embed(
                            title="🎣 낚시 중...",
                            description=random.choice(fake_msgs),
                            color=0x1a6ba0,
                        )
                        fake_embed.set_footer(text="⏱ 70초 안에 반응하셰요!")
                        await self._message.edit(embed=fake_embed)
                await asyncio.sleep(random.uniform(2.0, 6.0))
                await self._trigger_bite()
            elif pattern == "instant":
                await asyncio.sleep(random.uniform(1.0, 2.0))
                await self._trigger_bite()
        except asyncio.CancelledError:
            pass

    async def _trigger_bite(self):
        """실제 바이트 상태로 전환"""
        if self.state != "waiting":
            return
        self.state = "bite"
        if self._message:
            from ui_theme import spider_scene
            bite_msgs = [
                f"{spider_scene('fishing_bite')}\n🎣❗ **찌가 움직였슴미댜!! 지금 당기셰요!!** 🕷️💨",
                "🎣🔥 **입질임미댜!!! 빨리빨리!!** 🕷️✨",
                "🎣💥 **물고기댜!! 당기라고오오!!** 🕸️",
            ]
            embed = discord.Embed(
                title="❗❗❗ 앗!! 찌에 느낌이!!!",
                description=random.choice(bite_msgs),
                color=0xff2200,
            )
            embed.set_footer(text="⚡ 3초 안에 버튼을 눌러야 함미댜!")
            await self._message.edit(embed=embed, view=self)

        # 타임아웃 — 3초 안에 안 누르면 놓침
        await asyncio.sleep(3.0)
        if self.state == "bite":
            self.state = "done"
            self._disable_buttons()
            if self._message:
                embed = discord.Embed(
                    title="🎣 낚시 실패",
                    description="🕷️💧 물고기가 미끼만 먹고 도망갔슴미댜... 다음엔 더 빨리 당기셰요!",
                    color=0x884444,
                )
                await self._message.edit(embed=embed, view=self)
            self.stop()

    async def _handle_catch(self, interaction: discord.Interaction):
        """물고기를 잡았을 때의 처리 로직"""
        if self._bite_task and not self._bite_task.done():
            self._bite_task.cancel()

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

        try:
            from collection import collection_manager
            is_new, total = collection_manager.register("낚시", fish_id, caught_name, grade, size_cm)
            if is_new and self._message:
                await self._message.channel.send(
                    f"📖✨ **새로운 도감 등록!** 🎣 `{caught_name}` 이(가) 낚시 도감에 추가됐슴미댜!"
                )
        except Exception:
            pass

        try:
            from achievements import achievement_manager
            achievement_manager.increment("fish_caught", 1)
        except Exception:
            pass

        FLAVOR_TEXT = {
            "Normal":    "평범한 녀석이지만 기분은 좋다!",
            "Rare":      "오! 꽤 귀한 녀석인데?!",
            "Epic":      "대박!! 이건 정말 레어한 녀석이다!!",
            "Legendary": "전설의 물고기?! 이건 대단한 발견이다!!!",
        }
        flavor = FLAVOR_TEXT.get(grade, "")
        card_sent = False
        if added and hi > 0:
            try:
                import fishing_card
                from ui_theme import spider_scene
                buf  = fishing_card.generate_fishing_card(
                    caught_name, size_cm, price, fee, 0, net, grade=grade
                )
                file = discord.File(buf, filename="fishing_result.png")
                embed = discord.Embed(
                    title=f"🎣 {fishing_card.GRADE_TITLE_TEXT.get(grade, '🕷️ {name}을(를) 낚았슴미댜!').format(name=caught_name)}",
                    description=f"{spider_scene('fishing_catch')}\n{flavor}",
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
                from ui_theme import spider_scene
                desc = (
                    f"{spider_scene('fishing_catch')}\n"
                    f"**{grade_mark} {caught_name}** 을(를) 낚았슴미댜!\n\n"
                    f"📏 크기: **{size_cm} cm**\n"
                    f"💰 {price:,}G  수수료 -{fee:,}G  순수익 {net:,}G"
                )
                if rank_msg:
                    desc += f"\n\n{rank_msg}"
                embed = discord.Embed(
                    title=f"🎣 와! {caught_name}을(를) 낚았다!! [{grade}]",
                    description=f"{desc}\n\n{flavor}" if flavor else desc,
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

    # ① 항상 보이는 "당기기" 버튼
    @discord.ui.button(label="🎣 낚싯줄 당기기!", style=discord.ButtonStyle.primary, row=0)
    async def pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.state == "waiting":
            self.state = "done"
            self._disable_buttons()
            await interaction.response.edit_message(
                content="🕷️💦 앗! 너무 일찍 당겼슴미댜... 물고기가 놀라서 도망갔슴미댜!",
                view=self,
            )
            self.stop()
        elif self.state == "bite":
            self.state = "done"
            self._disable_buttons()
            await self._handle_catch(interaction)
            self.stop()
        elif self.state == "done":
            await interaction.response.send_message("이미 끝났슴미댜!", ephemeral=True)

    # ② 보조 버튼 — waiting 상태에서 마우스 위치 유지용
    @discord.ui.button(label="🕸️ 기다리는 중...", style=discord.ButtonStyle.secondary, row=0)
    async def wait_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.state == "waiting":
            await interaction.response.send_message(
                "🕷️ 조용히 기다리는 중임미댜... 찌가 움직이면 당기기를 누르셰요!",
                ephemeral=True,
            )
        elif self.state == "bite":
            self.state = "done"
            self._disable_buttons()
            await self._handle_catch(interaction)
            self.stop()
        elif self.state == "done":
            await interaction.response.send_message("이미 끝났슴미댜!", ephemeral=True)

    @discord.ui.button(label="🚫 그만하기", style=discord.ButtonStyle.danger, row=1)
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
