# 🕷️ 비전 타운 봇 — UX 개선 기획서

- **작성일**: 2026-03-20
- **상태**: Draft
- **관련 PR**: #17 (가방 시스템 수정)

---

## 1. 현재 UX 현황 요약

현재 봇의 주요 UI/UX 파일 목록:

| 파일 | 역할 |
|---|---|
| `ui_theme.py` | ANSI 색상, Embed 컬러, SPIDER_ART, bar/section/header_box 유틸 |
| `shop_ui.py` | discord.ui.View 기반 인터랙티브 구매/판매 UI (SellView, BuyView) |
| `fishing_card.py` | PIL 기반 통일 카드 이미지 생성기 (낚시/요리/제련/채집/알바/휴식 카드) |
| `fishing.py` | 이프 스타일 낚시 타이밍 게임 (FishingView with 버튼 인터랙션) |
| `story_quest_ui.py` | 스토리 퀘스트 UI (ShadowChoiceView, ForcedBattleView, ExploreStepView) |

---

## 2. 🎴 핵심: 이프봇 낚시카드 디자인 분석 및 반영안

### 2-1. 이프봇 카드 시스템 분석 (참고 소스)

- **레포**: [KimuSoft/Epbot-Origin](https://github.com/KimuSoft/Epbot-Origin)
  - `utils/fish_card/generator.py` — theme.json 기반 동적 카드 생성기
  - `utils/fish_card/utils/fish_card/fishcard.py` — 레거시 카드 생성 (하드코딩 좌표)
  - `utils/fish_card/utils/fish_card_new/fish_card.py` — 신규 테마 기반 카드
  - `cogs/fishing/game.py` — 낚시 결과 → 카드 이미지 → Embed 연동 흐름
- **카드 에디터**: [paring-chan/fishcard-editor](https://github.com/paring-chan/fishcard-editor) — TS/JS 기반 카드 레이아웃 GUI 편집기

### 2-2. 이프 vs 현재 봇 비교표

| 특징 | 이프봇 (Epbot-Origin) | 현재 봇 (fishing_card.py) |
|---|---|---|
| 테마 시스템 | `theme.json`으로 레이아웃 정의, 테마별 폴더 분리 | ❌ 하드코딩 단일 디자인 |
| 배경 이미지 | 등급별 PNG (`rank-{n}.png`) + `default.png` fallback | 그라디언트만 사용, bg_path 로직 있으나 파일 미존재 |
| 레이아웃 방식 | JSON 배열로 텍스트 position/size/color 동적 렌더링 | Python 코드에 좌표 하드코딩 |
| 변수 포맷팅 | `{name}`, `{cost}`, `{length}`, `{fee}`, `{bonus}`, `{profit}`, `{roomname}`, `{username}`, `{time}` 등 풍부 | 제한적 (이름, 크기, 가격, 수수료, 보너스, 순수익) |
| 커스텀 폰트 | 테마별 커스텀 폰트 지정 가능 | 시스템 폰트 자동 탐색 |
| 등급 체계 | 숫자(0~5) rarity 6등급 | 문자열 (Normal/Rare/Epic/Legendary/Fail) 5등급 |
| 낚시터/유저 정보 | 카드에 낚시터 이름 + 유저 이름 + 시간 표기 | 카드 이미지에 미포함 (Embed footer에만) |
| 소유자 특혜 | 낚시터 주인일 때 별도 텍스트/수수료 표시 | ❌ 없음 |
| 평균가/평균크기 | 표시됨 | ❌ 없음 |

### 2-3. 카드 시스템 개선 항목 (우선순위 포함)

| # | 카테고리 | 현재 상태 | 이프 참고 개선안 | 우선순위 |
|---|---|---|---|---|
| 1 | 🎴 카드 테마 시스템 | 하드코딩 단일 디자인 | JSON 기반 테마 레이아웃 도입 (theme.json에 position/size/color 정의), 테마 폴더 구조 (`static/cards/themes/{name}/`) | ⭐⭐⭐ |
| 2 | 🖼️ 등급별 배경 PNG | 코드로 그라디언트 생성 | `rank_{grade}.png` 배경 이미지 제작 + 그라디언트 fallback 유지 | ⭐⭐⭐ |
| 3 | 📝 카드 정보 확장 | 물고기/크기/가격/수수료/보너스/순수익 | +낚시터 이름, +유저 이름, +날짜/시간, +평균가/평균크기 추가 | ⭐⭐ |
| 4 | 🔤 커스텀 폰트 지원 | 시스템 폰트 자동 탐색 | 테마별 폰트 지정 가능 (theme.json에 "font" 키) | ⭐ |
| 5 | 📐 동적 레이아웃 렌더링 | 좌표 하드코딩 | theme.json의 position/size 배열 기반 동적 렌더링 전환 (이프 generator.py 방식) | ⭐⭐⭐ |
| 6 | 🎨 컨텐츠별 카드 통합 | generate_fishing_card 등 개별 함수 | 통합 카드 팩토리: generate_card() 하나로 rows + theme 조합 | ⭐⭐ |
| 7 | 🏷️ 카드 뱃지 영역 강화 | 하단 등급 뱃지만 표시 | 낚시터 주인 뱃지, 신기록 뱃지, 첫 잡이 뱃지 등 조건부 뱃지 오버레이 | ⭐ |

### 2-4. 제안 파일 구조

```
static/cards/
├── themes/
│   ├── default/
│   │   ├── theme.json
│   │   ├── rank_Normal.png
│   │   ├── rank_Rare.png
│   │   ├── rank_Epic.png
│   │   ├── rank_Legendary.png
│   │   ├── rank_Fail.png
│   │   └── default.png
│   └── dark/
│       ├── theme.json
│       └── ...
```

### 2-5. theme.json 예시

```json
{
  "font": "NanumGothic.ttf",
  "default": [
    { "text": "{title}", "position": [20, 16], "size": 24, "color": [230, 232, 245] },
    { "text": "{grade_label}", "position": [420, 20], "size": 18, "color": [100, 130, 255] },
    { "text": "물고기: {name}", "position": [30, 80], "size": 15, "color": [175, 180, 200] },
    { "text": "{length}cm", "position": [260, 80], "size": 16, "color": [180, 200, 255] },
    { "text": "판매가: {cost}G", "position": [30, 110], "size": 15 },
    { "text": "수수료: -{fee}G", "position": [30, 140], "size": 15 },
    { "text": "순수익: {profit}G", "position": [30, 170], "size": 16, "color": [100, 240, 190] },
    { "text": "📍 {roomname}", "position": [30, 240], "size": 12 },
    { "text": "🕷️ {username} | {time}", "position": [30, 260], "size": 10, "color": [120, 120, 140] }
  ],
  "rank_Legendary": [
    { "text": "👑 전설이댜!!! {name}?!?!", "position": [20, 16], "size": 24, "color": [255, 230, 100] }
  ]
}
```

---

## 3. 기타 UX 개선 주요 영역

| 카테고리 | 현재 상태 | 개선 포인트 |
|---|---|---|
| 인벤토리/가방 | PR #17에서 일부 수정됨 | 페이지네이션, 카테고리 필터, 정렬 기능 |
| 상점 UI | shop_ui.py에 Select 기반 UI | 선택 시 실시간 미리보기, 소지금 표시 강화 |
| 도움말 | /도움말 한 페이지에 모든 명령어 | 카테고리별 페이지네이션, 인터랙티브 탭 |
| 전투 | 텍스트 기반 출력 | 버튼 UI (공격/스킬/도주), 턴 진행 시각화 |
| 상태창 | Embed 기반 | 장비+스탯 통합 뷰, 비교 기능 |
| NPC 대화 | 선형 텍스트 | 선택지 버튼, 호감도 시각화 |
| 낚시/채집 | 텍스트 + SPIDER_ART | 진행 바, 애니메이션 피드백 강화 |
| 에러 메시지 | 일관성 부족 | 통일된 에러 포맷, 다음 행동 안내 |

---

## 4. 구현 로드맵 (Phase)

- **Phase 1** (⭐⭐⭐): 카드 테마 시스템 + 등급별 배경 + 동적 레이아웃
- **Phase 2** (⭐⭐): 카드 정보 확장 + 컨텐츠별 카드 통합 + 인벤토리 개선
- **Phase 3** (⭐): 커스텀 폰트 + 카드 뱃지 + 전투 UI + 도움말 탭

---

## 5. 참고 소스

| 레포 | 역할 | 핵심 파일 |
|---|---|---|
| [KimuSoft/Epbot-Origin](https://github.com/KimuSoft/Epbot-Origin) | 이프봇 본체 | `utils/fish_card/generator.py`, `utils/fish_card/utils/fish_card_new/fish_card.py`, `cogs/fishing/game.py` |
| [paring-chan/fishcard-editor](https://github.com/paring-chan/fishcard-editor) | 이프 낚시카드 에디터 (TS/JS) | `src/` — 카드 레이아웃 GUI 편집기 |
