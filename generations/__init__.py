"""generations/__init__.py — 제네레이션 데이터 패키지

각 제네레이션별 스토리 데이터를 관리합니다.
"""
from typing import Dict
from story_generation import Generation

# 제네레이션 레지스트리
GENERATIONS: Dict[int, Generation] = {}


def register_generation(generation: Generation) -> None:
    """제네레이션 등록"""
    GENERATIONS[generation.id] = generation


def get_generation(gen_id: int) -> Generation:
    """제네레이션 조회"""
    return GENERATIONS.get(gen_id)


def get_all_generations() -> Dict[int, Generation]:
    """모든 제네레이션 조회"""
    return GENERATIONS


# 제네레이션 자동 로드
try:
    from .g1_darkness_light import G1_GENERATION
    register_generation(G1_GENERATION)
except ImportError:
    pass

try:
    from .g2_template import G2_GENERATION
    register_generation(G2_GENERATION)
except ImportError:
    pass
