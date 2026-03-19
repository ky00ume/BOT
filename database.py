import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_town.db")

STATS_INFO = {
    "str":  {"name": "힘",   "desc": "물리 공격력에 영향"},
    "int":  {"name": "지력", "desc": "마법 공격력에 영향"},
    "dex":  {"name": "민첩", "desc": "명중률·회피율에 영향"},
    "will": {"name": "의지", "desc": "MP·정신력에 영향"},
    "luck": {"name": "운",   "desc": "크리티컬·드랍률에 영향"},
}

BAGS = {
    "bag_small": {
        "name": "작은 가방",
        "type": "bag",
        "grade": "Normal",
        "slots": 6,
        "price": 1000,
        "desc": "6칸 추가 인벤토리.",
    },
    "bag_medium": {
        "name": "중형 가방",
        "type": "bag",
        "grade": "Rare",
        "slots": 12,
        "price": 3000,
        "desc": "12칸 추가 인벤토리.",
    },
    "bag_large": {
        "name": "대형 가방",
        "type": "bag",
        "grade": "Epic",
        "slots": 20,
        "price": 8000,
        "desc": "20칸 추가 인벤토리.",
    },
}

EQUIPMENT = {
    "main":  None,
    "sub":   None,
    "body":  None,
    "head":  None,
    "hands": None,
    "feet":  None,
}

HUNTING_GROUNDS = {
    "방울숲": {
        "name": "방울숲",
        "level_req": 1,
        "desc": "초보 모험가들이 자주 찾는 작은 숲.",
        "energy_cost": 10,
    },
    "고블린동굴": {
        "name": "고블린 동굴",
        "level_req": 5,
        "desc": "고블린 무리가 사는 어두운 동굴.",
        "energy_cost": 20,
    },
    "소금광산": {
        "name": "소금 광산",
        "level_req": 10,
        "desc": "소금 광물과 언데드가 서식하는 광산.",
        "energy_cost": 30,
    },
}

NPC_DATA = {
    "크람": {
        "name": "크람",
        "role": "대장장이",
        "location": "비전 타운 광장",
        "desc": "무뚝뚝하지만 실력 있는 대장장이.",
        "greetings": [
            "흥, 뭘 원하는 거지.",
            "물건이 필요하면 골라봐.",
            "나는 쓸데없는 잡담은 싫어.",
            "좋은 무기 하나 골라가.",
        ],
        "job": {
            "name": "단조 보조",
            "reward_gold": 150,
            "reward_exp": 20,
            "energy_cost": 25,
            "duration": "30분",
            "desc": "크람의 대장간에서 쇠를 두드리는 일.",
        },
    },
    "레이나": {
        "name": "레이나",
        "role": "약초상",
        "location": "비전 타운 시장",
        "desc": "밝고 활기찬 약초 상인 아가씨.",
        "greetings": [
            "어서오세요~ 신선한 약초 있어요!",
            "오늘도 좋은 날이네요~",
            "뭔가 필요하신 게 있나요?",
            "약초는 잘 드시고 계신가요?",
        ],
        "job": {
            "name": "약초 채집 보조",
            "reward_gold": 100,
            "reward_exp": 15,
            "energy_cost": 20,
            "duration": "30분",
            "desc": "레이나를 도와 약초를 채집하는 일.",
        },
    },
    "곤트": {
        "name": "곤트",
        "role": "상인",
        "location": "비전 타운 상점가",
        "desc": "뚱뚱하고 욕심 많은 행상인.",
        "greetings": [
            "어이, 뭐 살 거야?",
            "싸게 팔아줄게~ 잘 골라봐.",
            "돈이 없으면 나가.",
            "오늘은 좀 특별한 물건도 있어.",
        ],
        "job": {
            "name": "짐 운반",
            "reward_gold": 120,
            "reward_exp": 12,
            "energy_cost": 30,
            "duration": "30분",
            "desc": "곤트의 짐을 대신 날라주는 일.",
        },
    },
    "엘리": {
        "name": "엘리",
        "role": "마법사",
        "location": "비전 타운 마법 연구소",
        "desc": "호기심 많은 젊은 마법사.",
        "greetings": [
            "마법에 관심 있으신가요?",
            "오늘도 연구 중이에요~",
            "마력의 흐름이 느껴지시나요?",
            "주문서 필요하세요?",
        ],
        "job": {
            "name": "마법 실험 보조",
            "reward_gold": 200,
            "reward_exp": 30,
            "energy_cost": 25,
            "duration": "30분",
            "desc": "엘리의 마법 실험을 돕는 일.",
        },
    },
    "그레고": {
        "name": "그레고",
        "role": "경비병",
        "location": "비전 타운 성문",
        "desc": "듬직한 마을 경비병 대장.",
        "greetings": [
            "마을을 지키는 것이 내 임무요.",
            "수상한 자는 없는지 살펴봐야지.",
            "오늘은 무사한 하루군.",
            "마을 안전은 내가 책임지오.",
        ],
        "job": {
            "name": "순찰 보조",
            "reward_gold": 130,
            "reward_exp": 18,
            "energy_cost": 28,
            "duration": "30분",
            "desc": "그레고를 도와 마을을 순찰하는 일.",
        },
    },
    "마리": {
        "name": "마리",
        "role": "요리사",
        "location": "비전 타운 식당",
        "desc": "마을 최고의 요리사 아주머니.",
        "greetings": [
            "어서와요~ 뭔가 드실 건가요?",
            "오늘 요리 정말 맛있게 됐어요~",
            "배고프면 언제든 와요!",
            "비법 레시피는 비밀이에요~",
        ],
        "job": {
            "name": "주방 보조",
            "reward_gold": 110,
            "reward_exp": 14,
            "energy_cost": 22,
            "duration": "30분",
            "desc": "마리의 식당에서 요리를 돕는 일.",
        },
    },
    "피터": {
        "name": "피터",
        "role": "낚시꾼",
        "location": "비전 타운 강가",
        "desc": "하루 종일 강에서 낚시를 즐기는 노인.",
        "greetings": [
            "낚시는 참을성이야~",
            "오늘 대어가 잡힐 것 같은 느낌!",
            "강물 소리가 듣기 좋구먼.",
            "자네도 낚시 한번 해봐~",
        ],
        "job": {
            "name": "낚시 보조",
            "reward_gold": 90,
            "reward_exp": 10,
            "energy_cost": 15,
            "duration": "30분",
            "desc": "피터를 도와 낚시하는 일.",
        },
    },
    "루카스": {
        "name": "루카스",
        "role": "음악가",
        "location": "비전 타운 광장",
        "desc": "광장에서 연주를 즐기는 떠돌이 악사.",
        "greetings": [
            "♪ 음악은 영혼의 언어~",
            "연주 들어볼래요?",
            "오늘도 좋은 음악 들려줄게요~",
            "리듬을 타봐요~!",
        ],
        "job": {
            "name": "공연 보조",
            "reward_gold": 80,
            "reward_exp": 12,
            "energy_cost": 18,
            "duration": "30분",
            "desc": "루카스의 공연을 돕는 일.",
        },
    },
    "나디아": {
        "name": "나디아",
        "role": "길드 마스터",
        "location": "비전 타운 모험가 길드",
        "desc": "비전 타운 모험가 길드를 이끄는 여성.",
        "greetings": [
            "모험가여, 어서 오세요.",
            "새 의뢰가 들어왔습니다.",
            "길드원들의 안전이 최우선입니다.",
            "오늘도 좋은 모험 되세요.",
        ],
        "job": {
            "name": "길드 잡무",
            "reward_gold": 160,
            "reward_exp": 25,
            "energy_cost": 20,
            "duration": "30분",
            "desc": "길드 사무소에서 잡무를 처리하는 일.",
        },
    },
}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            level       INTEGER DEFAULT 1,
            hp          INTEGER DEFAULT 100,
            max_hp      INTEGER DEFAULT 100,
            mp          INTEGER DEFAULT 50,
            max_mp      INTEGER DEFAULT 50,
            energy      INTEGER DEFAULT 100,
            max_energy  INTEGER DEFAULT 100,
            gold        INTEGER DEFAULT 500,
            base_stats  TEXT DEFAULT '{}',
            inventory   TEXT DEFAULT '{}',
            equipment   TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()


def save_player_to_db(player):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = player.get_save_data()
    cursor.execute("""
        INSERT OR REPLACE INTO players
        (user_id, name, level, hp, max_hp, mp, max_mp, energy, max_energy,
         gold, base_stats, inventory, equipment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_id", 0),
        data.get("name", "모험가"),
        data.get("level", 1),
        data.get("hp", 100),
        data.get("max_hp", 100),
        data.get("mp", 50),
        data.get("max_mp", 50),
        data.get("energy", 100),
        data.get("max_energy", 100),
        data.get("gold", 500),
        json.dumps(data.get("base_stats", {}), ensure_ascii=False),
        json.dumps(data.get("inventory", {}), ensure_ascii=False),
        json.dumps(data.get("equipment", {}), ensure_ascii=False),
    ))
    conn.commit()
    conn.close()


def load_player_from_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id":    row["user_id"],
        "name":       row["name"],
        "level":      row["level"],
        "hp":         row["hp"],
        "max_hp":     row["max_hp"],
        "mp":         row["mp"],
        "max_mp":     row["max_mp"],
        "energy":     row["energy"],
        "max_energy": row["max_energy"],
        "gold":       row["gold"],
        "base_stats": json.loads(row["base_stats"]),
        "inventory":  json.loads(row["inventory"]),
        "equipment":  json.loads(row["equipment"]),
    }
