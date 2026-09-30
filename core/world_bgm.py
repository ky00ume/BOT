"""World/location BGM routing for Discord voice playback."""
from __future__ import annotations

from core.sound_director import sound_director

BGM_CUES = {
    "tower": "bgm/locations/tower",
    "myconid_colony": "bgm/locations/myconid_colony",
    "colony_road": "bgm/locations/colony_road",
    "hunting_ground": "bgm/locations/hunting_ground",
}


def scene_for_location(location: str) -> str | None:
    if location.startswith("비전의 탑"):
        return "tower"
    if location.startswith("마이코니드 군락"):
        return "myconid_colony"
    return None


def play_scene_bgm(scene: str, *, volume: float = 0.18) -> bool:
    cue = BGM_CUES.get(scene)
    if not cue:
        return False
    return sound_director.play_bgm(cue, volume=volume)


def play_location_bgm(location: str, *, volume: float = 0.18) -> bool:
    scene = scene_for_location(location)
    if scene is None:
        sound_director.stop_bgm()
        return False
    return play_scene_bgm(scene, volume=volume)
