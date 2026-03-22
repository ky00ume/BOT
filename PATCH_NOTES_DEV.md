# 🛠️ 비전 타운 봇 개발자 패치 노트 — v0.5.1 (2026-03-22)

인수인계용 기술 패치노트입니다.

---

## 📁 파일 구조 변경

### 신규 파일
| 파일 | 설명 |
|------|------|
| `skill_ui.py` | `/스킬` 통합 UI (카테고리 드롭다운 → 스킬 버튼 → 상세 임베드) |
| `job_data.py` | NPC별 알바 풀 (`NPC_JOB_POOL`), 9개/NPC, 3난이도 × 3바리에이션 |
| `title_data.py` | 타이틀 데이터 분리 |
| `shop_ui.py` | `BuyView` (드롭다운+버튼 상점 UI) |
| `quest_ui.py` | `QuestWindowView` (퀘스트 셀렉트 메뉴 UI) |
| `town_ui.py` | `VisionTownView`, `WorldMapView`, 구역별 뷰 |
| `PATCH_NOTES_USER.md` | 유저용 패치노트 |
| `PATCH_NOTES_DEV.md` | 인수인계용 패치노트 (본 파일) |

### 삭제/변경된 파일
- `village.py`: `/마을` 명령 → `/비전타운` 으로 이전, 마을 기여도 로직은 유지
- `skills.py`: 텍스트 기반 스킬 조회 제거 → `skill_ui.py`로 통합

---

## 🏘️ 마을 & NPC 시스템

### town_ui.py
- `VisionTownView`: 마을 진입 버튼 UI (NPC 버튼, 탐험 버튼, 월드맵)
- `WorldMapView`: 존 이동 UI
- NPC 버튼 클릭 → `ConversationManager.send_conversation()` 호출

### npc_conversation.py
- `NPCConversationView`: 키워드 버튼 + 아르바이트/구매/수련 기능 버튼
- `_get_response(keyword_data, level_name)`: `default`가 `list`이면 `random.choice()` 처리 (이미 적용됨)
- `ConversationManager(player, aff_mgr, npc_manager_ref)`: 대화 관리

---

## 💬 npc_dialogue_db.py 구조 변경

### `default` 타입: `str` → `list[str]`
**v0.5.1 기준 모든 `NPC_KEYWORDS[npc][keyword]["default"]`는 길이 5 이상의 `list`여야 합니다.**

변경 전:
```python
"무기": {
    "default": "좋은 무기는 좋은 재료에서 시작합니다.",
    "affinity_points": 3,
}
```

변경 후:
```python
"무기": {
    "default": [
        "좋은 무기는 좋은 재료에서 시작합니다...",
        "... (4개 더)",
    ],
    "affinity_points": 3,
}
```

### 특수 NPC 대사 전면 재작성
- **카르니스**: 소심한 톤("으...으...마제스티가...") → 위압적·무심·냉소적 반말 톤
- **루바토**: "타브" 연관 키워드 전면 제거, 활발한 바드 이미지로 재작성
- **라파엘**: 기존 교활한 톤 유지, 모든 `default` → 5개 리스트 변환

### "타브" 참조 제거
다음 위치에서 "타브" 관련 내용 삭제:
- `npc_dialogue_db.py`: 루바토 `"타브"` 키워드 항목 삭제
- `database.py`: 루바토 `"desc"` 필드에서 "타브" 언급 제거
- `츄마고치 등장인물.txt`: "루바토(타브)" → "루바토" 수정
- `츄마고치 등장인물 수정본.txt`: "타브" 설명 제거

---

## 🏪 상점 시스템

### shop_ui.py
- `BuyView(player, shop_mgr, npc_name, catalog)`: 드롭다운으로 상품 선택 → 수량 선택 → 구매
- `InventorySellView(player, shop_mgr)`: 인벤토리 아이템 판매 UI

### shop.py
- `NPC_CATALOGS`: NPC별 판매 목록
- `ShopManager(player)`: 구매/판매 처리

### 삭제된 명령어
`/구매목록`, `/구매`, `/판매목록`, `/판매`, `/요리`, `/혼합`, `/레시피`, `/제련`, `/제련목록`, `/제작`, `/제작도감`, `/제조`

---

## 💼 알바 시스템 — job_data.py 연동

### job_data.py
```python
NPC_JOB_POOL: dict[str, list[dict]]  # NPC별 알바 풀 (9개/NPC)
DIFFICULTY_LABELS: dict              # {"easy": "쉬움", "normal": "보통", "hard": "어려움"}
get_random_job(npc_name: str) -> dict | None  # 랜덤 알바 반환
get_job_by_id(job_id: str) -> dict | None
```

### Job dict 구조
```python
{
    "id": "damon_e1",
    "name": "철 주괴 납품",
    "difficulty": "easy",           # easy / normal / hard
    "type": "gather",               # gather / deliver / hunt
    "target_item": "iron_bar",      # gather/deliver용
    "target_count": 2,              # gather용
    "target_npc": "제블로어",        # deliver용
    "deliver_item": "dq_damon_letter",    # deliver용 퀘스트 아이템 ID
    "deliver_item_name": "다몬의 서신",
    "target_monster": "goblin",     # hunt용
    "reward_gold": 40,
    "reward_exp": 10,
    "reward_item": None,            # 보상 아이템 ID 또는 None
    "reward_skill_exp": {"crafting": 20},  # 스킬 경험치 보상
    "energy_cost": 10,
    "desc": "철 주괴 2개를 가져다 주세요.",
}
```

### npcs.py 변경 (start_job_async)
- `from job_data import get_random_job, DIFFICULTY_LABELS` 임포트 추가
- `npc.get("job")` 단일 구조 → `get_random_job(npc_name)` 호출로 교체
- 유형별 처리:
  - `gather`: 인벤토리 아이템 확인·차감 → 보상 지급 (부족 시 기력 환불)
  - `deliver`: 퀘스트 아이템을 인벤토리에 추가 → 대상 NPC 전달 안내 메시지
  - `hunt`: 3초 대기 후 즉시 완료 → 보상 지급
- `reward_skill_exp` 처리: `player.skill_exp[skill_id] += amount`
- `reward_item` 처리: `player.add_item(reward_item, 1)`

---

## 📚 /스킬 창 — skill_ui.py 개편

### 핵심 변경
- `SkillCategorySelect.callback()`: 카테고리 선택 시 스킬 정보 버튼 추가
  - `_add_skill_info_buttons(view, player, skill_db)`: 보유 스킬마다 `[ℹ️ 이름]` 버튼 생성
  - 버튼 custom_id: `skill_info_{skill_id}`
  - Discord 25개 컴포넌트 제한 준수 (24개 버튼 + 카테고리 select 1개)

### 신규 함수
```python
def _exp_gauge(skill_id, rank, current_exp) -> str:
    """▓▓▓░░ 65% 형식 게이지 반환"""

def make_skill_detail_embed(player, skill_id) -> discord.Embed:
    """스킬 상세 임베드: desc, 현재 랭크, 수치, 게이지"""
```

### 스킬 수치 표시 로직
- 전투 스킬: `damage_bonus`, `damage_reduce`, `counter_multiplier`, `aoe_multiplier`
- 마법 스킬: `mp_cost`, `damage`
- 회복 스킬: `mp_cost`, `heal_amount`
- 마스터리: `stat_bonus`
- 생활 스킬: `desc` + 레시피 창 안내

---

## 🎭 special_npc.py 변경

### ENCOUNTER_INTROS
| NPC | 변경 내용 |
|-----|-----------|
| 라파엘 | "붉은 피부에 거대한 뿔" → 인간으로 변환한 모습 (잘생긴 인간형 묘사) |
| 카르니스 | "으...으...마제스티가..." 소심한 묘사 → 문학적+위압적 묘사로 교체 |

### DEPARTURE_MESSAGES
| NPC | 변경 내용 |
|-----|-----------|
| 카르니스 | "마제스티께 전하겠습니다" → "꺼져라. 다시 눈앞에 얼씬거리지 마." |

---

## 🔔 town_notice.py 개편

### make_commands_embed()
- 삭제된 명령어 제거: `/구매목록`, `/구매`, `/판매목록`, `/판매`, `/요리`, `/혼합`, `/레시피`, `/제련`, `/제련목록`, `/제작`, `/제작도감`, `/제조`
- 상점: "NPC 대화 창 `[구매]` 버튼" / "인벤토리 `[판매]` 버튼" 안내로 교체
- 스킬: `/스킬 [이름]` → `/스킬` (드롭다운+버튼 UI) 안내로 교체

### make_life_embed()
- 요리/제련/포션/제작: 삭제된 명령어 → `/스킬` 통합 UI 안내로 교체

### make_patchnote_embed()
- `v0.5 (2026-03-21)` → **`v0.5.1 (2026-03-22)`**
- 알바 시스템 개편, 스킬 상세 조회, NPC 대화 바리에이션, 특수 NPC 업데이트 내용 추가

---

## ⚠️ 알려진 제한 사항

- Discord 25개 컴포넌트 제한으로 스킬 버튼이 24개 초과 시 잘림 (현재 보유 가능 스킬 수 고려 시 문제 없음)
- `deliver` 타입 알바의 "전달 완료" 확인은 미구현 상태 (대상 NPC에게 전달하는 인터랙션 필요)
- `start_job()` 동기 메서드는 deprecated 처리됨 (실제 사용은 `start_job_async()`)

---

✦ **비전 타운 봇 v0.5.1** — 2026-03-22 ✦
