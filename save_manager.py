"""save_manager.py — 세이브 전담 매니저

기존 database.py의 save_player_to_db/load_player_from_db를 대체하는
안전한 저장/로드 시스템.

저장 순서: backup() → validate() → write()
실패 시 backup에서 자동 복원.
"""
import json
import logging
import re

from database import get_db_connection
from user_data import UserData

logger = logging.getLogger(__name__)

# 컬럼명 유효성 검사용 정규식 (SQL 인젝션 방지)
_SAFE_COL_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

REQUIRED_FIELDS = {"user_id", "name", "level", "gold", "inventory"}


class SaveManager:
    """백업-우선 세이브 매니저."""

    def save(self, player) -> bool:
        """세이브 순서: ① backup → ② validate → ③ write (실패 시 backup 복원).

        Returns:
            저장 성공 시 True, 실패 시 False.
        """
        user_id = getattr(player, "user_id", 0)

        # ① 백업 먼저
        try:
            self.backup(user_id)
        except Exception as e:
            logger.error(f"[SaveManager] backup 실패 (user_id={user_id}): {e}")
            # 백업 실패는 경고만 — 저장 자체는 계속 진행

        try:
            # ② 검증
            data = UserData.to_save_dict(player)
            if not self._validate(data):
                logger.error(
                    f"[SaveManager] validate 실패 (user_id={user_id}): "
                    f"필수 필드 누락"
                )
                return False

            # ③ 쓰기 (기존 save_player_to_db 사용)
            from database import save_player_to_db
            save_player_to_db(player)
            logger.info(f"[SaveManager] 저장 완료 (user_id={user_id})")
            return True

        except Exception as e:
            logger.error(f"[SaveManager] save 실패 (user_id={user_id}): {e}")
            try:
                self.restore_from_backup(user_id)
            except Exception as re:
                logger.error(f"[SaveManager] 복원도 실패 (user_id={user_id}): {re}")
            return False

    def load(self, user_id) -> dict | None:
        """DB에서 로드 → 스키마 마이그레이션 → 반환.

        Returns:
            마이그레이션이 적용된 플레이어 데이터 dict, 없으면 None.
        """
        from database import load_player_from_db
        data = load_player_from_db(user_id)
        if data is None:
            return None
        return self._migrate(data)

    def backup(self, user_id):
        """기존 DB 행을 players_backup 테이블에 복사 (최근 3개 유지)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players_backup (
                    backup_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL,
                    backed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                    data       TEXT NOT NULL
                )
            """)
            cursor.execute(
                "SELECT * FROM players WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                cursor.execute(
                    "INSERT INTO players_backup (user_id, data) VALUES (?, ?)",
                    (user_id, json.dumps(row_dict, ensure_ascii=False)),
                )
                # 최근 3개만 유지
                cursor.execute(
                    """
                    DELETE FROM players_backup
                    WHERE user_id = ? AND backup_id NOT IN (
                        SELECT backup_id FROM players_backup
                        WHERE user_id = ?
                        ORDER BY backup_id DESC LIMIT 3
                    )
                    """,
                    (user_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def restore_from_backup(self, user_id):
        """가장 최근 백업에서 players 테이블을 복원합니다."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT data FROM players_backup
                WHERE user_id = ?
                ORDER BY backup_id DESC LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                logger.warning(
                    f"[SaveManager] 복원할 백업 없음 (user_id={user_id})"
                )
                return
            backup_data = json.loads(row["data"])
            # 컬럼명을 화이트리스트로 검증하여 SQL 인젝션 방지
            safe_data = {
                k: v for k, v in backup_data.items()
                if _SAFE_COL_RE.match(k)
            }
            if not safe_data:
                logger.error(
                    f"[SaveManager] 백업 데이터에 유효한 컬럼이 없음 (user_id={user_id})"
                )
                return
            cols = ", ".join(safe_data.keys())
            placeholders = ", ".join("?" * len(safe_data))
            cursor.execute(
                f"INSERT OR REPLACE INTO players ({cols}) VALUES ({placeholders})",
                list(safe_data.values()),
            )
            conn.commit()
            logger.info(
                f"[SaveManager] 백업 복원 완료 (user_id={user_id})"
            )
        finally:
            conn.close()

    def _migrate(self, data: dict) -> dict:
        """schema_version 비교 후 순차 마이그레이션 적용."""
        return UserData._migrate(data)

    def _validate(self, data: dict) -> bool:
        """필수 필드 존재 여부 확인."""
        return all(k in data for k in REQUIRED_FIELDS)


# 모듈 레벨 싱글톤
save_manager = SaveManager()
