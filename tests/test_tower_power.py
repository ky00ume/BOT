from player import Player
from tower_power import ensure_tower_state, restore_generator, restore_facility, facility_online


def test_sussur_bloom_restores_tower_generator_and_lift():
    player = Player()
    player.inventory["sussur_bloom"] = 1
    assert restore_generator(player)
    assert "sussur_bloom" not in player.inventory
    assert ensure_tower_state(player)["generator_online"] is True
    assert facility_online(player, "lift")


def test_generator_does_not_consume_another_bloom_once_online():
    player = Player()
    player.inventory["sussur_bloom"] = 2
    assert restore_generator(player)
    assert not restore_generator(player)
    assert player.inventory["sussur_bloom"] == 1


def test_facility_restoration_expands_tower_storage():
    player = Player()
    player.inventory["sussur_bloom"] = 1
    restore_generator(player)
    player.inventory.update({"iron_ore": 9, "spider_web": 2, "herb": 3, "hard_horn": 1})
    assert player.home_storage_slots == 120
    assert restore_facility(player, "storage")
    assert player.home_storage_slots == 160
    assert restore_facility(player, "pantry")
    assert player.home_storage_slots == 180
    assert restore_facility(player, "gear_storage")
    assert player.home_storage_slots == 220


def test_tower_power_state_roundtrips_through_player_save_data():
    player = Player()
    player.inventory["sussur_bloom"] = 1
    restore_generator(player)
    player.inventory.update({"iron_ore": 3, "spider_web": 2})
    restore_facility(player, "storage")
    saved = player.get_save_data()
    loaded = Player()
    loaded.load_from_dict(saved)
    assert facility_online(loaded, "lift")
    assert facility_online(loaded, "storage")
    assert loaded.home_storage_slots == 160


import pytest

@pytest.mark.asyncio
async def test_storage_floor_exposes_generator_button():
    from ui.care_ui import TowerPlaceView
    player = Player()
    view = TowerPlaceView(player, object(), place="storage")
    assert any(getattr(child, "label", None) == "수서 발전기" for child in view.children)



def test_facility_restoration_requires_and_consumes_materials():
    player = Player()
    player.inventory.update({"sussur_bloom": 1, "iron_ore": 3, "spider_web": 2})
    restore_generator(player)
    assert restore_facility(player, "storage")
    assert player.inventory.get("iron_ore", 0) == 0
    assert player.inventory.get("spider_web", 0) == 0


@pytest.mark.asyncio
async def test_lift_is_blocked_until_generator_is_online():
    from ui.care_ui import TowerPlaceView
    player = Player()
    view = TowerPlaceView(player, object(), place="upper")
    class Response:
        def __init__(self): self.kwargs = None
        async def edit_message(self, **kwargs): self.kwargs = kwargs
    class Interaction:
        def __init__(self): self.response = Response()
    interaction = Interaction()
    await view._open_lift(interaction)
    assert interaction.response.kwargs["embed"].fields[0].name == "멈춘 승강기"
