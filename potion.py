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

    def craft(self, recipe_id: str) -> str:
        recipe = POTION_RECIPES.get(recipe_id)
        if not recipe:
            return ansi(f"  {C.RED}✖ [{recipe_id}]은(는) 존재하지 않는 레시피임미댜!{C.R}")

        rank     = self.player.skill_ranks.get("alchemy", "연습")
        rank_req = recipe.get("rank_req", "연습")
        if not _rank_gte(rank, rank_req):
            return ansi(f"  {C.RED}✖ 연금술 랭크 부족! (필요: {rank_req}, 현재: {rank}){C.R}")

        # 도구 확인
        tool_req = recipe.get("tool_req")
        if tool_req and self.player.inventory.get(tool_req, 0) == 0:
            from items import ALL_ITEMS
            tool_name = ALL_ITEMS.get(tool_req, {}).get("name", tool_req)
            return ansi(f"  {C.RED}✖ 도구 부족! [{tool_name}]이(가) 필요함미댜!{C.R}")

        # 재료 확인
        for ing_id, cnt in recipe["ingredients"].items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                from items import ALL_ITEMS
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return ansi(f"  {C.RED}✖ 재료 부족! [{ing_name}] x{cnt} 필요{C.R}")

        # 재료 소비
        for ing_id, cnt in recipe["ingredients"].items():
            self.player.remove_item(ing_id, cnt)

        # DEX 기반 성공률
        dex          = self.player.base_stats.get("dex", 10)
        success_rate = min(0.95, 0.55 + dex * 0.015)
        success      = random.random() < success_rate

        lines = [header_box("⚗ 포션 제조")]
        if success:
            result_id = recipe["result"]
            added     = self.player.add_item(result_id)
            exp       = recipe.get("exp", 20.0)
            rank_msg  = self.player.train_skill("alchemy", exp)

            if added:
                lines.append(f"  {C.GREEN}✔ {recipe['name']} 제조 성공임미댜!{C.R}")
            else:
                lines.append(f"  {C.RED}✖ 제조 성공했지만 인벤토리가 가득 차서 담지 못했슴미댜!{C.R}")
            lines.append(f"  {C.GOLD}연금술 숙련도 +{exp:.0f}{C.R}")
            if rank_msg:
                lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
        else:
            lines.append(f"  {C.RED}✖ 제조 실패! 재료가 낭비됐슴미댜...{C.R}")
            lines.append(f"  {C.GOLD}연금술 숙련도 +{recipe['exp'] * 0.3:.0f}{C.R}")
            self.player.train_skill("alchemy", recipe["exp"] * 0.3)

        return ansi("\n".join(lines))
