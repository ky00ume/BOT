"""Event-backed memory and diary projection for Churider."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from core.events import EventStore, GameEvent, event_store

KST = timezone(timedelta(hours=9))


def events_for_local_day(store: EventStore, day: datetime | None = None) -> list[GameEvent]:
    local_now = (day or datetime.now(KST)).astimezone(KST)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    return store.between(start_utc, end_utc)


def _event_sentence(event: GameEvent) -> str | None:
    payload = dict(event.payload)
    if event.event_type == "care.pet":
        return "누군가 방에 찾아와 쓰다듬어 주셨슴미댜. 가만히 받고 있으니까 마음이 몽글몽글해졌슴미댜. 🕷️💕"
    if event.event_type == "care.feed":
        snack = payload.get("snack") or "간식"
        return f"{snack}을(를) 얻어먹었슴미댜. 맛있는 걸 받으면 괜히 가까이 있고 싶어짐미댜. 🍪"
    if event.event_type == "care.play":
        return "같이 놀아주셔서 한참 신나게 움직였슴미댜. 다음에도 또 놀아주셨으면 좋겠슴미댜. 🎮"
    if event.event_type == "battle.won":
        monster = payload.get("monster") or "몬스터"
        location = event.location or "사냥터"
        return f"{location}에서 {monster}와 싸워서 이겼슴미댜. 돌아오고 나니 다리가 조금 후들거렸슴미댜. ⚔️"
    if event.event_type == "world.moved":
        origin = payload.get("from")
        destination = payload.get("to") or event.location
        if origin and destination:
            return f"{origin}에서 {destination}(으)로 걸어갔슴미댜. 길에서 본 것들을 오래 기억하고 싶슴미댜. 🍃"
    if event.event_type == "world.autonomous":
        return payload.get("diary_text") or payload.get("message")
    return None


def _memory_priority(event: GameEvent) -> int:
    """Importance of a fact as a remembered beat, not as a transaction."""
    if event.event_type in {"battle.won"}:
        return 90
    if event.event_type in {"world.moved"}:
        return 75
    if event.event_type in {"care.play", "care.feed", "care.pet"}:
        return 60
    if event.event_type == "world.autonomous":
        return 25
    return 0


def _select_memory_beats(events: list[GameEvent], *, limit: int = 3) -> list[GameEvent]:
    """Choose a small truthful shape of the day.

    Repeated routine facts collapse into one beat. Higher-salience facts survive
    over ordinary autonomous life, while final rendering remains chronological.
    """
    candidates: list[tuple[int, int, GameEvent, str]] = []
    seen: set[str] = set()
    for index, event in enumerate(events):
        sentence = _event_sentence(event)
        if not sentence or sentence in seen:
            continue
        seen.add(sentence)
        candidates.append((_memory_priority(event), index, event, sentence))
    chosen = sorted(candidates, key=lambda row: (row[0], row[1]), reverse=True)[:limit]
    return [row[2] for row in sorted(chosen, key=lambda row: row[1])]


def render_diary_from_events(events: Iterable[GameEvent], *, now: datetime | None = None) -> str | None:
    ordered = sorted(events, key=lambda event: event.occurred_at)
    beats = _select_memory_beats(ordered)
    sentences = [_event_sentence(event) for event in beats]
    if not sentences:
        return None
    body = "  ".join(sentence for sentence in sentences if sentence)
    local_now = (now or datetime.now(KST)).astimezone(KST)
    return f"{local_now.strftime('%Y년 %m월 %d일')} 일기\n\n{body}"


def render_today_diary(store: EventStore = event_store, *, now: datetime | None = None) -> str | None:
    return render_diary_from_events(events_for_local_day(store, now), now=now)
