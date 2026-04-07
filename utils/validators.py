"""사용자 입력 검증 유틸리티.

Discord 커맨드 경계에서 플레이어가 전달한 문자열/수치를 일관된 방식으로
검증하고, PIL 렌더링 등 하류 시스템이 안전한 값만 받도록 보장한다.
검증 실패 시 ``ValidationError`` 를 발생시키며, 호출자는 이를 붙잡아
친화적인 에러 메시지로 변환한다.
"""

from __future__ import annotations

import re
from typing import Optional

from utils.exceptions import GameError


class ValidationError(GameError):
    """사용자 입력 검증 실패."""


# ---- 제한 상수 --------------------------------------------------------------

MAX_NAME_LENGTH = 20
MAX_MESSAGE_LENGTH = 500
MAX_RENDER_TEXT_LENGTH = 200
MAX_COUNT = 9999

# 아이템 ID 는 소문자 영숫자 + 언더스코어만 허용.
_ITEM_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

# 한글, 영숫자, 공백, 일부 문장부호만 허용하는 안전한 텍스트 패턴.
_SAFE_TEXT_PATTERN = re.compile(
    r"^[\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?\-()·~]+$",
    re.UNICODE,
)


# ---- 검증 함수 --------------------------------------------------------------

def validate_player_name(name: Optional[str]) -> str:
    """플레이어 이름을 검증 및 정규화."""
    if name is None or not str(name).strip():
        raise ValidationError("이름은 비어 있을 수 없습니다")
    cleaned = str(name).strip()
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ValidationError(
            f"이름은 {MAX_NAME_LENGTH}자 이하여야 합니다 (입력 {len(cleaned)}자)"
        )
    if not _SAFE_TEXT_PATTERN.match(cleaned):
        raise ValidationError("이름에 허용되지 않는 문자가 포함되어 있습니다")
    return cleaned


def validate_item_id(item_id: Optional[str]) -> str:
    """아이템 ID 형식을 검증."""
    if not item_id or not _ITEM_ID_PATTERN.match(item_id):
        raise ValidationError(f"잘못된 아이템 ID 형식: {item_id!r}")
    return item_id


def validate_count(
    count: object,
    *,
    min_val: int = 1,
    max_val: int = MAX_COUNT,
) -> int:
    """수량이 정수이며 허용 범위 내인지 검증."""
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValidationError(f"수량은 정수여야 합니다: {count!r}")
    if count < min_val or count > max_val:
        raise ValidationError(
            f"수량은 {min_val}~{max_val} 사이여야 합니다 (입력 {count})"
        )
    return count


def validate_message(message: Optional[str]) -> str:
    """채팅/대화 메시지 길이 검증."""
    if message is None:
        raise ValidationError("메시지가 비어 있습니다")
    cleaned = str(message).strip()
    if not cleaned:
        raise ValidationError("메시지가 비어 있습니다")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"메시지는 {MAX_MESSAGE_LENGTH}자 이하여야 합니다"
        )
    return cleaned


def truncate_for_render(text: object, max_len: int = MAX_RENDER_TEXT_LENGTH) -> str:
    """PIL 렌더링에 전달할 텍스트의 길이 상한을 보장.

    DoS 방어 목적이므로 예외를 던지지 않고 안전하게 잘라낸다.
    """
    s = "" if text is None else str(text)
    if len(s) <= max_len:
        return s
    if max_len <= 3:
        return s[:max_len]
    return s[: max_len - 3] + "..."
