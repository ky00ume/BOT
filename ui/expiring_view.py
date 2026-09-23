import logging

import discord

logger = logging.getLogger(__name__)


class ExpiringView(discord.ui.View):
    """A game view that removes stale components instead of leaving dead buttons behind."""

    def __init__(self, *, timeout: float | None):
        super().__init__(timeout=timeout)
        self._message: discord.Message | None = None

    def bind_message(self, message):
        self._message = message
        return self

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Any interaction proves which message currently owns this view.
        self._message = interaction.message
        return True

    async def on_timeout(self):
        if not self._message:
            return
        try:
            # Expired game windows should look closed, not deceptively clickable.
            await self._message.edit(view=None)
        except (discord.NotFound, discord.Forbidden):
            pass
        except Exception:
            logger.warning("expired view cleanup failed", exc_info=True)
