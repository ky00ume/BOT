import pytest

from core.activities import ActivityService
from core.directed_gathering import DirectedGatheringService, GATHERABLE_MODES, missing_recipe_ingredients
from core.events import EventStore


def test_recipe_missing_materials_only_offer_real_gather_routes(fresh_player, temp_db):
    fresh_player.inventory["iron_ore"] = 2
    recipe = {"ingredients": {"iron_ore": 7, "nonexistent_story_thing": 3}}
    missing = missing_recipe_ingredients(fresh_player, recipe)
    assert missing == [{
        "item_id": "iron_ore", "name": "철광석", "have": 2,
        "need": 7, "missing": 5, "mode": "mine",
    }]


def test_recipe_target_starts_directed_goal_without_spending_material(fresh_player, temp_db):
    fresh_player.inventory["iron_ore"] = 2
    service = DirectedGatheringService(activities=ActivityService(store=EventStore()), store=EventStore())
    activity, target = service.start_for_recipe(fresh_player, item_id="iron_ore", required_count=7, actor_id=123)
    assert activity.kind == "gathering"
    assert target.missing == 5
    assert activity.context["target_count"] == 7
    assert fresh_player.inventory["iron_ore"] == 2


def test_goal_finishes_only_after_requested_inventory_target(fresh_player, temp_db):
    activities = ActivityService(store=EventStore())
    service = DirectedGatheringService(activities=activities, store=EventStore())
    activity, _ = service.start_for_recipe(fresh_player, item_id="iron_ore", required_count=3, actor_id=123)
    fresh_player.inventory["iron_ore"] = 2
    assert service.finish_if_reached(fresh_player, activity) is False
    fresh_player.inventory["iron_ore"] = 3
    assert service.finish_if_reached(fresh_player, activity) is True
    assert activities.current() is None


def test_unknown_material_cannot_be_silently_autofarmed(fresh_player, temp_db):
    service = DirectedGatheringService(activities=ActivityService(store=EventStore()), store=EventStore())
    with pytest.raises(ValueError):
        service.start_for_recipe(fresh_player, item_id="quest_secret", required_count=1, actor_id=123)
