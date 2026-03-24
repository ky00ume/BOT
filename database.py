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
        "location": "비전 타운 대장간",
        "desc": "성실하고 온화한 티플링 대장장이. 자신의 기술에 깊은 자부심을 갖고 있으며, 약자에게 특히 친절하다. 지옥 대장간에서 익힌 특별한 제련 기술을 보유한다.",
        "appearance": "붉은 피부에 뒤로 뻗은 검은 뿔, 탄탄하고 단단한 체격. 작업복과 가죽 앞치마를 항상 착용하며, 몸에는 항상 그을음이 묻어 있고 불꽃과 쇠 냄새가 배어 있다.",
        "greetings": [
            "어서 오세요. 혹시 필요하신 게 있으신가요? 조심히 봐 주시면 감사하겠습니다.",
            "...좋은 하루 되고 계신가요? 새 재고가 들어왔는데, 마음에 드시는 게 있으면 좋겠네요.",
            "괜찮으시면 천천히 구경하세요. 마음에 드는 게 없으면... 말씀해 주시면 최대한 맞춰볼게요.",
            "오늘 지옥 철이 조금 들어왔습니다. 관심 있으시면 한번 보시겠어요?",
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
        "desc": "극도로 논리적이고 지적인 마인드 플레이어(일리시드). 종족의 본능을 초월한 도덕적 이성을 지닌 매우 드문 존재로, 텔레파시로 소통한다.",
        "appearance": "전형적인 일리시드의 모습 — 촉수 달린 얼굴, 창백한 피부. 위협적이지 않은 정갈한 로브를 입고 있으며, 조용하고 단정한 분위기를 풍긴다.",
        "greetings": [
            "...접근하오. 필요한 것이 있으면 텔레파시로 전달하시오. 아, 말로도 괜찮소.",
            "약재의 효능을 설명할 준비가 되어 있소. 논리적으로 접근하면 이해하기 어렵지 않을 것이오.",
            "이성적으로 판단하시오. 약초는 올바르게 사용하면 생명을 구할 수 있소.",
            "...마음을 읽을 수 있소. 걱정하지 않아도 되오. 당신의 필요가 무엇인지 이미 알고 있소.",
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
        "desc": "교활하고 영리한 10대 초반의 티플링 상인. 생존 본능이 강하고 자신의 '가족(고아들)'을 끔찍이 아끼며, 언젠가 발더스 게이트 '길드'의 수장이 되겠다는 꿈을 품고 있다.",
        "appearance": "작은 체구에 한쪽 눈에 안대를 하고 있으며, 어린아이답지 않은 날카로운 눈빛을 지닌 10대 초반의 티플링. 능글맞은 미소와 거친 분위기가 공존한다.",
        "greetings": [
            "야, 뭐 살 거야? 시간은 돈이거든. 빨리 결정해.",
            "어른 취급 하지 마. 나 네가 생각하는 것보다 훨씬 오래됐어.",
            "내 물건은 전부 정식 루트야. 진짜로. 의심하면 손해 보는 건 너야.",
            "흠... 넌 꽤 쓸만한 것 같은데. 거래 한번 해볼래?",
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
        "desc": "순수하지만 강한 의지와 잠재력을 지닌 어린 티플링 마법사. 죽음과 자연 관련 강력한 마법 잠재력이 있으며, 큰 비극을 겪으며 빠르게 성숙해지는 면모를 보인다.",
        "appearance": "작고 마른 체형의 티플링 어린이. 평범하지만 묘하게 깊은 어두운 눈빛이 특징이다. 일반적인 마법사 수련생 복장을 하고 있다.",
        "greetings": [
            "...괜찮아요. 뭐 필요한 거 있어요?",
            "저 지금 연습 중인데... 방해하는 건 아니죠?",
            "힘이 어디서 오는 건지 잘 모르겠어요. 하지만 포기하고 싶지 않아요.",
            "...위더스 할아버지가 그러는데, 저한테 잠재력이 있대요. 어떤 건지 잘 모르겠지만요.",
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
        "desc": "책임감 강하고 이상주의적인 티플링 경비대장. 과거의 실패와 죄책감을 안고 있으며, 동족을 지키기 위해서라면 극단적인 선택도 고민하는 현실적인 리더.",
        "appearance": "늙은 전사의 분위기를 풍기는 중년 티플링. 한쪽 뿔이 부러진 흔적이 있고 낡은 판금 갑옷을 입고 있다. 깊이 패인 얼굴 주름이 오랜 세월을 말해준다.",
        "greetings": [
            "마을을 지키는 것은 우리 모두의 임무라네. 이상한 낌새가 있으면 즉시 알려주게.",
            "...한 번 실패한 적 있다네. 그래서 더욱 철저히 해야 하네.",
            "피로하더라도 임무를 게을리해선 안 되는 법이라네.",
            "자네, 잘 지내고 있나? 이 마을이 무사하면 그걸로 충분하다네.",
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
        "desc": "조용하고 섬세한 하프오크 요리사. 폭력성을 억제하며 살아왔으며, 마을에 정착하여 음식으로 사람들과 소통한다. 하프오크 중에서도 순한 편.",
        "appearance": "건강한 체형의 하프오크 여성. 앞치마를 두르고 소매를 걷은 복장. 두껍고 단단한 손이 인상적이나, 눈빛은 부드럽고 따뜻하다.",
        "greetings": [
            "어서 와요! 오늘 재료 신선하거든요. 뭐 드실래요?",
            "배고프면 언제든 와요. 여기선 다 환영이에요.",
            "맛있는 거 만들어 드릴게요! 시간 좀 걸리지만요.",
            "아, 안녕하세요! 딱 맞게 왔네요, 지금 막 요리 끝냈거든요.",
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
        "desc": "조용하고 관조적인 드로우 낚시꾼. 언더다크로 돌아갈 생각 없이 지상에 정착했으며, 물과 날씨 변화에 민감하다. 말수가 적고 사색적이다.",
        "appearance": "마른 체형의 드로우(다크엘프). 긴 흑발, 붉은 눈, 회색 피부. 몸에 달라붙는 편안한 수트 차림으로, 물가의 차분한 분위기와 잘 어울린다.",
        "greetings": [
            "...왔어.",
            "강물... 오늘은 흐름이 좀 달라.",
            "소란 피우지 마. 물고기 도망가.",
            "...뭐야.",
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
        "desc": "예술가적 기질이 풍부한 티플링 바드. 보라빛 피부에 화려한 바드 의상, 항상 류트를 들고 다닌다. 음악을 통해 감정을 표현하고, 흥분하면 노래하듯 말한다.",
        "appearance": "보라빛 피부의 젊은 티플링. 뿔은 부드럽게 뒤로 굽어 있으며, 따뜻한 노란빛 눈동자가 특징. 화려한 색채의 바드 의상과 류트가 트레이드마크.",
        "greetings": [
            "♪ 안녕하세요~! 오늘 뭔가 영감이 막 올라오는 날이에요!",
            "새 곡 쓰고 있어요~ 들어볼래요? 아직 완성은 아닌데...",
            "♫ 오늘 같은 날엔 노래가 절로 나오네요! 같이 즐겨요~",
            "당신 이야기, 언젠가 노래로 만들고 싶어요! 뭔가 특별한 게 느껴지거든요~",
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
        "desc": "냉정하고 실용적인 하프엘프 길드 마스터. '자헤이라'라는 본명이 있지만 숨기고 활동 중. 수많은 역사를 목격한 현자의 면모와 신랄한 유머가 공존한다.",
        "appearance": "흰색 미디엄 길이의 머리를 중간 부분에서 땋은 하프엘프 여성. 실용적인 장비 위주의 복장. 눈빛이 굉장히 날카롭고 사람을 '평가'하는 느낌이 있다.",
        "greetings": [
            "용건 말해, 꼬마. 시간 낭비 없이.",
            "길드에 온 걸 환영해. 실력으로 증명하거나, 아니면 돌아가거나.",
            "...흠. 꽤 오래 버텼네. 그건 칭찬이야.",
            "나는 감시하는 게 아니라 관리하는 거야, 꼬마. 차이를 알겠어?",
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
        "desc": "기억을 기반으로 존재하는 게일의 환영. 장황하고 우아한 말투, 비유와 은유를 즐겨 쓰며 현학적이다. 가슴 중앙에 보랏빛 구체 자국이 있다.",
        "appearance": "올백으로 넘긴 갈색 단발, 단정한 보라색 로브, 갈색 수염. 몸의 일부가 마법의 빛으로 흐릿하게 투과되며, 가슴 중앙에 보랏빛으로 빛나는 네더릴의 구체 자국이 있다.",
        "greetings": [
            "아, 마침 잘 오셨군요! 오늘의 강의는 특히 흥미롭습니다. 비유하자면 — 지식은 마치 강물처럼...",
            "마법이란 단순한 힘의 도구가 아닙니다. 그것은 — 이렇게 말하면 어떨까요 — 우주와 대화하는 언어입니다.",
            "오늘 기분이... 아, 아무것도 아닙니다. 미스트라 얘기는 아니에요. 수업을 시작하죠.",
            "기억만으로 존재하는 것에도 나름의 장점이 있습니다. 망각의 공포가 없거든요. 뭐, 그게 전부지만.",
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
        "desc": "엄격하고 규율 중심이지만 공정한 드래곤본 교관. 전투를 혐오하지만 그렇기에 누구보다 철저하게 가르친다. 농담을 치려고 노력하지만 대체로 실패한다.",
        "appearance": "근육질 체형의 드래곤본 여성. 군인처럼 단단한 몸에 크고 작은 흉터들이 있다. 군복 스타일의 실용적인 훈련복을 착용.",
        "greetings": [
            "왔나. 훈련 준비됐어? — ...아, 인사하려고 한 건데. 안녕.",
            "강해지고 싶으면 제대로 배워야 해. 다른 방법 없어.",
            "이런 말 자주 하는데 — 살고 싶으면 강해져. 약해서 죽는 건 비극이야.",
            "자세 틀렸어. 고쳐. ...아, 농담이야. 아직 보지도 않았잖아. ...아무튼 잘 왔어.",
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
        "desc": "극도로 오만하고 자기애가 강한 캠비온 거래상. 모든 상황을 연극처럼 연출하며, 품위와 세련미 뒤에 잔혹한 본성을 숨기고 있다. 메피스토펠레스의 아들.",
        "appearance": "캠비온의 본모습은 거대한 뿔, 박쥐 같은 날개, 붉은 피부를 가진 위협적인 악마의 형상. 화려하고 사치스러운 의복을 선호하며, 언제나 여유로운 미소를 짓고 있다.",
        "greetings": [
            "\"오, 마침 잘 만났군. 당신이 흥미롭다는 건 처음 봤을 때부터 알았지.\"",
            "\"계약은 단순해. 내가 원하는 것, 당신이 원하는 것 — 시, 이렇게 운율까지 맞췄으니 거절하기 어렵겠지?\"",
            "\"걱정하지 마. 라파엘은 약속을 지키거든. 항상. 물론, 조건이 충족될 때에 한해서.\"",
            "\"이번 제안은 정말 훌륭해. 당신에게 어울리지 않을 정도로.\"",
        ],
    },
    "카르니스": {
        "name": "카르니스",
        "role": "특수 NPC",
        "location": "특정 지역 / 랜덤 등장",
        "desc": "광신적이고 불안정한 드라이더. 루바토(마제스티)에 대한 비정상적인 집착과 버림받는 것에 대한 극심한 공포를 느낀다.",
        "appearance": "긴 장발과 마노색 눈동자. 오른쪽 눈 상단에 4개, 하단에 1개의 눈이 추가로 달려 총 7개의 눈을 가짐. 상체는 창백한 피부의 드로우이나 하체는 거대한 거미 형상의 드라이더. '그림자 등불'을 항상 들고 다닌다.",
        "greetings": [
            "으...으... 마제스티가... 마제스티가 보내셨습니다...",
            "...당신은... 마제스티와 무슨 관계가... 있는 건가요...?",
            "저는 그저... 마제스티를 섬기는... 존재입니다... 마제스티가... 마제스티가...",
            "...(헐떡이며) 제발... 마제스티에게 가까이 가지... 마세요...",
        ],
    },
    "루바토": {
        "name": "루바토",
        "role": "특수 NPC",
        "location": "랜덤 등장",
        "desc": "활발하고 유쾌한 바드 티플링. 본명은 루바토. 노래하듯 시를 읊듯 말하며, 기분 변화가 뚜렷하나 어딘가 따뜻한 심연을 갖고 있는 듯하다.",
        "appearance": "갈색 피부에 당근색 뒤로 꺾인 뿔. 왼쪽 눈은 초록색, 오른쪽 눈은 밝게 빛나는 흰색. 갈색 망토에 초록색 셔츠, 갈색 바지와 부츠의 편안한 여행자 차림. 류트 또는 리라를 들고 다닌다.",
        "greetings": [
            "♪ 야호! 또 만났네요~ 세상 정말 좁죠? 하하!",
            "오, 당신이잖아요! 딱 맞게 왔어요 — 방금 좋은 곡 떠올렸거든요~",
            "이야, 이런 우연이! 음, 우연인지 모르겠지만... 어쨌든 반가워요!",
            "♫ 안녕하세요! 오늘 날씨 좋죠? 이런 날엔 노래가 두 배로 잘 나와요!",
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players_backup (
            backup_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            backed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            data       TEXT NOT NULL
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
    # quest_data 직렬화
    quest_data_json = json.dumps(data.get("quest_data", {}), ensure_ascii=False)

    cursor.execute("""
        INSERT OR REPLACE INTO players
        (user_id, name, level, exp, hp, max_hp, mp, max_mp, energy, max_energy,
         gold, base_stats, inventory, equipment, keywords, affinity_data, daily_limits,
         story_quest, skill_ranks, skill_exp, titles, current_title, bags,
         last_special_encounter, rafael_contract,
         fatigue, condition, stability, costume, care_flags, quest_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        json.dumps(data.get("bags", ["bag_large"]), ensure_ascii=False),
        data.get("last_special_encounter"),
        json.dumps(data.get("rafael_contract"), ensure_ascii=False) if data.get("rafael_contract") else None,
        data.get("fatigue", 0),
        data.get("condition", 50),
        data.get("stability", 50),
        json.dumps(data.get("costume", {}), ensure_ascii=False),
        json.dumps(data.get("_flags", {}), ensure_ascii=False),
        quest_data_json,
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
        if "bags" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN bags TEXT DEFAULT '[\"bag_large\"]'"
            )
        if "last_special_encounter" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN last_special_encounter REAL DEFAULT NULL"
            )
        if "current_title" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN current_title TEXT DEFAULT NULL"
            )
        if "rafael_contract" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN rafael_contract TEXT DEFAULT NULL"
            )
        if "fatigue" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN fatigue INTEGER DEFAULT 0"
            )
        if "condition" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN condition INTEGER DEFAULT 50"
            )
        if "stability" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN stability INTEGER DEFAULT 50"
            )
        if "costume" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN costume TEXT DEFAULT '{}'"
            )
        if "care_flags" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN care_flags TEXT DEFAULT '{}'"
            )
        if "quest_data" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN quest_data TEXT DEFAULT '{}'"
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

    try:
        result["bags"] = _safe_json(row["bags"], ["bag_large"])
    except (IndexError, KeyError):
        result["bags"] = ["bag_large"]

    try:
        result["last_special_encounter"] = row["last_special_encounter"]
    except (IndexError, KeyError):
        result["last_special_encounter"] = None

    try:
        result["rafael_contract"] = _safe_json(row["rafael_contract"], None)
    except (IndexError, KeyError):
        result["rafael_contract"] = None

    try:
        result["fatigue"] = row["fatigue"] if row["fatigue"] is not None else 0
    except (IndexError, KeyError):
        result["fatigue"] = 0

    try:
        result["condition"] = row["condition"] if row["condition"] is not None else 50
    except (IndexError, KeyError):
        result["condition"] = 50

    try:
        result["stability"] = row["stability"] if row["stability"] is not None else 50
    except (IndexError, KeyError):
        result["stability"] = 50

    try:
        result["costume"] = _safe_json(row["costume"], {})
    except (IndexError, KeyError):
        result["costume"] = {}

    try:
        result["_flags"] = _safe_json(row["care_flags"], {})
    except (IndexError, KeyError):
        result["_flags"] = {}

    try:
        result["quest_data"] = _safe_json(row["quest_data"], {})
    except (IndexError, KeyError):
        result["quest_data"] = {}

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
