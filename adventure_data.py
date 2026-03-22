# adventure_data.py — 텍스트 어드벤처 탐험 시나리오 데이터
# 사냥터별 3개 이상 시나리오, 숨겨진 트리거, 범용 랜덤 이벤트

ADVENTURE_SCENARIOS = {
    "방울숲": [
        {
            "id": "bell_forest_mystery",
            "title": "수상한 방울 소리",
            "steps": [
                {
                    "step": 0,
                    "desc": "숲 깊은 곳에서 맑은 방울 소리가 들려온다. 바람 소리와 섞여 신비롭게 울린다.",
                    "choices": [
                        {
                            "label": "소리를 따라간다",
                            "stat_check": {"stat": "dex", "difficulty": 12},
                            "success": {"next_step": 1, "text": "조심스럽게 나뭇가지를 피하며 소리를 따라가니... 작은 빈터가 나타났다."},
                            "fail":    {"next_step": 2, "text": "나뭇가지를 밟아 넘어졌다! 무릎이 긁혔다.", "damage": 5},
                        },
                        {
                            "label": "무시하고 돌아간다",
                            "auto": True,
                            "result": {"text": "현명한 선택이었다. 안전하게 돌아왔다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "빈터 중앙에 이상하게 빛나는 방울이 나무에 걸려 있다. 손에 닿을 것 같다.",
                    "choices": [
                        {
                            "label": "방울을 가져간다",
                            "stat_check": {"stat": "luck", "difficulty": 10},
                            "success": {"next_step": 3, "text": "방울을 조심스럽게 집어들자 따뜻한 빛이 감쌌다.", "reward": {"gold": 30, "item": "mp_crystal"}},
                            "fail":    {"next_step": 3, "text": "방울을 건드리자 갑자기 몬스터가 튀어나왔다!", "battle": True},
                        },
                        {
                            "label": "절을 하고 조용히 물러선다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "정중히 물러섰다. 숲의 기운이 따뜻하게 느껴진다.", "reward": {"exp": 20}},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "넘어진 탓에 발소리를 내버렸다. 근처에서 무언가 움직이는 소리가 난다.",
                    "choices": [
                        {
                            "label": "몸을 숨긴다",
                            "stat_check": {"stat": "dex", "difficulty": 11},
                            "success": {"next_step": 3, "text": "재빠르게 덤불 뒤에 몸을 숨겼다. 위험이 지나갔다."},
                            "fail":    {"next_step": 3, "text": "몸을 숨기지 못하고 몬스터와 마주쳤다!", "battle": True},
                        },
                        {
                            "label": "정면으로 맞선다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "용감하게 맞섰다! 몬스터와 전투가 시작된다!", "battle": True},
                        },
                    ],
                },
                {
                    "step": 3,
                    "desc": "탐험이 끝났다. 방울숲의 바람이 부드럽게 머리카락을 스친다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
        {
            "id": "lost_traveler",
            "title": "길을 잃은 여행자",
            "steps": [
                {
                    "step": 0,
                    "desc": "숲 가장자리에 짐을 잔뜩 진 채 당황한 얼굴로 주위를 두리번거리는 사람이 보인다.",
                    "choices": [
                        {
                            "label": "다가가 말을 건다",
                            "auto": True,
                            "result": {"next_step": 1, "text": "여행자가 반갑게 손을 흔들며 도움을 요청한다."},
                        },
                        {
                            "label": "무시하고 지나친다",
                            "auto": True,
                            "result": {"text": "그냥 지나쳤다. 뭔가 찜찜하다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "\"저, 마을로 가는 길을 잃었어요. 이 쪽 숲을 잘 아시나요?\" 여행자가 묻는다.",
                    "choices": [
                        {
                            "label": "마을 방향을 알려준다",
                            "stat_check": {"stat": "int", "difficulty": 10},
                            "success": {"next_step": 2, "text": "정확하게 방향을 안내해줬다. 여행자가 감사히 여긴다.", "reward": {"gold": 40, "exp": 25}},
                            "fail":    {"next_step": 2, "text": "잘못된 방향을 알려줬다... 여행자가 더 헤매게 됐다."},
                        },
                        {
                            "label": "직접 데려다 준다",
                            "stat_check": {"stat": "str", "difficulty": 8},
                            "success": {"next_step": 2, "text": "함께 걸어 마을에 무사히 도착했다!", "reward": {"gold": 60, "exp": 35, "item": "con_bread"}},
                            "fail":    {"next_step": 2, "text": "길을 걷다 발을 헛디뎌 에너지를 많이 소모했다.", "energy_cost": 3},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "여행자와 이런저런 이야기를 나눴다. 먼 곳에서 온 상인인 것 같다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
        {
            "id": "ancient_tree",
            "title": "고대 나무의 속삭임",
            "steps": [
                {
                    "step": 0,
                    "desc": "방울숲 한복판에 수백 년은 된 것 같은 거대한 나무가 서 있다. 나무 기둥에 문양이 새겨져 있다.",
                    "choices": [
                        {
                            "label": "문양을 자세히 살핀다",
                            "stat_check": {"stat": "int", "difficulty": 13},
                            "success": {"next_step": 1, "text": "고대 문자다! 해석하자 \"이 숲을 지키는 자에게 가호를\"이라고 써 있다."},
                            "fail":    {"next_step": 2, "text": "뭔지 알 수 없는 문자다. 이상하게 기분이 나빠진다.", "damage": 3},
                        },
                        {
                            "label": "나무에 손을 얹는다",
                            "stat_check": {"stat": "will", "difficulty": 11},
                            "success": {"next_step": 1, "text": "나무의 따스한 기운이 몸에 퍼진다. 활력이 돌아온다!", "reward": {"hp": 20, "mp": 10}},
                            "fail":    {"next_step": 2, "text": "갑자기 두통이 몰려온다. 뭔가 잘못된 것 같다.", "damage": 8},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "나무 뒤에서 작은 요정처럼 생긴 생물이 나타나 뭔가를 내밀었다.",
                    "choices": [
                        {
                            "label": "받아든다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "빛나는 MP 크리스탈을 선물받았다!", "reward": {"item": "mp_crystal", "exp": 30}},
                        },
                        {
                            "label": "거절한다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "정중히 거절했다. 작은 생물이 슬프게 사라졌다."},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "기분 나쁜 기운이 사라졌다. 조용히 그 자리를 떠나는 것이 나을 것 같다.",
                    "choices": [],
                    "end": True,
                },
                {
                    "step": 3,
                    "desc": "고대 나무가 바람에 흔들리며 마치 인사를 하는 것 같다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
    ],

    "고블린동굴": [
        {
            "id": "goblin_secret_room",
            "title": "고블린의 비밀 창고",
            "steps": [
                {
                    "step": 0,
                    "desc": "동굴 깊은 곳에서 고블린들의 수다 소리가 들린다. 무언가를 열심히 지키는 것 같다.",
                    "choices": [
                        {
                            "label": "몰래 엿본다",
                            "stat_check": {"stat": "dex", "difficulty": 13},
                            "success": {"next_step": 1, "text": "조심스럽게 바위 뒤에서 엿보니 금화가 쌓인 창고가 보인다!"},
                            "fail":    {"next_step": 2, "text": "발소리를 내버렸다! 고블린들이 알아채고 달려든다!", "battle": True},
                        },
                        {
                            "label": "정면으로 들이닥친다",
                            "auto": True,
                            "result": {"next_step": 2, "text": "고블린들이 놀라서 달려든다!", "battle": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "고블린 창고에는 훔쳐온 물건들이 가득하다. 재빠르게 챙길 수 있을 것 같다.",
                    "choices": [
                        {
                            "label": "최대한 챙긴다",
                            "stat_check": {"stat": "dex", "difficulty": 14},
                            "success": {"next_step": 3, "text": "재빠르게 짐을 챙겨 도망쳤다!", "reward": {"gold": 80, "item": "iron_ore"}},
                            "fail":    {"next_step": 2, "text": "짐을 챙기다 소리를 냈다! 고블린이 쫓아온다!", "battle": True},
                        },
                        {
                            "label": "금화만 조금 가져간다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "조심스럽게 금화 몇 개만 가져왔다.", "reward": {"gold": 30}},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "고블린과 전투 후 창고 근처에서 무언가를 발견했다.",
                    "choices": [
                        {
                            "label": "주위를 살핀다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "고블린이 숨겨둔 작은 보물 상자를 발견했다!", "reward": {"gold": 40, "exp": 20}},
                        },
                    ],
                },
                {
                    "step": 3,
                    "desc": "동굴을 빠져나왔다. 고블린들의 분노한 외침이 뒤에서 들린다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
        {
            "id": "trapped_prisoner",
            "title": "갇힌 포로",
            "steps": [
                {
                    "step": 0,
                    "desc": "동굴 깊은 곳에서 신음 소리가 들린다. 사람이 갇혀 있는 것 같다.",
                    "choices": [
                        {
                            "label": "확인하러 간다",
                            "auto": True,
                            "result": {"next_step": 1, "text": "어둠 속에서 밧줄에 묶인 사람을 발견했다!"},
                        },
                        {
                            "label": "위험할 수 있으니 돌아간다",
                            "auto": True,
                            "result": {"text": "안전을 위해 돌아갔다. 마음이 조금 무겁다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "\"제발 도와주세요! 고블린에게 잡혔어요!\" 여행자가 울부짖는다.",
                    "choices": [
                        {
                            "label": "밧줄을 풀어준다",
                            "stat_check": {"stat": "str", "difficulty": 10},
                            "success": {"next_step": 2, "text": "밧줄을 끊고 무사히 구출했다!", "reward": {"gold": 70, "exp": 50}},
                            "fail":    {"next_step": 3, "text": "밧줄이 워낙 튼튼해 풀지 못했다. 고블린이 돌아온다!", "battle": True},
                        },
                        {
                            "label": "주위 고블린을 먼저 처치한다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "고블린을 처치하고 여행자를 구출했다!", "battle": True},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "여행자를 구출했다. 깊은 감사를 표하며 가방에서 뭔가를 꺼낸다.",
                    "choices": [],
                    "end": True,
                    "reward": {"gold": 50, "item": "con_bread"},
                },
                {
                    "step": 3,
                    "desc": "고투 끝에 여행자를 구출했다! 힘들었지만 보람 있다.",
                    "choices": [],
                    "end": True,
                    "reward": {"gold": 30, "exp": 30},
                },
            ],
        },
        {
            "id": "goblin_shaman",
            "title": "고블린 주술사의 제단",
            "steps": [
                {
                    "step": 0,
                    "desc": "동굴 깊숙한 곳에서 으스스한 붉은 빛이 새어나온다. 이상한 주문 소리가 들린다.",
                    "choices": [
                        {
                            "label": "조심스럽게 다가간다",
                            "stat_check": {"stat": "will", "difficulty": 12},
                            "success": {"next_step": 1, "text": "정신을 강하게 부여잡고 접근했다. 제단 앞에 주술사가 보인다."},
                            "fail":    {"next_step": 2, "text": "주술에 정신이 흐려진다! 잠시 방향 감각을 잃었다.", "damage": 10},
                        },
                        {
                            "label": "돌아간다",
                            "auto": True,
                            "result": {"text": "불길한 느낌에 돌아갔다. 현명한 선택이었다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "제단에는 빛나는 돌이 놓여 있다. 주술사가 긴장하며 돌을 지키고 있다.",
                    "choices": [
                        {
                            "label": "돌을 빼앗는다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "주술사와 격렬히 싸웠다!", "battle": True},
                        },
                        {
                            "label": "협상을 시도한다",
                            "stat_check": {"stat": "int", "difficulty": 14},
                            "success": {"next_step": 3, "text": "주술사를 설득해 돌을 평화적으로 얻었다!", "reward": {"item": "re_stone", "exp": 60}},
                            "fail":    {"next_step": 3, "text": "협상에 실패했다. 주술사가 공격해 온다!", "battle": True},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "정신이 돌아왔다. 주술의 영향이 가신 것 같다.",
                    "choices": [],
                    "end": True,
                },
                {
                    "step": 3,
                    "desc": "제단의 빛이 꺼지고 동굴이 조용해졌다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
    ],

    "소금광산": [
        {
            "id": "crystal_vein",
            "title": "신비한 소금 결정맥",
            "steps": [
                {
                    "step": 0,
                    "desc": "광산 벽에서 유난히 반짝이는 소금 결정이 눈에 띈다. 보통 것과는 다른 빛깔이다.",
                    "choices": [
                        {
                            "label": "곡괭이로 파낸다",
                            "stat_check": {"stat": "str", "difficulty": 12},
                            "success": {"next_step": 1, "text": "힘차게 결정을 파냈다! 빛나는 소금 덩어리가 나왔다.", "reward": {"item": "silver_ore", "exp": 20}},
                            "fail":    {"next_step": 2, "text": "너무 세게 쳐서 결정이 부서졌다. 작은 조각만 남았다."},
                        },
                        {
                            "label": "신중하게 조금씩 캔다",
                            "stat_check": {"stat": "dex", "difficulty": 11},
                            "success": {"next_step": 1, "text": "조심스럽게 캐낸 결정은 온전했다!", "reward": {"item": "silver_ore", "gold": 20}},
                            "fail":    {"next_step": 2, "text": "손이 미끄러져 캐지 못했다."},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "결정을 캐는 동안 근처에서 광부 유령이 나타났다!",
                    "choices": [
                        {
                            "label": "말을 걸어본다",
                            "stat_check": {"stat": "will", "difficulty": 11},
                            "success": {"next_step": 3, "text": "광부 유령이 광맥의 위치를 알려줬다!", "reward": {"gold": 50, "exp": 40}},
                            "fail":    {"next_step": 3, "text": "유령이 위협하며 사라졌다. 으스스하다.", "damage": 5},
                        },
                        {
                            "label": "무시하고 도망친다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "달려서 빠져나왔다! 심장이 두근거린다."},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "실패했지만 다른 곳을 살펴보기로 했다.",
                    "choices": [
                        {
                            "label": "다른 곳을 탐색한다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "다른 광맥 근처에서 소량의 철광석을 발견했다!", "reward": {"item": "iron_ore"}},
                        },
                    ],
                },
                {
                    "step": 3,
                    "desc": "소금광산 탐험을 마쳤다. 몸에 소금 냄새가 진하게 배었다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
        {
            "id": "collapsed_tunnel",
            "title": "무너진 갱도",
            "steps": [
                {
                    "step": 0,
                    "desc": "광산 깊은 곳에서 돌이 무너지는 소리가 들렸다. 가봐야 할까?",
                    "choices": [
                        {
                            "label": "확인하러 간다",
                            "stat_check": {"stat": "dex", "difficulty": 11},
                            "success": {"next_step": 1, "text": "조심스럽게 이동해 무너진 갱도에 도착했다."},
                            "fail":    {"next_step": 2, "text": "이동 중 돌에 발이 걸려 넘어졌다.", "damage": 7},
                        },
                        {
                            "label": "안전한 곳으로 피한다",
                            "auto": True,
                            "result": {"text": "안전하게 대피했다. 잠시 후 소리가 멈췄다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "무너진 갱도 안에 광부 한 명이 갇혀 있다!",
                    "choices": [
                        {
                            "label": "돌을 치워 구출한다",
                            "stat_check": {"stat": "str", "difficulty": 14},
                            "success": {"next_step": 3, "text": "힘껏 돌을 치워 광부를 구출했다!", "reward": {"gold": 80, "exp": 60, "item": "coal"}},
                            "fail":    {"next_step": 3, "text": "돌이 너무 무거워 혼자서는 무리였다. 광부와 함께 다른 방법을 찾았다.", "reward": {"gold": 20}},
                        },
                        {
                            "label": "도움을 부르러 간다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "마을 사람들을 데려와 광부를 구출했다!", "reward": {"gold": 50, "exp": 40}},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "상처를 추슬렀다. 더 조심해야겠다.",
                    "choices": [
                        {
                            "label": "계속 탐험한다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "갱도를 더 조심스럽게 탐험했다."},
                        },
                    ],
                },
                {
                    "step": 3,
                    "desc": "무너진 갱도를 뒤로하고 광산을 나왔다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
        {
            "id": "salt_guardian",
            "title": "소금 수호자",
            "steps": [
                {
                    "step": 0,
                    "desc": "광산 중앙의 오래된 제단에 거대한 소금 조각상이 서 있다. 눈 부분이 희미하게 빛난다.",
                    "choices": [
                        {
                            "label": "제단에 공물을 바친다",
                            "item_cost": {"item": "iron_ore", "count": 1},
                            "result": {"next_step": 1, "text": "조각상의 눈이 밝게 빛나며 무언가를 가리킨다!"},
                        },
                        {
                            "label": "조각상을 자세히 살핀다",
                            "stat_check": {"stat": "int", "difficulty": 12},
                            "success": {"next_step": 1, "text": "조각상 뒤에 숨겨진 통로를 발견했다!"},
                            "fail":    {"next_step": 2, "text": "조각상이 갑자기 움직인다! 수호 정령이 깨어났다!", "battle": True},
                        },
                        {
                            "label": "그냥 지나친다",
                            "auto": True,
                            "result": {"text": "아무 일도 없었다. 조각상이 덜 무섭게 느껴진다.", "end": True},
                        },
                    ],
                },
                {
                    "step": 1,
                    "desc": "숨겨진 방에서 오래된 광부의 일지가 발견됐다. 소금광산의 비밀이 적혀 있다.",
                    "choices": [
                        {
                            "label": "일지를 읽는다",
                            "auto": True,
                            "result": {"next_step": 3, "text": "광맥의 정확한 위치와 몬스터 약점을 알아냈다!", "reward": {"exp": 80, "gold": 60}},
                        },
                    ],
                },
                {
                    "step": 2,
                    "desc": "수호 정령과 전투 끝에 제단이 빛을 발했다.",
                    "choices": [],
                    "end": True,
                    "reward": {"gold": 40, "item": "silver_ore"},
                },
                {
                    "step": 3,
                    "desc": "소금 수호자가 조용히 다시 잠들었다.",
                    "choices": [],
                    "end": True,
                },
            ],
        },
    ],
}

# ─── 범용 랜덤 이벤트 풀 ────────────────────────────────────────────────
RANDOM_ADVENTURE_EVENTS = [
    {
        "id": "shiny_item",
        "desc": "길 옆에 빛나는 무언가가 있다.",
        "choices": [
            {
                "label": "집어든다",
                "auto": True,
                "result": {"text": "반짝이는 동전 몇 개를 주웠다!", "reward": {"gold": 15}},
            },
            {
                "label": "무시한다",
                "auto": True,
                "result": {"text": "그냥 지나쳤다.", "end": True},
            },
        ],
    },
    {
        "id": "strange_mushroom",
        "desc": "길가에 색색깔의 버섯이 자라고 있다.",
        "choices": [
            {
                "label": "버섯을 먹어본다",
                "stat_check": {"stat": "luck", "difficulty": 12},
                "success": {"text": "맛있는 버섯이었다! 기력이 회복됐다.", "reward": {"energy": 5}},
                "fail":    {"text": "독버섯이었다! 약간의 피해를 입었다.", "damage": 8},
            },
            {
                "label": "채취한다",
                "auto": True,
                "result": {"text": "버섯을 조심스럽게 채취했다.", "reward": {"item": "gt_herb_01"}},
            },
        ],
    },
    {
        "id": "lost_coin_pouch",
        "desc": "땅바닥에 낡은 동전 주머니가 떨어져 있다.",
        "choices": [
            {
                "label": "주워 간다",
                "auto": True,
                "result": {"text": "동전 주머니를 가져갔다. 상당한 금액이 들어있다!", "reward": {"gold": 35}},
            },
            {
                "label": "주인을 찾아본다",
                "stat_check": {"stat": "luck", "difficulty": 10},
                "success": {"text": "주인을 찾아줬다. 감사 표시로 더 많은 보상을 받았다!", "reward": {"gold": 50, "exp": 20}},
                "fail":    {"text": "주인을 찾지 못했다. 동전을 수거했다.", "reward": {"gold": 20}},
            },
        ],
    },
]

# ─── 숨겨진 트리거 ──────────────────────────────────────────────────────
HIDDEN_TRIGGERS = [
    {
        "id": "midnight_bell",
        "conditions": {"zone": "방울숲", "hour_range": (0, 6), "min_adventures": 3},
        "event": {
            "title": "새벽의 방울 소리",
            "desc": "새벽의 방울숲에서... 들어본 적 없는 방울 소리가 울려퍼진다. 숲 전체가 희미하게 빛나는 것 같다.",
            "reward": {"item": "mp_crystal", "gold": 100, "exp": 50},
        },
    },
    {
        "id": "goblin_secret",
        "conditions": {"zone": "고블린동굴", "min_level": 8, "min_adventures": 5},
        "event": {
            "title": "고블린의 비밀 통로",
            "desc": "동굴 깊은 곳에서 비밀 통로를 발견했다! 고블린 왕의 보물창고로 통하는 길인 것 같다.",
            "reward": {"item": "re_stone", "exp": 200, "gold": 150},
        },
    },
    {
        "id": "salt_crystal",
        "conditions": {"zone": "소금광산", "hour_range": (12, 18), "min_level": 12},
        "event": {
            "title": "소금 결정의 기적",
            "desc": "오후의 햇빛이 광산 입구로 쏟아지며 벽면의 거대한 소금 결정에 반사된다. 그 빛 속에서 무언가 반짝인다.",
            "reward": {"item": "silver_ore", "gold": 200, "exp": 80},
        },
    },
]
