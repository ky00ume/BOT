# 기존 스토리 퀘스트 마이그레이션 가이드

## 📋 목적

기존 `story_quest.py` 및 `story_quest_data.py`를 새로운 제네레이션 시스템으로 점진적으로 마이그레이션하는 가이드입니다.

---

## 🔄 마이그레이션 전략

### Option 1: 점진적 마이그레이션 (권장)

기존 시스템과 새 시스템을 병행 운영하며 천천히 전환:

1. **새 시스템 추가**: `story_generation.py` 및 `generations/` 추가
2. **호환 레이어**: 기존 코드가 새 시스템을 사용하도록 어댑터 작성
3. **데이터 마이그레이션**: G1 데이터를 `generations/g1_darkness_light.py`로 이동
4. **테스트**: 기존 기능이 정상 작동하는지 확인
5. **점진적 교체**: main.py의 스토리 퀘스트 코드를 새 시스템으로 전환

### Option 2: 완전 교체

기존 시스템을 한 번에 교체 (위험도 높음, 테스트 필수):

1. 모든 데이터 마이그레이션
2. main.py 전면 수정
3. 기존 파일 제거 또는 백업

---

## 🛠️ 점진적 마이그레이션 단계별 가이드

### Step 1: 새 시스템 설치

이미 완료:
- ✅ `story_generation.py` 생성
- ✅ `generations/__init__.py` 생성
- ✅ `generations/g1_darkness_light.py` 생성 (템플릿)
- ✅ `generations/g2_template.py` 생성

### Step 2: 호환 레이어 작성

`story_quest_adapter.py` 생성:

```python
"""story_quest_adapter.py — 기존 시스템과 새 시스템 간 호환 레이어"""

from story_quest import StoryQuestManager
from story_generation import GenerationManager
from generations import GENERATIONS

def migrate_old_to_new(old_manager: StoryQuestManager, player) -> GenerationManager:
    """
    기존 StoryQuestManager 데이터를 GenerationManager로 변환
    """
    new_manager = GenerationManager(player)

    # 모든 제네레이션 등록
    for gen in GENERATIONS.values():
        new_manager.register_generation(gen)

    # 기존 데이터 마이그레이션
    old_data = old_manager.to_dict()

    # G1으로 마이그레이션
    gen_id = 1
    new_manager.current_generation_id = gen_id

    progress = new_manager.generation_progress[gen_id]
    progress["chapter"] = old_data.get("chapter", 1)
    progress["quest"] = old_data.get("quest", 1)
    progress["hints"] = old_data.get("hints", [])
    progress["flags"] = old_data.get("flags", {})

    # shadow_sync 마이그레이션
    shadow_sync = old_data.get("shadow_sync", 0)
    new_manager.stats[gen_id] = {"shadow_sync": shadow_sync}

    # quest_log를 completed_quests로 변환
    quest_log = old_data.get("quest_log", [])
    for log_entry in quest_log:
        # "ch1_q1" -> "g1_ch1_q1" 형식으로 변환
        if log_entry.startswith("ch"):
            new_entry = f"g1_{log_entry}"
            progress["completed_quests"].append(new_entry)

    return new_manager

def get_legacy_quest_data(gen_manager: GenerationManager, chapter: int, quest: int):
    """
    새 시스템에서 기존 형식의 퀘스트 데이터 조회
    (기존 코드 호환용)
    """
    gen = gen_manager.get_current_generation()
    if not gen:
        return None

    ch = gen.get_chapter(chapter)
    if not ch:
        return None

    q = ch.get_quest(quest)
    if not q:
        return None

    # 기존 형식으로 변환
    return {
        "title": q.title,
        "npc": q.npc,
        "dialogue": q.dialogue,
        "hint": q.hint,
        "choices": q.choices,
        "rewards": {
            "affinity": q.rewards.affinity,
            "items": q.rewards.items,
            "gold": q.rewards.gold,
            "exp": q.rewards.exp,
        },
        # ... 기타 필드
    }
```

### Step 3: main.py 수정

기존 코드:
```python
from story_quest import StoryQuestManager
story_quest_manager = StoryQuestManager(shared_player)
```

호환 레이어 추가:
```python
from story_quest import StoryQuestManager
from story_generation import GenerationManager
from story_quest_adapter import migrate_old_to_new

# 기존 시스템 (임시)
story_quest_manager = StoryQuestManager(shared_player)

# 새 시스템 초기화
generation_manager = GenerationManager(shared_player)

# 기존 데이터 로드 시 마이그레이션
if loaded:
    sq_data = loaded.get("story_quest", {})
    if sq_data:
        story_quest_manager.from_dict(sq_data)
        # 새 시스템으로 마이그레이션
        generation_manager = migrate_old_to_new(story_quest_manager, shared_player)
```

### Step 4: 저장/로드 수정

기존:
```python
data["story_quest"] = story_quest_manager.to_dict()
```

추가:
```python
data["story_generation"] = generation_manager.to_dict()
```

로드 시:
```python
if "story_generation" in loaded:
    # 새 시스템 사용
    generation_manager.from_dict(loaded["story_generation"])
elif "story_quest" in loaded:
    # 기존 시스템 데이터를 마이그레이션
    story_quest_manager.from_dict(loaded["story_quest"])
    generation_manager = migrate_old_to_new(story_quest_manager, shared_player)
```

### Step 5: 커맨드 수정

기존 `/스토리` 커맨드:
```python
@bot.command(name="스토리")
async def story_quest_cmd(ctx):
    ch = story_quest_manager.chapter
    q = story_quest_manager.quest
    # ...
```

새 시스템으로 전환:
```python
@bot.command(name="스토리")
async def story_quest_cmd(ctx):
    gen = generation_manager.get_current_generation()
    progress = generation_manager.generation_progress[gen.id]

    ch = progress["chapter"]
    q = progress["quest"]

    # 퀘스트 조회
    quest = gen.get_chapter(ch).get_quest(q)
    # ...
```

---

## 📊 마이그레이션 체크리스트

### Phase 1: 기초 작업
- [x] `story_generation.py` 생성
- [x] `generations/` 디렉토리 생성
- [x] G1 템플릿 작성
- [ ] `story_quest_adapter.py` 작성
- [ ] 단위 테스트 작성

### Phase 2: 데이터 마이그레이션
- [ ] G1 전체 데이터를 `generations/g1_darkness_light.py`로 이동
- [ ] 기존 `story_quest_data.py`의 모든 퀘스트 변환
- [ ] 선택지, 컷씬, 전투 데이터 변환 확인

### Phase 3: 코드 통합
- [ ] main.py에 GenerationManager 추가
- [ ] 저장/로드 로직 업데이트
- [ ] `/스토리` 커맨드 업데이트
- [ ] 기타 스토리 관련 커맨드 업데이트

### Phase 4: 테스트
- [ ] 기존 플레이어 데이터로 로드 테스트
- [ ] 새 플레이어 시작 테스트
- [ ] 퀘스트 진행 테스트
- [ ] 선택지 및 분기 테스트

### Phase 5: 정리
- [ ] 기존 `story_quest_data.py` 백업 또는 제거
- [ ] 문서 업데이트
- [ ] 주석 정리

---

## 🎯 새 제네레이션 추가 방법

### 1. 템플릿 복사
```bash
cp generations/g2_template.py generations/g2_spider_web.py
```

### 2. 데이터 작성
`generations/g2_spider_web.py`에서:
- 제네레이션 정보 수정
- 챕터 작성
- 퀘스트 작성

### 3. 등록
`generations/__init__.py`에 추가:
```python
try:
    from .g2_spider_web import G2_GENERATION
    register_generation(G2_GENERATION)
except ImportError:
    pass
```

### 4. main.py에서 로드
```python
from generations import GENERATIONS

for gen in GENERATIONS.values():
    generation_manager.register_generation(gen)
```

---

## ⚠️ 주의사항

1. **기존 플레이어 데이터 호환**: 마이그레이션 함수를 반드시 구현
2. **테스트 필수**: 프로덕션 배포 전 충분한 테스트
3. **백업**: 기존 파일을 백업 후 작업
4. **점진적 전환**: 한 번에 모든 걸 바꾸지 말고 단계적으로

---

## 📝 롤백 방법

문제 발생 시:

1. `story_generation.py` 및 `generations/` 제거
2. main.py에서 새 시스템 관련 코드 제거
3. 기존 `story_quest.py` 복원
4. Git으로 되돌리기

---

## 🎉 마이그레이션 완료 후

새 시스템의 장점:
- ✅ 무한 확장 가능한 제네레이션
- ✅ 명확한 데이터 구조
- ✅ 타입 안정성
- ✅ 독립적인 스토리 관리
- ✅ 재사용 가능한 컴포넌트

G2, G3 등 새 제네레이션 추가가 매우 쉬워집니다!
