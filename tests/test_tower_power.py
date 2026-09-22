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

