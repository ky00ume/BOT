"""cache.py — 성능 최적화를 위한 캐싱 유틸리티

정적 데이터(몬스터 DB, 아이템 DB 등)에 대한 캐싱을 제공합니다.
functools.lru_cache를 활용하여 반복적인 계산과 데이터 접근을 최적화합니다.
"""
from functools import lru_cache
from typing import Dict, Any, Optional


@lru_cache(maxsize=128)
def get_cached_item(item_id: str) -> Optional[Dict[str, Any]]:
    """아이템 데이터를 캐시에서 조회.

    Args:
        item_id: 아이템 ID

    Returns:
        아이템 데이터 딕셔너리, 없으면 None
    """
    from items import ALL_ITEMS
    return ALL_ITEMS.get(item_id)


@lru_cache(maxsize=64)
def get_cached_monster(monster_id: str) -> Optional[Dict[str, Any]]:
    """몬스터 데이터를 캐시에서 조회.

    Args:
        monster_id: 몬스터 ID

    Returns:
        몬스터 데이터 딕셔너리, 없으면 None
    """
    from monsters_db import MONSTERS_DB
    for zone_data in MONSTERS_DB.values():
        for monster in zone_data.get("monsters", []):
            if monster.get("id") == monster_id:
                return monster
    return None


@lru_cache(maxsize=32)
def get_cached_npc(npc_name: str) -> Optional[Dict[str, Any]]:
    """NPC 데이터를 캐시에서 조회.

    Args:
        npc_name: NPC 이름

    Returns:
        NPC 데이터 딕셔너리, 없으면 None
    """
    from database import NPC_DATA
    return NPC_DATA.get(npc_name)


@lru_cache(maxsize=16)
def get_cached_skill(skill_id: str, skill_type: str = "combat") -> Optional[Dict[str, Any]]:
    """스킬 데이터를 캐시에서 조회.

    Args:
        skill_id: 스킬 ID
        skill_type: 스킬 타입 ("combat" 또는 "magic")

    Returns:
        스킬 데이터 딕셔너리, 없으면 None
    """
    from skills_db import COMBAT_SKILLS, MAGIC_SKILLS
    if skill_type == "combat":
        return COMBAT_SKILLS.get(skill_id)
    elif skill_type == "magic":
        return MAGIC_SKILLS.get(skill_id)
    return None


def clear_all_caches() -> None:
    """모든 캐시 클리어."""
    get_cached_item.cache_clear()
    get_cached_monster.cache_clear()
    get_cached_npc.cache_clear()
    get_cached_skill.cache_clear()


def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 정보 조회.

    Returns:
        각 캐시의 히트/미스 정보
    """
    return {
        "item_cache": get_cached_item.cache_info()._asdict(),
        "monster_cache": get_cached_monster.cache_info()._asdict(),
        "npc_cache": get_cached_npc.cache_info()._asdict(),
        "skill_cache": get_cached_skill.cache_info()._asdict(),
    }
