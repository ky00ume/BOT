from __future__ import annotations

import discord
from discord.ui import Button, View


class GatherProgressView(View):
    """Controls one visible directed-gathering interaction."""
    def __init__(self, *, actor_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.actor_id = actor_id
        self.cancelled = False
        stop = Button(label="그만하기", style=discord.ButtonStyle.danger, custom_id="gather_goal_stop")
        stop.callback = self._stop
        self.add_item(stop)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.actor_id:
            await interaction.response.send_message("이 채집을 시작한 사람이 조작할 수 있슴미댜.", ephemeral=True)
            return False
        return True

    async def _stop(self, interaction: discord.Interaction):
        self.cancelled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

    def should_stop(self) -> bool:
        return self.cancelled
