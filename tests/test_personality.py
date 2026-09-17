from core.events import EventStore, GameEvent
from core.personality import behaviour_cue


def test_pet_habit_leaks_into_arrival_behaviour(temp_db):
    store = EventStore()
    for _ in range(3):
        store.append(GameEvent(event_type="care.pet", actor_id=1))
    cue = behaviour_cue(store)
    assert cue.habit == "pet"
    assert "먼저 가까이" in cue.care_arrival
    assert "쓰다듬" in cue.idle_message


def test_fishing_habit_changes_fishing_expression(temp_db):
    store = EventStore()
    for _ in range(3):
        store.append(GameEvent(event_type="activity.finished", actor_id=1, payload={"kind": "fishing"}))
    cue = behaviour_cue(store)
    assert cue.habit == "fishing"
    assert "낚싯대" in cue.fishing_start
    assert "물가" in cue.fishing_start


def test_no_hardened_habit_does_not_invent_behaviour(temp_db):
    store = EventStore()
    store.append(GameEvent(event_type="care.play", actor_id=1))
    cue = behaviour_cue(store)
    assert cue.habit is None
    assert cue.care_arrival is None
    assert cue.fishing_start is None
