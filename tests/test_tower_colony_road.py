import pytest

from care import CareManager
from movement import MAP_NODES
from player import Player
from ui.care_ui import TowerColonyRoadView, TowerUpperFloorView
from ui.town_ui import VisionTownView


def test_tower_and_colony_are_direct_neighbors_in_world_map():
    assert "마이코니드 군락" in MAP_NODES["비전의 탑"]["adjacent"]
    assert "비전의 탑" in MAP_NODES["마이코니드 군락"]["adjacent"]


@pytest.mark.asyncio
async def test_tower_upper_floor_exposes_colony_road_button():
    view = TowerUpperFloorView(Player(), CareManager())
    labels = {getattr(child, "label", "") for child in view.children}
    assert "군락으로 가는 길" in labels


@pytest.mark.asyncio
async def test_road_has_three_same_message_stages_each_direction():
    p = Player()
    cm = CareManager()
    out = TowerColonyRoadView(p, cm, direction="to_colony")
    back = TowerColonyRoadView(p, cm, direction="to_tower")
    assert len(out.ROUTES["to_colony"]) == 3
    assert len(back.ROUTES["to_tower"]) == 3
    assert "1/3" in out.make_embed().fields[0].value
    final = TowerColonyRoadView(p, cm, direction="to_colony", step=2)
    assert "3/3" in final.make_embed().fields[0].value
    assert "군락으로 들어간다" in {getattr(c, "label", "") for c in final.children}


@pytest.mark.asyncio
async def test_colony_view_has_tower_road_and_world_map_exit():
    view = VisionTownView(Player(), None, None, care_manager=CareManager())
    labels = {getattr(child, "label", "") for child in view.children}
    assert "비전의 탑으로 가는 길" in labels
    assert "언더다크로 나간다" in labels


@pytest.mark.asyncio
async def test_arrival_callback_updates_location_without_import_error(monkeypatch):
    import ui.care_ui as care_ui

    class DummyResponse:
        def __init__(self):
            self.edits = []
        async def edit_message(self, **kwargs):
            self.edits.append(kwargs)

    class DummyInteraction:
        def __init__(self):
            self.response = DummyResponse()
            self.message = object()

    monkeypatch.setattr(care_ui, "save_player_to_db", lambda player: None)

    player = Player()
    view = TowerColonyRoadView(player, CareManager(), direction="to_tower", step=2)
    interaction = DummyInteraction()
    await view._arrive(interaction)

    assert player.current_location == "비전의 탑"
    assert interaction.response.edits
