import pytest

from care import CareManager
from player import Player
from ui.town_ui import GatheringZoneView, WorldMapView
from world_activities import WORLD_ACTIVITY_ZONES, activities_for


def _zones(location, kind=None):
    rows = activities_for(location)
    if kind:
        rows = [row for row in rows if row["kind"] == kind]
    return {row["zone"] for row in rows}


def test_first_pass_places_have_local_activity_distribution():
    assert _zones("마이코니드 군락", "gather") == {"마이코니드 군락 외곽"}
    assert _zones("드레드 할로우", "hunt") == {"드레드 할로우"}
    assert _zones("드레드 할로우", "gather") == {"수서 나무 숲"}
    assert _zones("에본레이크", "fish") == {
        "에본레이크 북안",
        "에본레이크 얕은 물가",
        "에본레이크 선착장",
    }
    assert _zones("그림포지", "hunt") == {"그림포지"}
    assert _zones("그림포지", "mine") == {"그림포지 광맥"}
    assert _zones("그림포지", "fish") == {"그림포지 용암지대"}


@pytest.mark.asyncio
async def test_world_map_only_shows_activities_at_current_location():
    player = Player()
    player.current_location = "에본레이크"
    view = WorldMapView(player, None, None)
    labels = {getattr(child, "label", "") for child in view.children}
    assert "북안 낚시터" in labels
    assert "얕은 물가" in labels
    assert "선착장 낚시터" in labels
    assert "드레드 할로우 사냥터" not in labels
    assert "그림포지 광맥" not in labels


@pytest.mark.asyncio
async def test_gathering_subzones_expose_only_their_supported_actions():
    player = Player()
    mushroom = GatheringZoneView("마이코니드 군락 외곽", player, None, None)
    forest = GatheringZoneView("수서 나무 숲", player, None, None)
    mine = GatheringZoneView("그림포지 광맥", player, None, None)

    mushroom_labels = {getattr(c, "label", "") for c in mushroom.children}
    forest_labels = {getattr(c, "label", "") for c in forest.children}
    mine_labels = {getattr(c, "label", "") for c in mine.children}

    assert "채집" in mushroom_labels and "채광" not in mushroom_labels and "벌목" not in mushroom_labels
    assert "채집" in forest_labels and "벌목" in forest_labels and "채광" not in forest_labels
    assert "채광" in mine_labels and "채집" not in mine_labels and "벌목" not in mine_labels


def test_activity_zone_ids_exist_in_their_engines():
    from fishing import FISH_GUIDE
    from monsters_db import MONSTERS_DB
    from gathering import GATHER_ZONE_ITEMS, MINE_ZONE_ITEM_IDS

    for location, rows in WORLD_ACTIVITY_ZONES.items():
        for row in rows:
            if row["kind"] == "hunt":
                assert row["zone"] in MONSTERS_DB
            elif row["kind"] == "fish":
                assert row["zone"] in FISH_GUIDE
            elif row["kind"] == "gather" and row["zone"] == "마이코니드 군락 외곽":
                assert row["zone"] in GATHER_ZONE_ITEMS
            elif row["kind"] == "mine":
                assert row["zone"] in MINE_ZONE_ITEM_IDS
