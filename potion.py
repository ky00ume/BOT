"""potion.py — 포션 제조 시스템"""
import random
from ui_theme import C, ansi, header_box, divider, rank_badge, GRADE_ICON_PLAIN


POTION_RECIPES = {
    "hp_potion_basic": {
        "name":        "기초 HP 포션",
        "rank_req":    "연습",
        "ingredients": {"herb": 2, "water": 1},
        "result":      "con_potion_h",
        "tool_req":    "tool_mortar",
        "exp":         20.0,
        "hp": 100, "mp": 0, "en": 0,
        "desc": "약초+물 → 기초 HP 포션",
    },
    "mp_potion_basic": {
        "name":        "기초 MP 포션",
        "rank_req":    "F",
        "ingredients": {"mana_herb": 1, "water": 1},
        "result":      "mp_potion_basic",
        "tool_req":    "tool_mortar",
        "exp":         35.0,
        "hp": 0, "mp": 80, "en": 0,
        "desc": "마나 허브+물 → 기초 MP 포션",
    },
    "pot_potion": {
        "name":        "특제 포션",
        "rank_req":    "C",
        "ingredients": {"herb": 3, "mana_herb": 2, "honey": 1, "water": 2},
        "result":      "pot_potion",
        "tool_req":    "tool_mortar",
        "exp":         100.0,
        "hp": 300, "mp": 100, "en": 0,
        "desc": "여러 재료 → 강력한 특제 포션",
    },
    "hp_potion_mid": {
        "name":        "중급 HP 포션",
        "rank_req":    "E",
        "ingredients": {"healing_root": 2, "herb": 1, "water": 2},
        "result":      "hp_potion_mid",
        "tool_req":    "tool_mortar",
        "exp":         50.0,
        "hp": 250, "mp": 0, "en": 0,
        "desc": "치유의 뿌리+약초+물 → 중급 HP 포션",
    },
    "mp_potion_mid": {
        "name":        "중급 MP 포션",
        "rank_req":    "E",
        "ingredients": {"mana_flower": 2, "water": 2},
        "result":      "mp_potion_mid",
        "tool_req":    "tool_mortar",
        "exp":         55.0,
        "hp": 0, "mp": 200, "en": 0,
        "desc": "마나꽃+물 → 중급 MP 포션",
    },
    "energy_potion": {
        "name":        "기력 포션",
        "rank_req":    "F",
        "ingredients": {"energy_leaf": 2, "honey": 1, "water": 1},
        "result":      "energy_potion",
        "tool_req":    "tool_mortar",
        "exp":         30.0,
        "hp": 0, "mp": 0, "en": 50,
        "desc": "원기잎+꿀+물 → 기력 포션",
    },
    "antidote": {
        "name":        "해독 포션",
        "rank_req":    "F",
        "ingredients": {"antidote_herb": 2, "water": 1},
        "result":      "antidote",
        "tool_req":    "tool_mortar",
        "exp":         25.0,
        "hp": 50, "mp": 0, "en": 0,
        "desc": "해독초+물 → 해독 포션",
    },
    "all_potion": {
        "name":        "만능 포션",
        "rank_req":    "B",
        "ingredients": {"moonlight_dew": 1, "healing_root": 1, "mana_flower": 1, "water": 3},
        "result":      "all_potion",
        "tool_req":    "tool_mortar",
        "exp":         200.0,
        "hp": 500, "mp": 300, "en": 50,
        "desc": "달빛 이슬+치유의 뿌리+마나꽃+물 → 만능 포션",
    },
}

RANK_ORDER_POTION = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    if rank_a not in RANK_ORDER_POTION or rank_b not in RANK_ORDER_POTION:
        return False
    return RANK_ORDER_POTION.index(rank_a) >= RANK_ORDER_POTION.index(rank_b)


class PotionEngine:
    def __init__(self, player):
        self.player = player

    def show_recipe_list(self) -> str:
        rank  = self.player.skill_ranks.get("alchemy", "연습")
        lines = [header_box("⚗ 포션 레시피"), "  포션 제조 목록"]

        for rid, recipe in POTION_RECIPES.items():
            rank_req  = recipe.get("rank_req", "연습")
            unlocked  = _rank_gte(rank, rank_req)
            badge     = rank_badge(rank_req)
            available = f"{C.GREEN}[제조 가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"
            tool      = recipe.get("tool_req") or "없음"
            ing_str   = ", ".join(f"{k}×{v}" for k, v in recipe["ingredients"].items())

            lines.append(f"\n  {available} {badge} {C.WHITE}{recipe['name']}{C.R}")
            lines.append(f"    {C.DARK}ID: {rid}  {recipe['desc']}{C.R}")
            lines.append(f"    {C.DARK}재료: {ing_str}  도구: {tool}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/제조 [레시피ID]{C.R} 으로 제조하셰요!")
        return ansi("\n".join(lines))

    def craft(self, recipe_id: str) -> dict:
        """포션 제조. 결과를 dict로 반환 (BG3 렌더링 호환)."""
        from items import ALL_ITEMS
        recipe = POTION_RECIPES.get(recipe_id)
        if not recipe:
            return {"success": False, "error": f"[{recipe_id}] 레시피 없음",
                    "recipe_name": recipe_id, "system_key": "cooking"}

        rank     = self.player.skill_ranks.get("alchemy", "연습")
        rank_req = recipe.get("rank_req", "연습")
        if not _rank_gte(rank, rank_req):
            return {"success": False,
                    "error": f"랭크 부족 (필요: {rank_req}, 현재: {rank})",
                    "recipe_name": recipe["name"], "system_key": "cooking"}

        tool_req = recipe.get("tool_req")
        if tool_req and self.player.inventory.get(tool_req, 0) == 0:
            tool_name = ALL_ITEMS.get(tool_req, {}).get("name", tool_req)
            return {"success": False,
                    "error": f"도구 부족: {tool_name} 필요",
                    "recipe_name": recipe["name"], "system_key": "cooking"}

        for ing_id, cnt in recipe["ingredients"].items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return {"success": False,
                        "error": f"재료 부족: {ing_name} x{cnt} 필요",
                        "recipe_name": recipe["name"], "system_key": "cooking"}

        # 재료 소모
        ing_list = []
        for ing_id, cnt in recipe["ingredients"].items():
            self.player.remove_item(ing_id, cnt)
            ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
            ing_list.append((ing_name, cnt))

        dex          = self.player.base_stats.get("dex", 10)
        success_rate = min(0.95, 0.55 + dex * 0.015)
        success      = random.random() < success_rate

        if success:
            result_id = recipe["result"]
            added     = self.player.add_item(result_id)
            exp       = recipe.get("exp", 20.0)
            rank_msg  = self.player.train_skill("alchemy", exp)
            result_name = ALL_ITEMS.get(result_id, {}).get("name", result_id)
            result_grade = ALL_ITEMS.get(result_id, {}).get("grade", "Normal")

            return {
                "success": True,
                "recipe_name": recipe["name"],
                "result_name": result_name,
                "result_grade": result_grade,
                "ingredients": ing_list,
                "exp": exp,
                "rank_up_msg": rank_msg or "",
                "system_key": "cooking",
                "inv_full": not added,
            }
        else:
            fail_exp = recipe["exp"] * 0.3
            rank_msg = self.player.train_skill("alchemy", fail_exp)
            return {
                "success": False,
                "recipe_name": recipe["name"],
                "error": "제조 실패! 재료가 낭비되었습니다.",
                "ingredients": ing_list,
                "exp": fail_exp,
                "rank_up_msg": rank_msg or "",
                "system_key": "cooking",
                "crafted_but_failed": True,
            }
