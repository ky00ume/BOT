"""악보 저장/로드/삭제."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.logger import setup_logger
from db.connection import get_db_connection

logger = setup_logger('db.music')


def save_sheet_music(user_id: int, title: str, melody: str) -> None:
    """악보 저장.

    Args:
        user_id: Discord 유저 ID
        title: 악보 제목
        melody: 악보 멜로디 문자열
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sheet_music (user_id, title, melody)
        VALUES (?, ?, ?)
    """, (user_id, title, melody))
    conn.commit()
    conn.close()


def load_sheet_music_list(user_id: int) -> List[Dict[str, Any]]:
    """유저의 모든 악보 목록 조회.

    Args:
        user_id: Discord 유저 ID

    Returns:
        악보 목록 ({"id": int, "title": str, "melody": str, "created": str})
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, melody, created FROM sheet_music WHERE user_id = ? ORDER BY id",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "title": r["title"], "melody": r["melody"], "created": r["created"]} for r in rows]
    except Exception as e:
        logger.warning("악보 목록 조회 실패 (user_id=%s): %s", user_id, e, exc_info=True)
        return []


def load_sheet_music(user_id: int, title_or_id: str) -> Optional[Dict[str, str]]:
    """제목 또는 숫자 ID로 악보를 조회합니다.

    Args:
        user_id: Discord 유저 ID
        title_or_id: 악보 제목 또는 ID

    Returns:
        악보 데이터 ({"id": int, "title": str, "melody": str}), 없으면 None
    """
    if not title_or_id:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if title_or_id.isdigit() and int(title_or_id) > 0:
            cursor.execute(
                "SELECT id, title, melody FROM sheet_music WHERE user_id = ? AND id = ?",
                (user_id, int(title_or_id))
            )
        else:
            cursor.execute(
                "SELECT id, title, melody FROM sheet_music WHERE user_id = ? AND title = ?",
                (user_id, title_or_id)
            )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row["id"], "title": row["title"], "melody": row["melody"]}
        return None
    except Exception as e:
        logger.warning("악보 조회 실패 (user_id=%s, key=%s): %s", user_id, title_or_id, e, exc_info=True)
        return None


def delete_sheet_music(user_id: int, title_or_id: str) -> bool:
    """악보 삭제.

    Args:
        user_id: Discord 유저 ID
        title_or_id: 악보 제목 또는 ID

    Returns:
        삭제 성공 시 True, 실패 시 False
    """
    if not title_or_id:
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if title_or_id.isdigit() and int(title_or_id) > 0:
            cursor.execute(
                "DELETE FROM sheet_music WHERE user_id = ? AND id = ?",
                (user_id, int(title_or_id))
            )
        else:
            cursor.execute(
                "DELETE FROM sheet_music WHERE user_id = ? AND title = ?",
                (user_id, title_or_id)
            )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error("악보 삭제 실패 (user_id=%s, key=%s): %s", user_id, title_or_id, e, exc_info=True)
        return False
