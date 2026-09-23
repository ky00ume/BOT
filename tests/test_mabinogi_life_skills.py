from blacksmith import BLACKSMITH_RECIPES, BlacksmithEngine
from player import Player
from skills_db import OTHER_SKILLS
from world_activities import activities_for


def test_mining_metallurgy_blacksmith_are_separate_life_skills():
    assert OTHER_SKILLS["mining"]["name"] == "채광"
    assert OTHER_SKILLS["metallurgy"]["name"] == "제련"
    assert OTHER_SKILLS["blacksmith"]["name"] == "블랙스미스"


def test_blacksmith_uses_metal_equipment_recipes_only():
    assert BLACKSMITH_RECIPES
    assert all(rid.startswith(("wp_sword_", "ar_helm_", "ar_body_", "ar_glove_")) for rid in BLACKSMITH_RECIPES)


def test_blacksmith_forging_consumes_bars_and_trains_blacksmith():
    p = Player()
    p.inventory["iron_bar"] = 3
    p.inventory["gt_wood_01"] = 1
    engine = BlacksmithEngine(p)
    result = engine.forge("wp_sword_02")
    assert result["success"] is True
    assert p.skill_ranks.get("blacksmith") is not None
    assert p.skill_exp.get("blacksmith", 0) > 0
    assert p.inventory.get("iron_bar", 0) == 0


def test_high_tier_resource_locations_are_distributed():
    adamantine = activities_for("아다만틴 대장간")
    bibberbang = activities_for("비버뱅 군락")
    selune = activities_for("셀루네 전초기지")
    shar = activities_for("샤의 고대 사원")
    assert any(x["zone"] == "아다만틴 심층 광맥" and x["kind"] == "mine" for x in adamantine)
    assert any(x["zone"] == "비버뱅 군락지" and x["kind"] == "gather" for x in bibberbang)
    assert any(x["zone"] == "셀루네 수정지" and x["kind"] == "gather" for x in selune)
    assert any(x["zone"] == "샤의 잔해 채집지" and x["kind"] == "gather" for x in shar)
