from pathlib import Path

import pytest

from core.sound_director import SoundDirector


class FakeVoice:
    def __init__(self):
        self.played = []
        self.stopped = False
        self.playing = False
    def is_connected(self): return True
    def is_playing(self): return self.playing
    def stop(self): self.stopped = True; self.playing = False
    def play(self, source): self.played.append(source); self.playing = True


def test_missing_cue_is_safe_noop(tmp_path):
    director = SoundDirector(asset_root=tmp_path)
    director.voice_client = FakeVoice()
    assert director.cue("life/mining/hit") is False
    assert director.voice_client.played == []


def test_disconnected_sound_is_safe_noop(tmp_path):
    cue = tmp_path / "life" / "mining" / "hit"
    cue.mkdir(parents=True)
    (cue / "hit.wav").write_bytes(b"not-used-without-voice")
    director = SoundDirector(asset_root=tmp_path)
    assert director.cue("life/mining/hit") is False


def test_cue_folder_mapping(tmp_path):
    cue = tmp_path / "life" / "woodcut" / "hit"
    cue.mkdir(parents=True)
    good = cue / "axe.ogg"; good.write_bytes(b"x")
    (cue / "note.txt").write_text("ignore")
    director = SoundDirector(asset_root=tmp_path)
    assert director._files("life/woodcut/hit") == [good]
