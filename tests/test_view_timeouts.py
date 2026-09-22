import pytest

from player import Player
from care import CareManager
from ui.view_timeouts import CARE_VIEW_TIMEOUT, GAME_VIEW_TIMEOUT, SUBMENU_TIMEOUT


@pytest.mark.asyncio
async def test_chumagotchi_home_view_stays_alive_for_an_hour():
    from ui.care_ui import CareRoomView, TowerUpperFloorView

    player = Player()
    care = CareManager()
    assert CareRoomView(player, care).timeout == CARE_VIEW_TIMEOUT == 3600.0
    assert TowerUpperFloorView(player, care).timeout == CARE_VIEW_TIMEOUT


@pytest.mark.asyncio
async def test_town_navigation_uses_long_game_timeout():
    from ui.town_ui import ColonyPlaceView

    player = Player()
    view = ColonyPlaceView("마이코니드 군락 군주의 터", player, object(), object())
    assert view.timeout == GAME_VIEW_TIMEOUT == 1800.0


def test_timeout_policy_keeps_confirmations_separate():
    assert SUBMENU_TIMEOUT == 900.0
    assert GAME_VIEW_TIMEOUT > SUBMENU_TIMEOUT
    assert CARE_VIEW_TIMEOUT > GAME_VIEW_TIMEOUT
