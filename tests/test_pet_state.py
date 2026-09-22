from core.activities import ActivityService
from core.events import EventStore, GameEvent
from core.pet_state import observe_pet
from player import Player


def test_observation_describes_pet_without_exposing_raw_numbers(temp_db):
    player = Player("츄라이더")
    player.stability = 82
    player.energy = 90
    obs = observe_pet(player, activities=ActivityService(store=EventStore()), store=EventStore())
    text = " ".join((obs.headline, obs.body, obs.mood, obs.energy, obs.care_memory))
    assert "비전의 탑" in text
    assert "82" not in text
    assert "90" not in text
    assert "편안" in text


def test_observation_knows_when_player_sent_churider_fishing(temp_db):
    store = EventStore()
    activities = ActivityService(store=store)
    player = Player("츄라이더")
    activities.start_directed("fishing", actor_id=7, location="에본레이크 북안")
    obs = observe_pet(player, activities=activities, store=store)
    assert "에본레이크 북안" in obs.headline
    assert "낚시" in obs.headline
    assert "시키신 일" in obs.body


def test_repeated_care_becomes_visible_as_a_habit_memory(temp_db):
    store = EventStore()
    player = Player("츄라이더")
    store.append(GameEvent(event_type="care.pet", actor_id=1))
    store.append(GameEvent(event_type="care.pet", actor_id=2))
    obs = observe_pet(player, activities=ActivityService(store=store), store=store)
    assert "쓰다듬" in obs.care_memory
    assert "피하지" in obs.care_memory

def test_idle_pet_lives_in_hidden_upper_tower_nest(temp_db):
    from player import Player
    from core.pet_state import observe_pet
    from core.activities import ActivityService
    from core.events import EventStore

    store = EventStore()
    activities = ActivityService(store=store)
    player = Player()
    obs = observe_pet(player, activities=activities, store=store)

    assert "비전의 탑 상층" in obs.headline
    assert "책장 뒤 작은 틈" in obs.headline
    assert "자기 방" not in obs.headline
