from rest import rest_allows, interrupt_rest


def test_rest_allows_gentle_town_life():
    assert rest_allows("town")
    assert rest_allows("fishing_near_town")
    assert rest_allows("gather_near_town")
    assert not rest_allows("battle")
    assert not rest_allows("adventure")


def test_strenuous_action_clears_player_rest_status(fresh_player):
    fresh_player.is_resting = True
    fresh_player._flags["is_resting"] = True
    assert interrupt_rest(fresh_player, "battle") is True
    assert fresh_player.is_resting is False
    assert fresh_player._flags["is_resting"] is False
