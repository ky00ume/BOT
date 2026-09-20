"""Memory projection tests: world facts become Churider's remembered day."""
from datetime import datetime, timedelta, timezone

from core.events import EventStore, GameEvent
from core.memory import KST, events_for_local_day, render_diary_from_events


def test_local_day_window_uses_korea_time(temp_db):
    store = EventStore()
    # 00:30 KST on Sep 18 belongs to Sep 18, although it is Sep 17 in UTC.
    inside = GameEvent(event_type="care.pet", occurred_at=datetime(2026, 9, 17, 15, 30, tzinfo=timezone.utc))
    outside = GameEvent(event_type="care.pet", occurred_at=datetime(2026, 9, 17, 14, 59, tzinfo=timezone.utc))
    store.append(outside)
    store.append(inside)

    now = datetime(2026, 9, 18, 22, 0, tzinfo=KST)
    assert [event.event_id for event in events_for_local_day(store, now)] == [inside.event_id]


def test_diary_is_composed_from_actual_events():
    events = [
        GameEvent(event_type="world.moved", location="방울숲", payload={"from": "마을", "to": "방울숲"}, occurred_at=datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)),
        GameEvent(event_type="care.pet", actor_id=7, subject="츄라이더", occurred_at=datetime(2026, 9, 18, 2, 0, tzinfo=timezone.utc)),
        GameEvent(event_type="battle.won", location="방울숲", payload={"monster": "슬라임"}, occurred_at=datetime(2026, 9, 18, 3, 0, tzinfo=timezone.utc)),
    ]
    text = render_diary_from_events(events, now=datetime(2026, 9, 18, 22, 0, tzinfo=KST))
    assert "마을에서 방울숲" in text
    assert "쓰다듬어" in text
    assert "슬라임" in text
    assert "2026년 09월 18일" in text


def test_diary_collapses_repeated_identical_beats():
    events = [
        GameEvent(event_type="world.autonomous", payload={"diary_text": "창가에서 혼자 바깥을 오래 구경했슴미댜."}, occurred_at=datetime(2026, 9, 18, 1, i, tzinfo=timezone.utc))
        for i in range(3)
    ]
    text = render_diary_from_events(events, now=datetime(2026, 9, 18, 22, 0, tzinfo=KST))
    assert text.count("창가에서 혼자 바깥을 오래 구경했슴미댜.") == 1


def test_diary_keeps_meaningful_beats_over_routine_noise():
    events = [
        GameEvent(event_type="world.autonomous", payload={"diary_text": f"혼자 조용히 시간을 보냈슴미댜 {i}."}, occurred_at=datetime(2026, 9, 18, 1, i, tzinfo=timezone.utc))
        for i in range(5)
    ]
    events += [
        GameEvent(event_type="care.feed", payload={"snack": "거미 쿠키"}, occurred_at=datetime(2026, 9, 18, 2, 0, tzinfo=timezone.utc)),
        GameEvent(event_type="world.moved", location="방울숲", payload={"from": "마을", "to": "방울숲"}, occurred_at=datetime(2026, 9, 18, 3, 0, tzinfo=timezone.utc)),
        GameEvent(event_type="battle.won", location="방울숲", payload={"monster": "슬라임"}, occurred_at=datetime(2026, 9, 18, 4, 0, tzinfo=timezone.utc)),
    ]
    text = render_diary_from_events(events, now=datetime(2026, 9, 18, 22, 0, tzinfo=KST))
    assert "거미 쿠키" in text
    assert "마을에서 방울숲" in text
    assert "슬라임" in text
    assert "혼자 조용히" not in text
