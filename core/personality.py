"""Small behavioural leaks from Churider's lived habits.

Habits change expression, not rewards or player-owned decisions.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.traits import trait_profile
from core.events import EventStore, event_store


@dataclass(frozen=True)
class BehaviourCue:
    habit: str | None
    care_arrival: str | None = None
    fishing_start: str | None = None
    idle_message: str | None = None


def behaviour_cue(store: EventStore = event_store) -> BehaviourCue:
    """Pick expression from several coexisting traits without changing rewards."""
    traits = trait_profile(store)
    keys = {trait.key for trait in traits}
    cues = {
        "pet": BehaviourCue("pet", care_arrival="릴리들이 들어오는 기척이 나자 츄라이더가 먼저 가까이 와서 손 근처에 머리를 슬쩍 들이밈미댜.", idle_message="🕷️ 츄라이더가 인기척을 듣고 문 쪽을 힐끔 보더니, 쓰다듬을 기다리는 것처럼 가까운 자리에 앉았슴미댜."),
        "feed": BehaviourCue("feed", care_arrival="츄라이더가 손에 든 게 있나 먼저 빤히 살펴봄미댜. 요즘 먹을 것을 챙겨준 일을 제대로 기억하는 눈치임미댜.", idle_message="🕷️ 츄라이더가 간식 보관함 앞을 괜히 한 바퀴 돌고는 아무 일도 없었다는 듯 자리를 옮겼슴미댜."),
        "play": BehaviourCue("play", care_arrival="츄라이더가 누가 들어오자 금세 몸을 일으킴미댜. 혹시 같이 놀자는 건가 조금 기대하는 얼굴임미댜.", idle_message="🕷️ 츄라이더가 혼자 장난감을 툭 건드리다가 누가 보고 있나 슬쩍 주변을 확인했슴미댜."),
        "fishing": BehaviourCue("fishing", care_arrival="츄라이더는 느긋하게 쉬다가도 낚싯대 쪽을 한 번씩 확인함미댜. 물가에 나간 기억이 꽤 좋은 모양임미댜.", fishing_start="낚싯대를 꺼내자 츄라이더가 먼저 물가 쪽으로 몇 걸음 앞서감미댜. 어디 가는지 이미 아는 눈치임미댜. 🎣", idle_message="🕷️ 츄라이더가 낚싯대를 한참 바라보다가 창밖 물가 쪽으로 시선을 돌렸슴미댜. 🎣"),
        "adventure": BehaviourCue("adventure", care_arrival="츄라이더가 장비 쪽을 한 번 확인하고 릴리들을 봄미댜. 밖에 나갈 일이 있나 눈치를 챈 모양임미댜.", idle_message="🕷️ 츄라이더가 외출 장비를 정리해 두고는 괜히 문밖을 한 번 내다봤슴미댜."),
        "independent": BehaviourCue("independent", care_arrival="혼자 잘 놀고 있던 츄라이더가 인기척을 듣고 하던 일을 멈춘 채 이쪽을 봄미댜.", idle_message="🕷️ 츄라이더가 혼자 거미줄을 손보다가 작은 장난감을 툭 건드리며 제법 바쁘게 시간을 보내고 있슴미댜."),
    }
    # Context-specific traits win; otherwise strongest recent trait supplies flavour.
    fishing = cues["fishing"].fishing_start if "fishing" in keys else None
    chosen = cues[traits[0].key] if traits else BehaviourCue(None)
    return BehaviourCue(chosen.habit, chosen.care_arrival, fishing, chosen.idle_message)
