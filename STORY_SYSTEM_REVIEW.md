# 스토리 퀘스트 시스템 리뷰 및 확장 가이드

## 📋 현재 시스템 분석

### 1. 퀘스트 시스템 구조

현재 프로젝트는 **두 가지 독립적인 퀘스트 시스템**을 가지고 있습니다:

#### A. 일반 퀘스트 시스템 (`quest.py`)
- **목적**: NPC 알바/의뢰 시스템
- **타입**: collect (수집), kill (처치), deliver (전달)
- **난이도**: easy, normal, hard
- **특징**:
  - 36개의 반복 가능한 퀘스트
  - NPC별로 분류된 퀘스트 풀
  - 골드, 경험치, 아이템 보상
  - 마을 기여도 시스템 연계

#### B. 스토리 퀘스트 시스템 (`story_quest.py`, `story_quest_data.py`)
- **목적**: 메인 스토리 라인 진행
- **구조**: 챕터(Chapter) > 퀘스트(Quest) 계층
- **현재 상태**: 챕터 1~3 구현, 챕터 4 미해금
- **핵심 메커니즘**:
  - `shadow_sync`: -100 ~ +100 히든 스탯 (선택에 따른 성향 변화)
  - `hints`: 수집된 힌트 목록
  - `flags`: 스토리 진행 플래그
  - `quest_log`: 완료된 퀘스트 기록

---

## 🎮 마비노기 제네레이션 시스템과의 비교

### 마비노기 여신강림 시스템의 핵심 요소:

1. **세대별 독립된 스토리 (Generation)**
   - G1: 여신강림, G2: 팔라딘, G3: 다크나이트
   - 각 세대는 완결된 스토리
   - 세대 간 느슨한 연결

2. **다층 구조**
   - Generation > Chapter > Episode > Quest
   - 각 단계마다 의미 있는 구분

3. **분기와 선택**
   - 플레이어 선택에 따른 스토리 변화
   - 다중 엔딩 또는 루트 분기

4. **진행 조건**
   - 레벨 제한, 스킬 요구사항
   - 이전 제네레이션 완료 여부

5. **전용 보상**
   - 세대별 고유 칭호, 아이템, 스킬
   - 세계관 확장 요소

---

## 🔍 현재 시스템의 강점과 약점

### ✅ 강점:

1. **shadow_sync 시스템**: 마비노기의 성향 시스템과 유사한 히든 스탯
2. **선택 분기**: CH1_Q4, CH2_Q3 등에서 이미 선택지 구현
3. **힌트 수집**: 탐정/추리 요소 내장
4. **컷씬 시스템**: `story_quest_ui.py`에 이미 구현됨
5. **강제 패배 전투**: CH3_Q4에서 연출 전투 구현
6. **챕터별 테마**: 각 챕터가 명확한 주제를 가짐

### ⚠️ 개선 필요 사항:

1. **단층 구조**: Generation > Chapter > Quest가 아닌 Chapter > Quest 2단계만 존재
2. **확장성 제한**: 새 챕터 추가 시 하드코딩 필요
3. **데이터 분리 부족**: 코드와 데이터가 섞여있음
4. **조건 시스템 미흡**: 레벨, 스탯 요구사항 등이 명확하지 않음
5. **보상 체계 단순**: 칭호, 아이템 외 특수 보상 부족
6. **세계관 연결 약함**: 일반 퀘스트와 스토리 퀘스트 간 연계 부족

---

## 🏗️ 확장 가능한 제네레이션 시스템 설계

### 제안하는 새 구조:

```
Generation (제네레이션)
  ├─ Chapter (챕터)
  │   ├─ Episode (에피소드) [선택사항]
  │   │   ├─ Quest (퀘스트)
  │   │   │   ├─ Step (단계) [선택사항]
```

### 1. 제네레이션 시스템 (`story_generation.py`)

```python
class Generation:
    """하나의 완결된 스토리 세대"""
    id: int                    # 제네레이션 번호 (G1, G2, ...)
    title: str                 # 제목 (예: "어둠 속의 빛")
    subtitle: str              # 부제 (예: "The Light in Darkness")
    description: str           # 세대 설명
    chapters: Dict[int, Chapter]  # 챕터 목록

    # 진행 조건
    requirements: Dict[str, Any]  # 레벨, 이전 Gen 완료 등

    # 세대별 고유 시스템
    special_stats: Dict[str, int]  # 예: shadow_sync, trust, karma
    special_mechanics: List[str]   # 예: ["time_system", "relationship"]

    # 보상
    completion_rewards: Dict[str, Any]
    achievements: List[str]
```

### 2. 챕터 시스템 (기존 확장)

```python
class Chapter:
    """챕터 - 하나의 큰 스토리 단위"""
    id: int
    generation_id: int
    title: str
    description: str
    episodes: Dict[int, Episode]  # 에피소드 목록 (선택사항)
    quests: Dict[int, Quest]      # 직접 퀘스트 (에피소드 없을 시)

    # 진행 조건
    unlock_condition: Callable

    # 테마
    theme_color: int    # 임베드 색상
    bgm: str           # BGM 태그 (선택사항)
```

### 3. 에피소드 시스템 (새로 추가)

```python
class Episode:
    """에피소드 - 챕터 내 작은 스토리 단위 (선택사항)"""
    id: int
    chapter_id: int
    title: str
    quests: Dict[int, Quest]

    # 에피소드는 더 세밀한 스토리 분할을 위한 선택적 계층
```

### 4. 퀘스트 시스템 (기존 개선)

현재 구조는 유지하되 다음 추가:

```python
class StoryQuest:
    """개선된 스토리 퀘스트"""
    # 기존 필드 유지
    title: str
    npc: Union[str, List[str], None]
    dialogue: Union[str, Dict[str, str]]

    # 새로 추가
    quest_type: str  # "dialogue", "collect", "battle", "cutscene", "choice"
    prerequisites: List[str]  # 선행 퀘스트/조건
    unlock_level: int
    unlock_stats: Dict[str, int]  # 특정 스탯 요구사항

    # 복잡한 구조 지원
    phases: List[QuestPhase]  # 여러 단계로 나뉜 퀘스트
    branches: Dict[str, QuestBranch]  # 분기 퀘스트

    # 효과
    on_complete: Callable  # 완료 시 트리거
    world_changes: Dict[str, Any]  # 세계 변화 (NPC 대사 변화 등)
```

---

## 📂 제안하는 파일 구조

```
story_system/
├── __init__.py
├── generation_manager.py      # 제네레이션 전체 관리
├── generation_data.py          # 제네레이션 데이터 정의
├── chapter_manager.py          # 챕터 관리 (기존 story_quest.py 확장)
├── quest_engine.py             # 퀘스트 실행 엔진
├── choice_system.py            # 선택지 시스템
├── stat_tracker.py             # 히든 스탯 추적 (shadow_sync 등)
└── generations/                # 각 제네레이션별 데이터
    ├── g1_darkness_light.py    # G1: 현재 챕터 1~3 (어둠 속의 빛)
    ├── g2_template.py          # G2: 템플릿
    └── g3_template.py          # G3: 템플릿
```

---

## 🎯 구현 로드맵

### Phase 1: 리팩토링 (현재 시스템 개선)

1. **데이터와 로직 분리**
   - `story_quest_data.py`를 `generations/g1_darkness_light.py`로 이동
   - 챕터 데이터를 명확한 클래스 구조로 변환

2. **제네레이션 추상화**
   - `Generation` 클래스 생성
   - 현재 챕터 1~3을 "G1: 어둠 속의 빛"으로 통합

3. **조건 시스템 구축**
   - 퀘스트 잠금/해금 조건 체계화
   - 레벨, 스탯, 플래그 기반 조건 처리

### Phase 2: 확장 기능 추가

1. **에피소드 시스템 (선택사항)**
   - 필요시 챕터를 에피소드로 세분화
   - 더 긴 스토리를 다루기 위한 계층

2. **분기 시스템 강화**
   - shadow_sync 외 추가 히든 스탯
   - 다중 엔딩 지원

3. **월드 이벤트 시스템**
   - 스토리 진행에 따른 NPC 대사 변화
   - 마을 상태 변경

### Phase 3: 새 제네레이션 추가

1. **G2 기획**
   - 독립된 스토리라인
   - G1 완료 시 해금
   - 새로운 테마와 메커니즘

2. **크로스오버 요소**
   - G1 선택이 G2에 미치는 영향 (선택사항)
   - 히든 퀘스트 연결

---

## 💡 예시: G1 리팩토링

### 현재 (story_quest_data.py):
```python
CH1_QUESTS = {
    1: {"title": "...", "npc": "다몬", ...},
    2: {"title": "...", "npc": "오멜룸", ...},
}
```

### 제안 (generations/g1_darkness_light.py):
```python
G1_METADATA = {
    "id": 1,
    "title": "어둠 속의 빛",
    "subtitle": "The Light in Darkness",
    "description": "그림자 등불의 비밀을 추적하는 첫 번째 이야기",
    "chapters": [1, 2, 3, 4],
    "special_stats": {"shadow_sync": 0},
    "unlock_level": 1,
    "completion_title": "등불을 찾은 자",
}

G1_CHAPTER_1 = {
    "id": 1,
    "generation": 1,
    "title": "마을 사람들이 말하는 것",
    "description": "등불의 소문을 추적한다",
    "unlock_level": 1,
    "theme_color": 0x2c1e3d,
    "quests": {
        1: StoryQuest(
            id="g1_ch1_q1",
            title="대장장이의 경고",
            npc="다몬",
            type="dialogue",
            prerequisites=[],
            dialogue="...",
            rewards={"affinity": {"다몬": 2}},
            hint="빛이 아니라 어둠을 담는 것",
        ),
        # ...
    }
}
```

---

## 🔧 기술적 개선사항

### 1. 타입 안정성
- 모든 데이터 클래스에 타입 힌트 추가
- `@dataclass` 데코레이터 활용

### 2. 검증 시스템
- 제네레이션 데이터 로드 시 유효성 검증
- 순환 참조, 누락된 의존성 체크

### 3. 에디터 툴 (선택사항)
- 스토리 데이터를 JSON/YAML로 외부화
- 비개발자도 스토리 추가 가능하도록

### 4. 테스트
- 각 제네레이션별 단위 테스트
- 분기 로직 테스트

---

## 📖 사용 예시

### 제네레이션 진행 체크:
```python
gen_mgr = GenerationManager(player)

# 현재 진행 중인 제네레이션
current_gen = gen_mgr.get_current_generation()
print(f"G{current_gen.id}: {current_gen.title}")

# 다음 퀘스트 확인
next_quest = gen_mgr.get_next_quest()
if next_quest:
    print(f"다음: {next_quest.title}")
```

### 새 제네레이션 추가:
```python
# generations/g2_spider_web.py
G2_METADATA = {
    "id": 2,
    "title": "거미줄과 속박",
    "subtitle": "Web and Binding",
    "requirements": {
        "completed_generations": [1],
        "min_level": 10,
    },
    # ...
}
```

---

## 🎨 칭호 시스템 확장

### 현재:
- 챕터 완료 시 칭호 부여 (예: "귀를 기울인 자")

### 제안:
```python
GENERATION_TITLES = {
    "g1_complete": "어둠을 헤친 자",
    "g1_light_path": "빛을 선택한 자",
    "g1_dark_path": "그림자를 받아들인 자",
    "g1_neutral_path": "균형을 지킨 자",
    "g1_perfect": "완벽한 추적자",  # 모든 힌트 수집
    "g1_speedrun": "신속한 발걸음",  # 7일 이내 완료
}
```

---

## 🌟 추가 아이디어

### 1. 계절 이벤트 제네레이션
- 기간 한정 스토리
- 특별 보상

### 2. 사이드 제네레이션
- 메인 스토리와 별개
- NPC 개인 스토리

### 3. 협동 제네레이션 (미래)
- 멀티플레이어 지원 시
- 공동 스토리 진행

### 4. 뉴 게임+ 시스템
- 제네레이션 재플레이
- 추가 보상 및 히든 루트

---

## 📝 마이그레이션 가이드

기존 플레이어 데이터를 새 시스템으로 마이그레이션:

```python
def migrate_old_story_data(old_data: dict) -> dict:
    """
    기존 story_quest 데이터를 새 generation 시스템으로 변환
    """
    return {
        "current_generation": 1,
        "generations": {
            1: {
                "chapter": old_data.get("chapter", 1),
                "quest": old_data.get("quest", 1),
                "shadow_sync": old_data.get("shadow_sync", 0),
                "hints": old_data.get("hints", []),
                "flags": old_data.get("flags", {}),
                "quest_log": old_data.get("quest_log", []),
                "completed": False,
            }
        }
    }
```

---

## 🚀 실행 계획

### 즉시 실행 가능한 작업:

1. **`story_generation.py` 생성**: Generation, Chapter 클래스 정의
2. **`generations/` 디렉토리 생성**: G1 데이터 이동
3. **`GenerationManager` 클래스**: 제네레이션 진행 관리
4. **기존 코드 호환성 유지**: 점진적 마이그레이션

### 단계별 우선순위:

1. **High**: 데이터/로직 분리, Generation 추상화
2. **Medium**: 조건 시스템, 에피소드 계층 (필요시)
3. **Low**: 에디터 툴, JSON/YAML 외부화

---

## 💬 결론

현재 스토리 시스템은 **탄탄한 기반**을 가지고 있습니다:
- shadow_sync 히든 스탯 시스템
- 선택 분기 메커니즘
- 컷씬 및 연출 전투

**제네레이션 시스템으로 확장**하면:
- 무한한 스토리 확장 가능
- 마비노기식 세대별 독립 스토리
- 명확한 진행 구조
- 플레이어 성취감 증대

**다음 단계**: 이 문서를 기반으로 `story_generation.py` 및 리팩토링 작업을 시작하면 됩니다.
