"""마을 데이터 저장/로드."""
from __future__ import annotations

from typing import Dict

from utils.logger import setup_logger
from db.connection import get_db_connection

logger = setup_logger('db.village')


def save_village_data(contribution: int, level: int) -> None:
    """마을 데이터 저장.

    Args:
        contribution: 마을 기여도
        level: 마을 레벨
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO village (id, contribution, level)
        VALUES (1, ?, ?)
    """, (contribution, level))
    conn.commit()
    conn.close()


def load_village_data() -> Dict[str, int]:
    """마을 데이터 로드.

    Returns:
        {"contribution": int, "level": int} 형태의 딕셔너리
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT contribution, level FROM village WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {"contribution": 0, "level": 1}
        return {"contribution": row["contribution"], "level": row["level"]}
    except Exception as e:
        logger.warning("마을 데이터 로드 실패: %s", e, exc_info=True)
        return {"contribution": 0, "level": 1}
