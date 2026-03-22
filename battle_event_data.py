# battle_event_data.py — 전투 중 랜덤 이벤트 풀
# process_turn()에서 20% 확률로 랜덤 선택

BATTLE_EVENTS = [
    {
        "id": "ground_shake",
        "desc": "갑자기 땅이 흔들린다! 발밑이 불안정하게 요동친다.",
        "choices": [
            {
                "label": "뒤로 물러난다",
                "effect": {"dodge_bonus": 0.3},
                "result_text": "안전하게 뒤로 물러났다! 다음 몬스터 공격을 피할 확률이 올랐다.",
            },
            {
                "label": "그대로 공격한다",
                "effect": {"damage_mult": 1.3, "take_damage": 5},
                "result_text": "위험을 무릅쓰고 강하게 공격했다! 하지만 발이 헛디뎌 약간의 피해를 입었다.",
            },
            {
                "label": "주위를 살핀다",
                "effect": {"item_find": True},
                "result_text": "발밑에 빛나는 무언가를 발견했다!",
            },
        ],
    },
    {
        "id": "sudden_wind",
        "desc": "갑작스러운 돌풍이 몰아친다! 시야가 순간 흐려진다.",
        "choices": [
            {
                "label": "눈을 감고 감각에 집중한다",
                "effect": {"crit_bonus": 0.2},
                "result_text": "어둠 속에서도 적의 움직임이 느껴진다. 크리티컬 확률이 올랐다!",
            },
            {
                "label": "바람을 이용해 돌진한다",
                "effect": {"damage_mult": 1.2},
                "result_text": "바람의 힘을 받아 강력한 돌진을 날렸다!",
            },
        ],
    },
    {
        "id": "mysterious_herb",
        "desc": "발밑에 알 수 없는 풀이 밟힌다. 향기가 어딘가 친숙하다.",
        "choices": [
            {
                "label": "풀을 먹어본다",
                "effect": {"heal_hp": 15},
                "result_text": "약초였다! HP가 약간 회복됐다.",
            },
            {
                "label": "무시하고 전투에 집중한다",
                "effect": {"damage_mult": 1.1},
                "result_text": "전투에만 집중했다. 집중력이 높아졌다!",
            },
        ],
    },
    {
        "id": "enemy_stumbles",
        "desc": "적이 발을 헛디뎌 잠시 빈틈이 생겼다!",
        "choices": [
            {
                "label": "즉시 공격한다",
                "effect": {"damage_mult": 1.5, "forced_crit": True},
                "result_text": "빈틈을 놓치지 않고 강력한 일격을 날렸다!",
            },
            {
                "label": "여유를 갖고 준비한다",
                "effect": {"heal_mp": 10},
                "result_text": "잠시 호흡을 가다듬으며 MP를 회복했다.",
            },
        ],
    },
    {
        "id": "shadow_blessing",
        "desc": "어둠 속에서 정체 모를 빛이 반짝인다...",
        "choices": [
            {
                "label": "빛을 향해 손을 뻗는다",
                "effect": {"random_buff": True},
                "result_text": "신비로운 에너지가 몸을 감쌌다!",
            },
            {
                "label": "경계하며 물러선다",
                "effect": {"dodge_bonus": 0.2},
                "result_text": "경계를 늦추지 않았다. 회피 확률이 올랐다.",
            },
        ],
    },
    {
        "id": "battle_cry",
        "desc": "멀리서 무언가가 외치는 소리가 들린다! 용기가 솟구치는 것 같다.",
        "choices": [
            {
                "label": "함성에 맞춰 기세를 올린다",
                "effect": {"damage_mult": 1.25},
                "result_text": "투지가 불타오른다! 공격력이 상승했다!!",
            },
            {
                "label": "무시하고 냉정을 유지한다",
                "effect": {"take_damage_reduce": 0.3},
                "result_text": "냉철하게 판단하며 방어를 강화했다.",
            },
        ],
    },
    {
        "id": "slippery_floor",
        "desc": "바닥이 미끄럽다! 균형을 잡기 어렵다.",
        "choices": [
            {
                "label": "낮게 자세를 잡는다",
                "effect": {"take_damage_reduce": 0.4},
                "result_text": "낮게 자세를 잡아 안정적인 방어 자세를 취했다.",
            },
            {
                "label": "미끄러지는 기세로 공격한다",
                "effect": {"damage_mult": 1.2, "take_damage": 3},
                "result_text": "미끄러지는 기세를 이용해 강타했다! 하지만 조금 다쳤다.",
            },
        ],
    },
    {
        "id": "wild_surge",
        "desc": "갑자기 마력이 불안정하게 요동친다!",
        "choices": [
            {
                "label": "마력을 억제한다",
                "effect": {"heal_mp": 20},
                "result_text": "마력을 안정시키며 MP를 회복했다.",
            },
            {
                "label": "마력을 폭발시킨다",
                "effect": {"damage_mult": 1.4, "mp_cost": 10},
                "result_text": "마력을 폭발시켜 강력한 공격을 날렸다! 하지만 MP가 소모됐다.",
            },
            {
                "label": "그대로 둔다",
                "effect": {"random_event": True},
                "result_text": "마력이 저절로 안정됐다... 이상한 일이다.",
            },
        ],
    },
    {
        "id": "lucky_find",
        "desc": "전투 중 발밑에서 반짝이는 작은 물체를 발견했다!",
        "choices": [
            {
                "label": "주워 담는다",
                "effect": {"item_find": True},
                "result_text": "아이템을 획득했다!",
            },
            {
                "label": "신경 쓰지 않는다",
                "effect": {"damage_mult": 1.1},
                "result_text": "전투에만 집중했다. 집중력이 높아졌다!",
            },
        ],
    },
    {
        "id": "monster_rage",
        "desc": "적이 분노에 휩싸여 공격적으로 변했다!",
        "choices": [
            {
                "label": "정면으로 맞선다",
                "effect": {"damage_mult": 1.3, "take_damage": 8},
                "result_text": "적의 분노를 정면으로 받아내며 강타를 날렸다!",
            },
            {
                "label": "냉정하게 거리를 둔다",
                "effect": {"take_damage_reduce": 0.5},
                "result_text": "거리를 유지하며 적의 분노가 가라앉길 기다렸다.",
            },
        ],
    },
]
