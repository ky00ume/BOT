from unittest.mock import Mock, patch

from core.sound_director import SoundDirector
from core.world_bgm import scene_for_location


class FakeVoice:
    def __init__(self):
        self.played = []
        self.stopped = False
        self.playing = False

    def is_connected(self):
        return True

    def is_playing(self):
        return self.playing

    def stop(self):
        self.stopped = True
        self.playing = False

    def play(self, source, *, after=None):
        self.played.append((source, after))
        self.playing = True


def test_location_scene_routing():
    assert scene_for_location("비전의 탑") == "tower"
    assert scene_for_location("비전의 탑 · 상층 생활 공간") == "tower"
    assert scene_for_location("마이코니드 군락") == "myconid_colony"
    assert scene_for_location("마이코니드 군락 군주의 터") == "myconid_colony"
    assert scene_for_location("드레드 할로우") is None


def test_bgm_uses_infinite_ffmpeg_loop_and_does_not_restart_same_scene(tmp_path):
    cue_dir = tmp_path / "bgm" / "locations" / "tower"
    cue_dir.mkdir(parents=True)
    track = cue_dir / "tower.ogg"
    track.write_bytes(b"fake")

    director = SoundDirector(asset_root=tmp_path)
    director.voice_client = FakeVoice()

    with patch("core.sound_director.discord.FFmpegPCMAudio") as ffmpeg, patch(
        "core.sound_director.discord.PCMVolumeTransformer", side_effect=lambda source, volume: (source, volume)
    ):
        ffmpeg.return_value = Mock(name="ffmpeg-source")
        assert director.play_bgm("bgm/locations/tower", volume=0.2) is True
        assert director.current_bgm == "bgm/locations/tower"
        assert len(director.voice_client.played) == 1
        ffmpeg.assert_called_once_with(str(track), before_options="-stream_loop -1", options="-vn")

        # Re-entering the same place should keep the running loop instead of restarting it.
        assert director.play_bgm("bgm/locations/tower", volume=0.2) is True
        assert len(director.voice_client.played) == 1


def test_stop_bgm_stops_active_loop(tmp_path):
    cue_dir = tmp_path / "bgm" / "locations" / "tower"
    cue_dir.mkdir(parents=True)
    (cue_dir / "tower.ogg").write_bytes(b"fake")
    director = SoundDirector(asset_root=tmp_path)
    director.voice_client = FakeVoice()

    with patch("core.sound_director.discord.FFmpegPCMAudio", return_value=Mock()), patch(
        "core.sound_director.discord.PCMVolumeTransformer", side_effect=lambda source, volume: source
    ):
        director.play_bgm("bgm/locations/tower")
        director.stop_bgm()

    assert director.current_bgm is None
    assert director.voice_client.stopped is True
