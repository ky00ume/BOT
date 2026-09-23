from player import Player
from ui.care_ui import _churider_mark, _make_room_embed, _make_walk_progress_embed


def _equipped_player():
    p = Player()
    p.costume["hat"] = "ct_hat_crown"
    p.costume["toy"] = "ct_toy_ball"
    return p


def test_featured_costume_must_be_equipped_and_persists_in_flags():
    p = _equipped_player()
    assert p.set_featured_costume("ct_hat_crown")
    assert p.get_featured_costume() == "ct_hat_crown"
    assert p._flags["featured_costume"] == "ct_hat_crown"
    assert not p.set_featured_costume("ct_hat_witch")


def test_featured_costume_is_cleared_when_unequipped():
    p = _equipped_player()
    p.set_featured_costume("ct_hat_crown")
    p.unequip_costume("hat")
    assert p.get_featured_costume() is None


def test_room_and_walk_show_featured_item_next_to_spider():
    p = _equipped_player()
    p.set_featured_costume("ct_hat_crown")
    room = _make_room_embed(p)
    assert room.title.startswith("🕷️ 👑")
    assert any(f.name == "⭐ 대표 의장" and "작은 왕관" in f.value for f in room.fields)
    walk = _make_walk_progress_embed("indoor", 24, 0, player=p)
    assert walk.title.startswith("🕷️ 👑")


def test_only_one_featured_costume_at_a_time():
    p = _equipped_player()
    p.set_featured_costume("ct_hat_crown")
    p.set_featured_costume("ct_toy_ball")
    assert p.get_featured_costume() == "ct_toy_ball"
