from blacksmith import BLACKSMITH_STAGES, BlacksmithEngine, quality_tier
from player import Player
from ui.skill_ui import BlacksmithForgeView


class FixedRng:
    def __init__(self, values):
        self.values = iter(values)

    def randint(self, lo, hi):
        value = next(self.values)
        assert lo <= value <= hi
        return value


def _ready_player():
    p = Player()
    p.inventory["iron_bar"] = 3
    p.inventory["gt_wood_01"] = 1
    return p


def test_blacksmith_session_is_heat_hammer_finish():
    assert BLACKSMITH_STAGES == ("heat", "hammer", "finish")
    p = _ready_player()
    engine = BlacksmithEngine(p)
    session = engine.start_session("wp_sword_02")
    assert session["success"] is True
    assert session["stage_index"] == 0
    assert session["quality"] == 50


def test_three_steps_move_quality_and_only_finish_consumes_materials():
    p = _ready_player()
    engine = BlacksmithEngine(p)
    session = engine.start_session("wp_sword_02")
    rng = FixedRng([15, 12, 10])

    r1 = engine.apply_stage(session, "steady", rng=rng)
    assert r1["stage"] == "heat" and r1["quality"] == 65
    assert p.inventory["iron_bar"] == 3

    r2 = engine.apply_stage(session, "steady", rng=rng)
    assert r2["stage"] == "hammer" and r2["quality"] == 77
    assert p.inventory["iron_bar"] == 3

    r3 = engine.apply_stage(session, "careful", rng=rng)
    assert r3["stage"] == "finish" and r3["quality"] == 87 and r3["complete"] is True
    assert p.inventory["iron_bar"] == 3

    result = engine.finish_session(session)
    assert result["success"] is True
    assert result["quality_score"] == 87
    assert result["quality_label"] == "✨ 훌륭함"
    assert p.inventory.get("iron_bar", 0) == 0
    assert p.gear_inventory.get("wp_sword_02", 0) == 1


def test_risky_action_can_lower_quality():
    p = _ready_player()
    engine = BlacksmithEngine(p)
    session = engine.start_session("wp_sword_02")
    result = engine.apply_stage(session, "hot", rng=FixedRng([-8]))
    assert result["delta"] == -8
    assert result["quality"] == 42


def test_quality_tiers_cover_rough_to_masterpiece():
    assert quality_tier(20)[1] == "🪨 거침"
    assert quality_tier(50)[1] == "⚒️ 보통"
    assert quality_tier(65)[1] == "🔷 양호"
    assert quality_tier(80)[1] == "✨ 훌륭함"
    assert quality_tier(95)[1] == "🏆 걸작"


import pytest


@pytest.mark.asyncio
async def test_ui_starts_with_three_heat_choices_and_quality_gauge():
    p = _ready_player()
    engine = BlacksmithEngine(p)
    session = engine.start_session("wp_sword_02")

    class Parent:
        player = p
        blacksmith_engine = engine

    view = BlacksmithForgeView(Parent(), "wp_sword_02", session)
    labels = {getattr(child, "label", "") for child in view.children}
    assert labels == {"약불로 천천히", "적정 화력 유지", "강불로 밀어붙이기"}
    embed = view.make_embed()
    assert "가열" in embed.title
    assert "50/100" in embed.fields[1].value
