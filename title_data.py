"""title_data.py — 타이틀별 전용 효과 데이터 (업적 난이도 비례)"""

# 타이틀 효과 형식:
# {
#   "stat_bonus": {"str": N, "int": N, ...},   # 기본 스탯 보너스
#   "atk_bonus": N,                             # 공격력 보너스
#   "def_bonus": N,                             # 방어력 보너스
#   "crit_bonus": N,                            # 크리티컬 확률 보너스 (%)
#   "gather_bonus": N,                          # 채집 성공률 보너스 (%)
#   "cook_bonus": N,                            # 요리 성공률 보너스 (%)
#   "fish_bonus": N,                            # 낚시 보너스
#   "hp_regen": N,                              # 전투 외 HP 회복량 보너스
#   "gold_bonus_pct": N,                        # 획득 골드 보너스 (%)
# }

TITLE_EFFECTS = {
    # ── 기본 시작 타이틀 ────────────────────────────────────────────────────
    "비전의 탑 신입": {
        "desc": "모험을 막 시작한 신입.",
        "effects": {},
    },

    # ── 전투 계열 (쉬움 → 어려움) ─────────────────────────────────────────
    "초보 전사": {
        "desc": "첫 전투에서 승리한 전사.",
        "effects": {
            "atk_bonus": 1,
            "stat_bonus": {"str": 1},
        },
    },
    "싸움꾼": {
        "desc": "10번의 전투를 이긴 용감한 전사.",
        "effects": {
            "atk_bonus": 2,
            "crit_bonus": 1,
            "stat_bonus": {"str": 2},
        },
    },
    "백전노장": {
        "desc": "50번의 전투를 이긴 노련한 전사.",
        "effects": {
            "atk_bonus": 5,
            "def_bonus": 2,
            "crit_bonus": 3,
            "stat_bonus": {"str": 5, "will": 2},
        },
    },
    "전장의 지배자": {
        "desc": "100번의 전투를 지배한 전설적 전사.",
        "effects": {
            "atk_bonus": 10,
            "def_bonus": 5,
            "crit_bonus": 5,
            "stat_bonus": {"str": 10, "will": 5, "max_hp": 30},
        },
    },

    # ── 낚시 계열 ────────────────────────────────────────────────────────
    "낚시 초보": {
        "desc": "처음으로 물고기를 낚은 낚시꾼.",
        "effects": {
            "fish_bonus": 1,
            "stat_bonus": {"dex": 1, "luck": 1},
        },
    },
    "베테랑 낚시꾼": {
        "desc": "50마리의 물고기를 낚은 베테랑.",
        "effects": {
            "fish_bonus": 3,
            "stat_bonus": {"dex": 3, "luck": 3},
        },
    },
    "전설의 낚시꾼": {
        "desc": "전설 등급 물고기를 낚은 낚시꾼.",
        "effects": {
            "fish_bonus": 5,
            "stat_bonus": {"dex": 5, "luck": 5},
            "gold_bonus_pct": 3,
        },
    },

    # ── 요리 계열 ────────────────────────────────────────────────────────
    "요리 초보": {
        "desc": "처음으로 요리를 완성한 요리사.",
        "effects": {
            "cook_bonus": 2,
            "stat_bonus": {"int": 1},
        },
    },
    "솜씨 좋은 요리사": {
        "desc": "30번 요리를 완성한 솜씨 좋은 요리사.",
        "effects": {
            "cook_bonus": 5,
            "stat_bonus": {"int": 3, "will": 1},
            "hp_regen": 5,
        },
    },

    # ── 경제 계열 ────────────────────────────────────────────────────────
    "소상공인": {
        "desc": "1,000G를 보유한 소상공인.",
        "effects": {
            "gold_bonus_pct": 2,
            "stat_bonus": {"luck": 1},
        },
    },
    "대부호": {
        "desc": "10,000G를 보유한 대부호.",
        "effects": {
            "gold_bonus_pct": 5,
            "stat_bonus": {"luck": 3, "int": 2},
        },
    },

    # ── 수집 계열 ────────────────────────────────────────────────────────
    "수집가": {
        "desc": "도감에 10종을 등록한 수집가.",
        "effects": {
            "gather_bonus": 2,
            "stat_bonus": {"dex": 1, "luck": 1},
        },
    },
    "박물학자": {
        "desc": "도감에 50종을 등록한 박물학자.",
        "effects": {
            "gather_bonus": 5,
            "stat_bonus": {"int": 3, "dex": 2, "luck": 2},
        },
    },

    # ── 특수 계열 ────────────────────────────────────────────────────────
    "츄라이더의 친구": {
        "desc": "츄라이더를 50번 쓰다듬은 인류 최고의 친구.",
        "effects": {
            "stat_bonus": {"will": 2, "luck": 3},
            "hp_regen": 3,
        },
    },
    "성장하는 모험가": {
        "desc": "레벨 10에 도달한 성장하는 모험가.",
        "effects": {
            "atk_bonus": 3,
            "def_bonus": 2,
            "stat_bonus": {"str": 3, "int": 2, "dex": 2, "will": 2},
        },
    },
}


def get_title_effects(title_name: str) -> dict:
    """타이틀 이름으로 효과 딕셔너리 반환. 미등록 타이틀은 빈 딕셔너리."""
    entry = TITLE_EFFECTS.get(title_name, {})
    return entry.get("effects", {})


def get_title_desc(title_name: str) -> str:
    """타이틀 설명 반환."""
    entry = TITLE_EFFECTS.get(title_name, {})
    return entry.get("desc", "")


def format_title_effects(title_name: str) -> str:
    """타이틀 효과를 표시용 문자열로 변환."""
    effects = get_title_effects(title_name)
    if not effects:
        return "효과 없음"
    parts = []
    stat_bonus = effects.get("stat_bonus", {})
    stat_names = {
        "str": "힘", "int": "지력", "dex": "민첩",
        "will": "의지", "luck": "운", "max_hp": "최대HP",
        "max_mp": "최대MP",
    }
    for stat, val in stat_bonus.items():
        name = stat_names.get(stat, stat)
        parts.append(f"{name}+{val}")
    if effects.get("atk_bonus"):
        parts.append(f"공격력+{effects['atk_bonus']}")
    if effects.get("def_bonus"):
        parts.append(f"방어력+{effects['def_bonus']}")
    if effects.get("crit_bonus"):
        parts.append(f"크리티컬+{effects['crit_bonus']}%")
    if effects.get("gather_bonus"):
        parts.append(f"채집성공+{effects['gather_bonus']}%")
    if effects.get("cook_bonus"):
        parts.append(f"요리성공+{effects['cook_bonus']}%")
    if effects.get("fish_bonus"):
        parts.append(f"낚시보너스+{effects['fish_bonus']}")
    if effects.get("hp_regen"):
        parts.append(f"자연회복HP+{effects['hp_regen']}")
    if effects.get("gold_bonus_pct"):
        parts.append(f"골드보너스+{effects['gold_bonus_pct']}%")
    return ", ".join(parts) if parts else "효과 없음"
