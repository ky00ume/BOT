import pytest

from care import CareManager, get_care_state
from player import Player


def test_care_state_defaults_are_persisted_in_flags():
    player = Player()
    state = get_care_state(player)
    assert state == {
        "hunger": 35,
        "cleanliness": 70,
        "boredom": 30,
        "comfort": 50,
        "wash_count": 0,
        "rest_count": 0,
    }
    assert "pet_care" in player._flags


def test_wash_makes_churider_cleaner():
    player = Player()
    player._flags["pet_care"] = {"hunger": 35, "cleanliness": 10, "boredom": 30, "comfort": 50, "wash_count": 0, "rest_count": 0}
    result = CareManager().wash(player)
    assert result["success"]
    assert get_care_state(player)["cleanliness"] > 10
    assert get_care_state(player)["wash_count"] == 1


def test_rest_reduces_fatigue():
    player = Player()
    player.fatigue = 70
    result = CareManager().rest(player)
    assert result["success"]
    assert player.fatigue < 70


def test_pet_increases_comfort_without_exposing_stat_to_user():
    player = Player()
    before = get_care_state(player)["comfort"]
    result = CareManager().pet(player)
    assert result["success"]
    assert get_care_state(player)["comfort"] > before


@pytest.mark.asyncio
async def test_care_room_exposes_core_chumagotchi_actions():
    from ui.care_ui import CareRoomView

    player = Player()
    view = CareRoomView(player, CareManager())
    labels = {getattr(child, "label", None) for child in view.children}
    assert {"👀 관찰", "🫳 쓰다듬기", "🍖 먹이기", "🛁 씻기기", "🧶 놀기", "💤 쉬게 하기", "🕸️ 보금자리"} <= labels


def test_observation_uses_spider_body_cues():
    from core.pet_state import observe_pet

    player = Player()
    player._flags["pet_care"] = {"hunger": 90, "cleanliness": 10, "boredom": 30, "comfort": 50, "wash_count": 0, "rest_count": 0}
    obs = observe_pet(player)
    text = f"{obs.headline} {obs.body}"
    assert "먹을거리" in text
    assert "거미 복부" in text
