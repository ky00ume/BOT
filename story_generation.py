"""story_generation.py — 제네레이션 시스템 프레임워크

마비노기 스타일의 Generation(세대) 기반 스토리 확장 시스템.
기존 story_quest.py를 확장하여 무한히 확장 가능한 스토리 구조를 제공합니다.

구조:
    Generation (G1, G2, ...)
      └─ Chapter (챕터 1, 2, 3, ...)
           └─ Quest (퀘스트 1, 2, 3, ...)

사용 예시:
    >>> gen_mgr = GenerationManager(player)
    >>> current = gen_mgr.get_current_generation()
    >>> print(f"G{current.id}: {current.title}")
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class QuestType(Enum):
    """퀘스트 타입"""
    DIALOGUE = "dialogue"       # NPC 대화
    COLLECT = "collect"         # 아이템 수집
    BATTLE = "battle"           # 전투
    CUTSCENE = "cutscene"       # 컷씬
    CHOICE = "choice"           # 선택지
    EXPLORE = "explore"         # 탐색
    DELIVER = "deliver"         # 전달


class GenerationStatus(Enum):
    """제네레이션 상태"""
    LOCKED = "locked"           # 잠김 (조건 미달)
    AVAILABLE = "available"     # 시작 가능
    IN_PROGRESS = "in_progress" # 진행 중
    COMPLETED = "completed"     # 완료


@dataclass
class QuestReward:
    """퀘스트 보상"""
    gold: int = 0
    exp: int = 0
    items: Dict[str, int] = field(default_factory=dict)
    affinity: Dict[str, int] = field(default_factory=dict)
    title: Optional[str] = None
    stat_changes: Dict[str, int] = field(default_factory=dict)  # shadow_sync 등


@dataclass
class StoryQuest:
    """스토리 퀘스트 데이터"""
    id: str                                    # 고유 ID (예: "g1_ch1_q1")
    title: str                                 # 퀘스트 제목
    quest_type: QuestType                      # 퀘스트 타입
    description: str = ""                      # 설명

    # NPC 관련
    npc: Optional[str | List[str]] = None      # NPC 이름(들)
    dialogue: Optional[str | Dict[str, str]] = None  # 대사

    # 조건
    prerequisites: List[str] = field(default_factory=list)  # 선행 퀘스트 ID
    unlock_level: int = 1                      # 최소 레벨
    unlock_stats: Dict[str, int] = field(default_factory=dict)  # 스탯 요구사항

    # 목표 (타입별)
    target_item: Optional[str] = None          # 수집 아이템
    target_count: int = 0                      # 수집/처치 개수
    target_zone: Optional[str] = None          # 전투 구역
    deliver_to: Optional[str] = None           # 전달 대상

    # 선택지
    choices: Optional[Dict[str, Any]] = None   # 선택지 데이터
    choice_effects: Optional[Dict[str, Any]] = None  # 선택 효과

    # 보상
    rewards: QuestReward = field(default_factory=QuestReward)

    # 힌트 시스템
    hint: Optional[str] = None                 # 수집 가능한 힌트

    # 완료 시 효과
    on_complete: Optional[Callable] = None     # 완료 시 실행 함수
    world_changes: Dict[str, Any] = field(default_factory=dict)  # 세계 변화

    # 기타
    cutscene_data: Optional[Dict[str, Any]] = None  # 컷씬 데이터
    battle_data: Optional[Dict[str, Any]] = None    # 전투 데이터
    explore_steps: int = 0                     # 탐색 단계 수


@dataclass
class Chapter:
    """챕터 - 하나의 큰 스토리 단위"""
    id: int                                    # 챕터 번호
    generation_id: int                         # 소속 제네레이션
    title: str                                 # 챕터 제목
    subtitle: str = ""                         # 부제
    description: str = ""                      # 설명

    # 퀘스트
    quests: Dict[int, StoryQuest] = field(default_factory=dict)

    # 진행 조건
    unlock_level: int = 1                      # 최소 레벨
    unlock_condition: Optional[Callable] = None  # 커스텀 조건 함수

    # 테마
    theme_color: int = 0xf5deb3               # 임베드 색상
    theme_time: Optional[str] = None          # "day" or "night"

    # 보상
    completion_rewards: QuestReward = field(default_factory=QuestReward)

    def get_max_quest(self) -> int:
        """챕터 내 최대 퀘스트 번호"""
        return max(self.quests.keys()) if self.quests else 0

    def get_quest(self, quest_num: int) -> Optional[StoryQuest]:
        """특정 퀘스트 조회"""
        return self.quests.get(quest_num)


@dataclass
class Generation:
    """제네레이션 - 하나의 완결된 스토리 세대"""
    id: int                                    # 제네레이션 번호 (1, 2, 3, ...)
    title: str                                 # 제목
    subtitle: str                              # 부제 (영문)
    description: str                           # 세대 설명
    icon: str = "📖"                           # 아이콘

    # 챕터
    chapters: Dict[int, Chapter] = field(default_factory=dict)

    # 진행 조건
    unlock_level: int = 1                      # 최소 레벨
    required_generations: List[int] = field(default_factory=list)  # 선행 Gen

    # 세대별 고유 시스템
    special_stats: Dict[str, int] = field(default_factory=dict)  # shadow_sync 등
    special_mechanics: List[str] = field(default_factory=list)   # 특수 메커니즘

    # 보상
    completion_rewards: QuestReward = field(default_factory=QuestReward)
    completion_title: Optional[str] = None     # 완료 칭호
    achievements: List[str] = field(default_factory=list)  # 업적

    def get_max_chapter(self) -> int:
        """제네레이션 내 최대 챕터 번호"""
        return max(self.chapters.keys()) if self.chapters else 0

    def get_chapter(self, chapter_num: int) -> Optional[Chapter]:
        """특정 챕터 조회"""
        return self.chapters.get(chapter_num)


class GenerationManager:
    """제네레이션 진행 관리자"""

    def __init__(self, player):
        self.player = player
        self.generations: Dict[int, Generation] = {}
        self.current_generation_id: int = 1
        self.current_chapter: int = 1
        self.current_quest: int = 1

        # 세대별 진행 상태
        self.generation_progress: Dict[int, Dict[str, Any]] = {}

        # 히든 스탯 (세대별)
        self.stats: Dict[int, Dict[str, int]] = {}

    def register_generation(self, generation: Generation) -> None:
        """제네레이션 등록"""
        self.generations[generation.id] = generation

        # 진행 상태 초기화
        if generation.id not in self.generation_progress:
            self.generation_progress[generation.id] = {
                "status": GenerationStatus.LOCKED,
                "chapter": 1,
                "quest": 1,
                "completed_quests": [],
                "hints": [],
                "flags": {},
            }

        # 특수 스탯 초기화
        if generation.id not in self.stats:
            self.stats[generation.id] = dict(generation.special_stats)

    def get_generation(self, gen_id: int) -> Optional[Generation]:
        """제네레이션 조회"""
        return self.generations.get(gen_id)

    def get_current_generation(self) -> Optional[Generation]:
        """현재 진행 중인 제네레이션"""
        return self.get_generation(self.current_generation_id)

    def is_generation_unlocked(self, gen_id: int) -> bool:
        """제네레이션 해금 여부 확인"""
        gen = self.get_generation(gen_id)
        if not gen:
            return False

        # 레벨 체크
        if self.player.level < gen.unlock_level:
            return False

        # 선행 제네레이션 체크
        for req_gen in gen.required_generations:
            if not self.is_generation_completed(req_gen):
                return False

        return True

    def is_generation_completed(self, gen_id: int) -> bool:
        """제네레이션 완료 여부"""
        progress = self.generation_progress.get(gen_id)
        if not progress:
            return False
        return progress["status"] == GenerationStatus.COMPLETED

    def get_current_quest(self) -> Optional[StoryQuest]:
        """현재 진행 중인 퀘스트"""
        gen = self.get_current_generation()
        if not gen:
            return None

        progress = self.generation_progress[gen.id]
        chapter = gen.get_chapter(progress["chapter"])
        if not chapter:
            return None

        return chapter.get_quest(progress["quest"])

    def complete_quest(self, gen_id: int, chapter_num: int, quest_num: int) -> None:
        """퀘스트 완료 처리"""
        progress = self.generation_progress.get(gen_id)
        if not progress:
            return

        quest_id = f"g{gen_id}_ch{chapter_num}_q{quest_num}"
        if quest_id not in progress["completed_quests"]:
            progress["completed_quests"].append(quest_id)

    def is_quest_completed(self, gen_id: int, chapter_num: int, quest_num: int) -> bool:
        """퀘스트 완료 여부"""
        progress = self.generation_progress.get(gen_id)
        if not progress:
            return False

        quest_id = f"g{gen_id}_ch{chapter_num}_q{quest_num}"
        return quest_id in progress["completed_quests"]

    def add_hint(self, gen_id: int, hint: str) -> None:
        """힌트 추가"""
        progress = self.generation_progress.get(gen_id)
        if progress and hint not in progress["hints"]:
            progress["hints"].append(hint)

    def set_flag(self, gen_id: int, flag_name: str, value: Any) -> None:
        """플래그 설정"""
        progress = self.generation_progress.get(gen_id)
        if progress:
            progress["flags"][flag_name] = value

    def get_flag(self, gen_id: int, flag_name: str, default: Any = None) -> Any:
        """플래그 조회"""
        progress = self.generation_progress.get(gen_id)
        if not progress:
            return default
        return progress["flags"].get(flag_name, default)

    def modify_stat(self, gen_id: int, stat_name: str, delta: int) -> None:
        """히든 스탯 변경"""
        if gen_id not in self.stats:
            self.stats[gen_id] = {}

        current = self.stats[gen_id].get(stat_name, 0)
        self.stats[gen_id][stat_name] = max(-100, min(100, current + delta))

    def get_stat(self, gen_id: int, stat_name: str, default: int = 0) -> int:
        """히든 스탯 조회"""
        if gen_id not in self.stats:
            return default
        return self.stats[gen_id].get(stat_name, default)

    def to_dict(self) -> Dict[str, Any]:
        """직렬화 (세이브)"""
        return {
            "current_generation_id": self.current_generation_id,
            "generation_progress": {
                gen_id: {
                    "status": progress["status"].value,
                    "chapter": progress["chapter"],
                    "quest": progress["quest"],
                    "completed_quests": progress["completed_quests"],
                    "hints": progress["hints"],
                    "flags": progress["flags"],
                }
                for gen_id, progress in self.generation_progress.items()
            },
            "stats": self.stats,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """역직렬화 (로드)"""
        self.current_generation_id = data.get("current_generation_id", 1)

        progress_data = data.get("generation_progress", {})
        for gen_id_str, progress in progress_data.items():
            gen_id = int(gen_id_str)
            self.generation_progress[gen_id] = {
                "status": GenerationStatus(progress["status"]),
                "chapter": progress["chapter"],
                "quest": progress["quest"],
                "completed_quests": progress["completed_quests"],
                "hints": progress["hints"],
                "flags": progress["flags"],
            }

        self.stats = data.get("stats", {})
        # Convert string keys to int
        self.stats = {int(k): v for k, v in self.stats.items()}


# ═══════════════════════════════════════════════════════════════════════════
# 유틸리티 함수
# ═══════════════════════════════════════════════════════════════════════════

def create_quest(
    quest_id: str,
    title: str,
    quest_type: QuestType,
    **kwargs
) -> StoryQuest:
    """퀘스트 생성 헬퍼 함수"""
    return StoryQuest(
        id=quest_id,
        title=title,
        quest_type=quest_type,
        **kwargs
    )


def create_chapter(
    chapter_id: int,
    generation_id: int,
    title: str,
    quests: Dict[int, StoryQuest],
    **kwargs
) -> Chapter:
    """챕터 생성 헬퍼 함수"""
    return Chapter(
        id=chapter_id,
        generation_id=generation_id,
        title=title,
        quests=quests,
        **kwargs
    )


def create_generation(
    gen_id: int,
    title: str,
    subtitle: str,
    description: str,
    chapters: Dict[int, Chapter],
    **kwargs
) -> Generation:
    """제네레이션 생성 헬퍼 함수"""
    return Generation(
        id=gen_id,
        title=title,
        subtitle=subtitle,
        description=description,
        chapters=chapters,
        **kwargs
    )
