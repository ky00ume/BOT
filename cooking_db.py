import random
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS
from utils.ranks import rank_gte as _rank_gte
from utils.logger import setup_logger

logger = setup_logger('cooking_db')

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
        "location":   ["마이코니드 군락 모닥불", "야외 캠프파이어", "비전의 탑 주방"],
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
        "location":   ["비전의 탑 주방"],
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
        "location":   ["비전의 탑 주방"],
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
        "location":   ["비전의 탑 주방", "마이코니드 군락 모닥불"],
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
        "location":   ["비전의 탑 주방", "마이코니드 군락 모닥불"],
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
        "location":   ["비전의 탑 주방"],
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
    # ── 신규 레시피 7종 ──────────────────────────────────────────────────────
    "ck_rice": {
        "name":       "밥",
        "method":     "cook",
        "rank_req":   "연습",
        "ingredients": {"water": 2, "rice": 1},
        "result":     {"ck_rice": 1},
        "tool_req":   "tool_pot",
        "exp":        10.0,
        "desc":       "물 + 쌀 → 밥 (냄비)",
    },
    "ck_tofu": {
        "name":       "두부",
        "method":     "cook",
        "rank_req":   "F",
        "ingredients": {"soybean": 2, "water": 1, "salt": 1},
        "result":     {"ck_tofu": 1},
        "tool_req":   "tool_pot",
        "exp":        25.0,
        "desc":       "대두 + 물 + 소금 → 두부",
    },
    "ck_soft_tofu": {
        "name":       "순두부",
        "method":     "cook",
        "rank_req":   "E",
        "ingredients": {"soybean": 3, "water": 2},
        "result":     {"ck_soft_tofu": 1},
        "tool_req":   "tool_pot",
        "exp":        35.0,
        "desc":       "대두 + 물 → 순두부",
    },
    "ck_soft_tofu_stew": {
        "name":       "순두부찌개",
        "method":     "cook",
        "rank_req":   "D",
        "ingredients": {"ck_soft_tofu": 1, "chili_powder": 1, "water": 1, "egg": 1},
        "result":     {"ck_soft_tofu_stew": 1},
        "tool_req":   "tool_pot",
        "exp":        65.0,
        "desc":       "순두부 + 고춧가루 + 물 + 달걀 → 순두부찌개",
    },
    "ck_yukhoe": {
        "name":       "육회",
        "method":     "mix",
        "rank_req":   "D",
        "ingredients": {"lt_leather_01": 1, "sesame_oil": 1, "egg": 1, "salt": 1},
        "result":     {"ck_yukhoe": 1},
        "tool_req":   None,
        "exp":        55.0,
        "desc":       "고기 + 참기름 + 달걀 + 소금 → 육회 (비가열)",
    },
    "ck_natto": {
        "name":       "낫또",
        "method":     "mix",
        "rank_req":   "F",
        "ingredients": {"soybean": 2, "salt": 1},
        "result":     {"ck_natto": 1},
        "tool_req":   None,
        "exp":        20.0,
        "desc":       "대두 + 소금 → 낫또 (발효)",
    },
    "ck_mandu": {
        "name":       "만두",
        "method":     "cook",
        "rank_req":   "E",
        "ingredients": {"flour": 1, "lt_leather_01": 1, "onion": 1, "garlic": 1},
        "result":     {"ck_mandu": 1},
        "tool_req":   "tool_pot",
        "exp":        45.0,
        "desc":       "밀가루 + 고기 + 양파 + 마늘 → 만두",
    },
    # ── 버섯 요리 10종 ───────────────────────────────────────────────────────
    "nightlight_soup": {
        "name":        "나이트라이트 수프",
        "method":      "cook",
        "rank_req":    "연습",
        "ingredients": {"nightlight_mushroom": 2, "water": 1, "salt": 1},
        "result":      {"nightlight_soup": 1},
        "tool_req":    "tool_pot",
        "exp":         18.0,
        "desc":        "나이트라이트 버섯 + 물 + 소금 → 발광 수프",
    },
    "bluecap_stew": {
        "name":        "블루캡 스튜",
        "method":      "cook",
        "rank_req":    "연습",
        "ingredients": {"bluecap": 2, "potato": 1, "water": 1},
        "result":      {"bluecap_stew": 1},
        "tool_req":    "tool_pot",
        "exp":         20.0,
        "desc":        "블루캡 + 감자 + 물 → 블루캡 스튜",
    },
    "mushroom_risotto": {
        "name":        "버섯 리소토",
        "method":      "cook",
        "rank_req":    "E",
        "ingredients": {"mushroom": 2, "rice": 1, "butter": 1, "shiitake": 1},
        "result":      {"mushroom_risotto": 1},
        "tool_req":    "tool_pan",
        "exp":         45.0,
        "desc":        "버섯 + 쌀 + 버터 + 표고버섯 → 버섯 리소토",
    },
    "torchstalk_grill": {
        "name":        "토치스톡 구이",
        "method":      "cook",
        "rank_req":    "연습",
        "ingredients": {"torchstalk": 2, "salt": 1, "olive_oil": 1},
        "result":      {"torchstalk_grill": 1},
        "tool_req":    "tool_pan",
        "exp":         22.0,
        "desc":        "토치스톡 + 소금 + 올리브오일 → 토치스톡 구이",
    },
    "underdark_mushroom_pie": {
        "name":        "언더다크 버섯 파이",
        "method":      "cook",
        "rank_req":    "D",
        "ingredients": {"mushroom": 2, "bluecap": 1, "flour": 2, "butter": 1},
        "result":      {"underdark_mushroom_pie": 1},
        "tool_req":    "tool_pot",
        "exp":         70.0,
        "desc":        "버섯 + 블루캡 + 밀가루 + 버터 → 언더다크 버섯 파이",
    },
    "timmask_poison_stew": {
        "name":        "팀마스크 독 스튜",
        "method":      "cook",
        "rank_req":    "C",
        "ingredients": {"timmask": 1, "water": 2, "herb": 1},
        "result":      {"timmask_poison_stew": 1},
        "tool_req":    "tool_pot",
        "exp":         90.0,
        "desc":        "팀마스크 + 물 + 허브 → 독 부여 스튜 (위험!)",
    },
    "glowing_mushroom_salad": {
        "name":        "발광 버섯 샐러드",
        "method":      "mix",
        "rank_req":    "F",
        "ingredients": {"glow_mushroom": 1, "nightlight_mushroom": 1, "lettuce": 1},
        "result":      {"glowing_mushroom_salad": 1},
        "tool_req":    None,
        "exp":         25.0,
        "desc":        "발광버섯 + 나이트라이트 버섯 + 상추 → 발광 버섯 샐러드",
    },
    "mushroom_cream_pasta": {
        "name":        "버섯 크림 파스타",
        "method":      "cook",
        "rank_req":    "E",
        "ingredients": {"shiitake": 2, "flour": 1, "milk": 1, "butter": 1},
        "result":      {"mushroom_cream_pasta": 1},
        "tool_req":    "tool_pan",
        "exp":         55.0,
        "desc":        "표고버섯 + 밀가루 + 우유 + 버터 → 버섯 크림 파스타",
    },
    "sussur_bloom_tea": {
        "name":        "서서 꽃 차",
        "method":      "mix",
        "rank_req":    "B",
        "ingredients": {"sussur_bloom": 1, "water": 2},
        "result":      {"sussur_bloom_tea": 1},
        "tool_req":    None,
        "exp":         150.0,
        "desc":        "서서 꽃 + 물 → 마법 저항 버프 차",
    },
    "bibberbang_hotpot": {
        "name":        "비버뱅 전골",
        "method":      "cook",
        "rank_req":    "D",
        "ingredients": {"bibberbang": 1, "mushroom": 2, "water": 2, "chili_powder": 1},
        "result":      {"bibberbang_hotpot": 1},
        "tool_req":    "tool_pot",
        "exp":         75.0,
        "desc":        "비버뱅 + 버섯 + 물 + 고춧가루 → 비버뱅 전골",
    },
    "noblestalk_stew": {"name":"공작버섯 약선 스튜","rank_req":"A","ingredients":{"noblestalk":1,"mushroom":2,"water":2},"result":{"noblestalk_stew":1},"tool_req":"tool_pot","exp":220.0,"desc":"희귀한 공작버섯의 향과 회복성을 살린 약선 스튜."},
    "underdark_truffle_pasta": {"name":"언더다크 트러플 파스타","rank_req":"C","ingredients":{"underdark_truffle":1,"flour":1,"butter":1,"milk":1},"result":{"underdark_truffle_pasta":1},"tool_req":"tool_pot","exp":85.0,"desc":"향 짙은 언더다크 트러플을 넣은 크림 파스타."},
    "spore_mushroom_broth": {"name":"포자 버섯 육수","rank_req":"D","ingredients":{"timmask_spores":1,"mushroom":2,"water":2},"result":{"spore_mushroom_broth":1},"tool_req":"tool_pot","exp":65.0,"desc":"팀마스크 포자를 극소량 써 향을 낸 위험한 언더다크식 육수."},

}


# ── 마비노기식 요리 비율 게이지 ─────────────────────────────────────────────
# 2재료 레시피는 숨은 제3재료를 찾아 넣으면 최고점(100점)에 도달할 수 있다.
# 제3재료를 쓰지 않아도 조리는 가능하지만 90점이 상한이다.
COOKING_BONUS_INGREDIENTS = {
    "ck_soup_01": "salt",
    "ck_steak_01": "pepper",
    "salt_grilled_fish": "olive_oil",
    "mushroom_soup": "butter",
    "honey_milk": "sugar",
    "coffee": "milk",
    "ck_rice": "salt",
    "ck_soft_tofu": "salt",
    "ck_natto": "soy_sauce",
    "sussur_bloom_tea": "honey",
}


def cooking_target_ratios(dish_id: str) -> dict[str, int]:
    """레시피 수량에서 숨은 목표 비율을 만든다. 합계는 항상 100."""
    recipe = RECIPES[dish_id]
    ing = recipe.get("ingredients", {})
    total = max(1, sum(max(0, int(v)) for v in ing.values()))
    bonus = COOKING_BONUS_INGREDIENTS.get(dish_id) if len(ing) == 2 else None
    bonus_share = 10 if bonus else 0
    base_total = 100 - bonus_share
    keys = list(ing)
    raw = [base_total * ing[k] / total for k in keys]
    vals = [int(round(x)) for x in raw]
    if vals:
        vals[-1] += base_total - sum(vals)
    out = dict(zip(keys, vals))
    if bonus:
        out[bonus] = bonus_share
    return out


def cooking_initial_ratios(dish_id: str) -> dict[str, int]:
    """정답을 노출하지 않는 시작점. 기본 재료끼리 거의 균등하게 놓는다."""
    ing = list(RECIPES[dish_id].get("ingredients", {}))
    bonus = COOKING_BONUS_INGREDIENTS.get(dish_id) if len(ing) == 2 else None
    keys = ing + ([bonus] if bonus else [])
    if not keys:
        return {}
    # 숨은 제3재료는 처음엔 0%. 플레이어가 찾아 넣어야 보너스를 받는다.
    active = len(ing)
    base = 100 // max(1, active)
    vals = [base] * active
    vals[-1] += 100 - sum(vals)
    out = dict(zip(ing, vals))
    if bonus:
        out[bonus] = 0
    return out


def cooking_score(dish_id: str, ratios: dict[str, int]) -> int:
    """비율 오차를 1~100 점수로 변환한다."""
    target = cooking_target_ratios(dish_id)
    keys = set(target) | set(ratios)
    error = sum(abs(int(ratios.get(k, 0)) - int(target.get(k, 0))) for k in keys)
    score = max(1, min(100, int(round(100 - error / 2))))
    # 2재료 레시피는 숨은 재료를 전혀 쓰지 않으면 90점이 최대.
    bonus = COOKING_BONUS_INGREDIENTS.get(dish_id)
    if bonus and int(ratios.get(bonus, 0)) <= 0:
        score = min(score, 90)
    return score


def cooking_quality_label(score: int) -> str:
    score = max(1, min(100, int(score)))
    if score >= 95: return "🌟 완벽한 요리"
    if score >= 85: return "✨ 훌륭한 요리"
    if score >= 70: return "🍽️ 맛있는 요리"
    if score >= 50: return "🥣 무난한 요리"
    if score >= 30: return "😐 아쉬운 요리"
    return "💀 처참한 요리"


def food_affinity_modifier(score: int) -> int:
    """요리 점수가 선물 호감도에 주는 가감점. NPC 선호도와 별도로 더해진다."""
    score = max(1, min(100, int(score)))
    if score >= 95: return 5
    if score >= 85: return 3
    if score >= 70: return 1
    if score < 20: return -5
    if score < 35: return -3
    if score < 50: return -1
    return 0


def record_food_quality(player, item_id: str, score: int) -> None:
    store = player._flags.setdefault("cooked_food_quality", {})
    store.setdefault(item_id, []).append(max(1, min(100, int(score))))


def peek_food_quality(player, item_id: str) -> int | None:
    scores = (getattr(player, "_flags", {}) or {}).get("cooked_food_quality", {}).get(item_id, [])
    return int(scores[0]) if scores else None


def pop_food_quality(player, item_id: str) -> int | None:
    store = (getattr(player, "_flags", {}) or {}).get("cooked_food_quality", {})
    scores = store.get(item_id, [])
    if not scores:
        return None
    value = int(scores.pop(0))
    if not scores:
        store.pop(item_id, None)
    return value

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
            from items import ALL_ITEMS
            from item_grade import grade_display, item_grade
            ing_str = ", ".join(
                f"{ALL_ITEMS.get(k, {}).get('name', k)}×{v} ({grade_display(item_grade(k, ALL_ITEMS))})"
                for k, v in recipe["ingredients"].items()
            )
            tool = recipe.get("tool_req") or "없음"
            lines.append(f"    {C.DARK}재료: {ing_str}  도구: {tool}{C.R}")

        lines.append(divider())
        cmd = "/혼합 [레시피ID]" if method_filter == "mix" else "/요리 [레시피ID]"
        lines.append(f"  {C.GREEN}{cmd}{C.R} 으로 조리하셰요!")
        return ansi("\n".join(lines))

    def cook_scored(self, dish_id: str, ratios: dict[str, int]) -> dict:
        """게이지 비율로 조리한다. 랜덤 성공 대신 1~100 품질을 결과 권위로 사용한다."""
        from items import ALL_ITEMS
        recipe = RECIPES.get(dish_id)
        if not recipe:
            return {"success": False, "error": f"[{dish_id}] 레시피 없음", "recipe_name": dish_id, "system_key": "cooking"}
        rank = self.player.skill_ranks.get("cooking", "연습")
        if not _rank_gte(rank, recipe.get("rank_req", "연습")):
            return {"success": False, "error": "요리 랭크가 부족합니다.", "recipe_name": recipe["name"], "system_key": "cooking"}
        tool_req = recipe.get("tool_req")
        if tool_req and self.player.inventory.get(tool_req, 0) <= 0:
            return {"success": False, "error": f"도구 부족: {ALL_ITEMS.get(tool_req, {}).get('name', tool_req)} 필요", "recipe_name": recipe["name"], "system_key": "cooking"}
        for ing_id, cnt in recipe.get("ingredients", {}).items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                return {"success": False, "error": f"재료 부족: {ALL_ITEMS.get(ing_id, {}).get('name', ing_id)} x{cnt} 필요", "recipe_name": recipe["name"], "system_key": "cooking"}
        base_ingredients = set(recipe.get("ingredients", {}))
        extras = [k for k, v in ratios.items() if k not in base_ingredients and int(v) > 0]
        for extra in extras:
            if self.player.inventory.get(extra, 0) <= 0:
                return {"success": False, "error": f"추가 재료 부족: {ALL_ITEMS.get(extra, {}).get('name', extra)} 필요", "recipe_name": recipe["name"], "system_key": "cooking"}

        ingredient_details=[]; ing_list=[]
        from item_grade import item_grade
        for ing_id,cnt in recipe.get("ingredients",{}).items():
            self.player.remove_item(ing_id,cnt)
            name=ALL_ITEMS.get(ing_id,{}).get("name",ing_id); grade=item_grade(ing_id,ALL_ITEMS)
            ing_list.append((name,cnt)); ingredient_details.append({"id":ing_id,"name":name,"count":cnt,"grade":grade})
        for extra in extras:
            self.player.remove_item(extra,1)
            name=ALL_ITEMS.get(extra,{}).get("name",extra); grade=item_grade(extra,ALL_ITEMS)
            ing_list.append((name,1)); ingredient_details.append({"id":extra,"name":name,"count":1,"grade":grade,"bonus":True})

        score=cooking_score(dish_id,ratios); label=cooking_quality_label(score)
        result_names=[]; result_grade="Normal"
        for result_id,cnt in recipe["result"].items():
            self.player.add_item(result_id,cnt)
            for _ in range(cnt): record_food_quality(self.player,result_id,score)
            result_name=ALL_ITEMS.get(result_id,{}).get("name",result_id)
            result_names.append(f"{result_name} x{cnt}")
            result_grade=ALL_ITEMS.get(result_id,{}).get("grade","Normal")
            try:
                from collection import collection_manager
                is_new, _total = collection_manager.register("요리", result_id, result_name)
                if is_new: collection_manager.apply_all_bonuses(self.player, "요리")
            except Exception:
                logger.warning('cooking_db: collection register 실패',exc_info=True)
            try:
                from achievements import achievement_manager
                achievement_manager.increment("items_cooked",cnt)
            except Exception:
                logger.warning('cooking_db: achievement increment 실패',exc_info=True)
            try:
                from diary import diary_manager
                diary_manager.increment("items_cooked",cnt)
            except Exception:
                logger.warning('cooking_db: diary increment 실패',exc_info=True)
        exp=recipe.get("exp",10.0) * (0.7 + score/100*0.6)
        rank_msg=self.player.train_skill("cooking",exp)
        try:
            from skill_breakthrough import record as record_breakthrough
            record_breakthrough(self.player,f"cook_{dish_id}")
        except Exception:
            logger.warning('cooking_db: 돌파 퀘스트 기록 실패',exc_info=True)
        return {"success":True,"recipe_name":recipe["name"],"result_name":", ".join(result_names),"result_grade":result_grade,
                "ingredients":ing_list,"ingredient_details":ingredient_details,"exp":exp,"rank_up_msg":rank_msg or "","system_key":"cooking",
                "quality_score":score,"quality_label":label,"ratios":dict(ratios)}

    def cook(self, dish_id: str, force_method: str = None) -> dict:
        """요리 실행. 결과를 dict로 반환 (BG3 렌더링 호환)."""
        from items import ALL_ITEMS
        recipe = RECIPES.get(dish_id)
        if not recipe:
            return {"success": False, "error": f"[{dish_id}] 레시피 없음",
                    "recipe_name": dish_id, "system_key": "cooking"}

        method = recipe.get("method", "cook")
        if force_method and method != force_method:
            label = "혼합" if force_method == "mix" else "요리"
            return {"success": False,
                    "error": f"잘못된 방식입니다. /{label}를 사용하세요.",
                    "recipe_name": recipe["name"], "system_key": "cooking"}

        rank     = self.player.skill_ranks.get("cooking", "연습")
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

        ingredients = recipe["ingredients"]
        for ing_id, cnt in ingredients.items():
            if self.player.inventory.get(ing_id, 0) < cnt:
                ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
                return {"success": False,
                        "error": f"재료 부족: {ing_name} x{cnt} 필요",
                        "recipe_name": recipe["name"], "system_key": "cooking"}

        # 재료 소비 — 낚시/채집과 같은 공통 등급을 결과에도 보존한다.
        from item_grade import item_grade
        ing_list = []
        ingredient_details = []
        for ing_id, cnt in ingredients.items():
            self.player.remove_item(ing_id, cnt)
            ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
            grade = item_grade(ing_id, ALL_ITEMS)
            ing_list.append((ing_name, cnt))
            ingredient_details.append({"id": ing_id, "name": ing_name, "count": cnt, "grade": grade})

        luck     = self.player.base_stats.get("luck", 5)
        success_rate = min(0.95, 0.65 + luck * 0.01)
        success  = random.random() < success_rate

        if success:
            result_names = []
            result_grade = "Normal"
            for result_id, cnt in recipe["result"].items():
                self.player.add_item(result_id, cnt)
                result_name = ALL_ITEMS.get(result_id, {}).get("name", result_id)
                result_names.append(f"{result_name} x{cnt}")
                result_grade = ALL_ITEMS.get(result_id, {}).get("grade", "Normal")
                try:
                    from collection import collection_manager
                    is_new, total = collection_manager.register("요리", result_id, result_name)
                    if is_new:
                        collection_manager.apply_all_bonuses(self.player, "요리")
                except Exception:
                    logger.warning('cooking_db: collection_manager.register 실패', exc_info=True)
                try:
                    from achievements import achievement_manager
                    achievement_manager.increment("items_cooked", 1)
                except Exception:
                    logger.warning('cooking_db: achievement_manager.increment 실패', exc_info=True)
                try:
                    from diary import diary_manager
                    diary_manager.increment("items_cooked", 1)
                except Exception:
                    logger.warning('cooking_db: diary_manager.increment 실패', exc_info=True)

            exp = recipe.get("exp", 10.0)
            try:
                from skill_breakthrough import record as record_breakthrough
                record_breakthrough(self.player, f"cook_{dish_id}")
            except Exception:
                logger.warning('cooking_db: 돌파 퀘스트 기록 실패', exc_info=True)
            rank_msg = self.player.train_skill("cooking", exp)
            return {
                "success": True,
                "recipe_name": recipe["name"],
                "result_name": ", ".join(result_names),
                "result_grade": result_grade,
                "ingredients": ing_list,
                "ingredient_details": ingredient_details,
                "exp": exp,
                "rank_up_msg": rank_msg or "",
                "system_key": "cooking",
            }
        else:
            exp_fail = recipe.get("exp", 10.0) * 0.3
            rank_msg = self.player.train_skill("cooking", exp_fail)
            return {
                "success": False,
                "recipe_name": recipe["name"],
                "error": "요리 실패! 재료가 낭비되었습니다.",
                "ingredients": ing_list,
                "ingredient_details": ingredient_details,
                "exp": exp_fail,
                "rank_up_msg": rank_msg or "",
                "system_key": "cooking",
                "crafted_but_failed": True,
            }
