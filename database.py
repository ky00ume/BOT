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
        "energy_cost": 5,
    },
    "고블린동굴": {
        "name": "고블린 동굴",
        "level_req": 5,
        "desc": "고블린 무리가 사는 어두운 동굴.",
        "energy_cost": 10,
    },
    "소금광산": {
        "name": "소금 광산",
        "level_req": 10,
        "desc": "소금 광물과 언데드가 서식하는 광산.",
        "energy_cost": 15,
    },
}

NPC_DATA = {
    "다몬": {
        "name": "다몬",
        "role": "대장장이",
        "location": "비전 타운 광장",
        "desc": "차분하고 책임감 있는 티플링 대장장이. 말수는 적지만 솜씨는 마을 최고.",
        "appearance": "단단하게 다져진 체격의 티플링. 짧고 거친 검은 머리카락, 진한 회색빛 피부, 곧게 뻗은 짙은 적갈색 뿔이 눈에 띈다. 불똥 자국이 남은 가죽 앞치마를 두르고, 맨팔에는 굵은 근육이 드러난다. 손은 항상 그을음으로 검게 물들어 있다.",
        "greetings": [
            "필요한 물건 있으면 말해. 쓸데없는 말은 빼고.",
            "...뭔가 필요한 게 있나? 조용히 골라.",
            "무기에 대해 알고 싶다면 나한테 물어봐. 하지만 잡담은 사양이야.",
            "좋은 철이 들어왔어. 관심 있으면 봐.",
        ],
        "job": {
            "name": "단조 보조",
            "reward_gold": 150,
            "reward_exp": 20,
            "energy_cost": 12,
            "duration": "30분",
            "desc": "다몬의 대장간에서 쇠를 두드리는 일.",
        },
    },
    "오멜룸": {
        "name": "오멜룸",
        "role": "약초상",
        "location": "비전 타운 시장",
        "desc": "이성적이고 차분한 약초상. 본능보다 이성을 따르는 걸 원칙으로 삼는다.",
        "appearance": "중간 키에 날렵한 인상의 인물. 은은한 회색빛을 띤 창백한 피부, 단정하게 묶은 밝은 은발, 그리고 감정을 잘 드러내지 않는 옅은 회녹색 눈동자가 인상적이다. 여러 주머니가 달린 연초록색 약초상 코트를 입고, 허리에는 작은 약재 주머니들을 가득 매달고 있다.",
        "greetings": [
            "...생각보다 흥미로운 시간이군. 약초가 필요한가?",
            "본능이 속삭이지만, 지금 중요한 건 당신의 필요야.",
            "약초는 정확히 측정해야 해. 과다 복용은 위험하니까.",
            "필요한 약재가 있으면 말해. 이성적으로 안내해 주겠어.",
        ],
        "job": {
            "name": "약초 채집 보조",
            "reward_gold": 100,
            "reward_exp": 15,
            "energy_cost": 10,
            "duration": "30분",
            "desc": "오멜룸을 도와 약초를 채집하는 일.",
        },
    },
    "몰": {
        "name": "몰",
        "role": "상인",
        "location": "비전 타운 상점가",
        "desc": "영리하고 능글맞은 젊은 상인. 겉으론 여유롭지만 언제나 한발 앞서 계산한다.",
        "appearance": "날카로운 눈매와 약삭빠른 미소가 특징인 젊은 티플링. 구릿빛 피부에 짧게 다듬은 검은 머리, 작고 매끈한 짧은 뿔. 거래에 유리한 인상을 주는 고급스러운 조끼와 셔츠를 차려입었으며, 항상 어딘가에 숨겨진 주머니가 있어 보인다.",
        "greetings": [
            "뭐 살 거야? 어서 결정해, 시간은 돈이야.",
            "싸게 팔아줄 것 같지? 천만에. 하지만 그 정도는 해줄게~",
            "내가 파는 물건은 전부 '정식' 루트로 들여온 거야. 진짜로.",
            "거래는 빠를수록 좋지. 뭘 원해?",
        ],
        "job": {
            "name": "짐 운반",
            "reward_gold": 120,
            "reward_exp": 12,
            "energy_cost": 15,
            "duration": "30분",
            "desc": "몰의 짐을 대신 날라주는 일.",
        },
    },
    "아라벨라": {
        "name": "아라벨라",
        "role": "마법사",
        "location": "비전 타운 마법 연구소",
        "desc": "조용하고 사려 깊은 티플링 마법사. 힘의 출처에 불안감을 품고 있다.",
        "appearance": "가냘프고 조용한 인상의 젊은 티플링. 짙은 보라빛이 감도는 피부에 가늘고 우아한 뿔, 크고 맑은 연보라색 눈동자가 인상적이다. 마법 문양이 수놓인 짙은 보라색 로브를 입고, 손에는 항상 마법 서적이나 작은 마법봉을 쥐고 있다.",
        "greetings": [
            "...주문을 연습 중이에요. 실수할 수도 있으니 조심해요.",
            "게일의 환영 교수님한테서 배우고 있어요. 배울 게 정말 많아요.",
            "마법에는 힘도 필요하지만, 인내가 더 중요해요.",
            "도움이 필요하신가요? 아직 많이 배우는 중이지만... 최선을 다할게요.",
        ],
        "job": {
            "name": "마법 실험 보조",
            "reward_gold": 200,
            "reward_exp": 30,
            "energy_cost": 12,
            "duration": "30분",
            "desc": "아라벨라의 마법 실험을 돕는 일.",
        },
    },
    "제블로어": {
        "name": "제블로어",
        "role": "경비대장",
        "location": "비전 타운 성문",
        "desc": "과거의 실패를 가슴에 새긴 티플링 경비대장. 무엇보다 마을의 안전을 최우선으로 여긴다.",
        "appearance": "다부지고 위엄 있는 체격의 중년 티플링. 깊은 구릿빛 피부, 이마에서 뒤로 굵게 뻗은 짙은 회색 뿔, 그리고 경계심이 서린 진한 호박색 눈동자. 낡았지만 잘 정돈된 경비대 갑옷을 걸치고, 허리에는 항상 검이 찼다. 얼굴의 작은 흉터가 과거의 전투를 말해준다.",
        "greetings": [
            "마을의 안전은 내 책임이오. 수상한 것이 보이면 즉시 신고하시오.",
            "우리는 한번 실패한 적 있소. 다시는 그런 일이 없도록 할 것이오.",
            "다몬도 같은 말을 했소. 질서가 있어야 마을이 유지된다고.",
            "감시를 게을리하지 마시오. 이 마을을 지키는 건 우리 모두의 임무요.",
        ],
        "job": {
            "name": "순찰 보조",
            "reward_gold": 130,
            "reward_exp": 18,
            "energy_cost": 14,
            "duration": "30분",
            "desc": "제블로어를 도와 마을을 순찰하는 일.",
        },
    },
    "브룩샤": {
        "name": "브룩샤",
        "role": "요리사",
        "location": "비전 타운 식당",
        "desc": "조용하고 섬세한 하프오크 요리사. 폭력과는 거리가 멀고, 오직 음식으로 마음을 전한다.",
        "appearance": "건장하지만 온화한 인상의 하프오크. 짙은 황록빛 피부에 부드럽게 닳은 작은 송곳니, 요리 과정에서 생긴 작은 화상 자국이 양 손등에 있다. 깔끔한 흰 요리사 복장에 자수가 놓인 앞치마를 두르고, 두꺼운 손으로 세밀한 요리를 다루는 솜씨가 놀랍다.",
        "greetings": [
            "...어서 오세요. 뭐 드실 건가요?",
            "요리는 힘이 아니라 섬세함으로 하는 거예요. 저도 배웠어요.",
            "오늘 재료가 신선해요. 맛있는 것 만들어 드릴게요.",
            "배고프면 언제든 와요. 여기선 누구든 환영이에요.",
        ],
        "job": {
            "name": "주방 보조",
            "reward_gold": 110,
            "reward_exp": 14,
            "energy_cost": 11,
            "duration": "30분",
            "desc": "브룩샤의 식당에서 요리를 돕는 일.",
        },
    },
    "실렌": {
        "name": "실렌",
        "role": "낚시꾼",
        "location": "비전 타운 강가",
        "desc": "지상에 적응 중인 드로우 낚시꾼. 말이 없고 사색적이지만, 강물을 바라보는 눈빛은 따뜻하다.",
        "appearance": "조용한 움직임을 가진 드로우(다크엘프). 칠흑같이 짙은 흑자색 피부, 머리끝까지 내려오는 순백색의 긴 머리카락, 그리고 어둠에 익숙한 옅은 연보라색 눈동자. 지상의 강한 햇빛을 피해 챙 넓은 모자를 즐겨 쓰며, 낡고 편안한 낚시꾼 복장을 입고 있다.",
        "greetings": [
            "...강물은 언제 봐도 신기해. 언더다크엔 이런 게 없었으니.",
            "기다리는 법을 배웠어. 언더다크에선 기다림이 생존이었거든.",
            "낚시? 그냥 강물을 바라보는 거야. 물고기는 부산물이고.",
            "지상의 빛이 아직도 낯설어. 하지만... 나쁘지 않아.",
        ],
        "job": {
            "name": "낚시 보조",
            "reward_gold": 90,
            "reward_exp": 10,
            "energy_cost": 7,
            "duration": "30분",
            "desc": "실렌을 도와 낚시하는 일.",
        },
    },
    "알피라": {
        "name": "알피라",
        "role": "음유시인",
        "location": "비전 타운 광장",
        "desc": "밝고 감성적인 티플링 음유시인. 노래를 잃을까 두려워하면서도 매일 새로운 곡을 짓는다.",
        "appearance": "밝고 생기 넘치는 인상의 젊은 티플링. 짙은 청보라빛 피부, 뿔은 부드럽게 뒤로 굽어있으며 끝이 조금 얇다. 따뜻한 노란빛이 도는 눈동자, 화려한 색채의 바드 의상을 걸치고 항상 류트를 들고 다닌다. BG3 원작의 알피라를 그대로 반영한 외형.",
        "greetings": [
            "♪ 오늘도 새로운 노래를 써봤는데... 어때요?",
            "음악이 없는 세상은 너무 쓸쓸해요~ 같이 즐겨요!",
            "이 멜로디, 마음에 드세요? 아직 완성은 못 했지만...",
            "당신의 이야기가 내 노래가 될지도 몰라요. 언젠가 어디선가 들리게 될 거예요~",
        ],
        "job": {
            "name": "공연 보조",
            "reward_gold": 80,
            "reward_exp": 12,
            "energy_cost": 9,
            "duration": "30분",
            "desc": "알피라의 공연을 돕는 일.",
        },
    },
    "엘레라신": {
        "name": "엘레라신",
        "role": "길드 마스터",
        "location": "비전 타운 모험가 길드",
        "desc": "냉정하고 효율적인 길드 마스터. 자헤이라라는 또 다른 이름을 가지고 있지만 쉽게 드러내지 않는다.",
        "appearance": "단호하고 위압감 있는 인상의 하프엘프 여성. BG3의 자헤이라를 기반으로, 붉은빛이 도는 진한 갈색 피부, 짧게 땋아 올린 어두운 녹빛 머리카락, 날카로운 눈매에 냉정한 황금빛 눈동자. 실용적인 가죽 갑옷과 길드 마스터 망토를 걸쳤다.",
        "greetings": [
            "시간 낭비 없이 용건을 말해.",
            "길드의 원칙은 단순해. 실력으로 증명하거나, 아니면 물러나거나.",
            "당신을 평가하고 있어. 판단은 내가 알아서 내려.",
            "나는 감시하는 게 아니라 관리하는 거야. 차이를 알아?",
        ],
        "job": {
            "name": "길드 잡무",
            "reward_gold": 160,
            "reward_exp": 25,
            "energy_cost": 10,
            "duration": "30분",
            "desc": "길드 사무소에서 잡무를 처리하는 일.",
        },
    },
    "게일의 환영": {
        "name": "게일의 환영",
        "role": "마법학교 교수",
        "location": "비전 타운 마법학교",
        "desc": "기억을 기반으로 존재하는 게일의 환영. 완벽하고 정제된 태도로 마법을 가르친다.",
        "appearance": "BG3 원작의 게일을 기반으로 한 반투명한 환영의 모습. 단정한 검은 머리카락, 따뜻한 갈색 눈동자, 인간 마법사의 인상적인 외모. 붉은빛 라이닝이 들어간 진한 청자색 로브를 걸쳤으며, 몸 일부가 마법의 빛으로 흐릿하게 투과되어 보인다. 마이스트라의 별 문양이 어딘가에 새겨져 있다.",
        "greetings": [
            "마법은 정확성과 우아함이 공존해야 해. 메모했나?",
            "나는 기억을 기반으로 존재하지. 하지만 지식은 진짜야.",
            "오늘 수업 준비는 되어 있나? 나는 항상 준비되어 있어.",
            "마이스트라... 아, 아무것도 아니야. 수업을 시작하지.",
        ],
        "job": {
            "name": "수업 보조",
            "reward_gold": 180,
            "reward_exp": 28,
            "energy_cost": 11,
            "duration": "30분",
            "desc": "게일의 환영이 진행하는 마법 수업을 보조하는 일.",
        },
    },
    "카엘릭": {
        "name": "카엘릭",
        "role": "교관",
        "location": "비전 타운 훈련소",
        "desc": "엄격하고 공정한 훈련 교관. 전투를 혐오하지만 그렇기에 누구보다 철저하게 가르친다.",
        "appearance": "근육질의 다부진 체형을 가진 중년 인간 남성. 짧게 자른 회끗한 갈색 머리와 전투에서 얻은 여러 흉터, 그리고 언제나 긴장을 늦추지 않는 회색빛 눈동자가 인상적이다. 낡았지만 잘 유지된 훈련 코트와 팔을 덮는 가죽 팔보호대를 착용하고 있다.",
        "greetings": [
            "훈련은 선택이 아니야. 살고 싶으면 강해져.",
            "나는 전투가 싫어. 그래서 더 철저하게 가르치는 거야.",
            "약한 채로 전장에 나가는 건 죽으러 가는 것과 같아.",
            "자세 틀렸어. 다시.",
        ],
        "job": {
            "name": "훈련 보조",
            "reward_gold": 140,
            "reward_exp": 22,
            "energy_cost": 15,
            "duration": "30분",
            "desc": "카엘릭의 훈련 수업을 보조하는 일.",
        },
    },
    "라파엘": {
        "name": "라파엘",
        "role": "특수 NPC",
        "location": "랜덤 등장",
        "desc": "매혹적이고 교활한 악마 거래상. 항상 흥미로운 제안을 들고 나타난다.",
        "appearance": "BG3 원작의 라파엘(캄비온). 완벽하게 차려입은 인간 모습에, 때때로 붉은 피부와 뿔, 날개의 진짜 모습이 비친다. 짧게 다듬은 붉은빛 갈색 머리, 언제나 여유로운 미소, 귀족적인 붉은색과 금색 의상. 악마적 매력이 넘쳐 경계가 느슨해지는 느낌을 준다.",
        "greetings": [
            "오, 당신이군. 마침 흥미로운 제안이 있는데 말이야...",
            "계약은 단순해. 내가 원하는 것, 당신이 원하는 것. 거래가 되지 않겠어?",
            "걱정하지 마. 나는 항상 약속을 지켜. 물론 조건부로.",
            "이번엔 정말 좋은 조건이야. 거절하기 아깝지 않겠어?",
        ],
    },
    "카르니스": {
        "name": "카르니스",
        "role": "특수 NPC",
        "location": "특정 지역 / 랜덤 등장",
        "desc": "집착적이고 불안정한 드라이더. 마제스티의 최측근으로, 절대적인 신념을 품고 있다.",
        "appearance": "마제스티(루바토)의 최측근인 드라이더. 상반신은 인간 여성의 형태이며, 짧고 날카로운 흰 머리카락, 냉랭한 황금빛 눈동자, 창백한 피부를 지닌다. 하반신은 크고 위압적인 검은색 거미 몸체. 단단한 검은 갑옷 조각들이 거미 몸체를 부분적으로 덮고 있다.",
        "greetings": [
            "...",
            "무슨 볼일이야. 빨리 말해.",
            "마제스티에게 가까이 가지 마.",
            "...넌 관계없어. 그냥 가.",
        ],
    },
    "루바토": {
        "name": "루바토",
        "role": "특수 NPC",
        "location": "랜덤 등장",
        "desc": "플레이어를 비추는 거울 같은 존재. 과거 선택의 잔재를 안고 살아가는 타브.",
        "appearance": "회색 장발에 끝부분만 초록빛으로 그을린 것처럼 물들어 있다. 갈색 피부에 당근색의 굵고 짧은 뿔을 가진 티플링. 갈색 망토 아래에 초록색 셔츠를 입은 바드 복장. 류트를 항상 어깨에 메고 다니며, 눈빛에는 어딘가 먼 곳을 바라보는 듯한 깊이가 있다.",
        "greetings": [
            "...당신을 보면 이상하게 마음이 복잡해.",
            "나는 당신이 아니야. 하지만... 비슷한 선택을 했겠지.",
            "과거는 바꿀 수 없어. 하지만 지금은 달라질 수 있어.",
            "타브... 아니, 미안. 그냥 잊어.",
        ],
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
            equipment   TEXT DEFAULT '{}',
            keywords    TEXT DEFAULT '["마을","날씨","소문"]',
            affinity_data  TEXT DEFAULT '{}',
            daily_limits   TEXT DEFAULT '{}'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS village (
            id           INTEGER PRIMARY KEY DEFAULT 1,
            contribution INTEGER DEFAULT 0,
            level        INTEGER DEFAULT 1,
            data         TEXT DEFAULT '{}'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sheet_music (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER DEFAULT 0,
            title    TEXT NOT NULL,
            melody   TEXT NOT NULL,
            created  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage (
            user_id       INTEGER PRIMARY KEY,
            items         TEXT DEFAULT '{}',
            max_capacity  INTEGER DEFAULT 20
        )
    """)
    conn.commit()
    conn.close()


def save_village_data(contribution: int, level: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO village (id, contribution, level)
        VALUES (1, ?, ?)
    """, (contribution, level))
    conn.commit()
    conn.close()


def load_village_data() -> dict:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT contribution, level FROM village WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {"contribution": 0, "level": 1}
        return {"contribution": row["contribution"], "level": row["level"]}
    except Exception:
        return {"contribution": 0, "level": 1}


def save_player_to_db(player):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 기존 테이블에 컬럼이 없을 경우 마이그레이션
    _migrate_players_table(cursor)
    data = player.get_save_data()

    # affinity 전체를 직렬화 (affinities + daily_limits + gift_history 포함)
    aff_full = {}
    aff_mgr = getattr(player, "_affinity_manager", None)
    if aff_mgr:
        aff_full = aff_mgr.to_dict()

    # story_quest 직렬화
    story_quest_json = json.dumps(data.get("story_quest", {}), ensure_ascii=False)

    cursor.execute("""
        INSERT OR REPLACE INTO players
        (user_id, name, level, exp, hp, max_hp, mp, max_mp, energy, max_energy,
         gold, base_stats, inventory, equipment, keywords, affinity_data, daily_limits,
         story_quest, skill_ranks, skill_exp, titles, current_title)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_id", 0),
        data.get("name", "모험가"),
        data.get("level", 1),
        data.get("exp", 0.0),
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
        json.dumps(data.get("keywords", ["마을", "날씨", "소문"]), ensure_ascii=False),
        json.dumps(aff_full, ensure_ascii=False),
        json.dumps(aff_full.get("daily_limits", {}), ensure_ascii=False),
        story_quest_json,
        json.dumps(data.get("skill_ranks", {"smash": "연습", "defense": "연습", "counter": "연습"}), ensure_ascii=False),
        json.dumps(data.get("skill_exp", {}), ensure_ascii=False),
        json.dumps(data.get("titles", []), ensure_ascii=False),
        data.get("current_title"),
    ))
    conn.commit()
    conn.close()


def _migrate_players_table(cursor):
    """기존 players 테이블에 새 컬럼이 없으면 추가합니다."""
    try:
        cursor.execute("PRAGMA table_info(players)")
        columns = {row[1] for row in cursor.fetchall()}
        if "keywords" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN keywords TEXT DEFAULT '[\"마을\",\"날씨\",\"소문\"]'"
            )
        if "affinity_data" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN affinity_data TEXT DEFAULT '{}'"
            )
        if "daily_limits" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN daily_limits TEXT DEFAULT '{}'"
            )
        if "story_quest" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN story_quest TEXT DEFAULT '{}'"
            )
        if "exp" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN exp REAL DEFAULT 0.0"
            )
        if "skill_ranks" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN skill_ranks TEXT DEFAULT '" + json.dumps({"smash": "연습", "defense": "연습", "counter": "연습"}, ensure_ascii=False) + "'"
            )
        if "skill_exp" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN skill_exp TEXT DEFAULT '{}'"
            )
        if "titles" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN titles TEXT DEFAULT '[]'"
            )
    except Exception:
        pass


def load_player_from_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    _migrate_players_table(cursor)
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    def _safe_json(val, default):
        try:
            if val is None:
                return default
            return json.loads(val)
        except Exception:
            return default

    result = {
        "user_id":      row["user_id"],
        "name":         row["name"],
        "level":        row["level"],
        "hp":           row["hp"],
        "max_hp":       row["max_hp"],
        "mp":           row["mp"],
        "max_mp":       row["max_mp"],
        "energy":       row["energy"],
        "max_energy":   row["max_energy"],
        "gold":         row["gold"],
        "base_stats":   _safe_json(row["base_stats"], {}),
        "inventory":    _safe_json(row["inventory"], {}),
        "equipment":    _safe_json(row["equipment"], {}),
    }

    # 신규 컬럼은 없을 수도 있으므로 안전하게 접근
    try:
        result["keywords"] = _safe_json(row["keywords"], ["마을", "날씨", "소문"])
    except (IndexError, KeyError):
        result["keywords"] = ["마을", "날씨", "소문"]

    try:
        result["affinity_full"] = _safe_json(row["affinity_data"], {})
    except (IndexError, KeyError):
        result["affinity_full"] = {}

    try:
        result["story_quest"] = _safe_json(row["story_quest"], {})
    except (IndexError, KeyError):
        result["story_quest"] = {}

    try:
        result["exp"] = row["exp"] if row["exp"] is not None else 0.0
    except (IndexError, KeyError):
        result["exp"] = 0.0

    try:
        result["skill_ranks"] = _safe_json(row["skill_ranks"], {"smash": "연습", "defense": "연습", "counter": "연습"})
    except (IndexError, KeyError):
        result["skill_ranks"] = {"smash": "연습", "defense": "연습", "counter": "연습"}

    try:
        result["skill_exp"] = _safe_json(row["skill_exp"], {})
    except (IndexError, KeyError):
        result["skill_exp"] = {}

    try:
        result["titles"] = _safe_json(row["titles"], [])
    except (IndexError, KeyError):
        result["titles"] = []

    try:
        result["current_title"] = row["current_title"]
    except (IndexError, KeyError):
        result["current_title"] = None

    return result


def save_sheet_music(user_id: int, title: str, melody: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sheet_music (user_id, title, melody)
        VALUES (?, ?, ?)
    """, (user_id, title, melody))
    conn.commit()
    conn.close()


def load_sheet_music_list(user_id: int) -> list:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, melody, created FROM sheet_music WHERE user_id = ? ORDER BY id",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "title": r["title"], "melody": r["melody"], "created": r["created"]} for r in rows]
    except Exception:
        return []


def load_sheet_music(user_id: int, title_or_id: str) -> dict | None:
    """제목 또는 숫자 ID로 악보를 조회합니다."""
    if not title_or_id:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if title_or_id.isdigit() and int(title_or_id) > 0:
            cursor.execute(
                "SELECT id, title, melody FROM sheet_music WHERE user_id = ? AND id = ?",
                (user_id, int(title_or_id))
            )
        else:
            cursor.execute(
                "SELECT id, title, melody FROM sheet_music WHERE user_id = ? AND title = ?",
                (user_id, title_or_id)
            )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row["id"], "title": row["title"], "melody": row["melody"]}
        return None
    except Exception:
        return None


def delete_sheet_music(user_id: int, title_or_id: str) -> bool:
    if not title_or_id:
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if title_or_id.isdigit() and int(title_or_id) > 0:
            cursor.execute(
                "DELETE FROM sheet_music WHERE user_id = ? AND id = ?",
                (user_id, int(title_or_id))
            )
        else:
            cursor.execute(
                "DELETE FROM sheet_music WHERE user_id = ? AND title = ?",
                (user_id, title_or_id)
            )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception:
        return False
