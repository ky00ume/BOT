"""로깅 시스템 유틸리티.

모든 모듈에서 일관된 로깅을 제공합니다.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# 프로젝트 루트 기준 상대 경로. 환경변수 BOT_LOG_DIR 로 오버라이드 가능.
_DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _resolve_log_dir() -> Path:
    override = os.getenv("BOT_LOG_DIR")
    return Path(override) if override else _DEFAULT_LOG_DIR


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """모듈별 로거 생성.

    Args:
        name: 로거 이름 (일반적으로 모듈 이름)
        level: 로그 레벨 (None이면 환경변수 기반 설정)

    Returns:
        설정된 Logger 인스턴스

    Example:
        >>> logger = setup_logger('economy')
        >>> logger.info('트랜잭션 처리 중...')
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 있으면 재설정하지 않음 (중복 방지)
    if logger.handlers:
        return logger

    # 로그 레벨 설정
    if level is None:
        debug_mode = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
        level = logging.DEBUG if debug_mode else logging.INFO

    logger.setLevel(level)

    # 콘솔 핸들러 (INFO 이상만 출력)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (모든 레벨, 10MB 로테이션)
    logs_dir = _resolve_log_dir()
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            str(logs_dir / f'{name}.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # 파일 핸들러 생성 실패 시 콘솔만 사용
        logger.warning(f"파일 로깅 설정 실패 ({logs_dir}): {e}")

    return logger
