"""Plural soft traits grown from Churider's recent lived experience."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from core.events import EventStore, event_store


@dataclass(frozen=True)
class PetTrait:
    key: str
    label: str
    description: str
    strength: int


_TRAITS = {
    "pet": ("🫳 쓰담 좋아함", "손이 가까이 오면 예전보다 먼저 기대어 옵니다."),
    "feed": ("🍪 먹을 것에 관심 많음", "챙겨주는 손에 뭐가 들렸는지 유심히 보는 버릇이 있습니다."),
    "play": ("🧸 같이 노는 걸 좋아함", "사람이 찾아오면 혹시 놀아주려나 조금 기대합니다."),
    "fishing": ("🎣 낚시 좋아함", "낚싯대만 보여도 물가에 나가는 건가 싶어 먼저 눈치챕니다."),
    "adventure": ("🎒 외출 눈치가 빠름", "장비를 챙기기 시작하면 밖에 나갈 일인지 먼저 알아챕니다."),
    "independent": ("🕸️ 은근 혼자 잘 놂", "조용한 시간이 이어져도 방 안에서 제 할 일을 찾아 꼼지락거립니다."),
}


def trait_profile(store: EventStore = event_store, *, limit: int = 80, max_traits: int = 3) -> list[PetTrait]:
    counts: Counter[str] = Counter()
    recent = store.recent(limit=limit)
    for event in recent:
        if event.event_type == "care.pet": counts["pet"] += 1
        elif event.event_type == "care.feed": counts["feed"] += 1
        elif event.event_type == "care.play": counts["play"] += 1
        elif event.event_type == "battle.won": counts["adventure"] += 1
        elif event.event_type == "activity.finished" and event.payload.get("kind") == "fishing": counts["fishing"] += 1
        elif event.event_type == "world.autonomous": counts["independent"] += 1

    grown = []
    for key, count in counts.most_common():
        if count < 3:
            continue
        label, description = _TRAITS[key]
        grown.append(PetTrait(key, label, description, min(3, 1 + (count >= 6) + (count >= 12))))
        if len(grown) >= max_traits:
            break
    return grown


def trait_summary(store: EventStore = event_store) -> str:
    traits = trait_profile(store)
    if not traits:
        return "아직 뚜렷하게 굳은 버릇은 없습니다. 같이 지내며 조금씩 생길 것 같습니다."
    return "\n".join(f"{trait.label} · {trait.description}" for trait in traits)
