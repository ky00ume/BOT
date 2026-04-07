"""utils/logger.py — 로거 경로 이식성 테스트."""

import logging
from pathlib import Path

from utils import logger as logger_module
from utils.logger import _resolve_log_dir, setup_logger


class TestLogDirResolution:
    def test_default_log_dir_is_relative_to_repo(self, monkeypatch):
        monkeypatch.delenv("BOT_LOG_DIR", raising=False)
        resolved = _resolve_log_dir()
        # 프로젝트 루트/logs 이어야 한다.
        expected = Path(logger_module.__file__).resolve().parent.parent / "logs"
        assert resolved == expected

    def test_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path))
        assert _resolve_log_dir() == tmp_path

    def test_no_hardcoded_runner_path(self):
        """과거 /home/runner/work/BOT/BOT/logs 하드코딩이 제거되었는지 확인."""
        source = Path(logger_module.__file__).read_text(encoding="utf-8")
        assert "/home/runner/work/BOT/BOT/logs" not in source


class TestSetupLogger:
    def test_returns_logger_instance(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path))
        # 고유 이름으로 캐시 충돌 회피
        lg = setup_logger("test_logger_unit_A")
        assert isinstance(lg, logging.Logger)
        assert lg.handlers, "콘솔 핸들러는 항상 생성되어야 한다"

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BOT_LOG_DIR", str(tmp_path))
        a = setup_logger("test_logger_unit_B")
        b = setup_logger("test_logger_unit_B")
        assert a is b
        # 중복 핸들러가 쌓이지 않아야 함
        assert len(a.handlers) == len(b.handlers)

    def test_falls_back_when_log_dir_unwritable(self, monkeypatch, tmp_path):
        # 존재하지 않는 부모 디렉토리 아래의 파일 경로로 오버라이드해서도
        # setup_logger 가 예외 없이 반환해야 한다 (콘솔 전용 폴백).
        bad = tmp_path / "not_a_dir_file"
        bad.write_text("x")  # 파일로 만들어 mkdir 이 실패하도록 함
        monkeypatch.setenv("BOT_LOG_DIR", str(bad / "child"))
        lg = setup_logger("test_logger_unit_C")
        assert isinstance(lg, logging.Logger)
