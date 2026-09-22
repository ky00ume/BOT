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
from core.traits import trait_summary


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
        progress = current.context.get("progress_count")
        target = current.context.get("target_count")
        item_name = current.context.get("item_name")
        if current.kind == "gathering" and progress is not None and target is not None:
            activity_label = f"{item_name or '재료'} 모으기 · {progress}/{target}"
        headline = f"츄라이더는 지금 {place}에서 {activity_label} 중입니다."
        body = "시키신 일을 제법 진지하게 하고 있슴미댜. 끝날 때까지 종종 이쪽을 힐끔거립니다."
    else:
        headline = "츄라이더는 지금 비전의 탑 상층, 책장 뒤 작은 틈에 숨어 쉬고 있습니다."
        if player.fatigue >= 70:
            body = "담요 조각 사이에 몸을 푹 묻고 있습니다. 복도 쪽에서 소리가 날 때마다 귀만 잠깐 세웁니다."
        elif player.condition < 35:
            body = "보금자리 깊숙한 곳에 웅크려 있습니다. 가까이 가면 그래도 슬쩍 고개를 듭니다."
        elif player.stability >= 75:
            body = "책장 밖으로 몸을 반쯤 내놓고 상층을 구경하고 있습니다. 마제스티가 지나간 쪽에는 별로 경계심이 없습니다."
        else:
            body = "담요와 주워 온 작은 물건 사이를 꼼지락거리다가 복도에서 발소리가 나자 얼른 책장 뒤로 몸을 숨깁니다."

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
    habit = trait_summary(store)
    return PetObservation(headline, body, mood, energy, care_memory, relationship, habit)
