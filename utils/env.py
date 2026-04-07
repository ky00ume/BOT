"""환경변수 로딩 유틸리티 (REMEDIATION_PLAN 3-D).

main.py 가 실행 중에 ``int(os.getenv(..., "하드코딩된기본값"))`` 패턴으로
개인 식별 가능한 Discord ID 를 기본값으로 사용하던 문제를 없앤다.
이 모듈의 헬퍼는 다음을 보장한다:

* 필수 환경변수가 누락되면 ``ConfigError`` 로 즉시 실패
* 선택 환경변수는 명시적 기본값만 허용 (원치 않는 값이 새어 나오지 않도록)
* 모든 로딩은 한 곳에서 관리되어 테스트 가능
"""

from __future__ import annotations

import os
from typing import Optional

from utils.exceptions import ConfigError


def load_required_str(name: str, *, min_length: int = 1) -> str:
    """필수 문자열 환경변수를 로드."""
    raw = os.getenv(name)
    if raw is None or len(raw) < min_length:
        raise ConfigError(
            f"필수 환경변수 {name} 이(가) 설정되지 않았거나 길이가 부족합니다"
        )
    return raw


def load_required_int(name: str) -> int:
    """필수 정수 환경변수를 로드. 누락 또는 파싱 실패 시 ConfigError."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        raise ConfigError(f"필수 환경변수 {name} 이(가) 설정되지 않았습니다")
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(
            f"환경변수 {name} 은(는) 정수여야 합니다: {raw!r}"
        ) from e


def load_optional_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """선택 정수 환경변수. 미설정 시 ``default`` 반환."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(
            f"환경변수 {name} 은(는) 정수여야 합니다: {raw!r}"
        ) from e


def load_discord_token(name: str = "DISCORD_TOKEN") -> str:
    """Discord 봇 토큰 로드. 토큰 길이가 비정상적으로 짧으면 실패한다.

    정확한 Discord 토큰 형식(base64url 점 3부분)을 엄격히 검증하지는 않지만,
    공백 또는 placeholder 값이 그대로 들어오는 상황을 막는 최소 방어선이다.
    """
    token = load_required_str(name, min_length=20)
    if token.lower().startswith("your_") or token.lower() == "changeme":
        raise ConfigError(
            f"{name} 이(가) 실제 값이 아닌 placeholder 로 설정되어 있습니다"
        )
    return token
