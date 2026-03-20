import random as _rnd

# ─── 몬스터 사이즈 시스템 ────────────────────────────────────────────────────
# 사이즈에 따라 HP·공격력·경험치·골드·드랍률이 보정됩니다.
# MEGA 사이즈는 추가로 1% 확률로 전설급 드랍 보너스를 부여합니다.
MONSTER_SIZES = {
    "XS":   {"icon": "🔹", "mult_hp": 0.5,  "mult_atk": 0.6,  "mult_exp": 0.7,  "mult_gold": 0.5,  "drop_mult": 0.6},
    "S":    {"icon": "◾", "mult_hp": 0.75, "mult_atk": 0.8,  "mult_exp": 0.85, "mult_gold": 0.75, "drop_mult": 0.8},
    "M":    {"icon": "⬛", "mult_hp": 1.0,  "mult_atk": 1.0,  "mult_exp": 1.0,  "mult_gold": 1.0,  "drop_mult": 1.0},
    "L":    {"icon": "🔶", "mult_hp": 1.5,  "mult_atk": 1.3,  "mult_exp": 1.3,  "mult_gold": 1.5,  "drop_mult": 1.2},
    "XL":   {"icon": "🔴", "mult_hp": 2.5,  "mult_atk": 1.7,  "mult_exp": 1.7,  "mult_gold": 2.0,  "drop_mult": 1.5},
    "MEGA": {"icon": "💥", "mult_hp": 5.0,  "mult_atk": 2.5,  "mult_exp": 3.0,  "mult_gold": 4.0,  "drop_mult": 2.0},
}

_SIZE_WEIGHTS = [("XS", 5), ("S", 20), ("M", 50), ("L", 18), ("XL", 6), ("MEGA", 1)]

# 전설급 아이템 풀 (MEGA 사이즈 전용 1% 추가 드랍)
LEGENDARY_DROP_POOL = [
    "diamond", "mithril_ore", "orichalcum_ore", "adamantium_ore",
    "reishi", "golden_apple", "moonlight_dew", "eye_of_truth",
    "treant_core", "ancient_wood",
]


def roll_monster_size() -> str:
    """사이즈를 가중치 확률로 뽑아 반환합니다."""
    total = sum(w for _, w in _SIZE_WEIGHTS)
    r = _rnd.randint(1, total)
    cumulative = 0
    for size, weight in _SIZE_WEIGHTS:
        cumulative += weight
        if r <= cumulative:
            return size
    return "M"


def apply_size_to_monster(base: dict, size: str) -> dict:
    """기본 몬스터 데이터에 사이즈 보정을 적용한 복사본을 반환합니다."""
    m = dict(base)
    mod = MONSTER_SIZES[size]
    m["_size"]  = size
    m["hp"]     = max(1, int(base["hp"] * mod["mult_hp"]))
    m["attack"] = max(1, int(base["attack"] * mod["mult_atk"]))
    m["exp"]    = max(1, int(base["exp"] * mod["mult_exp"]))
    gold_min, gold_max = base.get("gold", (1, 5))
    m["gold"] = (
        max(1, int(gold_min * mod["mult_gold"])),
        max(1, int(gold_max * mod["mult_gold"])),
    )
    # 드랍률 보정
    m["drops"] = [
        dict(d, rate=min(1.0, d["rate"] * mod["drop_mult"]))
        for d in base.get("drops", [])
    ]
    # MEGA 전설급 추가 드랍 (1% 확률)
    if size == "MEGA":
        leg_item = _rnd.choice(LEGENDARY_DROP_POOL)
        m["drops"] = list(m["drops"]) + [{"item": leg_item, "rate": 0.01}]
    return m


MONSTERS_DB = {
    "방울숲": {
        "name": "방울숲",
        "level_range": (1, 5),
        "monsters": [
            {
                "id": "slime",
                "name": "슬라임",
                "level": 1,
                "hp": 30,
                "attack": 5,
                "defense": 1,
                "exp": 8,
                "gold": (3, 8),
                "drops": [
                    {"item": "lt_leather_01", "rate": 0.4},
                    {"item": "gt_herb_01",    "rate": 0.3},
                    {"item": "water",         "rate": 0.5},
                ],
            },
            {
                "id": "forest_spider",
                "name": "숲 거미",
                "level": 2,
                "hp": 45,
                "attack": 7,
                "defense": 2,
                "exp": 12,
                "gold": (5, 12),
                "drops": [
                    {"item": "spider_web",   "rate": 0.6},
                    {"item": "lt_tooth_01",  "rate": 0.3},
                    {"item": "poison_sac",   "rate": 0.15},
                ],
            },
            {
                "id": "green_goblin",
                "name": "풀 고블린",
                "level": 3,
                "hp": 60,
                "attack": 10,
                "defense": 3,
                "exp": 18,
                "gold": (8, 18),
                "drops": [
                    {"item": "club",         "rate": 0.1},
                    {"item": "lt_leather_01","rate": 0.4},
                    {"item": "con_bread",    "rate": 0.2},
                ],
            },
            {
                "id": "honey_bear",
                "name": "꿀벌 곰",
                "level": 4,
                "hp": 90,
                "attack": 14,
                "defense": 5,
                "exp": 28,
                "gold": (12, 25),
                "drops": [
                    {"item": "honey",        "rate": 0.5},
                    {"item": "bear_paw",     "rate": 0.25},
                    {"item": "lt_leather_01","rate": 0.5},
                ],
            },
            {
                "id": "bell_sprite",
                "name": "방울 정령",
                "level": 5,
                "hp": 120,
                "attack": 18,
                "defense": 6,
                "exp": 40,
                "gold": (18, 35),
                "drops": [
                    {"item": "mp_crystal",   "rate": 0.2},
                    {"item": "feather",      "rate": 0.45},
                    {"item": "lt_core_01",   "rate": 0.1},
                ],
            },
        ],
    },
    "고블린동굴": {
        "name": "고블린 동굴",
        "level_range": (5, 12),
        "monsters": [
            {
                "id": "goblin_warrior",
                "name": "고블린 전사",
                "level": 5,
                "hp": 140,
                "attack": 22,
                "defense": 8,
                "exp": 55,
                "gold": (20, 40),
                "drops": [
                    {"item": "short_bow",    "rate": 0.08},
                    {"item": "lt_leather_01","rate": 0.5},
                    {"item": "iron_ore",     "rate": 0.3},
                ],
            },
            {
                "id": "goblin_shaman",
                "name": "고블린 주술사",
                "level": 7,
                "hp": 110,
                "attack": 28,
                "defense": 5,
                "exp": 70,
                "gold": (25, 50),
                "drops": [
                    {"item": "mana_herb",    "rate": 0.3},
                    {"item": "bad_score",    "rate": 0.4},
                    {"item": "mp_crystal",   "rate": 0.15},
                ],
            },
            {
                "id": "goblin_king",
                "name": "고블린 대왕",
                "level": 10,
                "hp": 300,
                "attack": 40,
                "defense": 15,
                "exp": 150,
                "gold": (60, 120),
                "drops": [
                    {"item": "hard_horn",    "rate": 0.4},
                    {"item": "iron_ore",     "rate": 0.6},
                    {"item": "copper_ore",   "rate": 0.5},
                    {"item": "re_stone",     "rate": 0.05},
                ],
            },
            {
                "id": "cave_bat",
                "name": "동굴 박쥐",
                "level": 6,
                "hp": 80,
                "attack": 15,
                "defense": 4,
                "exp": 35,
                "gold": (10, 22),
                "drops": [
                    {"item": "wing",         "rate": 0.4},
                    {"item": "feather",      "rate": 0.3},
                ],
            },
            {
                "id": "stone_golem",
                "name": "돌 골렘",
                "level": 11,
                "hp": 350,
                "attack": 35,
                "defense": 25,
                "exp": 180,
                "gold": (70, 140),
                "drops": [
                    {"item": "iron_ore",     "rate": 0.7},
                    {"item": "copper_ore",   "rate": 0.6},
                    {"item": "silver_ore",   "rate": 0.15},
                    {"item": "lt_core_01",   "rate": 0.1},
                ],
            },
        ],
    },
    "소금광산": {
        "name": "소금 광산",
        "level_range": (10, 20),
        "monsters": [
            {
                "id": "skeleton",
                "name": "해골 병사",
                "level": 10,
                "hp": 200,
                "attack": 38,
                "defense": 12,
                "exp": 130,
                "gold": (45, 90),
                "drops": [
                    {"item": "coal",         "rate": 0.5},
                    {"item": "iron_ore",     "rate": 0.4},
                    {"item": "rotten_meat",  "rate": 0.3},
                ],
            },
            {
                "id": "salt_golem",
                "name": "소금 골렘",
                "level": 13,
                "hp": 420,
                "attack": 50,
                "defense": 30,
                "exp": 220,
                "gold": (90, 170),
                "drops": [
                    {"item": "silver_ore",   "rate": 0.4},
                    {"item": "sulfur",       "rate": 0.5},
                    {"item": "iron_ore",     "rate": 0.6},
                ],
            },
            {
                "id": "dark_wizard",
                "name": "어둠 마법사",
                "level": 15,
                "hp": 280,
                "attack": 65,
                "defense": 10,
                "exp": 280,
                "gold": (110, 200),
                "drops": [
                    {"item": "eye_of_truth", "rate": 0.1},
                    {"item": "dark_matter",  "rate": 0.05},
                    {"item": "mp_crystal",   "rate": 0.35},
                    {"item": "mana_herb",    "rate": 0.4},
                ],
            },
            {
                "id": "mine_dragon",
                "name": "광산 드래곤",
                "level": 18,
                "hp": 800,
                "attack": 90,
                "defense": 35,
                "exp": 500,
                "gold": (200, 400),
                "drops": [
                    {"item": "gold_ore",     "rate": 0.5},
                    {"item": "mithril_ore",  "rate": 0.2},
                    {"item": "dragon_bacon", "rate": 0.08},
                    {"item": "ancient_scale","rate": 0.05},
                    {"item": "ruby",         "rate": 0.06},
                    {"item": "sapphire",     "rate": 0.06},
                    {"item": "emerald",      "rate": 0.06},
                ],
            },
            {
                "id": "crystal_demon",
                "name": "결정 악마",
                "level": 20,
                "hp": 1000,
                "attack": 110,
                "defense": 40,
                "exp": 700,
                "gold": (300, 600),
                "drops": [
                    {"item": "diamond",      "rate": 0.04},
                    {"item": "diamond_7",    "rate": 0.01},
                    {"item": "dark_matter",  "rate": 0.1},
                    {"item": "mithril_ore",  "rate": 0.3},
                    {"item": "re_stone",     "rate": 0.08},
                ],
            },
        ],
    },
    "요정의 숲": {
        "name": "요정의 숲",
        "level_range": (15, 25),
        "monsters": [
            {
                "id": "forest_fairy",
                "name": "숲 요정",
                "level": 15,
                "hp": 250,
                "attack": 55,
                "defense": 15,
                "exp": 200,
                "gold": (60, 120),
                "drops": [
                    {"item": "fairy_wing",   "rate": 0.05},
                    {"item": "mana_pool",    "rate": 0.4},
                    {"item": "lavender",     "rate": 0.5},
                    {"item": "magic_stone",  "rate": 0.08},
                ],
            },
            {
                "id": "elder_fairy",
                "name": "장로 요정",
                "level": 18,
                "hp": 320,
                "attack": 72,
                "defense": 20,
                "exp": 300,
                "gold": (80, 160),
                "drops": [
                    {"item": "fairy_wing",   "rate": 0.12},
                    {"item": "magic_stone",  "rate": 0.2},
                    {"item": "pearl",        "rate": 0.08},
                    {"item": "reishi",       "rate": 0.25},
                ],
            },
            {
                "id": "ancient_treant",
                "name": "고대 나무정령",
                "level": 22,
                "hp": 700,
                "attack": 85,
                "defense": 35,
                "exp": 480,
                "gold": (150, 280),
                "drops": [
                    {"item": "ancient_fragment","rate": 0.15},
                    {"item": "gt_wood_01",   "rate": 0.8},
                    {"item": "healing_herb", "rate": 0.6},
                    {"item": "pearl",        "rate": 0.1},
                ],
            },
            {
                "id": "fairy_queen",
                "name": "요정 여왕 (보스)",
                "level": 25,
                "hp": 2000,
                "attack": 130,
                "defense": 50,
                "exp": 1500,
                "gold": (500, 1000),
                "drops": [
                    {"item": "fairy_wing",   "rate": 0.4},
                    {"item": "star_fragment","rate": 0.08},
                    {"item": "golden_key",   "rate": 0.03},
                    {"item": "magic_stone",  "rate": 0.3},
                    {"item": "diamond",      "rate": 0.06},
                ],
            },
        ],
    },
    "용암 동굴": {
        "name": "용암 동굴",
        "level_range": (25, 40),
        "monsters": [
            {
                "id": "fire_imp",
                "name": "화염 임프",
                "level": 25,
                "hp": 400,
                "attack": 100,
                "defense": 25,
                "exp": 350,
                "gold": (100, 200),
                "drops": [
                    {"item": "sulfur",       "rate": 0.6},
                    {"item": "coal",         "rate": 0.5},
                    {"item": "ruby",         "rate": 0.1},
                    {"item": "chili_powder", "rate": 0.3},
                ],
            },
            {
                "id": "lava_golem",
                "name": "용암 골렘",
                "level": 30,
                "hp": 900,
                "attack": 130,
                "defense": 60,
                "exp": 600,
                "gold": (200, 400),
                "drops": [
                    {"item": "mithril_ore",  "rate": 0.25},
                    {"item": "orichalcum_ore","rate": 0.08},
                    {"item": "ruby",         "rate": 0.12},
                    {"item": "emerald",      "rate": 0.08},
                ],
            },
            {
                "id": "magma_dragon",
                "name": "마그마 드래곤",
                "level": 35,
                "hp": 2500,
                "attack": 200,
                "defense": 80,
                "exp": 2000,
                "gold": (800, 1500),
                "drops": [
                    {"item": "dragon_scale", "rate": 0.15},
                    {"item": "orichalcum_ore","rate": 0.3},
                    {"item": "adamantium_ore","rate": 0.08},
                    {"item": "dragonite_ore","rate": 0.02},
                    {"item": "ruby",         "rate": 0.2},
                ],
            },
            {
                "id": "fire_demon_lord",
                "name": "화염 마왕 (보스)",
                "level": 40,
                "hp": 6000,
                "attack": 280,
                "defense": 110,
                "exp": 5000,
                "gold": (2000, 4000),
                "drops": [
                    {"item": "dragonite_ore","rate": 0.1},
                    {"item": "dragon_scale", "rate": 0.3},
                    {"item": "star_fragment","rate": 0.1},
                    {"item": "golden_key",   "rate": 0.05},
                    {"item": "ancient_fragment","rate": 0.2},
                ],
            },
        ],
    },
    "심해 던전": {
        "name": "심해 던전",
        "level_range": (30, 50),
        "monsters": [
            {
                "id": "deep_sea_knight",
                "name": "심해 기사",
                "level": 30,
                "hp": 800,
                "attack": 150,
                "defense": 70,
                "exp": 550,
                "gold": (180, 350),
                "drops": [
                    {"item": "shark_tooth",  "rate": 0.3},
                    {"item": "pearl",        "rate": 0.15},
                    {"item": "fish_bone",    "rate": 0.7},
                    {"item": "silver_ore",   "rate": 0.3},
                ],
            },
            {
                "id": "sea_serpent",
                "name": "바다 뱀",
                "level": 35,
                "hp": 1200,
                "attack": 180,
                "defense": 55,
                "exp": 800,
                "gold": (250, 500),
                "drops": [
                    {"item": "deep_sea_tear","rate": 0.05},
                    {"item": "shark_tooth",  "rate": 0.4},
                    {"item": "ancient_scale","rate": 0.2},
                    {"item": "orichalcum_ore","rate": 0.06},
                ],
            },
            {
                "id": "abyssal_guardian",
                "name": "심연의 수호자 (보스)",
                "level": 45,
                "hp": 8000,
                "attack": 320,
                "defense": 130,
                "exp": 8000,
                "gold": (3000, 6000),
                "drops": [
                    {"item": "deep_sea_tear","rate": 0.2},
                    {"item": "star_fragment","rate": 0.12},
                    {"item": "adamantium_ore","rate": 0.25},
                    {"item": "dragonite_ore","rate": 0.08},
                    {"item": "ancient_fragment","rate": 0.3},
                ],
            },
        ],
    },
}
