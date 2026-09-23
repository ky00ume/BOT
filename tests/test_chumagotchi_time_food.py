import time

from care import CareManager, get_care_state, update_care_over_time
from player import Player


def test_real_time_decay_changes_needs_after_hours():
    player = Player()
    state = get_care_state(player)
    state_ref = player._flags["pet_care"]
    state_ref["last_update"] = time.time() - 2 * 3600
    before_hunger = state_ref["hunger"]
    before_boredom = state_ref["boredom"]
    before_clean = state_ref["cleanliness"]

    updated = update_care_over_time(player)

    assert updated["hunger"] > before_hunger
    assert updated["boredom"] > before_boredom
    assert updated["cleanliness"] < before_clean


def test_real_time_decay_is_capped_to_72_hours():
    player = Player()
    get_care_state(player)
    player._flags["pet_care"]["last_update"] = time.time() - 30 * 24 * 3600
    updated = update_care_over_time(player)
    assert 0 <= updated["cleanliness"] <= 100
    assert 0 <= updated["comfort"] <= 100
    assert updated["hunger"] <= 100
    assert updated["boredom"] <= 100


def test_cooked_food_is_removed_from_portable_inventory_and_reduces_hunger():
    player = Player()
    player.add_item("salt_grilled_fish", 2)
    state = get_care_state(player)
    player._flags["pet_care"]["hunger"] = 80
    result = CareManager().feed_food(player, "salt_grilled_fish")

    assert result["success"]
    assert player.inventory["salt_grilled_fish"] == 1
    assert get_care_state(player)["hunger"] < 80
    assert result["kind"] == "요리"


def test_caught_fish_can_be_fed_directly():
    player = Player()
    player.add_item("fs_carp_01", 1)
    player._flags["pet_care"] = {
        "hunger": 70,
        "cleanliness": 70,
        "boredom": 30,
        "comfort": 50,
        "wash_count": 0,
        "rest_count": 0,
        "rest_started_at": 0.0,
        "rest_until": 0.0,
        "last_rest_summary": "",
        "last_update": time.time(),
    }
    result = CareManager().feed_food(player, "fs_carp_01")
    assert result["success"]
    assert "fs_carp_01" not in player.inventory
    assert result["kind"] == "생선"
    assert "앞다리" in result["message"]


def test_non_food_cannot_be_fed():
    player = Player()
    player.add_item("iron_ore", 1)
    result = CareManager().feed_food(player, "iron_ore")
    assert not result["success"]
    assert player.inventory["iron_ore"] == 1


def test_available_foods_only_lists_edible_portable_items():
    player = Player()
    player.add_item("salt_grilled_fish", 1)
    player.add_item("iron_ore", 1)
    ids = {item_id for item_id, _, _ in CareManager().available_foods(player)}
    assert "salt_grilled_fish" in ids
    assert "iron_ore" not in ids
