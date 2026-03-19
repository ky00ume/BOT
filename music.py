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

MAX_MELODY_LEN = 32
VALID_NOTES_SET = set(NOTES)


def parse_melody(melody_str: str) -> list | None:
    """한글 음계 문자열을 파싱합니다. 유효하지 않으면 None 반환."""
    # 공백으로 구분된 경우
    if " " in melody_str:
        tokens = melody_str.split()
    else:
        # 글자 단위로 분리 (도/레/미/파/솔/라/시 각 1글자)
        tokens = list(melody_str)
    if not tokens or len(tokens) > MAX_MELODY_LEN:
        return None
    for t in tokens:
        if t not in VALID_NOTES_SET:
            return None
    return tokens


class NoteButton(discord.ui.Button):
    def __init__(self, note: str, view_ref):
        super().__init__(label=note, style=discord.ButtonStyle.secondary)
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
                f"{'✅' if a == b else '❌'} {a}" for a, b in zip(self.entered, self.target)
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
                f"{'✅' if a == b else '❌'} {a}"
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
            description="연주할 곡을 선택하세요!\n`/연주 [곡ID]` 로 연주 시작\n`/작곡 [곡이름] [멜로디]` 로 악보 저장",
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

    async def save_composition(self, ctx, title: str, melody_str: str):
        """악보를 저장합니다."""
        notes = parse_melody(melody_str)
        if notes is None:
            valid = "/".join(NOTES)
            await ctx.send(ansi(
                f"  {C.RED}✖ 멜로디가 잘못됐슴미댜!\n"
                f"  유효한 음표: {valid}\n"
                f"  최대 {MAX_MELODY_LEN}음표까지 입력 가능임미댜!{C.R}"
            ))
            return
        from database import save_sheet_music
        save_sheet_music(0, title, " ".join(notes))
        await ctx.send(ansi(
            f"  {C.GREEN}✔ 악보 [{title}] 저장 완료!{C.R}\n"
            f"  {C.WHITE}멜로디:{C.R} {' '.join(notes)} ({len(notes)}음표)"
        ))

    async def show_sheet_list(self, ctx):
        """저장된 악보 목록을 표시합니다."""
        from database import load_sheet_music_list
        sheets = load_sheet_music_list(0)
        if not sheets:
            await ctx.send(ansi(f"  {C.DARK}저장된 악보가 없슴미댜.{C.R}"))
            return
        lines = [header_box("📜 악보 목록")]
        for s in sheets:
            notes_preview = s["melody"][:20] + ("..." if len(s["melody"]) > 20 else "")
            lines.append(f"  {C.WHITE}[{s['id']}] {s['title']}{C.R}  {C.DARK}{notes_preview}{C.R}")
        lines.append(divider())
        lines.append(f"  {C.GREEN}/연주 [곡이름]{C.R} 으로 연주!")
        await ctx.send(ansi("\n".join(lines)))

    async def delete_sheet(self, ctx, title: str):
        """악보를 삭제합니다."""
        from database import delete_sheet_music
        ok = delete_sheet_music(0, title)
        if ok:
            await ctx.send(ansi(f"  {C.GREEN}✔ 악보 [{title}] 삭제 완료!{C.R}"))
        else:
            await ctx.send(ansi(f"  {C.RED}✖ 악보 [{title}]을(를) 찾을 수 없슴미댜!{C.R}"))

    async def perform(self, ctx, song_id: str):
        """지정한 곡을 연주합니다. 프리셋 곡 또는 유저 작곡 곡 지원."""
        # 1. 프리셋 곡 확인
        song = _SONG_BY_ID.get(song_id)
        user_melody = None

        if not song:
            # 2. 유저 작곡 악보 확인 (ID 숫자 또는 제목)
            from database import load_sheet_music
            sheet = load_sheet_music(0, song_id)
            if not sheet:
                ids = ", ".join(_SONG_BY_ID.keys())
                await ctx.send(ansi(
                    f"  {C.RED}✖ [{song_id}]는 없는 곡임미댜!\n"
                    f"  프리셋 ID: {ids}\n"
                    f"  또는 /악보목록 에서 저장된 악보를 확인하셰요!{C.R}"
                ))
                return
            user_melody = sheet["melody"].split()
            # 유저 악보는 가상 song dict 사용
            song = {
                "id": song_id,
                "name": sheet["title"],
                "length": len(user_melody),
                "reward_gold": min(50 * len(user_melody), 500),
                "reward_contrib": min(len(user_melody), 10),
            }

        energy_cost = 10
        if not self.player.consume_energy(energy_cost):
            await ctx.send(ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}){C.R}"
            ))
            return

        if user_melody:
            target = user_melody
        else:
            target = [random.choice(NOTES) for _ in range(song["length"])]

        target_s = " ".join(target)

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
