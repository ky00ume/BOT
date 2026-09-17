from core.bond import BondService, MAX_BOND_LEVEL, bond_title, habit_profile
from core.events import EventStore


def test_bond_starts_at_level_one_and_grows(temp_db):
    service = BondService(store=EventStore())
    assert service.get().level == 1
    state = service.award("care.play", actor_id=7)
    assert state.xp > 0
    assert state.lifetime_xp == state.xp


def test_repeating_same_care_has_diminishing_returns(temp_db):
    service = BondService(store=EventStore())
    gains = []
    for _ in range(7):
        before = service.get().lifetime_xp
        after = service.award("care.pet", actor_id=7)
        gains.append(after.lifetime_xp - before)
    assert gains[0] == gains[1]
    assert gains[2] < gains[0]
    assert gains[-1] < gains[2]


def test_bond_caps_level_but_keeps_lifetime_progress(temp_db):
    service = BondService(store=EventStore())
    for _ in range(120):
        service.award("story.milestone", actor_id=7, amount=1000)
    state = service.get()
    assert state.level == MAX_BOND_LEVEL
    lifetime = state.lifetime_xp
    state = service.award("care.pet", actor_id=7)
    assert state.level == MAX_BOND_LEVEL
    assert state.lifetime_xp > lifetime
    assert state.xp == 0
    assert bond_title(state.level) == "평생의 가족"


def test_repeated_pet_care_becomes_a_visible_habit(temp_db):
    store = EventStore()
    from core.events import GameEvent
    for actor in (1, 2, 1):
        store.append(GameEvent(event_type="care.pet", actor_id=actor))
    habit = habit_profile(store)
    assert habit.primary == "pet"
    assert "쓰다듬" in habit.description


def test_habit_needs_repetition_before_it_hardens(temp_db):
    store = EventStore()
    from core.events import GameEvent
    store.append(GameEvent(event_type="care.play", actor_id=1))
    assert habit_profile(store).primary is None
