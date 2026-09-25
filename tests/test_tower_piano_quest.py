from types import SimpleNamespace

from tower_exhibition import ensure_state, piano_quest_state, advance_piano_quest, piano_unlocked

def player_with(count):
    return SimpleNamespace(tower_state={"exhibition":{"displayed":[f"x{i}" for i in range(count)],"claimed":[]}})

def test_piano_quest_unlocks_after_first_exhibition_resonance():
    p=player_with(2); assert piano_quest_state(p)=="locked"
    p.tower_state["exhibition"]["displayed"].append("x2")
    assert piano_quest_state(p)=="available"

def test_piano_quest_advances_to_restored():
    p=player_with(3)
    assert piano_quest_state(p)=="available"
    assert advance_piano_quest(p)=="found"
    assert advance_piano_quest(p)=="opened"
    assert advance_piano_quest(p)=="restored"
    assert piano_unlocked(p)
    assert advance_piano_quest(p)=="restored"


def test_restored_piano_unlocks_three_drow_hymns():
    from tower_exhibition import piano_repertoire
    p=player_with(3)
    for _ in range(3): advance_piano_quest(p)
    songs=piano_repertoire(p)
    assert set(songs)=={"lolth_hymn","eilistraee_hymn","vhaeraun_hymn"}
