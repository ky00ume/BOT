from core.agency import AgencyLevel, rule_for, world_may_start


def test_world_only_starts_autonomous_life():
    assert world_may_start("rest") is True
    assert world_may_start("fishing") is False
    assert world_may_start("battle") is False
    assert world_may_start("quest") is False
    assert world_may_start("story") is False


def test_irreversible_choices_are_never_autonomous():
    assert rule_for("contract").level is AgencyLevel.FORBIDDEN_AUTONOMY
    assert rule_for("relationship_commitment").level is AgencyLevel.FORBIDDEN_AUTONOMY


def test_unknown_gameplay_defaults_to_player_control():
    assert rule_for("mysterious_future_feature").level is AgencyLevel.PLAYER_CONTROLLED
