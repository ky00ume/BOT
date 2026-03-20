"""crafting.py — 장비 제작 시스템"""
from ui_theme import C, header_box, divider, section, ansi, rank_badge

CRAFTING_RECIPES = {
    # ── 검 계열 ────────────────────────────────────────────────────────────────
    "wp_sword_02": {
        "name":     "철제 롱소드 제작",
        "rank_req": "F",
        "ingredients": {"iron_bar": 3, "gt_wood_01": 1},
        "result":   "wp_sword_02",
        "exp":      50.0,
        "desc":     "철 주괴 3개 + 나무 조각 1개 → 철제 롱소드",
    },
    "wp_sword_03": {
        "name":     "강철검 제작",
        "rank_req": "D",
        "ingredients": {"iron_bar": 5, "coal": 2},
        "result":   "wp_sword_03",
        "exp":      120.0,
        "desc":     "철 주괴 5개 + 석탄 2개 → 강철검",
    },
    "wp_sword_04": {
        "name":     "미스릴검 제작",
        "rank_req": "B",
        "ingredients": {"mithril_bar": 5, "magic_stone": 1},
        "result":   "wp_sword_04",
        "exp":      400.0,
        "desc":     "미스릴 주괴 5개 + 마법의 돌 1개 → 미스릴검",
    },
    "wp_sword_05": {
        "name":     "드래곤슬레이어 제작",
        "rank_req": "5",
        "ingredients": {"dragonite_bar": 10, "dragon_scale": 3, "star_fragment": 1},
        "result":   "wp_sword_05",
        "exp":      2000.0,
        "desc":     "드래곤나이트 주괴 10개 + 용의 비늘 3개 + 별의 파편 1개 → 드래곤슬레이어",
    },
    # ── 활 계열 ────────────────────────────────────────────────────────────────
    "wp_bow_02": {
        "name":     "합성 활 제작",
        "rank_req": "F",
        "ingredients": {"iron_bar": 2, "gt_wood_01": 3},
        "result":   "wp_bow_02",
        "exp":      45.0,
        "desc":     "철 주괴 2개 + 나무 조각 3개 → 합성 활",
    },
    "wp_bow_03": {
        "name":     "사냥꾼의 활 제작",
        "rank_req": "D",
        "ingredients": {"iron_bar": 4, "gt_wood_01": 2, "feather": 2},
        "result":   "wp_bow_03",
        "exp":      110.0,
        "desc":     "철 주괴 4개 + 나무 조각 2개 + 깃털 2개 → 사냥꾼의 활",
    },
    "wp_bow_04": {
        "name":     "미스릴활 제작",
        "rank_req": "B",
        "ingredients": {"mithril_bar": 5, "silver_bar": 2},
        "result":   "wp_bow_04",
        "exp":      380.0,
        "desc":     "미스릴 주괴 5개 + 은 주괴 2개 → 미스릴활",
    },
    "wp_bow_05": {
        "name":     "폭풍의 활 제작",
        "rank_req": "5",
        "ingredients": {"dragonite_bar": 8, "dragon_scale": 2, "fairy_wing": 1},
        "result":   "wp_bow_05",
        "exp":      1800.0,
        "desc":     "드래곤나이트 주괴 8개 + 용의 비늘 2개 + 요정의 날개 1개 → 폭풍의 활",
    },
    # ── 지팡이 계열 ────────────────────────────────────────────────────────────
    "wp_staff_02": {
        "name":     "마법지팡이 제작",
        "rank_req": "F",
        "ingredients": {"iron_bar": 2, "mana_herb": 3},
        "result":   "wp_staff_02",
        "exp":      55.0,
        "desc":     "철 주괴 2개 + 마나 허브 3개 → 마법지팡이",
    },
    "wp_staff_03": {
        "name":     "현자의 지팡이 제작",
        "rank_req": "C",
        "ingredients": {"silver_bar": 3, "magic_stone": 2},
        "result":   "wp_staff_03",
        "exp":      200.0,
        "desc":     "은 주괴 3개 + 마법의 돌 2개 → 현자의 지팡이",
    },
    "wp_staff_04": {
        "name":     "미스릴지팡이 제작",
        "rank_req": "A",
        "ingredients": {"mithril_bar": 5, "magic_stone": 3},
        "result":   "wp_staff_04",
        "exp":      500.0,
        "desc":     "미스릴 주괴 5개 + 마법의 돌 3개 → 미스릴지팡이",
    },
    "wp_staff_05": {
        "name":     "대마도사의 지팡이 제작",
        "rank_req": "5",
        "ingredients": {"dragonite_bar": 8, "star_fragment": 2, "fairy_wing": 2},
        "result":   "wp_staff_05",
        "exp":      2200.0,
        "desc":     "드래곤나이트 주괴 8개 + 별의 파편 2개 + 요정의 날개 2개 → 대마도사의 지팡이",
    },
    # ── 투구 계열 ──────────────────────────────────────────────────────────────
    "ar_helm_02": {
        "name":     "철투구 제작",
        "rank_req": "F",
        "ingredients": {"iron_bar": 3},
        "result":   "ar_helm_02",
        "exp":      40.0,
        "desc":     "철 주괴 3개 → 철투구",
    },
    "ar_helm_03": {
        "name":     "강철투구 제작",
        "rank_req": "D",
        "ingredients": {"iron_bar": 5, "coal": 1},
        "result":   "ar_helm_03",
        "exp":      100.0,
        "desc":     "철 주괴 5개 + 석탄 1개 → 강철투구",
    },
    "ar_helm_04": {
        "name":     "미스릴투구 제작",
        "rank_req": "B",
        "ingredients": {"mithril_bar": 4, "silver_bar": 1},
        "result":   "ar_helm_04",
        "exp":      350.0,
        "desc":     "미스릴 주괴 4개 + 은 주괴 1개 → 미스릴투구",
    },
    "ar_helm_05": {
        "name":     "드래곤투구 제작",
        "rank_req": "5",
        "ingredients": {"dragonite_bar": 8, "dragon_scale": 2},
        "result":   "ar_helm_05",
        "exp":      1600.0,
        "desc":     "드래곤나이트 주괴 8개 + 용의 비늘 2개 → 드래곤투구",
    },
    # ── 갑옷 계열 ──────────────────────────────────────────────────────────────
    "ar_body_02": {
        "name":     "체인메일 제작",
        "rank_req": "F",
        "ingredients": {"iron_bar": 5, "copper_bar": 2},
        "result":   "ar_body_02",
        "exp":      60.0,
        "desc":     "철 주괴 5개 + 구리 주괴 2개 → 체인메일",
    },
    "ar_body_03": {
        "name":     "강철갑옷 제작",
        "rank_req": "D",
        "ingredients": {"iron_bar": 8, "coal": 2},
        "result":   "ar_body_03",
        "exp":      150.0,
        "desc":     "철 주괴 8개 + 석탄 2개 → 강철갑옷",
    },
    "ar_body_04": {
        "name":     "미스릴갑옷 제작",
        "rank_req": "A",
        "ingredients": {"mithril_bar": 8, "silver_bar": 2},
        "result":   "ar_body_04",
        "exp":      600.0,
        "desc":     "미스릴 주괴 8개 + 은 주괴 2개 → 미스릴갑옷",
    },
    "ar_body_05": {
        "name":     "드래곤아머 제작",
        "rank_req": "4",
        "ingredients": {"dragonite_bar": 15, "dragon_scale": 5, "ancient_fragment": 2},
        "result":   "ar_body_05",
        "exp":      3000.0,
        "desc":     "드래곤나이트 주괴 15개 + 용의 비늘 5개 + 고대의 조각 2개 → 드래곤아머",
    },
    # ── 장갑 계열 ──────────────────────────────────────────────────────────────
    "ar_glove_03": {
        "name":     "강철장갑 제작",
        "rank_req": "E",
        "ingredients": {"iron_bar": 3, "coal": 1},
        "result":   "ar_glove_03",
        "exp":      80.0,
        "desc":     "철 주괴 3개 + 석탄 1개 → 강철장갑",
    },
    "ar_glove_04": {
        "name":     "미스릴장갑 제작",
        "rank_req": "B",
        "ingredients": {"mithril_bar": 3, "silver_bar": 1},
        "result":   "ar_glove_04",
        "exp":      280.0,
        "desc":     "미스릴 주괴 3개 + 은 주괴 1개 → 미스릴장갑",
    },
    "ar_glove_05": {
        "name":     "드래곤클로 제작",
        "rank_req": "5",
        "ingredients": {"dragonite_bar": 6, "dragon_scale": 2},
        "result":   "ar_glove_05",
        "exp":      1400.0,
        "desc":     "드래곤나이트 주괴 6개 + 용의 비늘 2개 → 드래곤클로",
    },
}

RANK_ORDER_CRAFT = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    if rank_a not in RANK_ORDER_CRAFT or rank_b not in RANK_ORDER_CRAFT:
        return False
    return RANK_ORDER_CRAFT.index(rank_a) >= RANK_ORDER_CRAFT.index(rank_b)


class CraftingEngine:
    def __init__(self, player):
        self.player = player

    def get_recipe_embeds(self) -> list:
        """제작 레시피를 Discord Embed 목록으로 반환합니다 (10개씩 분할)."""
        import discord
        from items import ALL_ITEMS
        rank = self.player.skill_ranks.get("crafting", "연습")
        all_recipes = list(CRAFTING_RECIPES.items())
        chunk_size = 10
        embeds = []
        for i in range(0, len(all_recipes), chunk_size):
            chunk = all_recipes[i:i + chunk_size]
            part  = i // chunk_size + 1
            total = (len(all_recipes) + chunk_size - 1) // chunk_size
            embed = discord.Embed(
                title=f"🔨 제작 도감 ({part}/{total})",
                color=0x8B6B3D,
            )
            for recipe_id, recipe in chunk:
                rank_req  = recipe.get("rank_req", "연습")
                unlocked  = _rank_gte(rank, rank_req)
                status    = "✅" if unlocked else "🔒"
                ing_parts = []
                for ing_id, cnt in recipe["ingredients"].items():
                    ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                    have     = self.player.inventory.get(ing_id, 0)
                    ing_parts.append(f"{ing_name} x{cnt}({'있음' if have >= cnt else f'부족-{have}'})")
                embed.add_field(
                    name=f"{status} [{rank_req}] {recipe['name']}",
                    value=f"재료: {', '.join(ing_parts)}\nID: `{recipe_id}`",
                    inline=False,
                )
            embed.set_footer(text=f"제작: /제작 [결과물ID] 또는 /제작 [결과물이름]")
            embeds.append(embed)
        if not embeds:
            empty = discord.Embed(title="🔨 제작 도감", description="레시피 없음", color=0x8B6B3D)
            embeds.append(empty)
        return embeds

    def show_recipe_list(self) -> str:
        rank = self.player.skill_ranks.get("crafting", "연습")
        lines = [header_box("🔨 제작 도감"), section("제작 레시피")]

        for recipe_id, recipe in CRAFTING_RECIPES.items():
            rank_req  = recipe.get("rank_req", "연습")
            unlocked  = _rank_gte(rank, rank_req)
            badge     = rank_badge(rank_req)
            available = f"{C.GREEN}[가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"

            lines.append(f"  {available} {badge} {C.WHITE}{recipe['name']}{C.R}")
            lines.append(f"    {C.DARK}ID: {recipe_id}  {recipe['desc']}{C.R}")
            ing_str = ", ".join(f"{k}×{v}" for k, v in recipe["ingredients"].items())
            lines.append(f"    {C.DARK}재료: {ing_str}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/제작 [결과물ID]{C.R} 으로 제작하셰요!")
        return ansi("\n".join(lines))

    def craft(self, result_id: str) -> str:
        recipe = CRAFTING_RECIPES.get(result_id)
        if not recipe:
            return ansi(f"  {C.RED}✖ [{result_id}]은(는) 제작 레시피가 없슴미댜!{C.R}")

        rank     = self.player.skill_ranks.get("crafting", "연습")
        rank_req = recipe.get("rank_req", "연습")

        if not _rank_gte(rank, rank_req):
            return ansi(
                f"  {C.RED}✖ 제작 랭크 부족! (필요: {rank_req}, 현재: {rank}){C.R}"
            )

        ingredients = recipe["ingredients"]
        for ing_id, cnt in ingredients.items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                from items import ALL_ITEMS
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return ansi(
                    f"  {C.RED}✖ 재료가 부족함미댜! [{ing_name}] x{cnt} 필요{C.R}"
                )

        for ing_id, cnt in ingredients.items():
            self.player.remove_item(ing_id, cnt)

        self.player.add_item(result_id, 1)

        from items import ALL_ITEMS
        result_name = ALL_ITEMS.get(result_id, {}).get("name", result_id)

        exp = recipe.get("exp", 30.0)
        rank_msg = self.player.train_skill("crafting", exp)

        lines = [
            header_box("🔨 제작 완료!"),
            f"  {C.GREEN}✔ {result_name}{C.R} 제작 성공!",
            f"  {C.GOLD}제작 숙련도 +{exp}{C.R}",
        ]
        if rank_msg:
            lines.append(f"  {C.GOLD}{rank_msg}{C.R}")

        return ansi("\n".join(lines))
