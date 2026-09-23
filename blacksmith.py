"""마비노기풍 대장장이 생활 스킬 패러디.

기존 장비 제작 레시피 중 금속 장비를 별도 '블랙스미스' 스킬로 다룬다.
"""
from crafting import CRAFTING_RECIPES
from items import ALL_ITEMS
from utils.ranks import rank_gte

BLACKSMITH_RECIPES = {
    rid: recipe for rid, recipe in CRAFTING_RECIPES.items()
    if rid.startswith(("wp_sword_", "ar_helm_", "ar_body_", "ar_glove_"))
}


class BlacksmithEngine:
    def __init__(self, player):
        self.player = player
        self.recipes = BLACKSMITH_RECIPES

    def forge(self, recipe_id: str) -> dict:
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "error": "블랙스미스 도면을 찾을 수 없습니다.", "recipe_name": recipe_id, "system_key": "craft"}
        rank = self.player.skill_ranks.get("blacksmith", "연습")
        req = recipe.get("rank_req", "연습")
        # 연습 랭크에서는 F랭 기본 도면으로 첫 수련을 시작할 수 있다.
        effective_rank = "F" if rank == "연습" and req == "F" else rank
        if not rank_gte(effective_rank, req):
            return {"success": False, "error": f"랭크 부족 (필요: {req}, 현재: {rank})", "recipe_name": recipe["name"], "system_key": "craft"}
        for item_id, count in recipe.get("ingredients", {}).items():
            if self.player.inventory.get(item_id, 0) < count:
                name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                return {"success": False, "error": f"재료 부족: {name} x{count}", "recipe_name": recipe["name"], "system_key": "craft"}
        ingredients = []
        for item_id, count in recipe["ingredients"].items():
            self.player.remove_item(item_id, count)
            ingredients.append((ALL_ITEMS.get(item_id, {}).get("name", item_id), count))
        result_id = recipe.get("result", recipe_id)
        self.player.add_gear_item(result_id, 1) or self.player.add_item(result_id, 1)
        exp = recipe.get("exp", 30.0)
        rank_msg = self.player.train_skill("blacksmith", exp)
        return {
            "success": True,
            "recipe_name": recipe["name"],
            "result_name": ALL_ITEMS.get(result_id, {}).get("name", result_id),
            "result_grade": ALL_ITEMS.get(result_id, {}).get("grade", "Normal"),
            "ingredients": ingredients,
            "exp": exp,
            "rank_up_msg": rank_msg or "",
            "system_key": "craft",
        }
