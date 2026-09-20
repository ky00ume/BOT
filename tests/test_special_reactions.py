from core.special_reactions import reaction_for


def test_lily_is_suspicious_flavour_without_relationship_split():
    reaction = reaction_for(11, suspicious_actor_id=11)
    assert reaction is not None
    assert "으심" in reaction.room_arrival
    assert "수상" in reaction.pet
    assert "신뢰는 별개" in reaction.feed


def test_friend_gets_no_suspicious_override():
    assert reaction_for(22, suspicious_actor_id=11) is None
