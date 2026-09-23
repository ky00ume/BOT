"""월드 장소별 생활/전투 활동 배치 정본.

각 월드 노드에서 실제로 접근 가능한 하위 활동 지역을 한 곳에서 관리한다.
UI와 엔진이 서로 다른 장소를 말하지 않도록 이 데이터를 공유한다.
"""

WORLD_ACTIVITY_ZONES = {
    "비전의 탑": [],
    "마이코니드 군락": [
        {"kind": "gather", "zone": "마이코니드 군락 외곽", "label": "군락 외곽 버섯숲", "emoji": "🍄"},
    ],
    "드레드 할로우": [
        {"kind": "hunt", "zone": "드레드 할로우", "label": "드레드 할로우 사냥터", "emoji": "⚔️"},
        {"kind": "gather", "zone": "수서 나무 숲", "label": "수서 나무 숲", "emoji": "🌿"},
    ],
    "에본레이크": [
        {"kind": "fish", "zone": "에본레이크 북안", "label": "북안 낚시터", "emoji": "🎣"},
        {"kind": "fish", "zone": "에본레이크 얕은 물가", "label": "얕은 물가", "emoji": "🐟"},
        {"kind": "fish", "zone": "에본레이크 선착장", "label": "선착장 낚시터", "emoji": "⚓"},
    ],
    "폐허가 된 마을": [
        {"kind": "hunt", "zone": "폐허가 된 마을", "label": "폐허 사냥터", "emoji": "⚔️"},
    ],
    "그림포지": [
        {"kind": "hunt", "zone": "그림포지", "label": "그림포지 사냥터", "emoji": "⚔️"},
        {"kind": "mine", "zone": "그림포지 광맥", "label": "그림포지 광맥", "emoji": "⛏️"},
        {"kind": "fish", "zone": "그림포지 용암지대", "label": "용암지대 낚시터", "emoji": "🌋"},
    ],
    "아다만틴 대장간": [],
    "샤의 고대 사원": [],
    "셀루네 전초기지": [],
    "곪아가는 만": [
        {"kind": "fish", "zone": "곪아가는 만", "label": "곪아가는 만 낚시터", "emoji": "🎣"},
    ],
    "비버뱅 군락": [],
}


def activities_for(location: str):
    return list(WORLD_ACTIVITY_ZONES.get(location, []))
