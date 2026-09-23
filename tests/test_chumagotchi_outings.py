from pathlib import Path

from care import CareManager, apply_outing_effect, get_care_state
from player import Player


def test_fishing_outing_changes_needs_and_leaves_persistent_trace():
    player = Player()
    state = get_care_state(player)
    before = dict(state)
    before_fatigue = player.fatigue

    result = apply_outing_effect(player, "fishing")
    after = get_care_state(player)

    assert result["kind"] == "fishing"
    assert after["hunger"] > before["hunger"]
    assert after["boredom"] < before["boredom"]
    assert after["cleanliness"] < before["cleanliness"]
    assert player.fatigue > before_fatigue
    assert after["traces"][-1]["kind"] == "fishing"
    assert "물비린내" in after["traces"][-1]["text"]


def test_battle_is_more_tiring_and_dirtier_than_walk():
    walking = Player()
    battling = Player()
    get_care_state(walking)
    get_care_state(battling)

    apply_outing_effect(walking, "walk")
    apply_outing_effect(battling, "battle")

    walk_state = get_care_state(walking)
    battle_state = get_care_state(battling)
    assert battle_state["cleanliness"] < walk_state["cleanliness"]
    assert battling.fatigue > walking.fatigue


def test_washing_removes_outing_traces():
    player = Player()
    apply_outing_effect(player, "gathering")
    assert get_care_state(player)["traces"]

    result = CareManager().wash(player)

    assert result["success"]
    assert get_care_state(player)["traces"] == []


def test_observation_surfaces_latest_outing_trace():
    from ui.care_ui import _observation_details

    player = Player()
    apply_outing_effect(player, "woodcut")
    text = " ".join(_observation_details(player))
    assert "톱밥" in text


def test_chumagotchi_description_sources_do_not_use_mimida_narration():
    root = Path(__file__).resolve().parents[1]
    for rel in ["care.py", "ui/care_ui.py"]:
        text = (root / rel).read_text(encoding="utf-8")
        assert "슴미댜" not in text
        assert "입미댜" not in text
        assert "합니댜" not in text
