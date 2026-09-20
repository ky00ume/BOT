from core.activities import ActivityService
from core.events import EventStore
from core.pet_state import observe_pet
import status_window


def test_activity_progress_is_persistent_and_observable(fresh_player, temp_db):
    store = EventStore()
    activities = ActivityService(store=store)
    activity = activities.start_directed(
        "gathering", actor_id=1, location="광산",
        context={"item_id": "iron_ore", "item_name": "철광석", "target_count": 5, "progress_count": 2},
    )
    activities.update_context(activity.activity_id, progress_count=3, energy=72, attempts=2)
    current = activities.current()
    assert current.context["progress_count"] == 3
    assert current.context["energy"] == 72
    obs = observe_pet(fresh_player, activities=activities, store=store)
    assert "철광석 모으기 · 3/5" in obs.headline


def test_status_window_reads_current_gathering_activity(monkeypatch, fresh_player, temp_db):
    activities = ActivityService(store=EventStore())
    activities.start_directed(
        "gathering", actor_id=1, location="광산",
        context={"item_id": "iron_ore", "item_name": "철광석", "target_count": 5, "progress_count": 2},
    )
    monkeypatch.setattr("core.activities.activity_service", activities)
    captured = {}
    class Renderer:
        def render_status_card(self, **kwargs):
            captured.update(kwargs)
            return object()
    monkeypatch.setattr(status_window, "get_renderer", lambda: Renderer())
    status_window.create_status_image(fresh_player)
    assert "철광석 모으는 중 2/5" in captured["title_str"]
