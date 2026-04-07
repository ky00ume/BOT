"""utils/validators.py — 사용자 입력 검증 테스트."""

import pytest

from utils.validators import (
    MAX_NAME_LENGTH,
    MAX_RENDER_TEXT_LENGTH,
    ValidationError,
    truncate_for_render,
    validate_count,
    validate_item_id,
    validate_message,
    validate_player_name,
)


class TestValidatePlayerName:
    def test_accepts_korean_name(self):
        assert validate_player_name("하이네스") == "하이네스"

    def test_accepts_english_and_numbers(self):
        assert validate_player_name("Hero123") == "Hero123"

    def test_strips_whitespace(self):
        assert validate_player_name("  붉은바람  ") == "붉은바람"

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            validate_player_name("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValidationError):
            validate_player_name("   ")

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            validate_player_name(None)

    def test_rejects_overly_long(self):
        with pytest.raises(ValidationError):
            validate_player_name("가" * (MAX_NAME_LENGTH + 1))

    def test_rejects_control_chars(self):
        with pytest.raises(ValidationError):
            validate_player_name("abc\x00def")


class TestValidateItemId:
    def test_accepts_valid(self):
        assert validate_item_id("iron_bar") == "iron_bar"
        assert validate_item_id("fs_tuna_01") == "fs_tuna_01"

    @pytest.mark.parametrize(
        "bad",
        ["", "Invalid", "item id", "아이템", "item-id", None],
    )
    def test_rejects_invalid(self, bad):
        with pytest.raises(ValidationError):
            validate_item_id(bad)  # type: ignore[arg-type]


class TestValidateCount:
    def test_accepts_one(self):
        assert validate_count(1) == 1

    def test_accepts_max(self):
        assert validate_count(9999) == 9999

    def test_rejects_zero_by_default(self):
        with pytest.raises(ValidationError):
            validate_count(0)

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            validate_count(-1)

    def test_rejects_too_large(self):
        with pytest.raises(ValidationError):
            validate_count(10_000)

    def test_rejects_float(self):
        with pytest.raises(ValidationError):
            validate_count(3.5)  # type: ignore[arg-type]

    def test_rejects_bool(self):
        with pytest.raises(ValidationError):
            validate_count(True)  # type: ignore[arg-type]

    def test_respects_custom_bounds(self):
        assert validate_count(0, min_val=0, max_val=10) == 0


class TestValidateMessage:
    def test_accepts_normal_message(self):
        assert validate_message("안녕하세요!") == "안녕하세요!"

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            validate_message("")

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            validate_message(None)

    def test_rejects_too_long(self):
        with pytest.raises(ValidationError):
            validate_message("a" * 5000)


class TestTruncateForRender:
    def test_keeps_short_text(self):
        assert truncate_for_render("hi") == "hi"

    def test_truncates_long_text(self):
        long = "x" * (MAX_RENDER_TEXT_LENGTH + 50)
        result = truncate_for_render(long)
        assert len(result) == MAX_RENDER_TEXT_LENGTH
        assert result.endswith("...")

    def test_non_string_input_coerced(self):
        assert truncate_for_render(42) == "42"

    def test_none_becomes_empty(self):
        assert truncate_for_render(None) == ""

    def test_custom_max_len(self):
        assert truncate_for_render("abcdefghij", max_len=5) == "ab..."
