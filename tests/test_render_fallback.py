"""utils/render_fallback.py — 렌더링 폴백 데코레이터 테스트 (2-B)."""

import io
import logging

import pytest

from utils.render_fallback import (
    DEFAULT_RENDER_EXCEPTIONS,
    is_text_fallback_result,
    with_text_fallback,
)


def _fallback(name: str, **kwargs) -> str:
    extras = ",".join(f"{k}={v}" for k, v in kwargs.items())
    return f"[TEXT] {name}" + (f" ({extras})" if extras else "")


class TestSuccessPath:
    def test_returns_original_result_when_no_exception(self):
        @with_text_fallback(_fallback)
        def render(name, **_):
            return b"\x89PNG"
        assert render("hero") == b"\x89PNG"

    def test_preserves_function_metadata(self):
        @with_text_fallback(_fallback)
        def render_status_card(name, **_):
            return b"x"
        assert render_status_card.__name__ == "render_status_card"


class TestFallbackPath:
    @pytest.mark.parametrize("exc", [OSError("font missing"),
                                     MemoryError(),
                                     ValueError("bad size"),
                                     RuntimeError("pil exploded")])
    def test_default_exceptions_trigger_fallback(self, exc):
        @with_text_fallback(_fallback)
        def render(name, **_):
            raise exc
        result = render("hero")
        assert result == "[TEXT] hero"

    def test_unlisted_exception_propagates(self):
        class SpecialBoom(Exception):
            pass

        @with_text_fallback(_fallback)
        def render(name, **_):
            raise SpecialBoom()

        with pytest.raises(SpecialBoom):
            render("hero")

    def test_custom_exception_whitelist(self):
        @with_text_fallback(_fallback, exceptions=(KeyError,))
        def render(name, **_):
            raise KeyError("missing asset")
        assert render("hero") == "[TEXT] hero"

    def test_fallback_receives_same_kwargs(self):
        @with_text_fallback(_fallback)
        def render(name, **_):
            raise OSError("boom")
        assert render("hero", level=3) == "[TEXT] hero (level=3)"

    def test_logs_when_fallback_fires(self, caplog):
        @with_text_fallback(_fallback, log_level=logging.ERROR)
        def render(name, **_):
            raise OSError("font missing")
        with caplog.at_level(logging.ERROR, logger="render_fallback"):
            render("hero")
        assert any(
            "텍스트 폴백" in rec.getMessage() for rec in caplog.records
        )


class TestValidation:
    def test_non_callable_fallback_raises(self):
        with pytest.raises(TypeError):
            with_text_fallback("not callable")  # type: ignore[arg-type]


class TestIsTextFallbackResult:
    def test_str_is_fallback(self):
        assert is_text_fallback_result("hello") is True

    def test_bytes_is_not_fallback(self):
        assert is_text_fallback_result(b"\x89PNG") is False

    def test_bytesio_is_not_fallback(self):
        assert is_text_fallback_result(io.BytesIO(b"x")) is False


class TestDefaultExceptionsConstant:
    def test_default_set_contains_core_pil_errors(self):
        assert OSError in DEFAULT_RENDER_EXCEPTIONS
        assert ValueError in DEFAULT_RENDER_EXCEPTIONS
        assert MemoryError in DEFAULT_RENDER_EXCEPTIONS
