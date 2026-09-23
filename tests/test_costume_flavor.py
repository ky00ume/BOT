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


def test_observation_shows_all_equipped_costume_flavors():
    player = Player()
    player.costume.update({
        "toy": "ct_toy_ball",
        "hat": "ct_hat_crown",
        "outfit": "ct_outfit_apron",
        "shoes": "ct_shoes_boots",
        "accessory": "ct_acc_brooch",
    })
    details = _observation_details(player)
    joined = " ".join(details)
    assert "털실 공" in joined
    assert "왕관" in joined
    assert "앞치마" in joined
    assert "리본" in joined
    assert "브로치" in joined


def test_room_embed_lists_all_equipped_costumes_compactly():
    from ui.care_ui import _make_room_embed

    player = Player()
    player.costume.update({
        "toy": "ct_toy_ball",
        "hat": "ct_hat_crown",
        "outfit": "ct_outfit_apron",
        "shoes": "ct_shoes_boots",
        "accessory": "ct_acc_brooch",
    })
    embed = _make_room_embed(player)
    field = next(f for f in embed.fields if f.name == "의장")
    assert all(name in field.value for name in ["털실 공", "작은 왕관", "앞치마", "리본 부츠", "별 브로치"])
