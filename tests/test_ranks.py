"""utils/ranks.py — 랭크 비교 회귀 테스트.

``fishing.py``, ``crafting.py``, ``cooking_db.py``, ``potion.py`` 에서
복제되었던 ``_rank_gte`` 로직이 단일 구현으로 통합되었음을 검증한다.
"""

import pytest

from utils.ranks import (
    RANK_ORDER,
    is_valid_rank,
    rank_gte,
    rank_index,
)


class TestRankOrdering:
    def test_rank_order_starts_with_practice(self):
        assert RANK_ORDER[0] == "연습"

    def test_rank_order_ends_with_one(self):
        assert RANK_ORDER[-1] == "1"

    def test_rank_order_is_unique(self):
        assert len(set(RANK_ORDER)) == len(RANK_ORDER)

    def test_rank_order_length(self):
        # 연습 + F~A + 9~1 = 16
        assert len(RANK_ORDER) == 16


class TestRankGte:
    def test_equal_ranks_return_true(self):
        assert rank_gte("연습", "연습") is True
        assert rank_gte("A", "A") is True
        assert rank_gte("1", "1") is True

    def test_higher_rank_is_gte(self):
        assert rank_gte("C", "F") is True
        assert rank_gte("1", "연습") is True
        assert rank_gte("A", "B") is True

    def test_lower_rank_is_not_gte(self):
        assert rank_gte("연습", "1") is False
        assert rank_gte("F", "C") is False
        assert rank_gte("B", "A") is False

    def test_unknown_rank_returns_false(self):
        # 과거 `_rank_gte` 구현과 동일: 알 수 없는 랭크는 False.
        assert rank_gte("bogus", "F") is False
        assert rank_gte("F", "bogus") is False
        assert rank_gte("", "") is False

    @pytest.mark.parametrize(
        "current,required,expected",
        [
            ("연습", "연습", True),
            ("F", "연습", True),
            ("E", "F", True),
            ("A", "9", False),  # 9는 A보다 높음
            ("9", "A", True),
            ("2", "3", True),
            ("3", "2", False),
        ],
    )
    def test_parametrized_comparisons(self, current, required, expected):
        assert rank_gte(current, required) is expected


class TestRankIndex:
    def test_index_known_rank(self):
        assert rank_index("연습") == 0
        assert rank_index("1") == len(RANK_ORDER) - 1

    def test_index_unknown_rank_raises(self):
        with pytest.raises(ValueError):
            rank_index("bogus")

    def test_is_valid_rank(self):
        assert is_valid_rank("A") is True
        assert is_valid_rank("연습") is True
        assert is_valid_rank("bogus") is False
