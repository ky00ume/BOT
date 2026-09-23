import pytest

from care import CareManager, get_care_state
from player import Player
from ui.care_ui import PettingView


@pytest.mark.asyncio
async def test_each_petting_spot_has_multiple_variants_at_every_depth():
    for spot, depths in PettingView.REACTIONS.items():
        assert len(depths) == 3, spot
        assert all(len(variants) >= 4 for variants in depths), spot


@pytest.mark.asyncio
async def test_repeated_same_spot_can_end_in_special_combo(monkeypatch):
    player = Player()
    view = PettingView(player, CareManager(), object(), step=2, history=["head", "head"])
    monkeypatch.setattr("ui.care_ui.random.random", lambda: 0.0)
    result = view._pick_reaction("head", 3, ["head", "head"])
    assert "여기가 제일 좋슴미댜" in result


@pytest.mark.asyncio
async def test_recent_reactions_are_avoided_when_alternatives_exist(monkeypatch):
    player = Player()
    view = PettingView(player, CareManager(), object())
    first = PettingView.REACTIONS["head"][0][0]
    player._flags["pet_reaction_recent"] = [first]
    monkeypatch.setattr("ui.care_ui.random.choice", lambda seq: seq[0])
    picked = view._pick_reaction("head", 1, [])
    assert picked != first


@pytest.mark.asyncio
async def test_state_specific_petting_reactions_exist():
    player = Player()
    player.fatigue = 80
    state = get_care_state(player)
    state_ref = player._flags["pet_care"]
    state_ref["cleanliness"] = 10
    state_ref["comfort"] = 90
    view = PettingView(player, CareManager(), object())
    assert any("졸림미댜" in x for x in [view._pick_reaction("head", 1, [])] + PettingView.REACTIONS["head"][0]) or player.fatigue >= 65
    assert state_ref["cleanliness"] < 35
    assert state_ref["comfort"] >= 75
