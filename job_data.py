"""job_data.py — NPC별 알바 데이터 (난이도 3단계 × 바리에이션 3개 = 9개/NPC)

알바 유형:
  - deliver: 퀘스트 전용 아이템 수령 → 대상 NPC에게 전달
  - gather:  특정 아이템 N개 채집/제출
  - hunt:    몬스터 N마리 처치 후 보고
"""
import random

# 각 NPC별 알바 풀 (9개)
# 난이도: easy / normal / hard
# type: deliver / gather / hunt
# reward: item_id 또는 None (없으면 골드+exp만)

NPC_JOB_POOL = {
    "다몬": [
        # 쉬움 ×3
        {
            "id": "damon_e1", "name": "철 주괴 납품",
            "difficulty": "easy", "type": "gather",
            "target_item": "iron_bar", "target_count": 2,
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {"crafting": 20},
            "energy_cost": 10,
            "desc": "철 주괴 2개를 가져다 주세요.",
        },
        {
            "id": "damon_e2", "name": "나무 조각 수집",
            "difficulty": "easy", "type": "gather",
            "target_item": "gt_wood_01", "target_count": 3,
            "reward_gold": 35, "reward_exp": 8, "reward_item": "con_bread",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "나무 조각 3개를 대장간에 가져다 주세요.",
        },
        {
            "id": "damon_e3", "name": "심부름",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "제블로어", "deliver_item": "dq_damon_letter",
            "deliver_item_name": "다몬의 서신",
            "reward_gold": 45, "reward_exp": 12, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "제블로어에게 다몬의 서신을 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "damon_n1", "name": "석탄 채굴 보조",
            "difficulty": "normal", "type": "gather",
            "target_item": "coal", "target_count": 5,
            "reward_gold": 90, "reward_exp": 20, "reward_item": "iron_bar",
            "reward_skill_exp": {"metallurgy": 30},
            "energy_cost": 20,
            "desc": "석탄 5개를 채굴해서 가져다 주세요.",
        },
        {
            "id": "damon_n2", "name": "광석 정리",
            "difficulty": "normal", "type": "gather",
            "target_item": "iron_ore", "target_count": 5,
            "reward_gold": 85, "reward_exp": 18, "reward_item": "tool_mortar",
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "철광석 5개를 가져다 주세요.",
        },
        {
            "id": "damon_n3", "name": "재료 배달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "몰", "deliver_item": "dq_damon_ore_sample",
            "deliver_item_name": "광석 견본",
            "reward_gold": 100, "reward_exp": 22, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "몰에게 광석 견본을 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "damon_h1", "name": "몬스터 소탕",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "goblin", "target_count": 3,
            "reward_gold": 200, "reward_exp": 40, "reward_item": "iron_bar",
            "reward_skill_exp": {"crafting": 60},
            "energy_cost": 35,
            "desc": "주변 고블린 3마리를 처치해 주세요.",
        },
        {
            "id": "damon_h2", "name": "은 주괴 납품",
            "difficulty": "hard", "type": "gather",
            "target_item": "silver_bar", "target_count": 2,
            "reward_gold": 220, "reward_exp": 45, "reward_item": "iron_bar",
            "reward_skill_exp": {"metallurgy": 80},
            "energy_cost": 35,
            "desc": "은 주괴 2개를 제련해서 가져다 주세요.",
        },
        {
            "id": "damon_h3", "name": "철제 검 납품",
            "difficulty": "hard", "type": "gather",
            "target_item": "wp_sword_02", "target_count": 1,
            "reward_gold": 250, "reward_exp": 50, "reward_item": "iron_bar",
            "reward_skill_exp": {"crafting": 100},
            "energy_cost": 35,
            "desc": "철제 롱소드 1개를 제작해서 납품해 주세요.",
        },
    ],

    "오멜룸": [
        # 쉬움 ×3
        {
            "id": "omelum_e1", "name": "약초 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "herb", "target_count": 3,
            "reward_gold": 30, "reward_exp": 8, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "약초 3개를 채집해서 가져다 주세요.",
        },
        {
            "id": "omelum_e2", "name": "물 뜨기",
            "difficulty": "easy", "type": "gather",
            "target_item": "water", "target_count": 2,
            "reward_gold": 25, "reward_exp": 6, "reward_item": "antidote",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "물 2개를 빈 병에 담아 가져다 주세요.",
        },
        {
            "id": "omelum_e3", "name": "심부름",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "브룩샤", "deliver_item": "dq_omelum_herb_tea",
            "deliver_item_name": "오멜룸의 허브 견본",
            "reward_gold": 35, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "브룩샤에게 허브 견본을 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "omelum_n1", "name": "마나 허브 채집",
            "difficulty": "normal", "type": "gather",
            "target_item": "mana_herb", "target_count": 3,
            "reward_gold": 80, "reward_exp": 18, "reward_item": "mp_potion_basic",
            "reward_skill_exp": {"alchemy": 20},
            "energy_cost": 20,
            "desc": "마나 허브 3개를 채집해서 가져다 주세요.",
        },
        {
            "id": "omelum_n2", "name": "포션 재료 정리",
            "difficulty": "normal", "type": "gather",
            "target_item": "healing_root", "target_count": 2,
            "reward_gold": 90, "reward_exp": 20, "reward_item": "con_potion_h",
            "reward_skill_exp": {"alchemy": 25},
            "energy_cost": 20,
            "desc": "치유의 뿌리 2개를 가져다 주세요.",
        },
        {
            "id": "omelum_n3", "name": "의약품 배달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "카엘릭", "deliver_item": "dq_omelum_medicine",
            "deliver_item_name": "오멜룸의 의약품",
            "reward_gold": 100, "reward_exp": 22, "reward_item": None,
            "reward_skill_exp": {"alchemy": 15},
            "energy_cost": 20,
            "desc": "카엘릭에게 의약품을 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "omelum_h1", "name": "독초 채집",
            "difficulty": "hard", "type": "gather",
            "target_item": "poison_herb", "target_count": 3,
            "reward_gold": 180, "reward_exp": 38, "reward_item": "energy_potion",
            "reward_skill_exp": {"alchemy": 50},
            "energy_cost": 35,
            "desc": "독초 3개를 조심히 채집해서 가져다 주세요.",
        },
        {
            "id": "omelum_h2", "name": "슬라임 처치",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "slime", "target_count": 5,
            "reward_gold": 200, "reward_exp": 42, "reward_item": "con_potion_h",
            "reward_skill_exp": {"alchemy": 40},
            "energy_cost": 35,
            "desc": "슬라임 5마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "omelum_h3", "name": "마나꽃 채집",
            "difficulty": "hard", "type": "gather",
            "target_item": "mana_flower", "target_count": 2,
            "reward_gold": 220, "reward_exp": 45, "reward_item": "mp_potion_mid",
            "reward_skill_exp": {"alchemy": 60},
            "energy_cost": 35,
            "desc": "마나꽃 2개를 채집해서 가져다 주세요.",
        },
    ],

    "브룩샤": [
        # 쉬움 ×3
        {
            "id": "brooksha_e1", "name": "소금 심부름",
            "difficulty": "easy", "type": "gather",
            "target_item": "salt", "target_count": 2,
            "reward_gold": 30, "reward_exp": 8, "reward_item": "ck_soup_01",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "소금 2개를 가져다 주세요.",
        },
        {
            "id": "brooksha_e2", "name": "달걀 가져오기",
            "difficulty": "easy", "type": "gather",
            "target_item": "egg", "target_count": 3,
            "reward_gold": 35, "reward_exp": 9, "reward_item": "mushroom_soup",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "달걀 3개를 가져다 주세요.",
        },
        {
            "id": "brooksha_e3", "name": "요리 배달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "아라벨라", "deliver_item": "dq_brooksha_lunch",
            "deliver_item_name": "브룩샤의 도시락",
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "아라벨라에게 도시락을 배달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "brooksha_n1", "name": "버섯 채집",
            "difficulty": "normal", "type": "gather",
            "target_item": "mushroom", "target_count": 4,
            "reward_gold": 85, "reward_exp": 18, "reward_item": "mushroom_soup",
            "reward_skill_exp": {"cooking": 20},
            "energy_cost": 20,
            "desc": "버섯 4개를 채집해서 가져다 주세요.",
        },
        {
            "id": "brooksha_n2", "name": "꿀 조달",
            "difficulty": "normal", "type": "gather",
            "target_item": "honey", "target_count": 2,
            "reward_gold": 90, "reward_exp": 20, "reward_item": "honey_milk",
            "reward_skill_exp": {"cooking": 25},
            "energy_cost": 20,
            "desc": "꿀 2개를 가져다 주세요.",
        },
        {
            "id": "brooksha_n3", "name": "식재료 배달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "오멜룸", "deliver_item": "dq_brooksha_ingredient",
            "deliver_item_name": "브룩샤의 식재료 견본",
            "reward_gold": 100, "reward_exp": 22, "reward_item": None,
            "reward_skill_exp": {"cooking": 15},
            "energy_cost": 20,
            "desc": "오멜룸에게 식재료 견본을 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "brooksha_h1", "name": "연어 조달",
            "difficulty": "hard", "type": "gather",
            "target_item": "fs_salmon_01", "target_count": 2,
            "reward_gold": 200, "reward_exp": 40, "reward_item": "ck_steak_01",
            "reward_skill_exp": {"cooking": 60},
            "energy_cost": 35,
            "desc": "연어 2마리를 낚아서 가져다 주세요.",
        },
        {
            "id": "brooksha_h2", "name": "특별 재료 사냥",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "boar", "target_count": 2,
            "reward_gold": 210, "reward_exp": 42, "reward_item": "ck_steak_01",
            "reward_skill_exp": {"cooking": 50},
            "energy_cost": 35,
            "desc": "멧돼지 2마리를 잡고 보고해 주세요.",
        },
        {
            "id": "brooksha_h3", "name": "고급 도시락 배달",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_brooksha_special",
            "deliver_item_name": "브룩샤의 특제 도시락",
            "reward_gold": 230, "reward_exp": 48, "reward_item": "ck_special_01",
            "reward_skill_exp": {"cooking": 70},
            "energy_cost": 35,
            "desc": "엘레라신에게 특제 도시락을 배달해 주세요.",
        },
    ],

    "몰": [
        # 쉬움 ×3
        {
            "id": "mol_e1", "name": "짐 운반 (소량)",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "다몬", "deliver_item": "dq_mol_package_s",
            "deliver_item_name": "몰의 소포 (소)",
            "reward_gold": 35, "reward_exp": 8, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "다몬에게 소포를 전달해 주세요.",
        },
        {
            "id": "mol_e2", "name": "빈 병 수거",
            "difficulty": "easy", "type": "gather",
            "target_item": "empty_bottle", "target_count": 3,
            "reward_gold": 30, "reward_exp": 7, "reward_item": "tool_mortar",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "빈 병 3개를 가져다 주세요.",
        },
        {
            "id": "mol_e3", "name": "도구 배달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "오멜룸", "deliver_item": "dq_mol_tools",
            "deliver_item_name": "몰의 도구 상자",
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "오멜룸에게 도구 상자를 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "mol_n1", "name": "짐 운반 (중간)",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "제블로어", "deliver_item": "dq_mol_package_m",
            "deliver_item_name": "몰의 소포 (중)",
            "reward_gold": 90, "reward_exp": 18, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "제블로어에게 소포를 전달해 주세요.",
        },
        {
            "id": "mol_n2", "name": "잡초 제거",
            "difficulty": "normal", "type": "gather",
            "target_item": "gt_herb_01", "target_count": 5,
            "reward_gold": 85, "reward_exp": 17, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "들풀 5개를 제거해 주세요.",
        },
        {
            "id": "mol_n3", "name": "나무 조각 수집",
            "difficulty": "normal", "type": "gather",
            "target_item": "gt_wood_01", "target_count": 4,
            "reward_gold": 80, "reward_exp": 16, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "나무 조각 4개를 가져다 주세요.",
        },
        # 어려움 ×3
        {
            "id": "mol_h1", "name": "가방 재료 조달",
            "difficulty": "hard", "type": "gather",
            "target_item": "lt_leather_01", "target_count": 4,
            "reward_gold": 190, "reward_exp": 38, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "가죽 4개를 가져다 주세요.",
        },
        {
            "id": "mol_h2", "name": "위험한 짐 운반",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "게일의 환영", "deliver_item": "dq_mol_magic_goods",
            "deliver_item_name": "몰의 마법 상품",
            "reward_gold": 210, "reward_exp": 42, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "게일의 환영에게 마법 상품을 전달해 주세요.",
        },
        {
            "id": "mol_h3", "name": "고블린 소탕",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "goblin", "target_count": 5,
            "reward_gold": 240, "reward_exp": 48, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "고블린 5마리를 소탕하고 보고해 주세요.",
        },
    ],

    "제블로어": [
        # 쉬움 ×3
        {
            "id": "zeblor_e1", "name": "초소 순찰",
            "difficulty": "easy", "type": "hunt",
            "target_monster": "slime", "target_count": 2,
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "슬라임 2마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "zeblor_e2", "name": "보고서 전달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_zeblor_report",
            "deliver_item_name": "제블로어의 순찰 보고서",
            "reward_gold": 35, "reward_exp": 8, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "엘레라신에게 순찰 보고서를 전달해 주세요.",
        },
        {
            "id": "zeblor_e3", "name": "경계 물자 수령",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "다몬", "deliver_item": "dq_zeblor_request",
            "deliver_item_name": "제블로어의 물자 요청서",
            "reward_gold": 45, "reward_exp": 11, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "다몬에게 물자 요청서를 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "zeblor_n1", "name": "고블린 토벌",
            "difficulty": "normal", "type": "hunt",
            "target_monster": "goblin", "target_count": 3,
            "reward_gold": 100, "reward_exp": 22, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "고블린 3마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "zeblor_n2", "name": "경비 지원",
            "difficulty": "normal", "type": "gather",
            "target_item": "iron_bar", "target_count": 3,
            "reward_gold": 95, "reward_exp": 20, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "경비 무기 수리를 위한 철 주괴 3개를 가져다 주세요.",
        },
        {
            "id": "zeblor_n3", "name": "순찰 보고",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_zeblor_patrol",
            "deliver_item_name": "순찰 결과 보고서",
            "reward_gold": 110, "reward_exp": 24, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "순찰 결과를 엘레라신에게 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "zeblor_h1", "name": "오크 토벌",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "orc", "target_count": 3,
            "reward_gold": 220, "reward_exp": 44, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "오크 3마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "zeblor_h2", "name": "방어 장비 조달",
            "difficulty": "hard", "type": "gather",
            "target_item": "ar_helm_02", "target_count": 1,
            "reward_gold": 200, "reward_exp": 40, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "철투구 1개를 만들어서 납품해 주세요.",
        },
        {
            "id": "zeblor_h3", "name": "긴급 보고",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_zeblor_urgent",
            "deliver_item_name": "긴급 위협 보고서",
            "reward_gold": 240, "reward_exp": 48, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "엘레라신에게 긴급 위협 보고서를 전달해 주세요.",
        },
    ],

    "실렌": [
        # 쉬움 ×3
        {
            "id": "silin_e1", "name": "낚시 보조",
            "difficulty": "easy", "type": "gather",
            "target_item": "fs_carp_01", "target_count": 2,
            "reward_gold": 30, "reward_exp": 8, "reward_item": "con_bread",
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "붕어 2마리를 낚아서 가져다 주세요.",
        },
        {
            "id": "silin_e2", "name": "낚시 도구 정리",
            "difficulty": "easy", "type": "gather",
            "target_item": "gt_wood_01", "target_count": 2,
            "reward_gold": 25, "reward_exp": 7, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "낚싯대 수리용 나무 조각 2개를 가져다 주세요.",
        },
        {
            "id": "silin_e3", "name": "소금 전달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "브룩샤", "deliver_item": "dq_silin_fish_package",
            "deliver_item_name": "실렌의 생선 꾸러미",
            "reward_gold": 35, "reward_exp": 9, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "브룩샤에게 생선 꾸러미를 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "silin_n1", "name": "연어 낚시",
            "difficulty": "normal", "type": "gather",
            "target_item": "fs_salmon_01", "target_count": 2,
            "reward_gold": 80, "reward_exp": 18, "reward_item": "salt_grilled_fish",
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "연어 2마리를 낚아서 가져다 주세요.",
        },
        {
            "id": "silin_n2", "name": "물 채집",
            "difficulty": "normal", "type": "gather",
            "target_item": "water", "target_count": 3,
            "reward_gold": 75, "reward_exp": 16, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "물 3개를 빈 병에 담아서 가져다 주세요.",
        },
        {
            "id": "silin_n3", "name": "낚시 보고서",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_silin_report",
            "deliver_item_name": "실렌의 낚시 보고서",
            "reward_gold": 90, "reward_exp": 20, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "엘레라신에게 낚시 보고서를 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "silin_h1", "name": "강 몬스터 처치",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "water_snake", "target_count": 3,
            "reward_gold": 190, "reward_exp": 38, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "강 뱀 3마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "silin_h2", "name": "전설의 물고기 낚기",
            "difficulty": "hard", "type": "gather",
            "target_item": "fs_gold_eel_01", "target_count": 1,
            "reward_gold": 220, "reward_exp": 44, "reward_item": "eel_special",
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "황금장어 1마리를 낚아서 가져다 주세요.",
        },
        {
            "id": "silin_h3", "name": "특별 생선 배달",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "브룩샤", "deliver_item": "dq_silin_rare_fish",
            "deliver_item_name": "실렌의 희귀 생선 꾸러미",
            "reward_gold": 210, "reward_exp": 42, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "브룩샤에게 희귀 생선 꾸러미를 전달해 주세요.",
        },
    ],

    "알피라": [
        # 쉬움 ×3
        {
            "id": "alpira_e1", "name": "악보 배달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "게일의 환영", "deliver_item": "dq_alpira_score",
            "deliver_item_name": "알피라의 악보",
            "reward_gold": 35, "reward_exp": 9, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "게일의 환영에게 악보를 전달해 주세요.",
        },
        {
            "id": "alpira_e2", "name": "들꽃 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "gt_flower_01", "target_count": 3,
            "reward_gold": 30, "reward_exp": 8, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "들꽃 3개를 채집해서 가져다 주세요.",
        },
        {
            "id": "alpira_e3", "name": "공연 전단 배포",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "몰", "deliver_item": "dq_alpira_flyer",
            "deliver_item_name": "알피라의 공연 전단",
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "몰에게 공연 전단을 나눠 주세요.",
        },
        # 보통 ×3
        {
            "id": "alpira_n1", "name": "꿀 조달",
            "difficulty": "normal", "type": "gather",
            "target_item": "honey", "target_count": 2,
            "reward_gold": 80, "reward_exp": 17, "reward_item": "honey_milk",
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "공연 준비용 꿀 2개를 가져다 주세요.",
        },
        {
            "id": "alpira_n2", "name": "공연 소품 배달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "아라벨라", "deliver_item": "dq_alpira_prop",
            "deliver_item_name": "알피라의 공연 소품",
            "reward_gold": 90, "reward_exp": 19, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "아라벨라에게 공연 소품을 전달해 주세요.",
        },
        {
            "id": "alpira_n3", "name": "나무 조각 수집",
            "difficulty": "normal", "type": "gather",
            "target_item": "gt_wood_01", "target_count": 3,
            "reward_gold": 85, "reward_exp": 18, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "악기 수리용 나무 조각 3개를 가져다 주세요.",
        },
        # 어려움 ×3
        {
            "id": "alpira_h1", "name": "몬스터 퇴치",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "goblin", "target_count": 4,
            "reward_gold": 195, "reward_exp": 39, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "공연장 주변 고블린 4마리를 처치해 주세요.",
        },
        {
            "id": "alpira_h2", "name": "희귀 재료 조달",
            "difficulty": "hard", "type": "gather",
            "target_item": "gt_flower_01", "target_count": 8,
            "reward_gold": 185, "reward_exp": 37, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "공연 장식용 들꽃 8개를 채집해 주세요.",
        },
        {
            "id": "alpira_h3", "name": "특별 공연 홍보",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_alpira_vip_invite",
            "deliver_item_name": "알피라의 VIP 초대장",
            "reward_gold": 220, "reward_exp": 44, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "엘레라신에게 VIP 초대장을 전달해 주세요.",
        },
    ],

    "아라벨라": [
        # 쉬움 ×3
        {
            "id": "arabela_e1", "name": "마법 재료 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "herb", "target_count": 3,
            "reward_gold": 35, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {"alchemy": 10},
            "energy_cost": 10,
            "desc": "약초 3개를 채집해서 가져다 주세요.",
        },
        {
            "id": "arabela_e2", "name": "메모 전달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "게일의 환영", "deliver_item": "dq_arabela_memo",
            "deliver_item_name": "아라벨라의 메모",
            "reward_gold": 40, "reward_exp": 11, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "게일의 환영에게 메모를 전달해 주세요.",
        },
        {
            "id": "arabela_e3", "name": "마나 허브 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "mana_herb", "target_count": 2,
            "reward_gold": 45, "reward_exp": 12, "reward_item": None,
            "reward_skill_exp": {"alchemy": 15},
            "energy_cost": 10,
            "desc": "마나 허브 2개를 채집해서 가져다 주세요.",
        },
        # 보통 ×3
        {
            "id": "arabela_n1", "name": "슬라임 처치",
            "difficulty": "normal", "type": "hunt",
            "target_monster": "slime", "target_count": 3,
            "reward_gold": 95, "reward_exp": 20, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "슬라임 3마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "arabela_n2", "name": "마법 실험 보조",
            "difficulty": "normal", "type": "gather",
            "target_item": "magic_stone", "target_count": 1,
            "reward_gold": 100, "reward_exp": 22, "reward_item": "mp_potion_basic",
            "reward_skill_exp": {"alchemy": 25},
            "energy_cost": 20,
            "desc": "마법의 돌 1개를 가져다 주세요.",
        },
        {
            "id": "arabela_n3", "name": "시약 배달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "오멜룸", "deliver_item": "dq_arabela_reagent",
            "deliver_item_name": "아라벨라의 시약",
            "reward_gold": 110, "reward_exp": 24, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "오멜룸에게 시약을 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "arabela_h1", "name": "고급 마법 재료 채집",
            "difficulty": "hard", "type": "gather",
            "target_item": "mana_flower", "target_count": 2,
            "reward_gold": 215, "reward_exp": 43, "reward_item": "mp_potion_mid",
            "reward_skill_exp": {"alchemy": 55},
            "energy_cost": 35,
            "desc": "마나꽃 2개를 채집해서 가져다 주세요.",
        },
        {
            "id": "arabela_h2", "name": "위험 몬스터 처치",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "forest_spirit", "target_count": 2,
            "reward_gold": 230, "reward_exp": 46, "reward_item": "all_potion",
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "숲 정령 2마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "arabela_h3", "name": "비밀 서류 전달",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "게일의 환영", "deliver_item": "dq_arabela_secret",
            "deliver_item_name": "아라벨라의 비밀 연구 노트",
            "reward_gold": 245, "reward_exp": 49, "reward_item": None,
            "reward_skill_exp": {"alchemy": 70},
            "energy_cost": 35,
            "desc": "게일의 환영에게 비밀 연구 노트를 전달해 주세요.",
        },
    ],

    "엘레라신": [
        # 쉬움 ×3
        {
            "id": "elerasin_e1", "name": "서류 전달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "제블로어", "deliver_item": "dq_elerasin_order",
            "deliver_item_name": "엘레라신의 명령서",
            "reward_gold": 45, "reward_exp": 12, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "제블로어에게 명령서를 전달해 주세요.",
        },
        {
            "id": "elerasin_e2", "name": "길드 심부름",
            "difficulty": "easy", "type": "gather",
            "target_item": "gt_herb_01", "target_count": 4,
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "들풀 4개를 채집해서 가져다 주세요.",
        },
        {
            "id": "elerasin_e3", "name": "슬라임 처치",
            "difficulty": "easy", "type": "hunt",
            "target_monster": "slime", "target_count": 2,
            "reward_gold": 50, "reward_exp": 13, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "슬라임 2마리를 처치하고 보고해 주세요.",
        },
        # 보통 ×3
        {
            "id": "elerasin_n1", "name": "고블린 정찰",
            "difficulty": "normal", "type": "hunt",
            "target_monster": "goblin", "target_count": 4,
            "reward_gold": 110, "reward_exp": 24, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "고블린 4마리를 처치하고 정찰 결과를 보고해 주세요.",
        },
        {
            "id": "elerasin_n2", "name": "무기 납품",
            "difficulty": "normal", "type": "gather",
            "target_item": "wp_sword_02", "target_count": 1,
            "reward_gold": 120, "reward_exp": 26, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "철제 롱소드 1개를 납품해 주세요.",
        },
        {
            "id": "elerasin_n3", "name": "긴급 연락",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "카엘릭", "deliver_item": "dq_elerasin_message",
            "deliver_item_name": "엘레라신의 긴급 메시지",
            "reward_gold": 115, "reward_exp": 25, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "카엘릭에게 긴급 메시지를 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "elerasin_h1", "name": "오크 토벌",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "orc", "target_count": 4,
            "reward_gold": 235, "reward_exp": 47, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "오크 4마리를 토벌하고 보고해 주세요.",
        },
        {
            "id": "elerasin_h2", "name": "비밀 임무",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "게일의 환영", "deliver_item": "dq_elerasin_secret",
            "deliver_item_name": "엘레라신의 기밀 서류",
            "reward_gold": 248, "reward_exp": 50, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "게일의 환영에게 기밀 서류를 전달해 주세요.",
        },
        {
            "id": "elerasin_h3", "name": "고급 방어구 납품",
            "difficulty": "hard", "type": "gather",
            "target_item": "ar_body_02", "target_count": 1,
            "reward_gold": 240, "reward_exp": 48, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "체인메일 1개를 납품해 주세요.",
        },
    ],

    "카엘릭": [
        # 쉬움 ×3
        {
            "id": "kaelik_e1", "name": "기초 훈련 보조",
            "difficulty": "easy", "type": "hunt",
            "target_monster": "slime", "target_count": 3,
            "reward_gold": 45, "reward_exp": 12, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "슬라임 3마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "kaelik_e2", "name": "훈련 장비 정리",
            "difficulty": "easy", "type": "gather",
            "target_item": "iron_bar", "target_count": 2,
            "reward_gold": 40, "reward_exp": 10, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "훈련 장비 수리용 철 주괴 2개를 가져다 주세요.",
        },
        {
            "id": "kaelik_e3", "name": "전술 서류 전달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_tactical_doc",
            "deliver_item_name": "기밀 전술 서류",
            "reward_gold": 50, "reward_exp": 13, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "엘레라신에게 전술 서류를 전달해 주세요.",
        },
        # 보통 ×3
        {
            "id": "kaelik_n1", "name": "고블린 토벌",
            "difficulty": "normal", "type": "hunt",
            "target_monster": "goblin", "target_count": 4,
            "reward_gold": 115, "reward_exp": 25, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "고블린 4마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "kaelik_n2", "name": "방어구 납품",
            "difficulty": "normal", "type": "gather",
            "target_item": "ar_helm_02", "target_count": 1,
            "reward_gold": 120, "reward_exp": 26, "reward_item": None,
            "reward_skill_exp": {"crafting": 30},
            "energy_cost": 20,
            "desc": "철투구 1개를 납품해 주세요.",
        },
        {
            "id": "kaelik_n3", "name": "훈련병 보고서 전달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "제블로어", "deliver_item": "dq_kaelik_trainee",
            "deliver_item_name": "카엘릭의 훈련병 보고서",
            "reward_gold": 110, "reward_exp": 24, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "제블로어에게 훈련병 보고서를 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "kaelik_h1", "name": "오크 토벌",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "orc", "target_count": 3,
            "reward_gold": 230, "reward_exp": 46, "reward_item": "con_potion_h",
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "오크 3마리를 토벌하고 보고해 주세요.",
        },
        {
            "id": "kaelik_h2", "name": "고급 무기 납품",
            "difficulty": "hard", "type": "gather",
            "target_item": "wp_sword_03", "target_count": 1,
            "reward_gold": 245, "reward_exp": 49, "reward_item": None,
            "reward_skill_exp": {"crafting": 80},
            "energy_cost": 35,
            "desc": "강철검 1개를 납품해 주세요.",
        },
        {
            "id": "kaelik_h3", "name": "비밀 임무 보고",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_kaelik_mission",
            "deliver_item_name": "카엘릭의 비밀 임무 보고서",
            "reward_gold": 250, "reward_exp": 50, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "엘레라신에게 비밀 임무 보고서를 전달해 주세요.",
        },
    ],

    "게일의 환영": [
        # 쉬움 ×3
        {
            "id": "gale_e1", "name": "마법 재료 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "mana_herb", "target_count": 2,
            "reward_gold": 40, "reward_exp": 11, "reward_item": "mp_potion_basic",
            "reward_skill_exp": {"alchemy": 10},
            "energy_cost": 10,
            "desc": "마나 허브 2개를 채집해서 가져다 주세요.",
        },
        {
            "id": "gale_e2", "name": "강의 자료 배달",
            "difficulty": "easy", "type": "deliver",
            "target_npc": "아라벨라", "deliver_item": "dq_gale_lecture",
            "deliver_item_name": "게일의 강의 자료",
            "reward_gold": 45, "reward_exp": 12, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "아라벨라에게 강의 자료를 전달해 주세요.",
        },
        {
            "id": "gale_e3", "name": "물 채집",
            "difficulty": "easy", "type": "gather",
            "target_item": "water", "target_count": 2,
            "reward_gold": 35, "reward_exp": 9, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 10,
            "desc": "마법 실험용 물 2개를 가져다 주세요.",
        },
        # 보통 ×3
        {
            "id": "gale_n1", "name": "마법의 돌 조달",
            "difficulty": "normal", "type": "gather",
            "target_item": "magic_stone", "target_count": 1,
            "reward_gold": 105, "reward_exp": 23, "reward_item": "mp_potion_mid",
            "reward_skill_exp": {"alchemy": 25},
            "energy_cost": 20,
            "desc": "마법의 돌 1개를 가져다 주세요.",
        },
        {
            "id": "gale_n2", "name": "슬라임 퇴치",
            "difficulty": "normal", "type": "hunt",
            "target_monster": "slime", "target_count": 4,
            "reward_gold": 100, "reward_exp": 22, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "슬라임 4마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "gale_n3", "name": "연구 보고서 전달",
            "difficulty": "normal", "type": "deliver",
            "target_npc": "엘레라신", "deliver_item": "dq_gale_research",
            "deliver_item_name": "게일의 연구 보고서",
            "reward_gold": 115, "reward_exp": 25, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 20,
            "desc": "엘레라신에게 연구 보고서를 전달해 주세요.",
        },
        # 어려움 ×3
        {
            "id": "gale_h1", "name": "고급 마법 재료 조달",
            "difficulty": "hard", "type": "gather",
            "target_item": "magic_stone", "target_count": 2,
            "reward_gold": 230, "reward_exp": 46, "reward_item": "all_potion",
            "reward_skill_exp": {"alchemy": 60},
            "energy_cost": 35,
            "desc": "마법의 돌 2개를 가져다 주세요.",
        },
        {
            "id": "gale_h2", "name": "위험 정령 처치",
            "difficulty": "hard", "type": "hunt",
            "target_monster": "forest_spirit", "target_count": 2,
            "reward_gold": 240, "reward_exp": 48, "reward_item": None,
            "reward_skill_exp": {},
            "energy_cost": 35,
            "desc": "폭주한 숲 정령 2마리를 처치하고 보고해 주세요.",
        },
        {
            "id": "gale_h3", "name": "비밀 연구 배달",
            "difficulty": "hard", "type": "deliver",
            "target_npc": "아라벨라", "deliver_item": "dq_gale_secret_research",
            "deliver_item_name": "게일의 비밀 연구 자료",
            "reward_gold": 248, "reward_exp": 50, "reward_item": "mp_potion_mid",
            "reward_skill_exp": {"alchemy": 75},
            "energy_cost": 35,
            "desc": "아라벨라에게 비밀 연구 자료를 전달해 주세요.",
        },
    ],
}

# 퀘스트 전용 배달 아이템 ID 목록 (사용/판매/버리기 불가)
JOB_DELIVER_ITEM_IDS = set()
for _jobs in NPC_JOB_POOL.values():
    for _job in _jobs:
        if _job.get("type") == "deliver" and _job.get("deliver_item"):
            JOB_DELIVER_ITEM_IDS.add(_job["deliver_item"])

DIFFICULTY_LABELS = {
    "easy":   "쉬움",
    "normal": "보통",
    "hard":   "어려움",
}
DIFFICULTY_ENERGY = {"easy": 10, "normal": 20, "hard": 35}


def _normalize_rank(rank: str, rank_order: list) -> str:
    """랭크 값이 rank_order에 없으면 '연습'으로 정규화합니다."""
    return rank if rank in rank_order else "연습"


def _can_craft_item(item_id: str, player) -> bool:
    """플레이어가 item_id를 제작/제련할 수 있는지 확인합니다.

    item_id가 CRAFTING_RECIPES 또는 SMELT_RECIPES 의 결과물인 경우
    플레이어의 해당 스킬 랭크가 rank_req 이상인지 체크합니다.
    제작/제련과 무관한 아이템이면 True를 반환합니다.
    """
    from crafting import CRAFTING_RECIPES, RANK_ORDER_CRAFT
    from metallurgy import SMELT_RECIPES, RANK_ORDER_SMELT

    # crafting 레시피 체크 (레시피 키 = 결과물 ID)
    if item_id in CRAFTING_RECIPES:
        rank_req = CRAFTING_RECIPES[item_id].get("rank_req", "연습")
        player_rank = _normalize_rank(
            getattr(player, "skill_ranks", {}).get("crafting", "연습"),
            RANK_ORDER_CRAFT,
        )
        return RANK_ORDER_CRAFT.index(player_rank) >= RANK_ORDER_CRAFT.index(rank_req)

    # metallurgy 레시피 체크 (output dict 의 키가 결과물 ID)
    for recipe in SMELT_RECIPES.values():
        if item_id in recipe.get("output", {}):
            rank_req = recipe.get("rank_req", "연습")
            player_rank = _normalize_rank(
                getattr(player, "skill_ranks", {}).get("metallurgy", "연습"),
                RANK_ORDER_SMELT,
            )
            return RANK_ORDER_SMELT.index(player_rank) >= RANK_ORDER_SMELT.index(rank_req)

    # 제작/제련 불필요 아이템
    return True


def _job_available_for_player(job: dict, player) -> bool:
    """플레이어가 해당 알바를 수행할 수 있는지 확인합니다.

    gather 유형이고 target_item 이 제작/제련 결과물인 경우에만
    스킬 랭크를 검사합니다. 다른 유형은 항상 True를 반환합니다.
    """
    if job.get("type") != "gather":
        return True
    target_item = job.get("target_item", "")
    if not target_item:
        return True
    return _can_craft_item(target_item, player)


def get_random_job(npc_name: str, player=None) -> dict | None:
    """NPC의 알바 풀에서 랜덤으로 1개 반환.

    player가 전달되면 플레이어가 수행 가능한 알바만 후보로 고려합니다.
    gather 유형 알바의 target_item이 제작/제련 결과물인 경우
    플레이어의 스킬 랭크가 rank_req를 충족하지 못하면 해당 알바는 제외됩니다.
    가능한 알바가 하나도 없으면 None을 반환합니다.
    player가 None이면 기존처럼 완전 랜덤으로 동작합니다.
    """
    pool = NPC_JOB_POOL.get(npc_name, [])
    if not pool:
        return None
    if player is None:
        return random.choice(pool)
    candidates = [job for job in pool if _job_available_for_player(job, player)]
    if not candidates:
        return None
    return random.choice(candidates)


def get_job_by_id(job_id: str) -> dict | None:
    """알바 ID로 알바 데이터 반환."""
    for jobs in NPC_JOB_POOL.values():
        for job in jobs:
            if job.get("id") == job_id:
                return job
    return None
