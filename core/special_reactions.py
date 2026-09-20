"""Actor-specific flavour rules that do not split shared Churider relationship state."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecialReaction:
    room_arrival: str
    pet: str
    feed: str
    play: str


SUSPICIOUS_LILY = SpecialReaction(
    room_arrival="츄라이더가 들어온 사람을 보고 잠깐 굳습니다. ……으심. 무서워. 수상해. 책상 밑으로 반쯤 숨었슴미댜.",
    pet="츄라이더가 손을 빤히 보다가 한 발 물러납니다. '……으심. 수상해.'",
    feed="간식은 받아 챙겼는데, 츄라이더는 먹으면서도 계속 이쪽을 경계합니다. '간식이랑 신뢰는 별개임미댜.'",
    play="놀이는 조금 궁금한 모양인데 먼저 가까이 오지는 않습니다. '……이거 함정 아님미까?'",
)


def reaction_for(actor_id: int | None, *, suspicious_actor_id: int | None) -> SpecialReaction | None:
    """Return flavour override for the known suspicious visitor.

    This deliberately does not alter bond, traits, rewards, or player agency.
    """
    if actor_id is not None and suspicious_actor_id is not None and actor_id == suspicious_actor_id:
        return SUSPICIOUS_LILY
    return None
