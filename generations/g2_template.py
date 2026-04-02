"""generations/g2_template.py — G2: 템플릿

새로운 제네레이션 작성 템플릿.
이 파일을 복사하여 G2, G3 등을 만들 수 있습니다.

작성 가이드:
1. 제네레이션 기본 정보 작성 (제목, 부제, 설명)
2. 각 챕터의 퀘스트 작성
3. 챕터 생성
4. 제네레이션 통합
"""
from story_generation import (
    Generation, Chapter, StoryQuest, QuestType, QuestReward,
    create_quest, create_chapter, create_generation
)

# ═══════════════════════════════════════════════════════════════════════════
# 챕터 1: [챕터 제목]
# ═══════════════════════════════════════════════════════════════════════════

G2_CH1_QUESTS = {
    1: create_quest(
        quest_id="g2_ch1_q1",
        title="[퀘스트 제목]",
        quest_type=QuestType.DIALOGUE,
        npc="[NPC 이름]",
        dialogue="[대사 내용]",
        hint="[힌트 내용]",
        rewards=QuestReward(
            gold=100,
            exp=50,
            affinity={"[NPC]": 2},
        ),
    ),
    # 퀘스트 2, 3, 4 ...
}

G2_CHAPTER_1 = create_chapter(
    chapter_id=1,
    generation_id=2,
    title="[챕터 제목]",
    subtitle="[Chapter Subtitle]",
    description="[챕터 설명]",
    quests=G2_CH1_QUESTS,
    theme_color=0x3366ff,  # 원하는 색상
    unlock_level=10,  # 필요 레벨
)

# ═══════════════════════════════════════════════════════════════════════════
# 챕터 2, 3, 4 ...
# ═══════════════════════════════════════════════════════════════════════════

# ... 추가 챕터 작성

# ═══════════════════════════════════════════════════════════════════════════
# G2: [제네레이션 제목]
# ═══════════════════════════════════════════════════════════════════════════

G2_GENERATION = create_generation(
    gen_id=2,
    title="[제네레이션 제목]",
    subtitle="[Generation Subtitle]",
    description="[제네레이션 설명]",
    icon="🎭",  # 원하는 아이콘
    chapters={
        1: G2_CHAPTER_1,
        # 2: G2_CHAPTER_2,
        # 3: G2_CHAPTER_3,
    },
    unlock_level=10,
    required_generations=[1],  # G1 완료 필요
    special_stats={
        # "trust": 0,
        # "karma": 0,
    },
    completion_title="[완료 칭호]",
    achievements=[
        "[업적 1]",
        "[업적 2]",
    ],
)


# ═══════════════════════════════════════════════════════════════════════════
# 사용 예시
# ═══════════════════════════════════════════════════════════════════════════

"""
# main.py 또는 초기화 코드에서:

from generations import register_generation
from generations.g2_template import G2_GENERATION

register_generation(G2_GENERATION)

# GenerationManager에 등록
gen_mgr.register_generation(G2_GENERATION)
"""
