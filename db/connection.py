"""DB 연결, 초기화, 마이그레이션."""
from __future__ import annotations

import json
import os
import sqlite3

from utils.logger import setup_logger

logger = setup_logger('db.connection')

# DB_PATH 환경변수로 경로 지정 가능 (기본값: 봇 폴더 내 vision_town.db)
# 머지/재배포 시 데이터 유지를 위해 .env에 DB_PATH=/data/vision_town.db 처럼 repo 외부 경로 설정 권장
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vision_town.db")
)


def get_db_connection() -> sqlite3.Connection:
    """DB 연결 반환."""
    # 런타임에 환경변수를 다시 읽어 임시 DB(테스트용) 지원
    db_path = os.environ.get("DB_PATH", DB_PATH)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.debug(f"DB 연결 성공: {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"DB 연결 실패: {db_path}, 오류={e}", exc_info=True)
        raise


def init_db() -> None:
    """데이터베이스 초기화 및 테이블 생성."""
    try:
        logger.info("DB 초기화 시작...")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id     INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                level       INTEGER DEFAULT 1,
                hp          INTEGER DEFAULT 100,
                max_hp      INTEGER DEFAULT 100,
                mp          INTEGER DEFAULT 50,
                max_mp      INTEGER DEFAULT 50,
                energy      INTEGER DEFAULT 100,
                max_energy  INTEGER DEFAULT 100,
                gold        INTEGER DEFAULT 500,
                base_stats  TEXT DEFAULT '{}',
                inventory   TEXT DEFAULT '{}',
                equipment   TEXT DEFAULT '{}',
                keywords    TEXT DEFAULT '["마을","날씨","소문"]',
                affinity_data  TEXT DEFAULT '{}',
                daily_limits   TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS village (
                id           INTEGER PRIMARY KEY DEFAULT 1,
                contribution INTEGER DEFAULT 0,
                level        INTEGER DEFAULT 1,
                data         TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheet_music (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER DEFAULT 0,
                title    TEXT NOT NULL,
                melody   TEXT NOT NULL,
                created  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage (
                user_id       INTEGER PRIMARY KEY,
                items         TEXT DEFAULT '{}',
                max_capacity  INTEGER DEFAULT 20
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players_backup (
                backup_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                backed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                data       TEXT NOT NULL
            )
        """)
        conn.commit()
        logger.info("DB 초기화 완료")
    except sqlite3.Error as e:
        logger.error(f"DB 초기화 실패: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def _migrate_players_table(cursor: sqlite3.Cursor) -> None:
    """기존 players 테이블에 새 컬럼이 없으면 추가합니다."""
    try:
        cursor.execute("PRAGMA table_info(players)")
        columns = {row[1] for row in cursor.fetchall()}
        if "keywords" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN keywords TEXT DEFAULT '[\"마을\",\"날씨\",\"소문\"]'"
            )
        if "affinity_data" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN affinity_data TEXT DEFAULT '{}'"
            )
        if "daily_limits" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN daily_limits TEXT DEFAULT '{}'"
            )
        if "story_quest" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN story_quest TEXT DEFAULT '{}'"
            )
        if "exp" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN exp REAL DEFAULT 0.0"
            )
        if "skill_ranks" not in columns:
            _default_skill_ranks = json.dumps(
                {"smash": "연습", "defense": "연습", "counter": "연습"}, ensure_ascii=False
            )
            cursor.execute(
                "ALTER TABLE players ADD COLUMN skill_ranks TEXT DEFAULT '" + _default_skill_ranks + "'"
            )
        if "skill_exp" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN skill_exp TEXT DEFAULT '{}'"
            )
        if "titles" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN titles TEXT DEFAULT '[]'"
            )
        if "bags" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN bags TEXT DEFAULT '[\"bag_large\"]'"
            )
        if "last_special_encounter" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN last_special_encounter REAL DEFAULT NULL"
            )
        if "current_title" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN current_title TEXT DEFAULT NULL"
            )
        if "rafael_contract" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN rafael_contract TEXT DEFAULT NULL"
            )
        if "fatigue" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN fatigue INTEGER DEFAULT 0"
            )
        if "condition" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN condition INTEGER DEFAULT 50"
            )
        if "stability" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN stability INTEGER DEFAULT 50"
            )
        if "costume" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN costume TEXT DEFAULT '{}'"
            )
        if "care_flags" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN care_flags TEXT DEFAULT '{}'"
            )
        if "quest_data" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN quest_data TEXT DEFAULT '{}'"
            )
        if "collection_data" not in columns:
            cursor.execute(
                "ALTER TABLE players ADD COLUMN collection_data TEXT DEFAULT '{}'"
            )
    except Exception as e:
        logger.error("players 테이블 마이그레이션 실패: %s", e, exc_info=True)
