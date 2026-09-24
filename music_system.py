"""츄라이더의 선율 습득·연주·작곡 시스템."""
from __future__ import annotations

from lubato_song_memory import REPERTOIRE

STATE_KEY = "music_book"


def _state(player) -> dict:
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    st = player._flags.setdefault(STATE_KEY, {"learned": [], "compositions": []})
    st.setdefault("learned", []); st.setdefault("compositions", [])
    return st


def ensure_music_skills(player) -> None:
    player.skill_ranks.setdefault("music", "연습")
    player.skill_exp.setdefault("music", 0.0)
    player.skill_ranks.setdefault("composition", "연습")
    player.skill_exp.setdefault("composition", 0.0)


def learn_melody(player, melody_id: str) -> bool:
    if melody_id not in REPERTOIRE:
        return False
    ensure_music_skills(player)
    learned = _state(player)["learned"]
    if melody_id in learned:
        return False
    learned.append(melody_id)
    return True


def learned_melodies(player):
    return [(key, REPERTOIRE[key]) for key in _state(player)["learned"] if key in REPERTOIRE]


def perform(player, melody_id: str) -> tuple[bool, str]:
    ensure_music_skills(player)
    if melody_id not in _state(player)["learned"]:
        return False, "아직 기억하지 못한 선율임미댜."
    player.skill_exp["music"] = float(player.skill_exp.get("music", 0.0)) + 20.0
    return True, f"🎻 츄라이더가 **〈{REPERTOIRE[melody_id]['title']}〉**의 선율을 악기로 연주합니다.  `연주 EXP +20`"


def compose_variation(player, melody_id: str) -> tuple[bool, str]:
    ensure_music_skills(player)
    if melody_id not in _state(player)["learned"]:
        return False, "먼저 원곡의 선율을 배워야 함미댜."
    comps = _state(player)["compositions"]
    cid = f"variation_{melody_id}"
    if cid not in comps:
        comps.append(cid)
    player.skill_exp["composition"] = float(player.skill_exp.get("composition", 0.0)) + 30.0
    title = REPERTOIRE[melody_id]["title"]
    return True, f"✍️ 원곡의 핵심 선율만 가져와 **〈{title} · 츄라이더 변주〉**를 만들었습니다.  `작곡 EXP +30`"


RHYTHM_KEYS = ("⬅️", "⬆️", "⬇️", "➡️")

def rhythm_chart(melody_id: str) -> list[dict]:
    """멜로디 음표에서 연주 미니게임용 키 타이밍을 만든다. 같은 곡은 항상 같은 패턴이다."""
    from melody_renderer import MELODIES
    melody=MELODIES.get(melody_id)
    if not melody:
        return []
    beat_ms=60000.0/melody["bpm"]
    elapsed=0.0; chart=[]
    for idx,(note,beats) in enumerate(melody["notes"]):
        if note != "R":
            chart.append({"at_ms": round(elapsed), "key": RHYTHM_KEYS[idx % len(RHYTHM_KEYS)], "note": note})
        elapsed += beat_ms*beats
    return chart
