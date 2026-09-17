"""Tests for the durable world-event boundary."""
from datetime import datetime, timezone

from core.events import EventStore, GameEvent
from database import get_db_connection


def test_init_db_creates_game_events_table(temp_db):
    with get_db_connection() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "game_events" in tables


def test_event_store_round_trip_preserves_world_fact(temp_db):
    store = EventStore()
    event = GameEvent(
        event_type="care.pet",
        actor_id=12345,
        subject="츄라이더",
        location="하이네스의 방",
        payload={"source": "discord", "affection": 1},
        occurred_at=datetime(2026, 9, 18, 1, 2, 3, tzinfo=timezone.utc),
    )
    store.append(event)

    loaded = store.recent(limit=1)[0]
    assert loaded == event


def test_event_store_filters_by_type_and_orders_newest_first(temp_db):
    store = EventStore()
    older_pet = GameEvent(event_type="care.pet", occurred_at=datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc))
    store.append(older_pet)
    store.append(GameEvent(event_type="battle.won", occurred_at=datetime(2026, 9, 18, 2, 0, tzinfo=timezone.utc)))
    newest_pet = GameEvent(event_type="care.pet", occurred_at=datetime(2026, 9, 18, 3, 0, tzinfo=timezone.utc))
    store.append(newest_pet)

    pets = store.recent(event_type="care.pet")
    assert [event.event_id for event in pets] == [newest_pet.event_id, older_pet.event_id]
