"""게임 상수 및 정적 데이터."""
from __future__ import annotations

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
    "드레드 할로우": {
        "name": "드레드 할로우",
        "level_req": 1,
        "desc": "초보 모험가들이 자주 찾는 작은 숲.",
        "energy_cost": 5,
    },
    "폐허가 된 마을": {
        "name": "고블린 동굴",
        "level_req": 5,
        "desc": "고블린 무리가 사는 어두운 동굴.",
        "energy_cost": 10,
    },
    "그림포지": {
        "name": "소금 광산",
        "level_req": 10,
        "desc": "소금 광물과 언데드가 서식하는 광산.",
        "energy_cost": 15,
    },
}

NPC_DATA = {
    "데리스 본클록": {
        "name": "데리스 본클록", "role": "상인 · 연금술 재료상", "location": "마이코니드 군락 서쪽 입구",
        "desc": "발더스 게이트에서 온 골드 드워프 상인. 버섯과 연금술 재료를 거래하며 남편 바엘렌을 기다리고 있다.",
        "appearance": "단단한 여행 장비를 갖춘 골드 드워프 상인.",
        "greetings": ["필요한 게 있으면 말해. 쓸 만한 건 팔고 있으니까.", "바엘렌을 봤다면 바로 말해 줘."],
        "job": {"name":"버섯과 물자 정리", "reward_gold":150, "reward_exp":20, "energy_cost":12, "duration":"30분", "desc":"데리스의 거래 물자와 버섯을 정리한다."},
    },
    "블러그": {
        "name":"블러그", "role":"광명회 학자 · 상인", "location":"마이코니드 군락 광명회 야영지",
        "desc":"언더다크의 생태를 연구하는 광명회 소속 홉고블린 학자이자 상인.",
        "appearance":"학자용 로브와 지팡이를 갖춘 홉고블린.",
        "greetings":["언더다크는 관찰할수록 흥미로운 곳이지.", "새로운 표본이라도 발견했나?"],
        "job":{"name":"연구 표본 정리", "reward_gold":120, "reward_exp":18, "energy_cost":10, "duration":"30분", "desc":"블러그의 언더다크 생태 표본을 정리한다."},
    },
    "오멜룸": {
        "name":"오멜룸", "role":"광명회 연구자 · 연금술사", "location":"마이코니드 군락 광명회 야영지",
        "desc":"엘더 브레인의 지배에서 벗어나 광명회와 함께 연구하는 친절한 일리시드.",
        "appearance":"로브를 입고 연구 도구를 지닌 일리시드.",
        "greetings":["흥미로운 변화가 있다면 관찰해 보고 싶습니다.", "두려워할 필요는 없습니다. 연구가 목적입니다."],
        "job":{"name":"연금술 연구 보조", "reward_gold":130, "reward_exp":18, "energy_cost":10, "duration":"30분", "desc":"오멜룸의 실험 재료와 기록을 정리한다."},
    },
    "군주 스포": {
        "name":"군주 스포", "role":"마이코니드 군주", "location":"마이코니드 군락 군주의 터",
        "desc":"마이코니드 군락을 이끄는 군주. 포자를 통해 생각과 기억을 전한다.",
        "appearance":"거대한 균사체와 포자 구름을 두른 마이코니드 군주.",
        "greetings":["포자가 기억을 전한다. 군락은 너를 보고 있다.", "우리의 원은 살아 있다. 그 노래를 들어라."],
        "job":{"name":"군락 순찰", "reward_gold":140, "reward_exp":22, "energy_cost":12, "duration":"30분", "desc":"군락 외곽의 위험을 살피고 포자 길을 확인한다."},
    },
    "글럿": {
        "name":"글럿", "role":"추방된 마이코니드 군주", "location":"마이코니드 군락 서쪽 통로", "train":True,
        "desc":"듀에르가에게 자신의 군락을 잃고 스포의 군락에 몸을 의탁한 마이코니드 군주.",
        "appearance":"크고 육중한 체구의 마이코니드.",
        "greetings":["내 군락은 사라졌다. 나는 기억하고 있다.", "싸울 생각이라면 약한 마음은 버려라."],
        "job":{"name":"전투 훈련", "reward_gold":140, "reward_exp":22, "energy_cost":15, "duration":"30분", "desc":"글럿과 함께 언더다크의 위협에 대비한다."},
    },
    "툴라": {
        "name":"툴라", "role":"딥 노움 생존자", "location":"마이코니드 군락 군주의 터",
        "desc":"듀에르가에게서 탈출해 마이코니드 군락의 보호를 받는 딥 노움.",
        "appearance":"지친 여행 장비를 갖춘 딥 노움.",
        "greetings":["여기까지 온 것만 해도 운이 좋았어.", "호수 건너편엔 아직 잡혀 있는 사람들이 있어."],
        "job":{"name":"보급품 정리", "reward_gold":90, "reward_exp":12, "energy_cost":7, "duration":"30분", "desc":"툴라가 회복하는 동안 필요한 보급품을 정리한다."},
    },
    "버나드": {
        "name":"버나드", "role":"비전의 탑 수호자", "location":"비전의 탑", "inn":True,
        "desc":"비전의 탑을 지키는 고대 자동인형. 탑의 옛 주인 레노어가 남긴 시구에 반응한다.",
        "appearance":"오래된 금속 몸체와 정교한 관절을 지닌 자동인형.",
        "greetings":["...탑은 조용합니다.", "당신의 말을 듣고 있습니다."],
    },
    "바엘렌 본클록": {
        "name":"바엘렌 본클록", "role":"버섯 채집꾼", "location":"비버뱅 군락",
        "desc":"데리스의 남편. 위험한 비버뱅 군락에서 버섯을 채집하다 곤경에 처한다.",
        "appearance":"채집 장비를 든 골드 드워프.", "greetings":["조심해! 여기 버섯들은 건드리면 큰일 나!"],
    },
}
