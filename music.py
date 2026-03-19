"""music.py — 마비노기식 작곡/연주 시스템"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR

NOTES = ["도", "레", "미", "파", "솔", "라", "시"]
NOTE_EMOJIS = {
    "도": "🎵", "레": "🎶", "미": "🎼",
    "파": "🎹", "솔": "🎸", "라": "🎺", "시": "🎻",
}

SONGS = [
    {"id": "forest_song", "name": "방울숲의 노래", "length": 4, "reward_gold": 100,  "reward_contrib": 5},
    {"id": "battle_hymn", "name": "전사의 찬가",   "length": 5, "reward_gold": 200,  "reward_contrib": 8},
    {"id": "love_ballad", "name": "사랑의 발라드", "length": 6, "reward_gold": 300,  "reward_contrib": 10},
    {"id": "epic_tale",   "name": "영웅의 이야기", "length": 8, "reward_gold": 500,  "reward_contrib": 15},
]

_SONG_BY_ID = {s["id"]: s for s in SONGS}


class NoteButton(discord.ui.Button):
    def __init__(self, note: str, view_ref):
        super().__init__(label=f"{NOTE_EMOJIS.get(note, '')} {note}", style=discord.ButtonStyle.secondary)
        self.note     = note
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.handle_note(interaction, self.note)


class MusicView(discord.ui.View):
    """음표 버튼 UI — 타겟 시퀀스에 맞춰 버튼 클릭."""

    def __init__(self, target_sequence: list, song: dict, player):
        super().__init__(timeout=60)
        self.target   = target_sequence
        self.song     = song
        self.player   = player
        self.entered  = []
        self._message = None

        for note in NOTES:
            self.add_item(NoteButton(note, self))

    async def handle_note(self, interaction: discord.Interaction, note: str):
        self.entered.append(note)
        idx = len(self.entered) - 1

        correct = (idx < len(self.target) and note == self.target[idx])

        if len(self.entered) >= len(self.target):
            # 채점
            matches   = sum(1 for a, b in zip(self.entered, self.target) if a == b)
            pct       = int(matches / len(self.target) * 100)
            gold_earn = int(self.song["reward_gold"] * pct / 100)
            contrib   = self.song["reward_contrib"] if pct >= 80 else 0

            self.player.gold += gold_earn
            for child in self.children:
                child.disabled = True

            try:
                from village import village_manager
                if contrib:
                    village_manager.add_contribution(contrib)
            except Exception:
                pass

            result_notes = " ".join(
                f"{'✅' if a == b else '❌'}{a}" for a, b in zip(self.entered, self.target)
            )
            embed = discord.Embed(
                title=f"🎵 {self.song['name']} — 연주 완료!",
                description=(
                    f"**정확도: {pct}%**  ({matches}/{len(self.target)})\n\n"
                    f"{result_notes}\n\n"
                    f"💰 획득 골드: **+{gold_earn:,}G**"
                    + (f"\n마을 기여도: +{contrib}" if contrib else "")
                ),
                color=0xffd700 if pct >= 80 else 0xaa6633,
            )
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        else:
            progress = " ".join(
                f"{'✅' if a == b else '❌'}{a}"
                for a, b in zip(self.entered, self.target[:len(self.entered)])
            )
            remain = len(self.target) - len(self.entered)
            embed = discord.Embed(
                title=f"🎵 {self.song['name']} 연주 중...",
                description=(
                    f"입력: {progress}\n"
                    f"남은 음표: **{remain}개**\n\n"
                    f"목표 음표 수: {len(self.target)}"
                ),
                color=0x4488cc,
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self._message:
            try:
                embed = discord.Embed(
                    title="⏰ 시간 초과",
                    description="연주 시간이 끝났슴미댜!",
                    color=0x555555,
                )
                await self._message.edit(embed=embed, view=self)
            except Exception:
                pass


class MusicEngine:
    def __init__(self, player):
        self.player = player

    async def compose(self, ctx):
        """곡 선택 임베드를 표시합니다."""
        embed = discord.Embed(
            title="🎵 작곡 & 연주",
            description="연주할 곡을 선택하세요!\n`/연주 [곡ID]` 로 연주 시작",
            color=EMBED_COLOR.get("help", 0x7B5EA7),
        )
        for song in SONGS:
            embed.add_field(
                name=f"{song['name']} (`{song['id']}`)",
                value=(
                    f"음표 {song['length']}개 | "
                    f"+{song['reward_gold']}G | "
                    f"기여도 +{song['reward_contrib']}"
                ),
                inline=False,
            )
        embed.set_footer(text="🎵 음표를 순서대로 클릭하면 점수가 계산됨미댜!")
        await ctx.send(embed=embed)

    async def perform(self, ctx, song_id: str):
        """지정한 곡을 연주합니다."""
        song = _SONG_BY_ID.get(song_id)
        if not song:
            ids = ", ".join(_SONG_BY_ID.keys())
            await ctx.send(ansi(f"  {C.RED}✖ [{song_id}]는 없는 곡임미댜! 가능한 ID: {ids}{C.R}"))
            return

        energy_cost = 10
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}){C.R}"
            ))
            return

        target   = [random.choice(NOTES) for _ in range(song["length"])]
        target_s = " ".join(f"{NOTE_EMOJIS.get(n,'')}{n}" for n in target)

        embed = discord.Embed(
            title=f"🎵 {song['name']} — 연주 시작!",
            description=(
                f"아래 음표를 **순서대로** 버튼으로 입력하셰요!\n\n"
                f"🎶 목표: **{target_s}**\n\n"
                f"⏱ 60초 안에 완성하셰요!"
            ),
            color=0x4488cc,
        )
        view = MusicView(target, song, self.player)
        msg  = await ctx.send(embed=embed, view=view)
        view._message = msg
