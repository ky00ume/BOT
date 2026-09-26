from music_system import (
    can_start_instrument_performance, equip_instrument, equip_score,
    learn_melody, music_loadout, required_instrument,
)


def test_music_performance_requires_instrument_and_score(fresh_player):
    ok, msg = can_start_instrument_performance(fresh_player)
    assert ok is False and "악기" in msg
    equip_instrument(fresh_player, "lyre")
    ok, msg = can_start_instrument_performance(fresh_player)
    assert ok is False and "악보" in msg


def test_equipped_score_must_match_instrument(fresh_player):
    assert learn_melody(fresh_player, "eight_shadows")
    assert required_instrument("eight_shadows") == "lute"
    equip_score(fresh_player, "eight_shadows")
    equip_instrument(fresh_player, "lyre")
    ok, msg = can_start_instrument_performance(fresh_player)
    assert ok is False and "류트" in msg
    equip_instrument(fresh_player, "lute")
    ok, msg = can_start_instrument_performance(fresh_player)
    assert ok is True
    assert music_loadout(fresh_player)["score"] == "eight_shadows"


def test_music_loadout_survives_save_roundtrip(fresh_player):
    assert learn_melody(fresh_player, "shadowlantern")
    equip_score(fresh_player, "shadowlantern")
    equip_instrument(fresh_player, "lyre")
    data=fresh_player.get_save_data()
    clone=type(fresh_player)()
    clone.load_from_dict(data)
    assert music_loadout(clone)["score"] == "shadowlantern"
    assert music_loadout(clone)["instrument"] == "lyre"
