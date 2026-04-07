"""utils/env.py — 환경변수 로딩 검증 테스트 (3-D)."""

import pytest

from utils.env import (
    load_discord_token,
    load_optional_int,
    load_required_int,
    load_required_str,
)
from utils.exceptions import ConfigError


class TestLoadRequiredInt:
    def test_parses_integer(self, monkeypatch):
        monkeypatch.setenv("X_PORT", "42")
        assert load_required_int("X_PORT") == 42

    def test_missing_raises(self, monkeypatch):
        monkeypatch.delenv("X_PORT", raising=False)
        with pytest.raises(ConfigError):
            load_required_int("X_PORT")

    def test_blank_raises(self, monkeypatch):
        monkeypatch.setenv("X_PORT", "   ")
        with pytest.raises(ConfigError):
            load_required_int("X_PORT")

    def test_non_numeric_raises(self, monkeypatch):
        monkeypatch.setenv("X_PORT", "abc")
        with pytest.raises(ConfigError):
            load_required_int("X_PORT")


class TestLoadOptionalInt:
    def test_returns_default_if_missing(self, monkeypatch):
        monkeypatch.delenv("X_OPT", raising=False)
        assert load_optional_int("X_OPT", default=7) == 7

    def test_parses_when_set(self, monkeypatch):
        monkeypatch.setenv("X_OPT", "9")
        assert load_optional_int("X_OPT", default=7) == 9

    def test_bad_value_raises(self, monkeypatch):
        monkeypatch.setenv("X_OPT", "nope")
        with pytest.raises(ConfigError):
            load_optional_int("X_OPT")


class TestLoadRequiredStr:
    def test_basic(self, monkeypatch):
        monkeypatch.setenv("X_STR", "value")
        assert load_required_str("X_STR") == "value"

    def test_missing_raises(self, monkeypatch):
        monkeypatch.delenv("X_STR", raising=False)
        with pytest.raises(ConfigError):
            load_required_str("X_STR")

    def test_too_short_raises(self, monkeypatch):
        monkeypatch.setenv("X_STR", "hi")
        with pytest.raises(ConfigError):
            load_required_str("X_STR", min_length=5)


class TestLoadDiscordToken:
    def test_accepts_realistic_token(self, monkeypatch):
        monkeypatch.setenv(
            "DISCORD_TOKEN", "MTEyMzQ1Njc4OTAuRXhhbXBsZS5UZXN0VG9rZW5Gb3JVbml0VGVzdA",
        )
        token = load_discord_token()
        assert token.startswith("MTEyMz")

    def test_rejects_placeholder(self, monkeypatch):
        monkeypatch.setenv("DISCORD_TOKEN", "your_bot_token_here_abcdefghij")
        with pytest.raises(ConfigError):
            load_discord_token()

    def test_rejects_too_short(self, monkeypatch):
        monkeypatch.setenv("DISCORD_TOKEN", "short")
        with pytest.raises(ConfigError):
            load_discord_token()

    def test_rejects_missing(self, monkeypatch):
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
        with pytest.raises(ConfigError):
            load_discord_token()


class TestEnvExample:
    def test_no_real_ids_in_env_example(self):
        """REMEDIATION_PLAN 3-D: .env.example 에 실제 Discord ID 가 남아 있지 않아야."""
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / ".env.example"
        text = path.read_text(encoding="utf-8")
        # 과거에 커밋되어 있던 실제 ID 들.
        leaked = [
            "446014281486565387",
            "778476921117343744",
            "1396150414549717207",
            "1483987513575215207",
        ]
        for sample in leaked:
            assert sample not in text, (
                f".env.example 에 실제 Discord ID 가 남아 있음: {sample}"
            )
