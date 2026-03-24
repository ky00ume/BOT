"""rest.py — 백그라운드 기력 회복 시스템"""
import asyncio
import time
import discord


class RestEngine:
    def __init__(self, player, channel=None):
        self.player = player
        self.resting = False
        self._task = None
        self._start_time = None
        self._start_energy = None
        self._channel = channel

    def get_recovery_per_tick(self) -> int:
        """랭크별 2초당 회복량"""
        rank = self.player.skill_ranks.get("rest", "연습")
        recovery_table = {
            "연습": 1, "F": 1, "E": 1,
            "D": 2, "C": 2, "B": 2,
            "A": 3, "9": 3,
            "8": 4, "7": 4, "6": 5,
            "5": 5, "4": 6, "3": 7,
            "2": 8, "1": 10,
        }
        return recovery_table.get(rank, 1)

    async def start_rest(self):
        """휴식 루프를 백그라운드 태스크로 시작합니다."""
        if self.resting:
            return
        self.resting = True
        self._start_time = time.time()
        self._start_energy = self.player.energy
        self._task = asyncio.create_task(self._rest_loop())

    async def _rest_loop(self):
        """2초마다 기력을 회복합니다."""
        try:
            while self.resting:
                await asyncio.sleep(2)
                recovery = self.get_recovery_per_tick()
                self.player.energy = min(
                    self.player.max_energy,
                    self.player.energy + recovery,
                )
                if self.player.energy >= self.player.max_energy:
                    self.resting = False
                    await self._send_complete_card()
                    break
        except asyncio.CancelledError:
            self.resting = False

    async def _send_complete_card(self):
        """휴식 완료 시 PIL 카드를 채널에 전송합니다."""
        if not self._channel:
            return

        elapsed = time.time() - self._start_time if self._start_time is not None else 0.0
        recovered = self.player.energy - self._start_energy if self._start_energy is not None else 0

        embed = discord.Embed(
            title="💤 휴식 완료!",
            color=0x7B68EE,
        )

        try:
            import fishing_card
            buf = fishing_card.generate_rest_card(
                recovered=recovered,
                current_energy=self.player.energy,
                max_energy=self.player.max_energy,
                elapsed_sec=elapsed,
            )
            file = discord.File(buf, filename="rest_result.png")
            embed.set_image(url="attachment://rest_result.png")

            rank_msg = self.player.train_skill("rest", 20.0)
            if rank_msg:
                embed.set_footer(text=rank_msg)

            await self._channel.send(embed=embed, file=file)
        except Exception:
            rank_msg = self.player.train_skill("rest", 20.0)
            embed.description = (
                f"기력이 완전히 회복됐슴미댜!\n"
                f"회복량: **+{recovered} EN**  |  "
                f"현재기력: **{self.player.energy}/{self.player.max_energy}**"
            )
            if rank_msg:
                embed.set_footer(text=rank_msg)
            await self._channel.send(embed=embed)

        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception:
            pass

    def stop_rest(self):
        """휴식을 강제 종료합니다."""
        if self._task and not self._task.done():
            self._task.cancel()
        self.resting = False
