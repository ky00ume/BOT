"""마비노기풍 대장장이 생활 스킬 패러디.

기존 장비 제작 레시피 중 금속 장비를 별도 '블랙스미스' 스킬로 다룬다.
"""
from crafting import CRAFTING_RECIPES
from items import ALL_ITEMS
from utils.ranks import rank_gte

BLACKSMITH_STAGES = ("heat", "hammer", "finish")
BLACKSMITH_STAGE_LABELS = {
    "heat": "🔥 가열",
    "hammer": "🔨 두드리기",
    "finish": "✨ 마감",
}
BLACKSMITH_ACTIONS = {
    "heat": {
        "low": ("약불로 천천히", 4, 10),
        "steady": ("적정 화력 유지", 10, 18),
        "hot": ("강불로 밀어붙이기", -8, 16),
    },
    "hammer": {
        "light": ("가볍게 두드리기", 4, 10),
        "steady": ("균형 있게 두드리기", 9, 16),
        "heavy": ("강하게 내려치기", -10, 17),
    },
    "finish": {
        "quick": ("빠르게 마감", 2, 8),
        "careful": ("정성껏 마감", 8, 14),
        "polish": ("광택까지 다듬기", 5, 12),
    },
}


def quality_tier(score: int) -> tuple[str, str]:
    if score >= 90:
        return "Masterpiece", "🏆 걸작"
    if score >= 75:
        return "Excellent", "✨ 훌륭함"
    if score >= 60:
        return "Fine", "🔷 양호"
    if score >= 40:
        return "Normal", "⚒️ 보통"
    return "Rough", "🪨 거침"


BLACKSMITH_RECIPES = {
    rid: recipe for rid, recipe in CRAFTING_RECIPES.items()
    if rid.startswith(("wp_sword_", "ar_helm_", "ar_body_", "ar_glove_"))
}


class BlacksmithEngine:
    def __init__(self, player):
        self.player = player
        self.recipes = BLACKSMITH_RECIPES

    def validate_recipe(self, recipe_id: str) -> dict:
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "error": "블랙스미스 도면을 찾을 수 없습니다.", "recipe_name": recipe_id, "system_key": "craft"}
        rank = self.player.skill_ranks.get("blacksmith", "연습")
        req = recipe.get("rank_req", "연습")
        effective_rank = "F" if rank == "연습" and req == "F" else rank
        if not rank_gte(effective_rank, req):
            return {"success": False, "error": f"랭크 부족 (필요: {req}, 현재: {rank})", "recipe_name": recipe["name"], "system_key": "craft"}
        for item_id, count in recipe.get("ingredients", {}).items():
            if self.player.inventory.get(item_id, 0) < count:
                name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                return {"success": False, "error": f"재료 부족: {name} x{count}", "recipe_name": recipe["name"], "system_key": "craft"}
        return {"success": True, "recipe": recipe}

    def start_session(self, recipe_id: str) -> dict:
        valid = self.validate_recipe(recipe_id)
        if not valid.get("success"):
            return valid
        return {
            "success": True,
            "recipe_id": recipe_id,
            "recipe_name": valid["recipe"]["name"],
            "stage_index": 0,
            "quality": 50,
            "history": [],
        }

    def apply_stage(self, session: dict, action_id: str, *, rng=None) -> dict:
        import random
        rng = rng or random
        idx = int(session.get("stage_index", 0))
        if idx >= len(BLACKSMITH_STAGES):
            return {"success": False, "error": "이미 마감까지 끝난 작업입니다."}
        stage = BLACKSMITH_STAGES[idx]
        action = BLACKSMITH_ACTIONS.get(stage, {}).get(action_id)
        if not action:
            return {"success": False, "error": "선택할 수 없는 작업입니다."}
        label, lo, hi = action
        delta = rng.randint(lo, hi)
        before = int(session.get("quality", 50))
        after = max(0, min(100, before + delta))
        session["quality"] = after
        session["stage_index"] = idx + 1
        session.setdefault("history", []).append({"stage": stage, "action": action_id, "label": label, "delta": delta, "before": before, "after": after})
        return {"success": True, "stage": stage, "label": label, "delta": delta, "quality": after, "complete": session["stage_index"] >= len(BLACKSMITH_STAGES)}

    def finish_session(self, session: dict) -> dict:
        if int(session.get("stage_index", 0)) < len(BLACKSMITH_STAGES):
            return {"success": False, "error": "아직 모든 공정을 끝내지 않았습니다.", "recipe_name": session.get("recipe_name", "블랙스미스")}
        recipe_id = session.get("recipe_id")
        valid = self.validate_recipe(recipe_id)
        if not valid.get("success"):
            return valid
        recipe = valid["recipe"]
        ingredients = []
        for item_id, count in recipe["ingredients"].items():
            self.player.remove_item(item_id, count)
            ingredients.append((ALL_ITEMS.get(item_id, {}).get("name", item_id), count))
        result_id = recipe.get("result", recipe_id)
        self.player.add_gear_item(result_id, 1) or self.player.add_item(result_id, 1)
        score = int(session.get("quality", 50))
        quality_key, quality_label = quality_tier(score)
        multiplier = {"Rough": 0.8, "Normal": 1.0, "Fine": 1.1, "Excellent": 1.25, "Masterpiece": 1.5}[quality_key]
        exp = round(recipe.get("exp", 30.0) * multiplier, 1)
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
            "quality_score": score,
            "quality_key": quality_key,
            "quality_label": quality_label,
            "history": list(session.get("history", [])),
        }

    def forge(self, recipe_id: str) -> dict:
        """호환용 즉시 제작. UI에서는 3단계 세션을 사용한다."""
        session = self.start_session(recipe_id)
        if not session.get("success"):
            return session
        import random
        class _NeutralRng:
            def randint(self, lo, hi):
                return max(lo, min(hi, (lo + hi) // 2))
        rng = _NeutralRng()
        for action in ("steady", "steady", "careful"):
            self.apply_stage(session, action, rng=rng)
        return self.finish_session(session)
