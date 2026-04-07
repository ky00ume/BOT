"""생활/전투 스킬 랭크 체계 중앙 관리.

fishing.py, crafting.py, cooking_db.py, potion.py 에서 중복으로
정의하던 `_rank_gte` 로직을 단일 진실 소스로 통합한다.

랭크 순서는 게임 전반에 걸쳐 사용되는 다음과 같다::

    연습 < F < E < D < C < B < A < 9 < 8 < 7 < 6 < 5 < 4 < 3 < 2 < 1

랭크가 높아질수록 리스트 인덱스가 커지므로 ``>=`` 비교가 곧 "이상" 관계를
나타낸다.
"""

from __future__ import annotations

from typing import List, Tuple


RANK_ORDER: Tuple[str, ...] = (
    "연습", "F", "E", "D", "C", "B", "A",
    "9", "8", "7", "6", "5", "4", "3", "2", "1",
)

# 외부에서 반복 가능한 리스트 형태도 제공 (기존 코드와의 호환용).
RANK_ORDER_LIST: List[str] = list(RANK_ORDER)

_RANK_INDEX = {name: idx for idx, name in enumerate(RANK_ORDER)}


def is_valid_rank(rank: str) -> bool:
    """``rank`` 가 알려진 랭크명인지 여부."""
    return rank in _RANK_INDEX


def rank_index(rank: str) -> int:
    """랭크의 정수 인덱스를 반환. 알 수 없는 경우 ``ValueError``."""
    try:
        return _RANK_INDEX[rank]
    except KeyError as exc:
        raise ValueError(f"알 수 없는 랭크: {rank!r}") from exc


def rank_gte(current: str, required: str) -> bool:
    """``current`` 랭크가 ``required`` 랭크 이상인지 확인.

    두 값 중 하나라도 알 수 없는 랭크명이면 ``False`` 를 반환한다.
    기존 `_rank_gte` 구현과 동일한 동작을 보장하여 호출부 수정 시
    회귀가 발생하지 않도록 한다.
    """
    if current not in _RANK_INDEX or required not in _RANK_INDEX:
        return False
    return _RANK_INDEX[current] >= _RANK_INDEX[required]
