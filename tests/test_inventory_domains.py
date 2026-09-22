from player import Player
from db.player import save_player_to_db, load_player_from_db


def _equipment_id():
    from items import ALL_ITEMS
    return next(i for i, d in ALL_ITEMS.items() if d.get("type") in {"weapon", "armor"})


def test_equipment_uses_separate_gear_bag():
    player = Player()
    equipment = _equipment_id()
    assert player.add_gear_item(equipment)
    assert equipment in player.gear_inventory
    assert equipment not in player.inventory


def test_battle_loot_can_be_claimed_by_domain():
    player = Player()
    equipment = _equipment_id()
    assert player.add_loot("herb", 2)
    assert player.add_loot(equipment, 1)
    assert player.claim_loot("herb", 2)
    assert player.claim_loot(equipment, 1)
    assert player.inventory["herb"] == 2
    assert player.gear_inventory[equipment] == 1
    assert player.loot_buffer == {}


def test_remaining_loot_can_auto_store_on_safe_return():
    player = Player()
    player.add_loot("mushroom", 3)
    moved = player.store_all_loot_at_home()
    assert moved == {"mushroom": 3}
    assert player.home_storage["mushroom"] == 3
    assert player.loot_buffer == {}


def test_equipped_items_do_not_consume_gear_bag_slots():
    player = Player()
    equipment = _equipment_id()
    player.add_gear_item(equipment)
    before = len(player.gear_inventory)
    message = player.equip_item(equipment)
    assert "장착" in message
    assert len(player.gear_inventory) == before - 1
    assert equipment in player.equipment.values()


def test_inventory_domains_persist(temp_db):
    player = Player()
    player.user_id = 8080
    equipment = _equipment_id()
    player.gear_inventory[equipment] = 1
    player.loot_buffer["herb"] = 2
    player.home_storage["mushroom"] = 4
    player.gear_bag_slots = 11
    player.home_storage_slots = 180
    save_player_to_db(player)
    loaded = load_player_from_db(8080)
    assert loaded["gear_inventory"] == {equipment: 1}
    assert loaded["loot_buffer"] == {"herb": 2}
    assert loaded["home_storage"] == {"mushroom": 4}
    assert loaded["gear_bag_slots"] == 11
    assert loaded["home_storage_slots"] == 180
