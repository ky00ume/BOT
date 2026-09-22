import time

import pytest

from care import CareManager, get_care_state
from player import Player


def test_care_state_defaults_are_persisted_in_flags():
    player = Player()
    state = get_care_state(player)
    assert state["hunger"] == 35
    assert state["cleanliness"] == 70
    assert state["boredom"] == 30
    assert state["comfort"] == 50
    assert state["wash_count"] == 0
    assert state["rest_count"] == 0
    assert state["rest_until"] == 0.0
    assert "pet_care" in player._flags


def test_wash_makes_churider_cleaner_and_has_cooldown():
    player = Player()
    player._flags["pet_care"] = {"hunger": 35, "cleanliness": 10, "boredom": 30, "comfort": 50, "wash_count": 0, "rest_count": 0}
    manager = CareManager()
    result = manager.wash(player)
    assert result["success"]
    assert get_care_state(player)["cleanliness"] > 10
    assert get_care_state(player)["wash_count"] == 1
    second = manager.wash(player)
    assert not second["success"]
    assert second["cooldown"]
    assert manager.get_wash_cooldown_remaining(player) > 0


def test_rest_is_a_timed_state_and_recovers_when_finished():
    player = Player()
    player.fatigue = 70
    manager = CareManager()
    result = manager.start_rest(player)
    assert result["success"]
    assert player.fatigue == 70
    assert manager.get_rest_status(player)["active"]
    player._flags["pet_care"]["rest_started_at"] = time.time() - manager.REST_DURATION
    player._flags["pet_care"]["rest_until"] = time.time() - 1
    finished = manager.finish_rest_if_ready(player)
    assert finished["success"]
    assert player.fatigue < 70
    assert not manager.get_rest_status(player)["active"]


def test_waking_early_gives_partial_rest_recovery():
    player = Player()
    player.fatigue = 70
    manager = CareManager()
    manager.start_rest(player)
    player._flags["pet_care"]["rest_started_at"] = time.time() - 300
    player._flags["pet_care"]["rest_until"] = time.time() + 900
    result = manager.finish_rest(player, wake_early=True)
    assert result["success"]
    assert 0 < result["fatigue_recovery"] < 22


def test_pet_increases_comfort_without_exposing_stat_to_user():
    player = Player()
    before = get_care_state(player)["comfort"]
    result = CareManager().pet(player)
    assert result["success"]
    assert get_care_state(player)["comfort"] > before


def test_play_can_continue_inside_same_session_even_after_cooldown_starts(monkeypatch):
    manager = CareManager()
    player = Player()
    monkeypatch.setattr("care.random.choice", lambda seq: "scissors")
    first = manager.play_result(player, "rock")
    assert first["success"]
    blocked = manager.play_result(player, "rock")
    assert not blocked["success"]
    again = manager.play_result(player, "rock", continue_session=True)
    assert again["success"]


@pytest.mark.asyncio
async def test_care_room_exposes_core_actions_without_redundant_nest_button():
    from ui.care_ui import CareRoomView

    player = Player()
    view = CareRoomView(player, CareManager())
    labels = {getattr(child, "label", None) for child in view.children}
    assert {"👀 관찰", "🫳 쓰다듬기", "🍖 먹이기", "🛁 씻기기", "🧶 놀기", "💤 쉬게 하기"} <= labels
    assert "🕸️ 보금자리" not in labels


def test_main_room_embed_keeps_status_visible_but_compact():
    from ui.care_ui import _make_room_embed

    player = Player()
    embed = _make_room_embed(player)
    assert embed.title == "🕷️ 츄라이더"
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "상태"
    assert "🍖" in embed.fields[0].value
    assert "🫧" in embed.fields[0].value
    assert "💤" in embed.fields[0].value
    assert "✨" in embed.fields[0].value


def test_observation_has_multiple_body_and_nest_details():
    from ui.care_ui import _observation_details

    player = Player()
    player._flags["pet_care"] = {"hunger": 90, "cleanliness": 10, "boredom": 80, "comfort": 50, "wash_count": 0, "rest_count": 0}
    details = _observation_details(player)
    text = " ".join(details)
    assert len(details) >= 4
    assert "먹을거리" in text
    assert "거미 복부" in text
    assert "실뭉치" in text


@pytest.mark.asyncio
async def test_petting_session_has_progressive_reactions():
    from ui.care_ui import PettingView

    player = Player()
    parent = object()
    view0 = PettingView(player, CareManager(), parent, step=0)
    view3 = PettingView(player, CareManager(), parent, step=3)
    assert view0.make_embed().description != view3.make_embed().description
    assert "🫳 계속 쓰다듬기" in {getattr(child, "label", "") for child in view0.children}


@pytest.mark.asyncio
async def test_rps_result_offers_again_or_stop():
    from ui.care_ui import RockPaperScissorsResultView

    player = Player()
    result = {"success": True, "message": "이겼슴미댜!", "player_choice": "✊", "bot_choice": "✌️"}
    view = RockPaperScissorsResultView(player, CareManager(), object(), result=result, rounds=1)
    labels = {getattr(child, "label", None) for child in view.children}
    assert labels == {"🔁 한 판 더", "그만 놀기"}
