from core.events import EventStore, GameEvent
from core.traits import trait_profile, trait_summary
from core.personality import behaviour_cue


def test_multiple_traits_can_coexist(temp_db):
    store = EventStore()
    for _ in range(4): store.append(GameEvent(event_type="care.pet", actor_id=1))
    for _ in range(3): store.append(GameEvent(event_type="care.play", actor_id=1))
    for _ in range(3): store.append(GameEvent(event_type="activity.finished", actor_id=1, payload={"kind":"fishing"}))
    keys = {trait.key for trait in trait_profile(store)}
    assert keys == {"pet", "play", "fishing"}
    text = trait_summary(store)
    assert "쓰담" in text and "같이 노는" in text and "낚시" in text


def test_contextual_fishing_cue_survives_when_not_primary(temp_db):
    store = EventStore()
    for _ in range(8): store.append(GameEvent(event_type="care.pet", actor_id=1))
    for _ in range(3): store.append(GameEvent(event_type="activity.finished", actor_id=1, payload={"kind":"fishing"}))
    cue = behaviour_cue(store)
    assert cue.habit == "pet"
    assert cue.fishing_start is not None
    assert "낚싯대" in cue.fishing_start


def test_autonomous_life_can_grow_independent_trait(temp_db):
    store = EventStore()
    for _ in range(3): store.append(GameEvent(event_type="world.autonomous", payload={"activity":"read"}))
    traits = trait_profile(store)
    assert traits[0].key == "independent"
    assert "혼자" in traits[0].label
