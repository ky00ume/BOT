import random
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS

SMELT_RECIPES = {
    "copper_ore": {
        "name":     "구리 주괴 제련",
        "rank_req": "연습",
        "input":    {"copper_ore": 3},
        "output":   {"copper_bar": 1},
        "fail_out": {"slag": 1},
        "exp":      10.0,
        "desc":     "구리 광석 3개 → 구리 주괴 1개",
    },
    "tin_ore": {
        "name":     "주석 주괴 제련",
        "rank_req": "연습",
        "input":    {"tin_ore": 3},
        "output":   {"tin_bar": 1},
        "fail_out": {"slag": 1},
        "exp":      10.0,
        "desc":     "주석 광석 3개 → 주석 주괴 1개",
    },
    "iron_ore": {
        "name":     "철 주괴 제련",
        "rank_req": "F",
        "input":    {"iron_ore": 3, "coal": 1},
        "output":   {"iron_bar": 1},
        "fail_out": {"slag": 1},
        "exp":      18.0,
        "desc":     "철광석 3개 + 석탄 1개 → 철 주괴 1개",
    },
    "silver_ore": {
        "name":     "은 주괴 제련",
        "rank_req": "D",
        "input":    {"silver_ore": 3, "coal": 2},
        "output":   {"silver_bar": 1},
        "fail_out": {"slag": 1},
        "exp":      40.0,
        "desc":     "은 광석 3개 + 석탄 2개 → 은 주괴 1개",
    },
    "gold_ore": {
        "name":     "금 주괴 제련",
        "rank_req": "C",
        "input":    {"gold_ore": 3, "coal": 2},
        "output":   {"gold_bar": 1},
        "fail_out": {"slag": 1},
        "exp":      80.0,
        "desc":     "금 광석 3개 + 석탄 2개 → 금 주괴 1개",
    },
    "mithril_ore": {
        "name":     "미스릴 주괴 제련",
        "rank_req": "B",
        "input":    {"mithril_ore": 3, "coal": 3},
        "output":   {"mithril_bar": 1},
        "fail_out": {"mithril_dust": 1},
        "exp":      180.0,
        "desc":     "미스릴 광석 3개 + 석탄 3개 → 미스릴 주괴 1개",
    },
    "orichalcum_ore": {
        "name":     "오리할콘 주괴 제련",
        "rank_req": "A",
        "input":    {"orichalcum_ore": 3, "coal": 4},
        "output":   {"orichalcum_bar": 1},
        "fail_out": {"slag": 2},
        "exp":      350.0,
        "desc":     "오리할콘 광석 3개 + 석탄 4개 → 오리할콘 주괴 1개",
    },
    "adamantium_ore": {
        "name":     "아다만티움 주괴 제련",
        "rank_req": "7",
        "input":    {"adamantium_ore": 3, "coal": 5},
        "output":   {"adamantium_bar": 1},
        "fail_out": {"slag": 3},
        "exp":      700.0,
        "desc":     "아다만티움 광석 3개 + 석탄 5개 → 아다만티움 주괴 1개",
    },
    "dragonite_ore": {
        "name":     "드래곤나이트 주괴 제련",
        "rank_req": "5",
        "input":    {"dragonite_ore": 3, "coal": 6, "dragon_scale": 1},
        "output":   {"dragonite_bar": 1},
        "fail_out": {"slag": 3},
        "exp":      1500.0,
        "desc":     "드래곤나이트 광석 3개 + 석탄 6개 + 용의 비늘 1개 → 드래곤나이트 주괴 1개",
    },
}

RANK_ORDER_SMELT = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    if rank_a not in RANK_ORDER_SMELT or rank_b not in RANK_ORDER_SMELT:
        return False
    return RANK_ORDER_SMELT.index(rank_a) >= RANK_ORDER_SMELT.index(rank_b)


class MetallurgyEngine:
    def __init__(self, player):
        self.player = player

    def show_recipe_list(self) -> str:
        rank = self.player.skill_ranks.get("metallurgy", "연습")
        lines = [header_box("⚒ 제련 목록"), section("제련 레시피")]

        for ore_id, recipe in SMELT_RECIPES.items():
            rank_req  = recipe.get("rank_req", "연습")
            unlocked  = _rank_gte(rank, rank_req)
            badge     = rank_badge(rank_req)
            available = f"{C.GREEN}[가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"

            lines.append(f"  {available} {badge} {C.WHITE}{recipe['name']}{C.R}")
            lines.append(f"    {C.DARK}ID: {ore_id}  {recipe['desc']}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/제련 [광석이름 또는 ID]{C.R} 으로 제련하셰요!")
        return ansi("\n".join(lines))

    def smelt(self, ore_input: str) -> dict:
        """제련 실행. 결과를 dict로 반환 (BG3 렌더링 호환)."""
        from items import ALL_ITEMS
        # 1. 직접 키 매칭
        recipe = SMELT_RECIPES.get(ore_input)

        # 2. 광석/결과물 이름으로 검색
        if recipe is None:
            inp_normalized = ore_input.replace(" ", "")
            for key, rec in SMELT_RECIPES.items():
                for ing_id in rec["input"]:
                    ing_name = ALL_ITEMS.get(ing_id, {}).get("name", "")
                    if ing_name == ore_input or ing_name.replace(" ", "") == inp_normalized:
                        recipe = rec
                        ore_input = key
                        break
                if recipe:
                    break
                for out_id in rec["output"]:
                    out_name = ALL_ITEMS.get(out_id, {}).get("name", "")
                    if out_name == ore_input or out_name.replace(" ", "") == inp_normalized:
                        recipe = rec
                        ore_input = key
                        break
                if recipe:
                    break
                rec_name = rec.get("name", "")
                if rec_name == ore_input or rec_name.replace(" ", "") == inp_normalized:
                    recipe = rec; ore_input = key; break

        if not recipe:
            return {"success": False, "error": f"[{ore_input}] 레시피 없음",
                    "recipe_name": ore_input, "system_key": "craft"}

        rank     = self.player.skill_ranks.get("metallurgy", "연습")
        rank_req = recipe.get("rank_req", "연습")

        if not _rank_gte(rank, rank_req):
            return {"success": False,
                    "error": f"랭크 부족 (필요: {rank_req}, 현재: {rank})",
                    "recipe_name": recipe["name"], "system_key": "craft"}

        for ing_id, cnt in recipe["input"].items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return {"success": False,
                        "error": f"재료 부족: {ing_name} x{cnt} 필요",
                        "recipe_name": recipe["name"], "system_key": "craft"}

        # 재료 소모
        ing_list = []
        for ing_id, cnt in recipe["input"].items():
            self.player.remove_item(ing_id, cnt)
            ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
            ing_list.append((ing_name, cnt))

        will = self.player.base_stats.get("will", 10)
        success_rate = min(0.95, 0.60 + will * 0.01)
        success = random.random() < success_rate

        if success:
            result_names = []
            result_grade = "Normal"
            for out_id, cnt in recipe["output"].items():
                self.player.add_item(out_id, cnt)
                out_name = ALL_ITEMS.get(out_id, {}).get("name", out_id)
                result_names.append(f"{out_name} x{cnt}")
                result_grade = ALL_ITEMS.get(out_id, {}).get("grade", "Normal")
                try:
                    from collection import collection_manager
                    grade = ALL_ITEMS.get(out_id, {}).get("grade", "Normal")
                    is_new, total = collection_manager.register("채광", out_id, out_name, grade)
                except Exception:
                    pass

            exp = recipe.get("exp", 10.0)
            rank_msg = self.player.train_skill("metallurgy", exp)
            return {
                "success": True,
                "recipe_name": recipe["name"],
                "result_name": ", ".join(result_names),
                "result_grade": result_grade,
                "ingredients": ing_list,
                "exp": exp,
                "rank_up_msg": rank_msg or "",
                "system_key": "craft",
            }
        else:
            fail_names = []
            for out_id, cnt in recipe["fail_out"].items():
                self.player.add_item(out_id, cnt)
                out_name = ALL_ITEMS.get(out_id, {}).get("name", out_id)
                fail_names.append(f"{out_name} x{cnt}")
            exp_fail = recipe.get("exp", 10.0) * 0.2
            rank_msg = self.player.train_skill("metallurgy", exp_fail)
            return {
                "success": False,
                "recipe_name": recipe["name"],
                "error": f"제련 실패! {', '.join(fail_names)} 생성",
                "ingredients": ing_list,
                "exp": exp_fail,
                "rank_up_msg": rank_msg or "",
                "system_key": "craft",
                "crafted_but_failed": True,
            }
