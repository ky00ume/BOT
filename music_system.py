"""츄라이더의 선율 습득·연주·작곡 시스템."""
from __future__ import annotations

from lubato_song_memory import REPERTOIRE, REPERTOIRE_INSTRUMENTS

STATE_KEY = "music_book"

INSTRUMENTS = {
    "lyre": {"name": "리라", "emoji": "🎵"},
    "lute": {"name": "류트", "emoji": "🎻"},
    "piano": {"name": "피아노", "emoji": "🎹"},
}

FAITH_SONGS = {
    "lolth_hymn": {"title": "거미줄 아래의 여덟 번째 기도", "instrument": "piano"},
    "eilistraee_hymn": {"title": "달빛 아래 맨발의 춤", "instrument": "piano"},
    "vhaeraun_hymn": {"title": "가면 뒤에 남긴 길", "instrument": "piano"},
}

def required_instrument(melody_id: str) -> str | None:
    if melody_id in FAITH_SONGS:
        return FAITH_SONGS[melody_id]["instrument"]
    name = REPERTOIRE_INSTRUMENTS.get(melody_id)
    return {"리라": "lyre", "류트": "lute", "피아노": "piano"}.get(name)

def song_title(melody_id: str) -> str:
    if melody_id in REPERTOIRE:
        return REPERTOIRE[melody_id]["title"]
    if melody_id in FAITH_SONGS:
        return FAITH_SONGS[melody_id]["title"]
    return melody_id


def _state(player) -> dict:
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    st = player._flags.setdefault(STATE_KEY, {"learned": [], "compositions": [], "instrument": None, "score": None})
    st.setdefault("learned", []); st.setdefault("compositions", []); st.setdefault("instrument", None); st.setdefault("score", None)
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


def performance_result(player, melody_id: str, hits: int, total: int) -> tuple[str, int]:
    """리듬 연주 결과를 판정하고 실제 성공도에 비례해 수련치를 준다."""
    ensure_music_skills(player)
    total=max(1,int(total));hits=max(0,min(int(hits),total));rate=hits/total
    exp=max(5,round(10+30*rate))
    player.skill_exp["music"] = float(player.skill_exp.get("music",0.0))+exp
    if rate>=.9: grade="✨ 완벽한 연주"
    elif rate>=.7: grade="🎶 좋은 연주"
    elif rate>=.45: grade="🎵 끝까지 연주했다"
    else: grade="💦 조금 엉켰다"
    return grade,exp


def equip_instrument(player, instrument_id: str) -> tuple[bool, str]:
    ensure_music_skills(player)
    if instrument_id not in INSTRUMENTS:
        return False, "알 수 없는 악기임미댜."
    _state(player)["instrument"] = instrument_id
    return True, f"{INSTRUMENTS[instrument_id]['emoji']} **{INSTRUMENTS[instrument_id]['name']}**를 연주 악기로 장착했슴미댜."

def equip_score(player, melody_id: str) -> tuple[bool, str]:
    ensure_music_skills(player)
    known = melody_id in _state(player)["learned"] or melody_id in FAITH_SONGS
    if not known:
        return False, "아직 갖고 있지 않은 악보임미댜."
    _state(player)["score"] = melody_id
    return True, f"📜 **〈{song_title(melody_id)}〉** 악보를 장착했슴미댜."

def music_loadout(player) -> dict:
    st=_state(player); mid=st.get("score"); iid=st.get("instrument")
    return {"instrument": iid, "score": mid, "required": required_instrument(mid) if mid else None}

def can_start_instrument_performance(player) -> tuple[bool, str]:
    ld=music_loadout(player)
    if not ld["instrument"]:
        return False, "먼저 연주할 **악기**를 장착해야 함미댜."
    if not ld["score"]:
        return False, "먼저 연주할 **악보**를 장착해야 함미댜."
    if ld["required"] and ld["instrument"] != ld["required"]:
        want=INSTRUMENTS[ld["required"]]["name"]; got=INSTRUMENTS[ld["instrument"]]["name"]
        return False, f"이 악보는 **{want}**용임미댜. 지금 장착한 악기는 **{got}**임미댜."
    return True, ""
