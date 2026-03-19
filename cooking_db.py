import random
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS

# method: "cook" = 가열 요리 (도구 필요), "mix" = 혼합 요리 (비가열, 도구 불필요)
RECIPES = {
    # ── 기존 가열 요리 ───────────────────────────────────────────────────────
    "ck_soup_01": {
        "name":       "야채 수프",
        "method":     "cook",
        "rank_req":   "연습",
        "ingredients": {"water": 1, "herb": 1},
        "result":     {"ck_soup_01": 1},
        "tool_req":   "tool_pot",
        "exp":        15.0,
        "desc":       "물과 허브로 끓인 따뜻한 야채 수프.",
    },
    "ck_steak_01": {
        "name":       "고기 스테이크",
        "method":     "cook",
        "rank_req":   "E",
        "ingredients": {"lt_leather_01": 1, "salt": 1},
        "result":     {"ck_steak_01": 1},
        "tool_req":   "tool_pan",
        "exp":        35.0,
        "desc":       "고기를 소금으로 간해 구운 스테이크.",
    },
    "ck_special_01": {
        "name":       "특제 도시락",
        "method":     "cook",
        "rank_req":   "C",
        "ingredients": {"ck_soup_01": 1, "ck_steak_01": 1, "egg": 1},
        "result":     {"ck_special_01": 1},
        "tool_req":   None,
        "exp":        80.0,
        "desc":       "정성껏 만든 특제 도시락.",
    },
    "salt_grilled_fish": {
        "name":       "소금구이",
        "method":     "cook",
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
        "method":     "cook",
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
        "method":     "cook",
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
        "method":     "cook",
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
        "method":     "cook",
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
        "method":     "cook",
        "rank_req":   "F",
        "ingredients": {"coffee_bean": 1, "water": 1},
        "result":     {"coffee": 1},
        "tool_req":   None,
        "location":   ["레이나 가게 주방"],
        "exp":        18.0,
        "desc":       "커피 원두 + 물 → 커피",
    },
    # ── 신규 가열 요리 ───────────────────────────────────────────────────────
    "grilled_carp": {
        "name":       "붕어구이",
        "method":     "cook",
        "rank_req":   "연습",
        "ingredients": {"fs_carp_01": 1, "salt": 1, "oil": 1},
        "result":     {"grilled_carp": 1},
        "tool_req":   "tool_pan",
        "exp":        15.0,
        "desc":       "붕어를 기름에 바삭하게 구운 요리.",
    },
    "salmon_steak": {
        "name":       "연어 스테이크",
        "method":     "cook",
        "rank_req":   "D",
        "ingredients": {"fs_salmon_01": 1, "butter": 1, "pepper": 1, "salt": 1},
        "result":     {"salmon_steak": 1},
        "tool_req":   "tool_pan",
        "exp":        60.0,
        "desc":       "버터에 구운 연어 스테이크.",
    },
    "eel_rice_bowl": {
        "name":       "장어덮밥",
        "method":     "cook",
        "rank_req":   "C",
        "ingredients": {"fs_eel_01": 1, "soy_sauce": 1, "sugar": 1},
        "result":     {"eel_rice_bowl": 1},
        "tool_req":   "tool_pan",
        "exp":        90.0,
        "desc":       "달콤짭짤한 양념 장어덮밥.",
    },
    "tuna_rice_bowl": {
        "name":       "참치회덮밥",
        "method":     "cook",
        "rank_req":   "D",
        "ingredients": {"fs_tuna_01": 1, "soy_sauce": 1, "wasabi": 1},
        "result":     {"tuna_rice_bowl": 1},
        "tool_req":   "tool_pan",
        "exp":        75.0,
        "desc":       "신선한 참치로 만든 회덮밥.",
    },
    "mackerel_stew": {
        "name":       "고등어조림",
        "method":     "cook",
        "rank_req":   "E",
        "ingredients": {"fs_mackerel_01": 1, "soy_sauce": 1, "chili_powder": 1, "water": 1},
        "result":     {"mackerel_stew": 1},
        "tool_req":   "tool_pot",
        "exp":        50.0,
        "desc":       "매콤달콤한 고등어조림.",
    },
    "shiitake_soup": {
        "name":       "표고버섯 수프",
        "method":     "cook",
        "rank_req":   "F",
        "ingredients": {"shiitake": 2, "water": 1, "butter": 1},
        "result":     {"shiitake_soup": 1},
        "tool_req":   "tool_pot",
        "exp":        25.0,
        "desc":       "향긋한 표고버섯 수프.",
    },
    "potato_soup": {
        "name":       "감자 수프",
        "method":     "cook",
        "rank_req":   "연습",
        "ingredients": {"potato": 2, "milk": 1, "butter": 1},
        "result":     {"potato_soup": 1},
        "tool_req":   "tool_pot",
        "exp":        20.0,
        "desc":       "부드러운 크림 감자 수프.",
    },
    "tomato_pasta": {
        "name":       "토마토 파스타",
        "method":     "cook",
        "rank_req":   "E",
        "ingredients": {"tomato": 2, "flour": 1, "olive_oil": 1, "garlic": 1},
        "result":     {"tomato_pasta": 1},
        "tool_req":   "tool_pot",
        "exp":        55.0,
        "desc":       "토마토 소스의 진한 파스타.",
    },
    "seafood_stew": {
        "name":       "해물탕",
        "method":     "cook",
        "rank_req":   "C",
        "ingredients": {"fs_crab_01": 1, "fs_octopus_01": 1, "chili_powder": 1, "water": 2},
        "result":     {"seafood_stew": 1},
        "tool_req":   "tool_pot",
        "exp":        120.0,
        "desc":       "해산물이 가득한 시원한 해물탕.",
    },
    "spicy_fish_stew": {
        "name":       "매운탕",
        "method":     "cook",
        "rank_req":   "D",
        "ingredients": {"fs_catfish_01": 1, "chili_powder": 2, "garlic": 1, "water": 2},
        "result":     {"spicy_fish_stew": 1},
        "tool_req":   "tool_pot",
        "exp":        70.0,
        "desc":       "칼칼하고 시원한 메기 매운탕.",
    },
    "pine_mushroom_rice": {
        "name":       "송이버섯밥",
        "method":     "cook",
        "rank_req":   "B",
        "ingredients": {"pine_mushroom": 1, "water": 2, "salt": 1},
        "result":     {"pine_mushroom_rice": 1},
        "tool_req":   "tool_pot",
        "exp":        160.0,
        "desc":       "귀한 송이버섯으로 만든 솥밥.",
    },
    "dragon_fish_soup": {
        "name":       "용의 물고기 요리",
        "method":     "cook",
        "rank_req":   "5",
        "ingredients": {"fs_dragon_01": 1, "dragon_scale": 1, "honey": 2, "wine": 2},
        "result":     {"dragon_fish_soup": 1},
        "tool_req":   "tool_pot",
        "exp":        2000.0,
        "desc":       "전설의 용의 물고기로 만든 궁극의 요리.",
    },
    # ── 혼합 요리 (method: "mix", 도구 불필요, 불 없이 가능) ──────────────────
    "salmon_sashimi": {
        "name":       "연어회",
        "method":     "mix",
        "rank_req":   "E",
        "ingredients": {"fs_salmon_01": 1, "soy_sauce": 1, "wasabi": 1},
        "result":     {"salmon_sashimi": 1},
        "tool_req":   None,
        "exp":        40.0,
        "desc":       "신선한 연어를 얇게 썰어낸 연어회. 민첩 버프 효과.",
        "buff":       {"agi": 3, "duration": 600},
    },
    "fresh_salad": {
        "name":       "신선한 샐러드",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"lettuce": 1, "tomato": 1, "olive_oil": 1},
        "result":     {"fresh_salad": 1},
        "tool_req":   None,
        "exp":        12.0,
        "desc":       "상추와 토마토를 섞은 신선한 샐러드.",
    },
    "strawberry_smoothie": {
        "name":       "딸기 스무디",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"strawberry": 2, "milk": 1, "honey": 1},
        "result":     {"strawberry_smoothie": 1},
        "tool_req":   None,
        "exp":        15.0,
        "desc":       "딸기와 우유를 섞은 달콤한 스무디.",
    },
    "fruit_platter": {
        "name":       "과일 모듬",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"apple": 1, "grape": 1, "cherry": 1},
        "result":     {"fruit_platter": 1},
        "tool_req":   None,
        "exp":        10.0,
        "desc":       "사과, 포도, 체리를 모아놓은 과일 모듬.",
    },
    "cucumber_pickle": {
        "name":       "오이 피클",
        "method":     "mix",
        "rank_req":   "F",
        "ingredients": {"cucumber": 2, "salt": 1, "vinegar": 1},
        "result":     {"cucumber_pickle": 1},
        "tool_req":   None,
        "exp":        20.0,
        "desc":       "오이를 소금과 식초에 절인 피클.",
    },
    "herb_tea": {
        "name":       "허브차",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"lavender": 1, "healing_herb": 1, "water": 1},
        "result":     {"herb_tea": 1},
        "tool_req":   None,
        "exp":        18.0,
        "desc":       "라벤더와 힐링허브로 우린 향기로운 차.",
    },
    "tuna_sashimi": {
        "name":       "참치회",
        "method":     "mix",
        "rank_req":   "D",
        "ingredients": {"fs_tuna_01": 1, "soy_sauce": 1, "wasabi": 1},
        "result":     {"tuna_sashimi": 1},
        "tool_req":   None,
        "exp":        55.0,
        "desc":       "신선한 참치를 썰어낸 고급 회.",
    },
    "lemon_juice": {
        "name":       "레몬 주스",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"lemon": 2, "water": 1, "sugar": 1},
        "result":     {"lemon_juice": 1},
        "tool_req":   None,
        "exp":        12.0,
        "desc":       "상큼한 레몬 주스.",
    },
    "onion_salad": {
        "name":       "양파 샐러드",
        "method":     "mix",
        "rank_req":   "연습",
        "ingredients": {"onion": 1, "vinegar": 1, "sugar": 1},
        "result":     {"onion_salad": 1},
        "tool_req":   None,
        "exp":        10.0,
        "desc":       "양파를 달콤하게 절인 샐러드.",
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

    def show_recipe_list(self, method_filter: str = None) -> str:
        rank = self.player.skill_ranks.get("cooking", "연습")
        title = "🍳 요리 레시피" if method_filter != "mix" else "🔪 혼합 레시피"
        lines = [header_box(title), section("레시피 목록")]

        for dish_id, recipe in RECIPES.items():
            if method_filter and recipe.get("method", "cook") != method_filter:
                continue
            rank_req   = recipe.get("rank_req", "연습")
            unlocked   = _rank_gte(rank, rank_req)
            name       = recipe["name"]
            badge      = rank_badge(rank_req)
            method_tag = f"{C.CYAN}[혼합]{C.R}" if recipe.get("method") == "mix" else f"{C.GOLD}[가열]{C.R}"
            available  = f"{C.GREEN}[조리 가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"

            lines.append(f"  {available} {badge} {method_tag} {C.WHITE}{name}{C.R}")
            lines.append(f"    {C.DARK}ID: {dish_id}  {recipe['desc']}{C.R}")
            ing_str = ", ".join(
                f"{k}×{v}" for k, v in recipe["ingredients"].items()
            )
            tool = recipe.get("tool_req") or "없음"
            lines.append(f"    {C.DARK}재료: {ing_str}  도구: {tool}{C.R}")

        lines.append(divider())
        cmd = "/혼합 [레시피ID]" if method_filter == "mix" else "/요리 [레시피ID]"
        lines.append(f"  {C.GREEN}{cmd}{C.R} 으로 조리하셰요!")
        return ansi("\n".join(lines))

    def cook(self, dish_id: str, force_method: str = None) -> str:
        recipe = RECIPES.get(dish_id)
        if not recipe:
            return ansi(f"  {C.RED}✖ [{dish_id}]은(는) 존재하지 않는 레시피임미댜!{C.R}")

        # 혼합 레시피를 /요리로, 또는 가열 레시피를 /혼합으로 사용하는 경우 안내
        method = recipe.get("method", "cook")
        if force_method and method != force_method:
            if force_method == "mix":
                return ansi(f"  {C.RED}✖ [{recipe['name']}]은(는) 혼합 레시피가 아님미댜! /요리 를 사용하셰요.{C.R}")
            else:
                return ansi(f"  {C.RED}✖ [{recipe['name']}]은(는) 가열 레시피임미댜! /혼합 을 사용하셰요.{C.R}")

        rank     = self.player.skill_ranks.get("cooking", "연습")
        rank_req = recipe.get("rank_req", "연습")

        if not _rank_gte(rank, rank_req):
            return ansi(
                f"  {C.RED}✖ 요리 랭크 부족! (필요: {rank_req}, 현재: {rank}){C.R}"
            )

        # 도구 확인 (혼합은 tool_req가 None이므로 가열만 체크)
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

        method_label = "혼합" if method == "mix" else "요리"
        lines = [header_box(f"{'🔪' if method == 'mix' else '🍳'} {method_label}")]

        if success:
            for result_id, cnt in recipe["result"].items():
                self.player.add_item(result_id, cnt)
                from items import ALL_ITEMS
                result_name = ALL_ITEMS.get(result_id, {}).get("name", result_id)
                lines.append(f"  {C.GREEN}✔ {result_name}{C.R} x{cnt} 완성!")
                try:
                    from collection import collection_manager
                    is_new, total = collection_manager.register("요리", result_id, result_name)
                    if is_new:
                        lines.append(f"  📖✨ {C.GOLD}새로운 도감 등록! [{result_name}]{C.R}")
                except Exception:
                    pass
                try:
                    from achievements import achievement_manager
                    achievement_manager.increment("items_cooked", 1)
                except Exception:
                    pass
                try:
                    from diary import diary_manager
                    diary_manager.increment("items_cooked", 1)
                except Exception:
                    pass

            exp = recipe.get("exp", 10.0)
            rank_msg = self.player.train_skill("cooking", exp)
            lines.append(f"  {C.GOLD}요리 숙련도 +{exp}{C.R}")
            if rank_msg:
                lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
        else:
            lines.append(f"  {C.RED}✖ {method_label} 실패...(재료만 낭비됐슴미댜){C.R}")
            exp_fail = recipe.get("exp", 10.0) * 0.3
            self.player.train_skill("cooking", exp_fail)

        return ansi("\n".join(lines))
