# Graph Report - .  (2026-04-10)

## Corpus Check
- Large corpus: 170 files · ~1,132,958 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 2204 nodes · 4982 edges · 84 communities detected
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 1107 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `C` - 126 edges
2. `Player` - 100 edges
3. `render()` - 84 edges
4. `Economy` - 76 edges
5. `addLog()` - 74 edges
6. `_check_channel()` - 73 edges
7. `handleEvent()` - 49 edges
8. `VisionTownView` - 47 edges
9. `saveAll()` - 46 edges
10. `playerAttack()` - 46 edges

## Surprising Connections (you probably didn't know these)
- `achievements.py — 업적(Achievement) & 타이틀 시스템` --uses--> `C`  [INFERRED]
  achievements.py → ui_theme.py
- `affinity.py — NPC 호감도 시스템` --uses--> `C`  [INFERRED]
  affinity.py → ui_theme.py
- `fishing_card.py — BG3 스타일 카드 이미지 생성기 (모든 콘텐츠 공용)  기존 함수 시그니처 100% 유지. 내부 렌더링은 bg` --uses--> `C`  [INFERRED]
  fishing_card.py → bg3_renderer.py
- `범용 카드 생성 — bg3_renderer에 위임.     icon 파라미터는 이모지 제거 후 타이틀에 결합.` --uses--> `C`  [INFERRED]
  fishing_card.py → bg3_renderer.py
- `bulletin.py — 마을 게시판 & 명예의전당 & 주간 낚시대회` --uses--> `C`  [INFERRED]
  bulletin.py → ui_theme.py

## Hyperedges (group relationships)
- **Vision Town NPC Ecosystem** — characters_revised_damon, characters_revised_mol, characters_revised_arabella, characters_revised_bruksha, characters_revised_silen [EXTRACTED 0.95]
- **Game Banner Asset Collection** — fishing_background, gathering_underdark_background, hunting_background, town_arcane_background [INFERRED 0.95]
- **Dark Fantasy Game Settings** — concept_underground_cave, concept_underdark_zone, concept_dark_forest, concept_arcane_magic [INFERRED 0.80]
- **Game Activities** — concept_fishing_activity, concept_gathering_activity, concept_hunting_activity, concept_town_location [INFERRED 0.90]
- **Animal Portrait Set** — goyangi_portrait, scratch_portrait, isanghan_so_portrait [EXTRACTED 1.00]
- **Realistic 3D Animal NPC Portraits** — goyangi_portrait, scratch_portrait, isanghan_so_portrait, style_realistic_3d, role_npc_companion [INFERRED 0.75]
- **Gale's Apparition Portrait Pair** — 게일의_환영_초상화_npc, 게일의_환영_npc [EXTRACTED 1.00]
- **Damon Portrait Pair** — 다몬_초상화_npc, 다몬_npc [EXTRACTED 1.00]
- **NPC Portrait Group Chunk 4** — 게일의_환영_초상화_npc, 게일의_환영_npc, 고양이_초상화_npc, 다몬_초상화_npc, 다몬_npc [INFERRED 0.85]
- **Rafael NPC Portrait Pair** — 라파엘_초상화_npc, 라파엘_npc, npc_portrait_group_rafael [EXTRACTED 1.00]
- **Rubato NPC Portrait Pair** — 루바토_초상화_npc, 루바토_npc, npc_portrait_group_rubato [EXTRACTED 1.00]
- **NPC Portrait Set Chunk 5** — 라파엘_초상화_npc, 라파엘_npc, 루바토_초상화_npc, 루바토_npc, 몰_초상화_npc [EXTRACTED 1.00]
- **NPC Portrait Images Chunk 6** — mol_npc, bruksha_portrait_npc, bruksha_npc, scratch_portrait_npc, silen_portrait_npc [EXTRACTED 1.00]
- **Arabella Portrait Pair** — 아라벨라_초상화_npc, 아라벨라_npc [EXTRACTED 1.00]
- **NPC Portrait Chunk 7 Group** — 실렌_npc, 아라벨라_초상화_npc, 아라벨라_npc, 아울베어_초상화_npc, 알피라_초상화_npc [EXTRACTED 1.00]
- **Elven Female NPC Portraits** — 알피라_npc, 엘레라신_npc, 엘리라신_초상화_npc [INFERRED 0.70]
- **오멜룸 Portrait Pair** — 오멜룸_npc, 오멜룸_초상화_npc [INFERRED 0.95]
- **엘레라신 Portrait Pair** — 엘레라신_npc, 엘리라신_초상화_npc [INFERRED 0.90]
- **Chunk 9 NPC Portrait Images** — 이상한_소_초상화_npc, 제블로어_초상화_npc, 카르니스_초상화_npc, 카르니스_npc, 카엘릭_초상화_npc [INFERRED 0.90]
- **카르니스 Portrait Pair** — 카르니스_초상화_npc, 카르니스_npc [EXTRACTED 1.00]
- **NPC Portrait Group - Chunk 10** — 카엘릭_npc, 팅커벨초상화_npc, 파울_npc [INFERRED 0.85]

## Communities

### Community 0 - "Adventure Engine"
Cohesion: 0.02
Nodes (152): AdventureEngine, AdventureView, NPCInteractionView, NPC 상호작용 처리. action: 'accept'/'refuse'/'trade'/'fight' 등, 탐험 시작.         Returns dict with keys: 'ok', 'error', 'scenario', 'step_data', ', 탐험 종료 후 10% 확률로 외부 자극 이벤트, D&D 5e 스타일 능력치 체크.         stat: base_stats 키 (str/int/dex/will/luck, 기본값 10), 시나리오에서 step 번호에 해당하는 인덱스 반환 (+144 more)

### Community 1 - "Risulike RPG JS"
Cohesion: 0.02
Nodes (330): abilityCheck(), addClassPassive(), addDroppablePassive(), addEquipToInventory(), addGraveyardEntry(), addLog(), addShieldToPlayer(), advanceQuest() (+322 more)

### Community 2 - "Config & Core System"
Cohesion: 0.02
Nodes (108): Config, 게임 설정 관리 시스템.  YAML 기반 설정 파일에서 게임 상수를 로드합니다., 게임 설정 관리자.      config/game.yaml 파일에서 설정을 로드하며,     파일이 없거나 YAML 라이브러리가 없는 경우 기본, 설정값 조회.          Args:             key_path: "game.max_level" 형식의 경로 (점으로 구분), economy(), fresh_player(), player_with_gold(), player_with_items() (+100 more)

### Community 3 - "NPC Affinity & Events"
Cohesion: 0.02
Nodes (109): affinity.py — NPC 호감도 시스템, alarms.py — 츄라이더 BOT 알람 및 랜덤 이벤트 시스템, crafting.py — 장비 제작 시스템, gacha.py — 몰의 수상한 상자 (가챠), get_current_season(), _pick_by_rate(), gathering.py — 채집 & 채광 시스템, 채집을 수행합니다. zone_name이 있으면 해당 존 전용 풀을 사용합니다. (+101 more)

### Community 4 - "BG3 Battle Card Renderer"
Cohesion: 0.05
Nodes (54): _bar_A(), BG3Renderer, _f(), _find_fonts(), get_renderer(), _glow(), _gold_frame(), _grade_badge() (+46 more)

### Community 5 - "Achievement System"
Cohesion: 0.03
Nodes (25): AchievementManager, achievements.py — 업적(Achievement) & 타이틀 시스템, setup(), care.py — 돌봄 시스템 (쓰담쓰담 / 간식주기 / 놀아주기), costume_data.py — 의장 아이템 DB, 간식 아이템 DB, 제작 레시피, DiaryManager, diary.py — 츄라이더 일기 시스템 (매일 22시 자동 생성 + /일기 명령어), 일기를 생성하고 채널에 전송한 뒤 파일에 저장합니다. (+17 more)

### Community 6 - "Music Performance"
Cohesion: 0.05
Nodes (25): _get_audience_reaction(), MusicView, NoteButton, parse_melody(), music.py — 마비노기식 작곡/연주 시스템, 한글 음계 문자열을 파싱합니다. 유효하지 않으면 None 반환., _get_affinity_level_name(), _get_affinity_points() (+17 more)

### Community 7 - "Life & Fishing Commands"
Cohesion: 0.04
Nodes (30): LifeCog, setup(), setup(), save_manager.py — 세이브 전담 매니저  기존 database.py의 save_player_to_db/load_player_from, 기존 DB 행을 players_backup 테이블에 복사 (최근 3개 유지)., 가장 최근 백업에서 players 테이블을 복원합니다., schema_version 비교 후 순차 마이그레이션 적용., 세이브 순서: ① backup → ② validate → ③ write (실패 시 backup 복원).          Returns: (+22 more)

### Community 8 - "Bulletin Board"
Cohesion: 0.05
Nodes (9): BulletinBoard, bulletin.py — 마을 게시판 & 명예의전당 & 주간 낚시대회, WeeklyFishing, CollectionManager, collection.py — 수집일기(도감) 시스템, 도감에 아이템을 등록합니다.         Returns:             (is_new: bool, total_count: int), (collected, total_possible, percent) 반환, MiscCog (+1 more)

### Community 9 - "Data Externalization Tests"
Cohesion: 0.04
Nodes (12): data JSON 외부화 테스트 (REMEDIATION_PLAN 1-D).  items.py / job_data.py / npc_dialogue, 모든 아이템의 grade 가 유효한 값인지 확인.          costume_data / snack 아이템은 한국어 등급명을 사용하므로 함께, 무기 아이템은 slot 필드를 가져야 한다., 각 알바 데이터에 필수 필드가 있는지 확인., NPC 키워드는 default 응답을 포함해야 한다., 선물 반응 데이터에 필수 필드가 있는지 확인., NPC_KEYWORDS 와 NPC_GIFT_REACTIONS 가 동일한 NPC를 커버하는지 확인., BAGS (database.py에서 로드) 가 ALL_ITEMS에 포함되는지 확인. (+4 more)

### Community 10 - "Town UI & Banners"
Cohesion: 0.07
Nodes (16): create_fishing_banner(), create_gathering_banner(), create_hunting_banner(), create_location_banner(), create_town_banner(), FishingZoneView, GatheringZoneView, HuntingZoneView (+8 more)

### Community 11 - "Story Generation System"
Cohesion: 0.07
Nodes (18): Enum, get_legacy_chapter_data(), generations/g1_darkness_light.py — G1: 어둠 속의 빛  현재 story_quest_data.py의 챕터 1~4를, 기존 story_quest_data.py 형식으로 챕터 데이터 반환.     레거시 코드 호환용., generations/g2_template.py — G2: 템플릿  새로운 제네레이션 작성 템플릿. 이 파일을 복사하여 G2, G3 등을 만들, Utils package for Vision Town Bot., Chapter, create_chapter() (+10 more)

### Community 12 - "Validators & Error Handling"
Cohesion: 0.05
Nodes (16): GameError, utils/validators.py — 사용자 입력 검증 테스트., TestTruncateForRender, TestValidateCount, TestValidateItemId, TestValidateMessage, TestValidatePlayerName, 사용자 입력 검증 유틸리티.  Discord 커맨드 경계에서 플레이어가 전달한 문자열/수치를 일관된 방식으로 검증하고, PIL 렌더링 등 하류 (+8 more)

### Community 13 - "Care System UI"
Cohesion: 0.07
Nodes (12): _bar(), CostumeCraftView, CostumeManageView, _ItemSelectView, _make_room_card(), care_ui.py — "하이네스의 방" discord.ui.View 기반 돌봄 UI, 하이네스의 방 현황 카드 이미지 생성., Select 메뉴 하나만 가지는 임시 뷰 (ephemeral 사용용). (+4 more)

### Community 14 - "Battle Engine Tests"
Cohesion: 0.05
Nodes (9): engine(), battle.py — BattleEngine 유닛 테스트 (REMEDIATION_PLAN 4-C 확장).  discord / bg3_render, npc_manager 없이 BattleEngine 생성., 레벨 0 플레이어는 Lv.1 이상 요구 구역에 입장 불가., TestApplyEventEffect, TestCalcReward, TestEnterZone, TestUseCheer (+1 more)

### Community 15 - "Environment Config"
Cohesion: 0.07
Nodes (17): load_discord_token(), load_optional_int(), load_required_int(), load_required_str(), 환경변수 로딩 유틸리티 (REMEDIATION_PLAN 3-D).  main.py 가 실행 중에 ``int(os.getenv(..., "하드코딩, 필수 정수 환경변수를 로드. 누락 또는 파싱 실패 시 ConfigError., 선택 정수 환경변수. 미설정 시 ``default`` 반환., Discord 봇 토큰 로드. 토큰 길이가 비정상적으로 짧으면 실패한다.      정확한 Discord 토큰 형식(base64url 점 3부분) (+9 more)

### Community 16 - "Skill UI"
Cohesion: 0.13
Nodes (19): Select, _add_skill_info_buttons(), _exp_gauge(), _get_recipes_for_skill(), LifeSkillSelect, make_category_embed(), make_recipe_detail_embed(), make_recipe_list_embed() (+11 more)

### Community 17 - "Town Commands"
Cohesion: 0.1
Nodes (10): setup(), TownCog, make_commands_embed(), make_intro_embed(), make_life_embed(), make_npc_embed(), make_patchnote_embed(), make_patchnote_v052_embed() (+2 more)

### Community 18 - "Battle Formula Tests"
Cohesion: 0.11
Nodes (6): _mk_engine(), battle.py — 순수 함수 & 컨디션 보정식 회귀 테스트 (REMEDIATION_PLAN 4-C).  battle.py 는 discord, BattleEngine 을 부분적으로 초기화. __init__ 이 많은 기본값을 설정하므로     실제 생성자를 거치되 외부 의존(npc_man, TestBarText, TestBattleGrade, TestConditionModifiers

### Community 19 - "Player & Item Tests"
Cohesion: 0.08
Nodes (2): HP보다 큰 피해 받기 테스트 (0 이하로 내려가야 함)., TestPlayer

### Community 20 - "NPC Dialogue & Shop"
Cohesion: 0.15
Nodes (9): _make_quest_detail_image(), _make_quest_list_image(), _make_result_image(), QuestBackView, QuestDetailView, quest_ui.py — 마비노기식 PIL 이미지 퀘스트 창 UI, 퀘스트 완료/포기 후 목록으로 돌아가는 뷰, 메인 스토리에서 일반 퀘스트로 돌아가는 뷰 (+1 more)

### Community 21 - "Quest System"
Cohesion: 0.1
Nodes (10): tests/test_player_lock.py — utils.player_lock 단위 테스트., get_player_lock은 asyncio.Lock 인스턴스를 반환한다., 동일 user_id에 대해 항상 같은 Lock 객체를 반환한다., 서로 다른 user_id는 서로 다른 Lock 객체를 반환한다., 새로 생성된 Lock은 잠겨있지 않다., cleanup_lock 후 새로 요청하면 다른 Lock 객체가 반환된다., 존재하지 않는 user_id를 cleanup해도 오류가 발생하지 않는다., TestCleanupLock (+2 more)

### Community 22 - "Inventory Management"
Cohesion: 0.1
Nodes (6): utils/render_fallback.py — 렌더링 폴백 데코레이터 테스트 (2-B)., TestDefaultExceptionsConstant, TestFallbackPath, TestIsTextFallbackResult, TestSuccessPath, TestValidation

### Community 23 - "Economy & Currency"
Cohesion: 0.11
Nodes (11): QuestBridge, quest_bridge.py — 퀘스트-채집 연동 브릿지  알바/의뢰가 인벤토리를 참조할 때 거치는 브릿지. Economy를 경유하여 트랜잭션, 퀘스트/알바 완료 처리를 Economy를 통해 수행하는 브릿지., 아이템 보유량 확인.          Returns:             (보유량: int, 충족 여부: bool), 퀘스트 완료 처리: 아이템 차감 → Economy.pay_reward() → 로그.          Args:             econom, 알바 완료 처리: 타입별(hunt/gather/deliver) 로직 → Economy.pay_reward() → 로그.          Args, transaction_log.py — 트랜잭션 로그 시스템  모든 재화 변동(아이템 획득/소비, 골드 변동, EXP 변동)에 [LOG: TRAN, 모든 재화 변동을 시간/소스/상세 정보와 함께 기록하는 로거. (+3 more)

### Community 24 - "Battle Combat System"
Cohesion: 0.14
Nodes (17): AnsiColor, colorize(), energy(), format_gold(), format_percentage_bar(), format_stat_bar(), format_time_seconds(), gold() (+9 more)

### Community 25 - "Character Classes"
Cohesion: 0.12
Nodes (12): story_quest_data.py — 챕터 1~3 스토리 퀘스트 데이터 정의, make_hints_image(), make_story_journal_embed(), make_story_journal_image(), play_cutscene(), story_quest_ui.py — 스토리 퀘스트 Discord UI 컴포넌트 (PIL 이미지 기반), 여러 줄의 텍스트를 render_card rows로 변환하여 이미지 파일로 반환., lines_list: [str, str, ...] 형태의 장면 문자열 목록.     각 장면을 delay 초 간격으로 순서대로 이미지 카드로 전 (+4 more)

### Community 26 - "Crafting System"
Cohesion: 0.12
Nodes (4): utils/ranks.py — 랭크 비교 회귀 테스트.  ``fishing.py``, ``crafting.py``, ``cooking_db.py, TestRankGte, TestRankIndex, TestRankOrdering

### Community 27 - "Collection System"
Cohesion: 0.23
Nodes (5): FishingView, pull_button(), fishing.py — 이프 스타일 낚시 타이밍 게임, stop_button(), wait_button()

### Community 28 - "Diary & Journal"
Cohesion: 0.17
Nodes (10): get_encounter_chance(), special_npc.py — 특수 NPC 랜덤 인카운터 시스템, 특수 NPC 인카운터 등장 이미지를 PIL로 생성합니다., 마지막 인카운터로부터 경과 시간에 따라 인카운터 확률을 반환합니다.     - 0일: 2%     - 1일: 8%     - 2일: 20%, 인카운터 발동 여부를 확률에 따라 결정합니다., render_encounter_image(), should_trigger_encounter(), _get_aff_info() (+2 more)

### Community 29 - "Database Layer"
Cohesion: 0.15
Nodes (5): utils/assets.py — 에셋 무결성 검증 테스트., 레포에 실제 커밋된 필수 에셋이 모두 존재해야 한다., TestRequiredAssetsPresent, TestStaticDirPath, TestVerifyAssetsWithCustomList

### Community 30 - "Discord Cog Framework"
Cohesion: 0.15
Nodes (11): get_cache_stats(), get_cached_item(), get_cached_monster(), get_cached_npc(), get_cached_skill(), cache.py — 성능 최적화를 위한 캐싱 유틸리티  정적 데이터(몬스터 DB, 아이템 DB 등)에 대한 캐싱을 제공합니다. functools, 아이템 데이터를 캐시에서 조회.      Args:         item_id: 아이템 ID      Returns:         아이템 데, 몬스터 데이터를 캐시에서 조회.      Args:         monster_id: 몬스터 ID      Returns:         몬스 (+3 more)

### Community 31 - "NPC Portrait Assets"
Cohesion: 0.24
Nodes (13): Arcane Magic Theme, Dark Forest Setting, Fishing Activity, Game Banner Asset, Gathering Activity, Hunting Activity, Town Location, Underdark Zone (+5 more)

### Community 32 - "Game Banner Assets"
Cohesion: 0.26
Nodes (3): weather.py — 6시간 주기 랜덤 날씨 시스템, 6시간 이상 지났으면 날씨를 교체합니다., WeatherSystem

### Community 33 - "Bot Dependencies"
Cohesion: 0.31
Nodes (10): generate_card(), generate_card_v2(), generate_cooking_card(), generate_fishing_card(), generate_gather_card(), generate_job_card(), generate_rest_card(), generate_smelt_card() (+2 more)

### Community 34 - "Story Quest Legacy"
Cohesion: 0.18
Nodes (4): utils/logger.py — 로거 경로 이식성 테스트., 과거 /home/runner/work/BOT/BOT/logs 하드코딩이 제거되었는지 확인., TestLogDirResolution, TestSetupLogger

### Community 35 - "Cooking & Recipes"
Cohesion: 0.2
Nodes (6): _calc_battle_grade(), 남은 HP 비율에 따라 4단계 전투 등급 반환, apply_size_to_monster(), 사이즈를 가중치 확률로 뽑아 반환합니다., 기본 몬스터 데이터에 사이즈 보정을 적용한 복사본을 반환합니다., roll_monster_size()

### Community 36 - "Social Interactions"
Cohesion: 0.27
Nodes (2): 기여도 추가. (new_total, leveled_up, new_level) 반환., VillageManager

### Community 37 - "Equipment & Costumes"
Cohesion: 0.42
Nodes (9): Animal Portrait Collection, 고양이 초상화 (Cat Portrait), 이상한 소 초상화 (Strange Cow Portrait), NPC / Companion Animal Role, 스크래치 초상화 (Scratch Portrait), Cat (Species), Cow/Bull (Species), Dog (Species) (+1 more)

### Community 38 - "Module Group 38"
Cohesion: 0.29
Nodes (4): BattleEventView, _make_event_view(), 전투 중 이벤트 발생 시 선택지를 버튼으로 제공, 이벤트 선택지 View 생성 (클로저 방식)

### Community 39 - "Module Group 39"
Cohesion: 0.25
Nodes (5): GatherBridge, gather_bridge.py — 채집 결과 통합 브릿지  fishing.py, gathering.py 등에서 채집 완료 시 호출하는 브릿지., 채집/낚시 결과를 Economy를 통해 처리하고 연관 시스템을 호출하는 브릿지., 채집 완료 처리.          Economy를 통해 아이템을 추가하고, village/collection을         try/except, 낚시 완료 처리.          Economy를 통해 물고기를 추가하고, village/weekly_fishing/         collec

### Community 40 - "Module Group 40"
Cohesion: 0.25
Nodes (7): is_valid_rank(), rank_gte(), rank_index(), 생활/전투 스킬 랭크 체계 중앙 관리.  fishing.py, crafting.py, cooking_db.py, potion.py 에서 중복으로, ``rank`` 가 알려진 랭크명인지 여부., 랭크의 정수 인덱스를 반환. 알 수 없는 경우 ``ValueError``., ``current`` 랭크가 ``required`` 랭크 이상인지 확인.      두 값 중 하나라도 알 수 없는 랭크명이면 ``False``

### Community 41 - "Module Group 41"
Cohesion: 0.39
Nodes (8): Mol NPC Character, Rafael NPC Character, Rubato NPC Character, 라파엘 (Rafael) - Full Portrait, 라파엘 (Rafael) - Portrait Thumbnail, 루바토 (Rubato) - Full Portrait, 루바토 (Rubato) - Portrait Thumbnail, 몰 (Mol) - Portrait Thumbnail

### Community 42 - "Module Group 42"
Cohesion: 0.29
Nodes (3): 현재 요리 랭크로 dish_id 조리 가능 여부 확인., 마법 스킬 사용 가능 여부 반환 (bool, message)., SkillManager

### Community 43 - "Module Group 43"
Cohesion: 0.33
Nodes (5): process_all_portraits(), fix_portrait_bg.py — NPC 초상화 흰색/단색 배경 투명화 유틸리티 사용법: python3 fix_portrait_bg.py s, 흰색/밝은 단색 배경을 투명하게 변환., 디렉토리 내 모든 NPC 초상화의 배경 상태를 확인., remove_white_background()

### Community 44 - "Module Group 44"
Cohesion: 0.4
Nodes (4): format_title_effects(), get_title_effects(), title_data.py — 타이틀별 전용 효과 데이터 (업적 난이도 비례), 타이틀 이름으로 효과 딕셔너리 반환. 미등록 타이틀은 빈 딕셔너리.

### Community 45 - "Module Group 45"
Cohesion: 0.33
Nodes (5): is_text_fallback_result(), 렌더링 폴백 유틸리티 (REMEDIATION_PLAN 2-B).  PIL 렌더링은 에셋 누락, 폰트 로딩 실패, 메모리 부족, 손상된 입력 등으, 렌더 함수를 감싸는 데코레이터.      대상 함수가 ``exceptions`` 에 해당하는 오류로 실패하면 ``fallback_fn`` 의, 데코레이터의 반환값이 텍스트 폴백인지 여부를 구분.      Discord 응답 시 ``isinstance(value, (bytes, bytea, with_text_fallback()

### Community 46 - "Module Group 46"
Cohesion: 0.33
Nodes (6): NPC: Arabella (Tiefling Mage), NPC: Damon (Tiefling Blacksmith), NPC: Karnis (Drider Paladin), NPC Character Roster (Revised), NPC: Rubato (Tiefling Bard/Sorcerer), Dev Patch Notes v0.5.1

### Community 47 - "Module Group 47"
Cohesion: 0.53
Nodes (6): NPC Portrait Directory, 실렌 (Silen), 아라벨라 (Arabella), 아라벨라 초상화 (Arabella Portrait Thumbnail), 아울베어 초상화 (Owlbear Portrait), 알피라 초상화 (Alfira Portrait)

### Community 48 - "Module Group 48"
Cohesion: 0.47
Nodes (6): NPC Portrait Group - Chunk 9, 이상한 소 (Strange Cow) NPC Portrait, 제블로어 (Jeblore) NPC Portrait, 카르니스 (Karnis) NPC Full Portrait, 카르니스 (Karnis) NPC Portrait Thumbnail, 카엘릭 (Kaelik) NPC Portrait

### Community 49 - "Module Group 49"
Cohesion: 0.5
Nodes (4): find_missing_assets(), 에셋 무결성 검증 유틸리티.  ``static/`` 아래의 필수 에셋(폰트 등)이 모두 존재하는지 봇 시작 시에 검증해 FileNotFoundE, 필수 에셋이 모두 존재하는지 검증.      Raises:         FileNotFoundError: 하나라도 누락된 경우., verify_assets()

### Community 50 - "Module Group 50"
Cohesion: 0.5
Nodes (4): 로깅 시스템 유틸리티.  모든 모듈에서 일관된 로깅을 제공합니다., 모듈별 로거 생성.      Args:         name: 로거 이름 (일반적으로 모듈 이름)         level: 로그 레벨 (No, _resolve_log_dir(), setup_logger()

### Community 51 - "Module Group 51"
Cohesion: 0.4
Nodes (3): get_player_lock(), utils/player_lock.py — 플레이어별 asyncio.Lock 관리., user_id별 Lock을 반환. 없으면 생성.

### Community 52 - "Module Group 52"
Cohesion: 0.4
Nodes (5): 게일의 환영 (Gale's Apparition), 게일의 환영 초상화 (Gale's Apparition Portrait Thumbnail), 고양이 초상화 (Cat Portrait Thumbnail), 다몬 (Damon), 다몬 초상화 (Damon Portrait Thumbnail)

### Community 53 - "Module Group 53"
Cohesion: 0.4
Nodes (5): 브룩샤 (Bruksha), 브룩샤 초상화 (Bruksha Portrait Thumbnail), 몰 (Mol), 스크래치 초상화 (Scratch Portrait Thumbnail), 실렌 초상화 (Silen Portrait Thumbnail)

### Community 54 - "Module Group 54"
Cohesion: 0.4
Nodes (5): 알피라 (Alpira), 엘레라신 (Ellerasin), 엘리라신 초상화 (Ellirasin Portrait Thumbnail), 오멜룸 (Omellum), 오멜룸 초상화 (Omellum Portrait Thumbnail)

### Community 55 - "Module Group 55"
Cohesion: 1.0
Nodes (4): NPC Portrait Collection, 카엘릭 (Kaelrik), 팅커 벨 (Tinker Bell Portrait), 파울 (Pawl)

### Community 56 - "Module Group 56"
Cohesion: 1.0
Nodes (2): Story Quest Migration Guide, Generation System Design (Mabinogi-inspired)

### Community 57 - "Module Group 57"
Cohesion: 1.0
Nodes (2): Discord Game Bot Code Quality Improvement, requirements.txt Core Dependencies

### Community 58 - "Module Group 58"
Cohesion: 1.0
Nodes (2): bg3_renderer.py Async Renderer, Vision Town Bot UX Improvement Plan

### Community 59 - "Module Group 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Module Group 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Module Group 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Module Group 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Module Group 63"
Cohesion: 1.0
Nodes (1): Player → 저장용 dict (schema_version 포함).

### Community 64 - "Module Group 64"
Cohesion: 1.0
Nodes (1): dict → Player 로드 (마이그레이션 적용 후).

### Community 65 - "Module Group 65"
Cohesion: 1.0
Nodes (1): schema_version을 비교하여 순차적으로 마이그레이션을 적용합니다.          기존 값은 절대 건드리지 않고, 새 필드만 기본값으로

### Community 66 - "Module Group 66"
Cohesion: 1.0
Nodes (1): Lock이 실제로 동시 접근을 차단하는지 검증.

### Community 67 - "Module Group 67"
Cohesion: 1.0
Nodes (1): 서로 다른 user_id의 Lock은 서로 차단하지 않는다.

### Community 68 - "Module Group 68"
Cohesion: 1.0
Nodes (1): Lock이 점유 중일 때 lock.locked()가 True를 반환한다.

### Community 69 - "Module Group 69"
Cohesion: 1.0
Nodes (1): 텍스트에 색상 적용.          Args:             text: 색상을 적용할 텍스트             color: ANSI

### Community 70 - "Module Group 70"
Cohesion: 1.0
Nodes (1): Claude Code Instructions

### Community 71 - "Module Group 71"
Cohesion: 1.0
Nodes (1): Investigate Before Editing Principle

### Community 72 - "Module Group 72"
Cohesion: 1.0
Nodes (1): Git Workflow Guidelines

### Community 73 - "Module Group 73"
Cohesion: 1.0
Nodes (1): Code Quality Guidelines

### Community 74 - "Module Group 74"
Cohesion: 1.0
Nodes (1): NPC: Omeloom (Mind Flayer Herbalist)

### Community 75 - "Module Group 75"
Cohesion: 1.0
Nodes (1): NPC: Mol (Tiefling Merchant)

### Community 76 - "Module Group 76"
Cohesion: 1.0
Nodes (1): NPC: Zevlor (Tiefling Guard Captain)

### Community 77 - "Module Group 77"
Cohesion: 1.0
Nodes (1): NPC: Alfira (Tiefling Bard)

### Community 78 - "Module Group 78"
Cohesion: 1.0
Nodes (1): NPC: Bruksha (Half-orc Chef)

### Community 79 - "Module Group 79"
Cohesion: 1.0
Nodes (1): NPC: Silen (Drow Fisher)

### Community 80 - "Module Group 80"
Cohesion: 1.0
Nodes (1): NPC: Caelik (Dragonborn Instructor)

### Community 81 - "Module Group 81"
Cohesion: 1.0
Nodes (1): NPC: Ellerasin (Half-elf Guild Master)

### Community 82 - "Module Group 82"
Cohesion: 1.0
Nodes (1): NPC: Gale Projection (Wizard Professor)

### Community 83 - "Module Group 83"
Cohesion: 1.0
Nodes (1): NPC: Rafael (Cambion Dealer)

## Knowledge Gaps
- **266 isolated node(s):** `탐험 시작.         Returns dict with keys: 'ok', 'error', 'scenario', 'step_data', '`, `선택지 처리.         Returns dict: 'ok', 'text', 'reward', 'battle', 'next_step_data'`, `NPC 상호작용 처리. action: 'accept'/'refuse'/'trade'/'fight' 등`, `탐험 종료 후 10% 확률로 외부 자극 이벤트`, `D&D 5e 스타일 능력치 체크.         stat: base_stats 키 (str/int/dex/will/luck, 기본값 10)` (+261 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Module Group 56`** (2 nodes): `Story Quest Migration Guide`, `Generation System Design (Mabinogi-inspired)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 57`** (2 nodes): `Discord Game Bot Code Quality Improvement`, `requirements.txt Core Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 58`** (2 nodes): `bg3_renderer.py Async Renderer`, `Vision Town Bot UX Improvement Plan`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 59`** (1 nodes): `adventure_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 60`** (1 nodes): `adventure_npc_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 61`** (1 nodes): `battle_event_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 62`** (1 nodes): `battle_log_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 63`** (1 nodes): `Player → 저장용 dict (schema_version 포함).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 64`** (1 nodes): `dict → Player 로드 (마이그레이션 적용 후).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 65`** (1 nodes): `schema_version을 비교하여 순차적으로 마이그레이션을 적용합니다.          기존 값은 절대 건드리지 않고, 새 필드만 기본값으로`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 66`** (1 nodes): `Lock이 실제로 동시 접근을 차단하는지 검증.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 67`** (1 nodes): `서로 다른 user_id의 Lock은 서로 차단하지 않는다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 68`** (1 nodes): `Lock이 점유 중일 때 lock.locked()가 True를 반환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 69`** (1 nodes): `텍스트에 색상 적용.          Args:             text: 색상을 적용할 텍스트             color: ANSI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 70`** (1 nodes): `Claude Code Instructions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 71`** (1 nodes): `Investigate Before Editing Principle`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 72`** (1 nodes): `Git Workflow Guidelines`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 73`** (1 nodes): `Code Quality Guidelines`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 74`** (1 nodes): `NPC: Omeloom (Mind Flayer Herbalist)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 75`** (1 nodes): `NPC: Mol (Tiefling Merchant)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 76`** (1 nodes): `NPC: Zevlor (Tiefling Guard Captain)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 77`** (1 nodes): `NPC: Alfira (Tiefling Bard)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 78`** (1 nodes): `NPC: Bruksha (Half-orc Chef)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 79`** (1 nodes): `NPC: Silen (Drow Fisher)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 80`** (1 nodes): `NPC: Caelik (Dragonborn Instructor)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 81`** (1 nodes): `NPC: Ellerasin (Half-elf Guild Master)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 82`** (1 nodes): `NPC: Gale Projection (Wizard Professor)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Module Group 83`** (1 nodes): `NPC: Rafael (Cambion Dealer)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `C` connect `Adventure Engine` to `NPC Affinity & Events`, `Social Interactions`, `Achievement System`, `Music Performance`, `BG3 Battle Card Renderer`, `Bulletin Board`, `Life & Fishing Commands`, `Module Group 42`, `Town UI & Banners`, `Town Commands`, `Collection System`, `Diary & Journal`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Player` connect `Config & Core System` to `Adventure Engine`, `Player & Item Tests`, `Cooking & Recipes`, `Battle Engine Tests`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `Economy` connect `Config & Core System` to `Adventure Engine`, `NPC Affinity & Events`, `Collection System`, `Achievement System`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 125 inferred relationships involving `C` (e.g. with `AchievementManager` and `achievements.py — 업적(Achievement) & 타이틀 시스템`) actually correct?**
  _`C` has 125 INFERRED edges - model-reasoned connections that need verification._
- **Are the 74 inferred relationships involving `Player` (e.g. with `BattleEngine` and `남은 HP 비율에 따라 4단계 전투 등급 반환`) actually correct?**
  _`Player` has 74 INFERRED edges - model-reasoned connections that need verification._
- **Are the 65 inferred relationships involving `Economy` (e.g. with `Player` and `InsufficientResourceError`) actually correct?**
  _`Economy` has 65 INFERRED edges - model-reasoned connections that need verification._
- **What connects `탐험 시작.         Returns dict with keys: 'ok', 'error', 'scenario', 'step_data', '`, `선택지 처리.         Returns dict: 'ok', 'text', 'reward', 'battle', 'next_step_data'`, `NPC 상호작용 처리. action: 'accept'/'refuse'/'trade'/'fight' 등` to the rest of the system?**
  _266 weakly-connected nodes found - possible documentation gaps or missing edges._