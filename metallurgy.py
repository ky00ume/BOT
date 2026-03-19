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
        lines.append(f"  {C.GREEN}/제련 [광석ID]{C.R} 으로 제련하셰요!")
        return ansi("\n".join(lines))

    def smelt(self, ore_id: str) -> str:
        recipe = SMELT_RECIPES.get(ore_id)
        if not recipe:
            return ansi(f"  {C.RED}✖ [{ore_id}]은(는) 제련 레시피가 없슴미댜!{C.R}")

        rank     = self.player.skill_ranks.get("metallurgy", "연습")
        rank_req = recipe.get("rank_req", "연습")

        if not _rank_gte(rank, rank_req):
            return ansi(
                f"  {C.RED}✖ 제련술 랭크 부족! (필요: {rank_req}, 현재: {rank}){C.R}"
            )

        # 재료 확인
        for ing_id, cnt in recipe["input"].items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                from items import ALL_ITEMS
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return ansi(
                    f"  {C.RED}✖ 재료 부족! [{ing_name}] x{cnt} 필요{C.R}"
                )

        # 재료 소비
        for ing_id, cnt in recipe["input"].items():
            self.player.remove_item(ing_id, cnt)

        # 성공률 (will 기반)
        will = self.player.base_stats.get("will", 10)
        success_rate = min(0.95, 0.60 + will * 0.01)
        success = random.random() < success_rate

        lines = [header_box("⚒ 제련")]

        if success:
            for out_id, cnt in recipe["output"].items():
                self.player.add_item(out_id, cnt)
                from items import ALL_ITEMS
                out_name = ALL_ITEMS.get(out_id, {}).get("name", out_id)
                lines.append(f"  {C.GREEN}✔ {out_name}{C.R} x{cnt} 제련 완료!")

            exp = recipe.get("exp", 10.0)
            rank_msg = self.player.train_skill("metallurgy", exp)
            lines.append(f"  {C.GOLD}제련 숙련도 +{exp}{C.R}")
            if rank_msg:
                lines.append(f"  {C.GOLD}{rank_msg}{C.R}")
        else:
            for out_id, cnt in recipe["fail_out"].items():
                self.player.add_item(out_id, cnt)
                from items import ALL_ITEMS
                out_name = ALL_ITEMS.get(out_id, {}).get("name", out_id)
                lines.append(f"  {C.RED}✖ 제련 실패! {out_name}{C.R} x{cnt} 생성")
            exp_fail = recipe.get("exp", 10.0) * 0.2
            self.player.train_skill("metallurgy", exp_fail)

        return ansi("\n".join(lines))
