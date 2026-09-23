from costume_data import COSTUME_RECIPES
from ui.care_ui import WALK_RARE_EVENTS


def test_every_walk_rare_bonus_item_is_used_by_a_costume_recipe():
    bonus_items = {
        event["bonus_item"]
        for events in WALK_RARE_EVENTS.values()
        for event in events.values()
        if event.get("bonus_item")
    }
    costume_materials = {
        material
        for recipe in COSTUME_RECIPES.values()
        for material in recipe["materials"]
    }
    assert bonus_items <= costume_materials


def test_magic_dust_is_a_real_costume_material_not_snack_only():
    consumers = {
        costume_id
        for costume_id, recipe in COSTUME_RECIPES.items()
        if "mat_magic_dust" in recipe["materials"]
    }
    assert {"ct_toy_magic_wand", "ct_hat_witch", "ct_shoes_magic"} <= consumers
