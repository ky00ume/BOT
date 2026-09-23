from costume_data import COSTUME_FLAVOR, COSTUME_ITEMS
from player import Player
from ui.care_ui import _observation_details


def test_every_costume_has_unique_flavor_triplet():
    assert set(COSTUME_FLAVOR) == set(COSTUME_ITEMS)
    for item_id, flavor in COSTUME_FLAVOR.items():
        assert flavor.get("equip")
        assert flavor.get("observe")
        assert flavor.get("craft")


def test_costume_observation_uses_equipped_item_flavor():
    player = Player()
    player.costume["hat"] = "ct_hat_crown"
    details = _observation_details(player)
    assert any("왕관" in detail for detail in details)


def test_different_costumes_have_different_observation_text():
    assert COSTUME_FLAVOR["ct_hat_ribbon"]["observe"] != COSTUME_FLAVOR["ct_hat_witch"]["observe"]
    assert COSTUME_FLAVOR["ct_toy_ball"]["equip"] != COSTUME_FLAVOR["ct_toy_magic_wand"]["equip"]
