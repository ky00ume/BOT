"""렌더링 폴백 유틸리티 (REMEDIATION_PLAN 2-B).

PIL 렌더링은 에셋 누락, 폰트 로딩 실패, 메모리 부족, 손상된 입력 등으로
예기치 못하게 실패할 수 있다. 과거에는 호출부가 단순히 예외를 전파해서
사용자에게 빈 응답이나 스택 트레이스를 노출했다. 이 모듈의
``with_text_fallback`` 데코레이터는 렌더 함수의 예외를 잡아내고,
사전에 등록된 텍스트 폴백 함수를 호출해 안전하게 문자열을 반환한다.

사용 예::

    from utils.render_fallback import with_text_fallback

    def _status_text(player, **_):
        return f"{player.name} (Lv.{player.level}) HP {player.hp}/{player.max_hp}"

    @with_text_fallback(_status_text)
    def render_status_card(player, **kwargs):
        # PIL 기반 렌더링. 예외가 나면 _status_text 가 대신 호출된다.
        ...

Discord 커맨드 레이어에서는 반환 타입(bytes/BytesIO vs str)을 확인해서
``discord.File`` 또는 일반 텍스트로 응답하면 된다.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Tuple, Type, TypeVar

from utils.logger import setup_logger


logger = setup_logger("render_fallback")

# 기본적으로 폴백으로 전환할 예외 종류. 호출자가 override 가능.
DEFAULT_RENDER_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    OSError,          # 폰트·에셋 파일 접근 실패
    MemoryError,      # 거대한 이미지 요청
    ValueError,       # PIL 내부 검증 실패
    RuntimeError,     # PIL/런타임 경고
)


F = TypeVar("F", bound=Callable[..., Any])


def with_text_fallback(
    fallback_fn: Callable[..., str],
    *,
    exceptions: Tuple[Type[BaseException], ...] = DEFAULT_RENDER_EXCEPTIONS,
    log_level: int = logging.ERROR,
) -> Callable[[F], F]:
    """렌더 함수를 감싸는 데코레이터.

    대상 함수가 ``exceptions`` 에 해당하는 오류로 실패하면 ``fallback_fn`` 의
    반환값(문자열)을 대신 반환한다. 어떤 예외였는지는 ``exc_info`` 와 함께
    로깅되므로 운영 시 원인 분석이 가능하다.

    Args:
        fallback_fn: 원 함수와 동일한 인자를 받아 문자열을 반환하는 콜러블.
        exceptions: 폴백 대상 예외 튜플. 기본값은 렌더링에서 일반적으로
            나는 종류. 필요하면 호출부에서 축소하거나 확장할 수 있다.
        log_level: 폴백 발생 시 사용할 로그 레벨.
    """

    if not callable(fallback_fn):
        raise TypeError("fallback_fn must be callable")

    def decorator(render_fn: F) -> F:
        @wraps(render_fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return render_fn(*args, **kwargs)
            except exceptions as exc:
                logger.log(
                    log_level,
                    "렌더링 실패, 텍스트 폴백 사용: fn=%s, error=%s",
                    render_fn.__name__, exc, exc_info=True,
                )
                return fallback_fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def is_text_fallback_result(value: Any) -> bool:
    """데코레이터의 반환값이 텍스트 폴백인지 여부를 구분.

    Discord 응답 시 ``isinstance(value, (bytes, bytearray, memoryview))`` 검사와
    ``io.BytesIO`` 확인 로직을 호출부 여러 곳에 복제하지 않도록 하기 위해
    제공하는 헬퍼. 문자열이면 폴백으로 간주한다.
    """
    return isinstance(value, str)
