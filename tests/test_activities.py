from datetime import datetime, timedelta, timezone
from core.activities import ActivityService
from core.events import EventStore


def test_directed_fishing_has_persistent_lifecycle(temp_db):
    service = ActivityService(store=EventStore())
    activity = service.start_directed("fishing", actor_id=77, location="에본레이크 북안")
    assert service.current().activity_id == activity.activity_id
    assert service.current().actor_id == 77

    finished = service.finish(activity.activity_id, outcome="caught", payload={"fish": "붕어"})
    assert finished.activity_id == activity.activity_id
    assert service.current() is None
    events = list(reversed(EventStore().recent()))
    assert [event.event_type for event in events] == ["activity.started", "activity.finished"]
    assert events[-1].payload["fish"] == "붕어"


def test_player_controlled_content_cannot_be_started_as_directed(temp_db):
    service = ActivityService(store=EventStore())
    try:
        service.start_directed("battle", actor_id=77)
    except ValueError:
        pass
    else:
        raise AssertionError("battle must remain player-controlled")


def test_stale_interaction_is_reconciled_without_inventing_reward(temp_db):
    service = ActivityService(store=EventStore())
    started = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    activity = service.start_directed("fishing", actor_id=77, now=started)
    recovered = service.reconcile(now=started + timedelta(minutes=20))
    assert recovered.activity_id == activity.activity_id
    assert service.current() is None
    event = EventStore().recent(limit=1)[0]
    assert event.event_type == "activity.finished"
    assert event.payload["outcome"] == "interrupted"
    assert "fish" not in event.payload


def test_recent_interaction_is_not_reconciled(temp_db):
    service = ActivityService(store=EventStore())
    started = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    activity = service.start_directed("fishing", actor_id=77, now=started)
    assert service.reconcile(now=started + timedelta(minutes=5)) is None
    assert service.current().activity_id == activity.activity_id
