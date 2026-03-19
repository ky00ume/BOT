import random
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS

RECIPES = {
    "ck_soup_01": {
        "name":       "야채 수프",
        "rank_req":   "연습",
        "ingredients": {"water": 1, "herb": 1},
        "result":     {"ck_soup_01": 1},
        "tool_req":   "tool_pot",
        "exp":        15.0,
        "desc":       "물과 허브로 끓인 따뜻한 야채 수프.",
    },
    "ck_steak_01": {
        "name":       "고기 스테이크",
        "rank_req":   "E",
        "ingredients": {"lt_leather_01": 1, "salt": 1},
        "result":     {"ck_steak_01": 1},
        "tool_req":   "tool_pan",
        "exp":        35.0,
        "desc":       "고기를 소금으로 간해 구운 스테이크.",
    },
    "ck_special_01": {
        "name":       "특제 도시락",
        "rank_req":   "C",
        "ingredients": {"ck_soup_01": 1, "ck_steak_01": 1, "egg": 1},
        "result":     {"ck_special_01": 1},
        "tool_req":   None,
        "exp":        80.0,
        "desc":       "정성껏 만든 특제 도시락.",
    },
    "salt_grilled_fish": {
        "name":       "소금구이",
        "rank_req":   "연습",
        "ingredients": {"fs_carp_01": 1, "salt": 1},
        "result":     {"salt_grilled_fish": 1},
        "tool_req":   "tool_pan",
        "location":   ["마을 광장 모닥불", "야외 캠프파이어", "레이나 가게 주방"],
        "exp":        12.0,
        "desc":       "붕어 + 소금 → 소금구이 (굽기)",
    },
    "steamed_salmon": {
        "name":       "연어찜",
        "rank_req":   "E",
        "ingredients": {"fs_salmon_01": 1, "water": 1, "salt": 1},
        "result":     {"steamed_salmon": 1},
        "tool_req":   "tool_pot",
        "location":   ["레이나 가게 주방"],
        "exp":        45.0,
        "desc":       "연어 + 물 + 소금 → 연어찜 (찌기)",
    },
    "eel_special": {
        "name":       "장어 특선",
        "rank_req":   "B",
        "ingredients": {"fs_gold_eel_01": 1, "honey": 1, "wine": 1},
        "result":     {"eel_special": 1},
        "tool_req":   "tool_pot",
        "location":   ["레이나 가게 주방"],
        "exp":        200.0,
        "desc":       "황금장어 + 꿀 + 와인 → 장어 특선 (끓이기)",
    },
    "mushroom_soup": {
        "name":       "버섯 수프",
        "rank_req":   "연습",
        "ingredients": {"mushroom": 2, "water": 1},
        "result":     {"mushroom_soup": 1},
        "tool_req":   "tool_pot",
        "location":   ["레이나 가게 주방", "마을 광장 모닥불"],
        "exp":        15.0,
        "desc":       "버섯 + 물 → 버섯 수프 (끓이기)",
    },
    "honey_milk": {
        "name":       "꿀 우유",
        "rank_req":   "연습",
        "ingredients": {"honey": 1, "milk": 1},
        "result":     {"honey_milk": 1},
        "tool_req":   None,
        "location":   ["레이나 가게 주방", "마을 광장 모닥불"],
        "exp":        10.0,
        "desc":       "꿀 + 우유 원액 → 꿀 우유",
    },
    "coffee": {
        "name":       "커피",
        "rank_req":   "F",
        "ingredients": {"coffee_bean": 1, "water": 1},
        "result":     {"coffee": 1},
        "tool_req":   None,
        "location":   ["레이나 가게 주방"],
        "exp":        18.0,
        "desc":       "커피 원두 + 물 → 커피",
    },
}

RANK_ORDER_COOKING = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    """rank_a >= rank_b 이면 True."""
    if rank_a not in RANK_ORDER_COOKING or rank_b not in RANK_ORDER_COOKING:
        return False
    return RANK_ORDER_COOKING.index(rank_a) >= RANK_ORDER_COOKING.index(rank_b)


class CookingEngine:
    def __init__(self, player):
        self.player = player

    def show_recipe_list(self) -> str:
        rank = self.player.skill_ranks.get("cooking", "연습")
        lines = [header_box("🍳 요리 레시피"), section("레시피 목록")]

        for dish_id, recipe in RECIPES.items():
            rank_req   = recipe.get("rank_req", "연습")
            unlocked   = _rank_gte(rank, rank_req)
            name       = recipe["name"]
            badge      = rank_badge(rank_req)
            available  = f"{C.GREEN}[조리 가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"

            lines.append(f"  {available} {badge} {C.WHITE}{name}{C.R}")
            lines.append(f"    {C.DARK}ID: {dish_id}  {recipe['desc']}{C.R}")
            ing_str = ", ".join(
                f"{k}×{v}" for k, v in recipe["ingredients"].items()
            )
            tool = recipe.get("tool_req") or "없음"
            lines.append(f"    {C.DARK}재료: {ing_str}  도구: {tool}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/요리 [레시피ID]{C.R} 으로 조리하셰요!")
        return ansi("\n".join(lines))

    def cook(self, dish_id: str) -> str:
        recipe = RECIPES.get(dish_id)
        if not recipe:
            return ansi(f"  {C.RED}✖ [{dish_id}]은(는) 존재하지 않는 레시피임미댜!{C.R}")

        rank     = self.player.skill_ranks.get("cooking", "연습")
        rank_req = recipe.get("rank_req", "연습")

        if not _rank_gte(rank, rank_req):
            return ansi(
                f"  {C.RED}✖ 요리 랭크 부족! (필요: {rank_req}, 현재: {rank}){C.R}"
            )

        # 도구 확인
        tool_req = recipe.get("tool_req")
        if tool_req and self.player.inventory.get(tool_req, 0) == 0:
            from items import ALL_ITEMS
            tool_name = ALL_ITEMS.get(tool_req, {}).get("name", tool_req)
            return ansi(f"  {C.RED}✖ 도구 부족! [{tool_name}]이(가) 필요함미댜!{C.R}")

        # 재료 확인
        ingredients = recipe["ingredients"]
        for ing_id, cnt in ingredients.items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                from items import ALL_ITEMS
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return ansi(
                    f"  {C.RED}✖ 재료가 부족함미댜! [{ing_name}] x{cnt} 필요{C.R}"
                )

        # 재료 소비
        for ing_id, cnt in ingredients.items():
            self.player.remove_item(ing_id, cnt)

        # 성공률 (luck 기반)
        luck     = self.player.base_stats.get("luck", 5)
        success_rate = min(0.95, 0.65 + luck * 0.01)
        success  = random.random() < success_rate

        lines = [header_box("🍳 요리")]

        if success:
            for result_id, cnt in recipe["result"].items():
                self.player.add_item(result_id, cnt)
                from items import ALL_ITEMS
                result_name = ALL_ITEMS.get(result_id, {}).get("name", result_id)
                lines.append(f"  {C.GREEN}✔ {result_name}{C.R} x{cnt} 완성!")

            exp = recipe.get("exp", 10.0)
            rank_msg = self.player.train_skill("cooking", exp)
            lines.append(f"  {C.GOLD}요리 숙련도 +{exp}{C.R}")
            if rank_msg:
                lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
        else:
            lines.append(f"  {C.RED}✖ 요리 실패...(재료만 낭비됐슴미댜){C.R}")
            exp_fail = recipe.get("exp", 10.0) * 0.3
            self.player.train_skill("cooking", exp_fail)

        return ansi("\n".join(lines))
