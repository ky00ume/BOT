from unittest.mock import patch

from item_grade import GRADE_LABEL, grade_display, item_grade
from player import Player
from cooking_db import CookingEngine


def test_common_grade_applies_to_fish_and_cooking_ingredients():
    assert item_grade("fs_salmon_01") == "Rare"
    assert item_grade("pine_mushroom") == "Rare"
    assert item_grade("sussur_bloom") == "Epic"
    assert grade_display("Legendary") == "✦ 전설"
    assert GRADE_LABEL["Normal"] == "일반"


def test_cooking_result_keeps_ingredient_grades():
    player = Player()
    player.skill_ranks["cooking"] = "1"
    player.inventory.update({"fs_salmon_01": 1, "water": 1, "salt": 1, "tool_pot": 1})
    engine = CookingEngine(player)

    with patch("cooking_db.random.random", return_value=0.0):
        result = engine.cook("steamed_salmon")

    assert result["success"] is True
    grades = {row["id"]: row["grade"] for row in result["ingredient_details"]}
    assert grades["fs_salmon_01"] == "Rare"
    assert grades["water"] == "Normal"
    assert grades["salt"] == "Normal"


def test_recipe_list_shows_ingredient_grade_labels():
    player = Player()
    player.skill_ranks["cooking"] = "1"
    text = CookingEngine(player).show_recipe_list()
    assert "◆ 희귀" in text
    assert "⚬ 일반" in text
