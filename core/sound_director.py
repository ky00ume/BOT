"""Discord voice sound-effects director for game activities.

Game systems emit semantic cue names; this module alone owns Discord voice playback.
Missing assets or a disconnected voice session are intentional no-ops.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

import discord


class SoundDirector:
    def __init__(self, *, asset_root: Path | None = None, rng=None):
        self.asset_root = asset_root or Path(__file__).resolve().parents[1] / "assets" / "audio"
        self.rng = rng or random
        self.voice_client: discord.VoiceClient | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    async def join(self, channel: discord.VoiceChannel) -> None:
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
            return
        self.voice_client = await channel.connect()

    async def leave(self) -> None:
        if self.voice_client:
            try:
                await self.voice_client.disconnect(force=False)
            finally:
                self.voice_client = None

    def _files(self, cue: str) -> list[Path]:
        cue_dir = self.asset_root / cue.replace(".", "/")
        if not cue_dir.exists():
            return []
        return [p for p in cue_dir.iterdir() if p.suffix.lower() in {".mp3", ".ogg", ".wav", ".flac", ".m4a"}]

    def cue(self, cue: str, *, volume: float = 0.45, interrupt: bool = False) -> bool:
        """Play one short cue if voice is active. Returns whether playback started."""
        if not self.enabled:
            return False
        files = self._files(cue)
        if not files:
            return False
        if self.voice_client.is_playing():
            if not interrupt:
                return False
            self.voice_client.stop()
        source = discord.FFmpegPCMAudio(str(self.rng.choice(files)))
        self.voice_client.play(discord.PCMVolumeTransformer(source, volume=max(0.0, min(volume, 1.0))))
        return True


sound_director = SoundDirector()
