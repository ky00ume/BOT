"""Discord voice sound director for cues and looping world BGM.

Game systems emit semantic cue/scene names; this module alone owns Discord voice
playback. Missing assets or a disconnected voice session are intentional no-ops.
"""
from __future__ import annotations

import asyncio
import random
from pathlib import Path

import discord


class SoundDirector:
    def __init__(self, *, asset_root: Path | None = None, rng=None):
        self.asset_root = asset_root or Path(__file__).resolve().parents[1] / "assets" / "audio"
        self.rng = rng or random
        self.voice_client: discord.VoiceClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._bgm_cue: str | None = None
        self._bgm_volume = 0.18
        self._bgm_active = False
        self._bgm_generation = 0

    @property
    def enabled(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    @property
    def current_bgm(self) -> str | None:
        return self._bgm_cue

    async def join(self, channel: discord.VoiceChannel) -> None:
        self._loop = asyncio.get_running_loop()
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
            return
        self.voice_client = await channel.connect()

    async def leave(self) -> None:
        self._bgm_cue = None
        self._bgm_active = False
        self._bgm_generation += 1
        if self.voice_client:
            try:
                await self.voice_client.disconnect(force=False)
            finally:
                self.voice_client = None

    def _files(self, cue: str) -> list[Path]:
        cue_dir = self.asset_root / cue.replace(".", "/")
        if not cue_dir.exists():
            return []
        return sorted(p for p in cue_dir.iterdir() if p.suffix.lower() in {".mp3", ".ogg", ".wav", ".flac", ".m4a"})

    def _bgm_file(self, cue: str) -> Path | None:
        files = self._files(cue)
        return files[0] if files else None

    def _start_bgm_source(self, cue: str, volume: float) -> bool:
        if not self.enabled:
            return False
        path = self._bgm_file(cue)
        if path is None:
            return False
        source = discord.FFmpegPCMAudio(str(path), before_options="-stream_loop -1", options="-vn")
        self.voice_client.play(discord.PCMVolumeTransformer(source, volume=max(0.0, min(volume, 1.0))))
        self._bgm_active = True
        return True

    def play_bgm(self, cue: str, *, volume: float = 0.18) -> bool:
        """Start a location BGM as a continuous FFmpeg loop."""
        if not self.enabled or self._bgm_file(cue) is None:
            return False
        if self._bgm_cue == cue and self._bgm_active and self.voice_client.is_playing():
            return True
        self._bgm_generation += 1
        self._bgm_cue = cue
        self._bgm_volume = max(0.0, min(volume, 1.0))
        if self.voice_client.is_playing():
            self.voice_client.stop()
        self._bgm_active = False
        return self._start_bgm_source(cue, self._bgm_volume)

    def stop_bgm(self) -> None:
        self._bgm_generation += 1
        self._bgm_cue = None
        if self.enabled and self._bgm_active and self.voice_client.is_playing():
            self.voice_client.stop()
        self._bgm_active = False

    def _resume_bgm(self, cue: str, volume: float, generation: int) -> None:
        if generation != self._bgm_generation or self._bgm_cue != cue or not self.enabled:
            return
        if self.voice_client.is_playing():
            return
        self._start_bgm_source(cue, volume)

    def cue(self, cue: str, *, volume: float = 0.45, interrupt: bool = False) -> bool:
        """Play one short cue if voice is active. Returns whether playback started.

        If a location BGM is active, an interrupting cue temporarily replaces it and
        the BGM is resumed when the cue finishes.
        """
        if not self.enabled:
            return False
        files = self._files(cue)
        if not files:
            return False
        if self.voice_client.is_playing():
            if not interrupt:
                return False
            self._bgm_active = False
            self.voice_client.stop()
        resume_cue = self._bgm_cue
        resume_volume = self._bgm_volume
        generation = self._bgm_generation
        source = discord.FFmpegPCMAudio(str(self.rng.choice(files)))

        def _after(_error):
            if resume_cue and self._loop:
                self._loop.call_soon_threadsafe(self._resume_bgm, resume_cue, resume_volume, generation)

        self.voice_client.play(
            discord.PCMVolumeTransformer(source, volume=max(0.0, min(volume, 1.0))),
            after=_after,
        )
        return True


sound_director = SoundDirector()
