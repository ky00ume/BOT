"""tests/test_crafting.py — CraftingEngine 단위 테스트"""
import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _give_ingredients(player, recipe: dict):
    """플레이어 인벤토리에 레시피 재료를 충분히 추가합니다."""
    for ing_id, cnt in recipe["ingredients"].items():
        player.inventory[ing_id] = player.inventory.get(ing_id, 0) + cnt


# ── craft ────────────────────────────────────────────────────────────────────

class TestCraft:
    def test_craft_success(self, crafting_engine):
        from crafting import CRAFTING_RECIPES
        # '연습' 랭크로 제작 가능한 레시피 선택
        recipe_id = None
        for rid, rec in CRAFTING_RECIPES.items():
            if rec.get("rank_req", "연습") in ("연습", "F"):
                recipe_id = rid
                recipe = rec
                break
        if recipe_id is None:
            pytest.skip("연습/F 랭크 레시피 없음")

        crafting_engine.player.skill_ranks["crafting"] = recipe["rank_req"]
        _give_ingredients(crafting_engine.player, recipe)

        result = crafting_engine.craft(recipe_id)
        assert result["success"] is True
        assert result["system_key"] == "craft"
        assert crafting_engine.player.inventory.get(recipe["result"], 0) >= 1

    def test_craft_ingredients_consumed(self, crafting_engine):
        from crafting import CRAFTING_RECIPES
        recipe_id = "con_hp_potion"
        recipe = CRAFTING_RECIPES.get(recipe_id)
        if recipe is None:
            pytest.skip("con_hp_potion 레시피 없음")

        crafting_engine.player.skill_ranks["crafting"] = "연습"
        # 정확히 필요한 수량만 지급
        for ing_id, cnt in recipe["ingredients"].items():
            crafting_engine.player.inventory[ing_id] = cnt

        crafting_engine.craft(recipe_id)

        # 재료가 소모됐는지 확인
        for ing_id, cnt in recipe["ingredients"].items():
            assert crafting_engine.player.inventory.get(ing_id, 0) == 0

    def test_craft_nonexistent_recipe(self, crafting_engine):
        result = crafting_engine.craft("totally_fake_recipe_xyz")
        assert result["success"] is False
        assert "레시피 없음" in result["error"]

    def test_craft_rank_insufficient(self, crafting_engine):
        from crafting import CRAFTING_RECIPES
        # A 이상 랭크 필요 레시피 선택
        recipe_id = None
        for rid, rec in CRAFTING_RECIPES.items():
            if rec.get("rank_req") in ("A", "B", "S", "5", "4"):
                recipe_id = rid
                recipe = rec
                break
        if recipe_id is None:
            pytest.skip("고급 랭크 레시피 없음")

        crafting_engine.player.skill_ranks["crafting"] = "연습"
        _give_ingredients(crafting_engine.player, recipe)

        result = crafting_engine.craft(recipe_id)
        assert result["success"] is False
        assert "랭크" in result["error"]

    def test_craft_missing_ingredients(self, crafting_engine):
        from crafting import CRAFTING_RECIPES
        recipe_id = "con_hp_potion"
        recipe = CRAFTING_RECIPES.get(recipe_id)
        if recipe is None:
            pytest.skip("con_hp_potion 레시피 없음")

        crafting_engine.player.skill_ranks["crafting"] = "연습"
        # 재료를 주지 않음
        crafting_engine.player.inventory = {}

        result = crafting_engine.craft(recipe_id)
        assert result["success"] is False
        assert "재료 부족" in result["error"]


# ── show_recipe_list ─────────────────────────────────────────────────────────

class TestShowRecipeList:
    def test_returns_string(self, crafting_engine):
        result = crafting_engine.show_recipe_list()
        assert isinstance(result, str)

    def test_contains_recipe_names(self, crafting_engine):
        from crafting import CRAFTING_RECIPES
        result = crafting_engine.show_recipe_list()
        # 첫 번째 레시피 이름이 목록에 포함되어야 함
        first_recipe = next(iter(CRAFTING_RECIPES.values()))
        assert first_recipe["name"] in result

    def test_locked_recipe_shown(self, crafting_engine):
        result = crafting_engine.show_recipe_list()
        assert "미해금" in result or "가능" in result
