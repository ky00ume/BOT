"""generations/g1_darkness_light.py — G1: 어둠 속의 빛

현재 story_quest_data.py의 챕터 1~3을 제네레이션 시스템으로 마이그레이션한 버전.

스토리 개요:
  드라이더 츄라이더가 '그림자 등불'의 비밀을 추적하며
  빛과 어둠, 희생과 구원 사이에서 선택하는 이야기.

주요 메커니즘:
  - shadow_sync: 빛(-100)과 어둠(+100) 사이의 성향 수치
  - 선택지 분기: 플레이어의 선택이 shadow_sync에 영향
  - 힌트 수집: 스토리 진행에 따라 힌트 수집
"""
from story_generation import (
    Generation, Chapter, StoryQuest, QuestType, QuestReward,
    create_quest, create_chapter, create_generation
)

# ═══════════════════════════════════════════════════════════════════════════
# 챕터 1: 마을 사람들이 말하는 것
# ═══════════════════════════════════════════════════════════════════════════

G1_CH1_QUESTS = {
    1: create_quest(
        quest_id="g1_ch1_q1",
        title="대장장이의 경고",
        quest_type=QuestType.DIALOGUE,
        npc="다몬",
        dialogue=(
            "(망치질을 멈추고 허리를 숙여 아래를 내려다보며) 오, 조심하렴. 하마터면 밟을 "
            "뻔했구나. ...그림자 등불이라고? 그건 철을 두드려 만들 수 있는 게 아니란다. "
            "빛을 만드는 게 아니라 어둠을 담는 그릇이지. 누가 만들었는지는 모르겠지만, "
            "그건 제련된 물건이라기보다... 누군가의 '집착'이 굳은 결정체에 가깝단다."
        ),
        hint="빛이 아니라 어둠을 담는 것",
        rewards=QuestReward(affinity={"다몬": 2}),
    ),
    2: create_quest(
        quest_id="g1_ch1_q2",
        title="약초상의 분석",
        quest_type=QuestType.DIALOGUE,
        npc="오멜룸",
        dialogue=(
            "작은 드라이더로군요. 당신의 생물학적 기원을 생각하면 그 물건에 끌리는 것도 "
            "무리는 아닙니다. 하지만 경고하죠. 그 등불의 동력원은 '비윤리적'입니다. "
            "살아있는 빛(픽시)을 가두고 그 고통을 증폭시켜 어둠을 몰아내는 방식이니까요. "
            "죽어있는데도 빛을 내는 것... 그것이 그 등불이 가진 잔인한 모순입니다."
        ),
        hint="안에 뭔가 잔인하게 갇혀 있다",
        rewards=QuestReward(affinity={"오멜룸": 2}),
    ),
    3: create_quest(
        quest_id="g1_ch1_q3",
        title="상인의 충고",
        quest_type=QuestType.DIALOGUE,
        npc="몰",
        dialogue=(
            "야, 꼬맹이! 그 위험한 물건 얘긴 어디서 들었어? 그건 시장에서 파는 물건이 아냐. "
            "'찾는' 게 아니라 그 물건이 너를 '선택'하게 만들어야지. 뭐, 지금 네 실력으론 "
            "어림없겠지만. 일단 살아남는 법부터 배워와. 죽은 거미는 등불을 들 수 없으니까, "
            "안 그래?"
        ),
        hint="찾는 것이 아니라 도달하는 것",
        rewards=QuestReward(affinity={"몰": 1}),
    ),
    4: create_quest(
        quest_id="g1_ch1_q4",
        title="그림자와의 공명",
        quest_type=QuestType.CHOICE,
        description="내면의 독백. 선택의 순간.",
        choices={
            "dark": {
                "label": "그래, 어둠이 내 본질이다.",
                "shadow_sync": +15,
                "style": "red"
            },
            "neutral": {
                "label": "아직 모르겠어. 더 알아봐야 해.",
                "shadow_sync": 0,
                "style": "yellow"
            },
            "light": {
                "label": "아니, 빛에도 다른 방법이 있을 거야.",
                "shadow_sync": -15,
                "style": "blurple"
            },
        },
        rewards=QuestReward(
            items={"sq_moonlantern_fragment": 1},
            title="귀를 기울인 자"
        ),
    ),
}

G1_CHAPTER_1 = create_chapter(
    chapter_id=1,
    generation_id=1,
    title="마을 사람들이 말하는 것",
    subtitle="What the Villagers Say",
    description="등불의 소문을 추적한다.",
    quests=G1_CH1_QUESTS,
    theme_color=0x2c1e3d,
    unlock_level=1,
)

# ═══════════════════════════════════════════════════════════════════════════
# 챕터 2: 픽시의 흔적
# ═══════════════════════════════════════════════════════════════════════════

G1_CH2_QUESTS = {
    1: create_quest(
        quest_id="g1_ch2_q1",
        title="마법적 조언",
        quest_type=QuestType.DIALOGUE,
        npc="게일의 환영",
        dialogue=(
            "흥미로운 파편이군요. 이건 단순한 유물이 아니에요. '문랜턴(Moon Lantern)'의 "
            "파편입니다. 그림자 저주를 막기 위해 제작된 물건이지요. 하지만 이 등불은 마력이 "
            "아니라 살아있는 요정, 즉 픽시를 동력원으로 사용합니다. 오멜룸을 찾아가 "
            "보세요. 그 분야에 대해 나보다 실용적인 조언을 해줄 거예요."
        ),
        hint="문랜턴은 그림자 저주의 방패",
    ),
    # ... 나머지 퀘스트는 기존 story_quest_data.py 참조
}

G1_CHAPTER_2 = create_chapter(
    chapter_id=2,
    generation_id=1,
    title="픽시의 흔적",
    subtitle="Traces of the Pixie",
    description="갇힌 요정의 흔적을 찾아 나선다.",
    quests=G1_CH2_QUESTS,
    theme_color=0x4a2c5e,
    unlock_level=3,
)

# ═══════════════════════════════════════════════════════════════════════════
# 챕터 3: 선택의 무게
# ═══════════════════════════════════════════════════════════════════════════

G1_CH3_QUESTS = {
    # ... story_quest_data.py 참조
}

G1_CHAPTER_3 = create_chapter(
    chapter_id=3,
    generation_id=1,
    title="선택의 무게",
    subtitle="The Weight of Choice",
    description="살아있는 빛을 찾아 늪지대로 향한다.",
    quests=G1_CH3_QUESTS,
    theme_color=0x1a0033,
    unlock_level=5,
)

# ═══════════════════════════════════════════════════════════════════════════
# G1: 어둠 속의 빛
# ═══════════════════════════════════════════════════════════════════════════

G1_GENERATION = create_generation(
    gen_id=1,
    title="어둠 속의 빛",
    subtitle="The Light in Darkness",
    description=(
        "그림자 등불의 비밀을 추적하는 첫 번째 이야기. "
        "작은 드라이더 츄라이더는 빛과 어둠 사이에서 선택해야 한다."
    ),
    icon="🕯️",
    chapters={
        1: G1_CHAPTER_1,
        2: G1_CHAPTER_2,
        3: G1_CHAPTER_3,
    },
    unlock_level=1,
    special_stats={"shadow_sync": 0},
    completion_title="등불을 찾은 자",
    achievements=[
        "모든 힌트 수집",
        "선택의 길 (빛/어둠/중립)",
        "완벽한 추적자",
    ],
)


# ═══════════════════════════════════════════════════════════════════════════
# 호환성 함수 (기존 코드와의 호환을 위해)
# ═══════════════════════════════════════════════════════════════════════════

def get_legacy_chapter_data(chapter_num: int):
    """
    기존 story_quest_data.py 형식으로 챕터 데이터 반환.
    레거시 코드 호환용.
    """
    chapter = G1_GENERATION.get_chapter(chapter_num)
    if not chapter:
        return None

    # 기존 형식으로 변환
    legacy_quests = {}
    for q_num, quest in chapter.quests.items():
        legacy_quests[q_num] = {
            "title": quest.title,
            "npc": quest.npc,
            "dialogue": quest.dialogue,
            "hint": quest.hint,
            "rewards": {
                "affinity": quest.rewards.affinity,
                "items": quest.rewards.items,
            },
            "choices": quest.choices,
            # ... 기타 필드
        }

    return {
        "title": chapter.title,
        "quests": legacy_quests,
        "max_quest": chapter.get_max_quest(),
    }
