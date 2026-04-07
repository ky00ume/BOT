"""utils/player_lock.py — 플레이어별 asyncio.Lock 관리."""
import asyncio
from typing import Dict

_locks: Dict[int, asyncio.Lock] = {}


def get_player_lock(user_id: int) -> asyncio.Lock:
    """user_id별 Lock을 반환. 없으면 생성."""
    return _locks.setdefault(user_id, asyncio.Lock())


def cleanup_lock(user_id: int) -> None:
    """플레이어 Lock 정리 (선택)."""
    _locks.pop(user_id, None)
