"""Tamagotchi-style observation layer for the shared Churider.

Numbers remain useful internally; players primarily see behaviour and condition.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.activities import ActivityService, activity_service
from core.events import EventStore, event_store
from core.bond import BondService, bond_service, bond_title, habit_profile
from core.personality import behaviour_cue


@dataclass(frozen=True)
class PetObservation:
    headline: str
    body: str
    mood: str
    energy: str
    care_memory: str
    relationship: str
    habit: str


def _band(value: float, low: str, mid: str, high: str) -> str:
    if value < 35:
        return low
    if value < 70:
        return mid
    return high


def observe_pet(player, *, activities: ActivityService = activity_service, store: EventStore = event_store, now: datetime | None = None) -> PetObservation:
    current = activities.current()
    if current:
        labels = {"fishing": "낚시", "gathering": "채집", "crafting": "무언가 만들기"}
        activity_label = labels.get(current.kind, current.kind)
        place = current.location or "어딘가"
        headline = f"츄라이더는 지금 {place}에서 {activity_label} 중입니다."
        body = "시키신 일을 제법 진지하게 하고 있슴미댜. 끝날 때까지 종종 이쪽을 힐끔거립니다."
    else:
        headline = "츄라이더는 지금 하이네스의 방에서 쉬고 있습니다."
        if player.fatigue >= 70:
            body = "거미줄 해먹에 몸을 푹 묻고 있습니다. 눈꺼풀이 자꾸 내려오는 모양입니다."
        elif player.condition < 35:
            body = "평소보다 움직임이 조금 느립니다. 가까이 가면 그래도 슬쩍 고개를 듭니다."
        elif player.stability >= 75:
            body = "창가에 붙어서 바깥을 느긋하게 구경하고 있습니다. 꽤 편안해 보입니다."
        else:
            body = "방 안을 꼼지락거리며 돌아다니다가 누가 왔나 하고 이쪽을 봅니다."

    if not current:
        arrival = behaviour_cue(store).care_arrival
        if arrival:
            body = f"{body} {arrival}"

    mood = _band(player.stability, "조금 예민해 보입니다.", "평소처럼 차분해 보입니다.", "마음이 꽤 편안해 보입니다.")
    effective_energy = max(0, min(100, (player.energy / max(1, player.max_energy)) * 100 - player.fatigue * 0.35))
    energy = _band(effective_energy, "금방이라도 꾸벅 졸 것 같습니다.", "아직 이것저것 할 기운은 있어 보입니다.", "기운이 제법 넘쳐 보입니다.")

    recent = store.recent(limit=40)
    pets = sum(1 for event in recent if event.event_type == "care.pet")
    plays = sum(1 for event in recent if event.event_type == "care.play")
    feeds = sum(1 for event in recent if event.event_type == "care.feed")
    if pets + plays + feeds == 0:
        care_memory = "최근에는 조용히 혼자 시간을 보내고 있었습니다."
    elif pets >= max(plays, feeds) and pets >= 2:
        care_memory = "최근 쓰다듬을 자주 받아서인지 사람이 가까이 와도 먼저 피하지 않습니다."
    elif plays >= 2:
        care_memory = "최근 같이 놀아준 일을 기억하는지 누가 오면 조금 기대하는 눈치입니다."
    elif feeds >= 2:
        care_memory = "최근 맛있는 걸 몇 번 얻어먹어서인지 손에 든 것을 유심히 봅니다."
    else:
        care_memory = "최근 누군가 돌봐준 기억이 남아 있는 모양입니다."

    bond = bond_service.get() if store is event_store else BondService(store=store).get()
    relationship = f"{bond_title(bond.level)} · 인연 {bond.level}단계"
    habit = habit_profile(store).description
    return PetObservation(headline, body, mood, energy, care_memory, relationship, habit)
