"""포맷팅 유틸리티.

텍스트 포맷팅, 색상, 게이지 바 등의 공통 포맷팅 함수를 제공합니다.
"""
from typing import Optional

ESC = "\x1b"


class AnsiColor:
    """ANSI 색상 코드."""

    RESET = f"{ESC}[0m"
    RED = f"{ESC}[31m"
    GREEN = f"{ESC}[32m"
    YELLOW = f"{ESC}[33m"
    BLUE = f"{ESC}[34m"
    MAGENTA = f"{ESC}[35m"
    CYAN = f"{ESC}[36m"
    WHITE = f"{ESC}[37m"
    GOLD = f"{ESC}[33m"

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """텍스트에 색상 적용.

        Args:
            text: 색상을 적용할 텍스트
            color: ANSI 색상 코드

        Returns:
            색상이 적용된 텍스트
        """
        return f"{color}{text}{AnsiColor.RESET}"

    @staticmethod
    def gold(text: str) -> str:
        """골드 색상 (노랑)."""
        return AnsiColor.colorize(text, AnsiColor.GOLD)

    @staticmethod
    def hp(text: str) -> str:
        """HP 색상 (빨강)."""
        return AnsiColor.colorize(text, AnsiColor.RED)

    @staticmethod
    def mp(text: str) -> str:
        """MP 색상 (파랑)."""
        return AnsiColor.colorize(text, AnsiColor.BLUE)

    @staticmethod
    def energy(text: str) -> str:
        """기력 색상 (초록)."""
        return AnsiColor.colorize(text, AnsiColor.GREEN)


def format_stat_bar(
    current: int,
    maximum: int,
    length: int = 10,
    fill_char: str = "▓",
    empty_char: str = "░",
    show_numbers: bool = True,
) -> str:
    """스탯 바 포맷팅.

    Args:
        current: 현재 값
        maximum: 최대 값
        length: 바 길이 (문자 개수)
        fill_char: 채워진 부분 문자
        empty_char: 빈 부분 문자
        show_numbers: 숫자 표시 여부

    Returns:
        "▓▓▓▓▓░░░░░ 50/100" 형식의 문자열

    Example:
        >>> format_stat_bar(75, 100, length=10)
        '▓▓▓▓▓▓▓░░░ 75/100'
    """
    if maximum <= 0:
        bar = empty_char * length
        return f"{bar} 0/0" if show_numbers else bar

    ratio = min(current / maximum, 1.0)
    filled = int(ratio * length)
    bar = fill_char * filled + empty_char * (length - filled)

    if show_numbers:
        return f"{bar} {current}/{maximum}"
    return bar


def format_percentage_bar(
    value: float,
    length: int = 10,
    fill_char: str = "▓",
    empty_char: str = "░",
    show_percent: bool = True,
) -> str:
    """퍼센트 바 포맷팅.

    Args:
        value: 0.0 ~ 1.0 사이의 비율 값
        length: 바 길이
        fill_char: 채워진 부분 문자
        empty_char: 빈 부분 문자
        show_percent: 퍼센트 표시 여부

    Returns:
        "▓▓▓▓▓░░░░░ 50%" 형식의 문자열

    Example:
        >>> format_percentage_bar(0.75)
        '▓▓▓▓▓▓▓░░░ 75%'
    """
    ratio = max(0.0, min(value, 1.0))
    filled = int(ratio * length)
    bar = fill_char * filled + empty_char * (length - filled)

    if show_percent:
        percent = int(ratio * 100)
        return f"{bar} {percent}%"
    return bar


def format_gold(amount: int) -> str:
    """골드 포맷팅 (쉼표 구분 + 색상).

    Args:
        amount: 골드 양

    Returns:
        색상이 적용된 골드 문자열

    Example:
        >>> format_gold(1234567)
        '\x1b[33m1,234,567G\x1b[0m'
    """
    formatted = f"{amount:,}G"
    return AnsiColor.gold(formatted)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """텍스트 자르기.

    Args:
        text: 원본 텍스트
        max_length: 최대 길이
        suffix: 잘렸을 때 붙일 접미사

    Returns:
        잘린 텍스트

    Example:
        >>> truncate_text("매우 긴 텍스트입니다", 10)
        '매우 긴 텍...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_time_seconds(seconds: int) -> str:
    """초를 시:분:초 형식으로 변환.

    Args:
        seconds: 초 단위 시간

    Returns:
        "1:23:45" 형식의 문자열

    Example:
        >>> format_time_seconds(3665)
        '1:01:05'
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
