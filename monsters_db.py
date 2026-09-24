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
    "드레드 할로우": {
        "name": "드레드 할로우",
        "level_range": (1, 5),
        "monsters": [
            {
                "id": "slime",
                "creature_type": 'Ooze',
                "lore_basis": 'BG3 대응: Ochre Jelly',
                "bestiary": '산성 점액을 두른 동굴성 우즈. 베기와 번개에 강하고 산성 공격을 사용한다.',
                "traits": ['베기 저항', '번개 저항', '산성 공격'],
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
                "creature_type": 'Beast',
                "lore_basis": 'BG3 대응: Giant Spider',
                "bestiary": '거미줄 지형을 자유롭게 오가며 독성 물기로 사냥하는 거대 거미.',
                "traits": ['거미줄 이동', '독성 물기'],
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
                "creature_type": 'Humanoid',
                "lore_basis": 'BG3 계열: Goblin',
                "bestiary": '민첩하고 기습에 능한 소형 고블린. 츄라이더 지역 변종이다.',
                "traits": ['기습', '소형'],
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
                "creature_type": 'Beast',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '꿀 향을 따라 숲을 떠도는 곰. BG3 직접 대응 개체는 없다.',
                "traits": ['강한 근접 공격'],
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
                "creature_type": 'Fey',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '방울 같은 마력을 흩뿌리는 작은 페이 정령. BG3 직접 대응 개체는 없다.',
                "traits": ['마법 생물'],
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
    "폐허가 된 마을": {
        "name": "폐허가 된 마을",
        "level_range": (5, 12),
        "monsters": [
            {
                "id": "goblin_warrior",
                "creature_type": 'Humanoid',
                "lore_basis": 'BG3 대응: Goblin Warrior',
                "bestiary": '큰 무기를 휘두르는 전열 고블린. BG3의 Goblin Warrior는 Cleave와 Lacerate를 사용한다.',
                "traits": ['강공', '베기'],
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
                "creature_type": 'Humanoid',
                "lore_basis": 'BG3 영감: Goblin spellcaster',
                "bestiary": '주술과 지원 마법을 사용하는 고블린 술사. 특정 BG3 고유 개체를 그대로 옮긴 것은 아니다.',
                "traits": ['주술', '원거리 마법'],
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
                "creature_type": 'Humanoid',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '고블린 무리를 지배하는 우두머리. BG3의 특정 Goblin King과 직접 대응하지 않는다.',
                "traits": ['지휘관', '강공'],
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
        ],
    },
    "그림포지": {
        "name": "그림포지",
        "level_range": (10, 20),
        "monsters": [
            {
                "id": "skeleton",
                "creature_type": 'Undead',
                "lore_basis": 'BG3 대응: Skeleton',
                "bestiary": '암흑 마법으로 움직이는 뼈 언데드. 둔기에 약하고 독에 면역이다.',
                "traits": ['둔기 취약', '독 면역'],
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
                "creature_type": 'Construct',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '소금 결정으로 만들어진 골렘. BG3 직접 대응 개체는 없다.',
                "traits": ['구조물', '높은 방어'],
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
                "creature_type": 'Humanoid',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '그림포지의 어둠 마법사. BG3 특정 몬스터와 직접 대응하지 않는다.',
                "traits": ['암흑 마법'],
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
                    {"item": "magic_stone",  "rate": 0.08},
                ],
            },
        ],
    },
    "요정의숲": {
        "name": "셀루네 전초기지",
        "level_range": (18, 30),
        "monsters": [
            {
                "id": "ent_guardian",
                "creature_type": 'Plant',
                "lore_basis": 'BG3 영감: Wood Woad',
                "bestiary": '숲과 결속된 식물 수호자. BG3의 Wood Woad/Dryad 계열에서 전투 정체성을 참고했다.',
                "traits": ['속박', '자연 마법'],
                "name": "엔트 수호자",
                "level": 18,
                "hp": 500,
                "attack": 55,
                "defense": 35,
                "exp": 350,
                "gold": (120, 220),
                "drops": [
                    {"item": "gt_wood_01",       "rate": 0.7},
                    {"item": "ancient_fragment",  "rate": 0.06},
                    {"item": "magic_stone",       "rate": 0.1},
                ],
            },
            {
                "id": "forest_fairy",
                "creature_type": 'Fey',
                "lore_basis": 'BG3 영감: Dryad',
                "bestiary": '자연 마법과 속박을 다루는 숲의 페이. BG3 Dryad의 자연 마법 정체성을 참고했다.',
                "traits": ['자연 마법', '속박'],
                "name": "숲의 요정",
                "level": 22,
                "hp": 350,
                "attack": 70,
                "defense": 18,
                "exp": 450,
                "gold": (150, 280),
                "drops": [
                    {"item": "fairy_wing",  "rate": 0.05},
                    {"item": "mana_herb",   "rate": 0.5},
                    {"item": "magic_stone", "rate": 0.15},
                    {"item": "feather",     "rate": 0.4},
                ],
            },
            {
                "id": "fairy_queen",
                "creature_type": 'Fey',
                "lore_basis": '츄라이더 오리지널',
                "bestiary": '요정의 숲을 다스리는 지배자. BG3 직접 대응 개체는 없다.',
                "traits": ['마법 저항', '자연 마법'],
                "name": "요정 여왕",
                "level": 28,
                "hp": 800,
                "attack": 95,
                "defense": 30,
                "exp": 750,
                "gold": (250, 500),
                "drops": [
                    {"item": "fairy_wing",       "rate": 0.15},
                    {"item": "star_fragment",    "rate": 0.05},
                    {"item": "magic_stone",      "rate": 0.25},
                    {"item": "mana_herb",        "rate": 0.6},
                ],
            },
        ],
    },
    "용의둥지": {
        "name": "용의 둥지",
        "level_range": (30, 50),
        "monsters": [
            {
                "id": "drake",
                "creature_type": 'Dragon',
                "lore_basis": 'D&D/BG3 용족 영감',
                "bestiary": '용의 혈통을 지닌 포식자. BG3의 특정 이름 개체와 직접 대응하지 않는다.',
                "traits": ['용족', '브레스 영감'],
                "name": "드레이크",
                "level": 30,
                "hp": 1200,
                "attack": 110,
                "defense": 50,
                "exp": 1000,
                "gold": (300, 600),
                "drops": [
                    {"item": "dragon_scale",     "rate": 0.12},
                    {"item": "dragonite_ore",    "rate": 0.25},
                    {"item": "magic_stone",      "rate": 0.2},
                ],
            },
            {
                "id": "elder_dragon",
                "creature_type": 'Dragon',
                "lore_basis": 'D&D/BG3 용족 영감',
                "bestiary": '오랜 세월 힘을 축적한 츄라이더 용. BG3 특정 개체의 복제는 아니다.',
                "traits": ['마법 저항', '브레스'],
                "name": "장로 드래곤",
                "level": 40,
                "hp": 3000,
                "attack": 180,
                "defense": 80,
                "exp": 2500,
                "gold": (600, 1200),
                "drops": [
                    {"item": "dragon_scale",     "rate": 0.3},
                    {"item": "dragonite_ore",    "rate": 0.5},
                    {"item": "star_fragment",    "rate": 0.08},
                    {"item": "ancient_fragment", "rate": 0.1},
                ],
            },
            {
                "id": "ancient_dragon",
                "creature_type": 'Dragon',
                "lore_basis": 'BG3 Red Dragon 영감',
                "bestiary": '거대한 고대 용. BG3 Red Dragon의 화염 브레스와 마법 저항 정체성을 참고했다.',
                "traits": ['화염 브레스', '마법 저항'],
                "name": "태고의 드래곤",
                "level": 50,
                "hp": 6000,
                "attack": 280,
                "defense": 120,
                "exp": 5000,
                "gold": (1500, 3000),
                "drops": [
                    {"item": "dragon_scale",     "rate": 0.5},
                    {"item": "dragonite_ore",    "rate": 0.7},
                    {"item": "star_fragment",    "rate": 0.15},
                    {"item": "ancient_fragment", "rate": 0.2},
                    {"item": "fairy_wing",       "rate": 0.08},
                ],
            },
        ],
    },
}
