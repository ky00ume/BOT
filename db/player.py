"""플레이어 CRUD 작업."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from utils.logger import setup_logger
from db.connection import get_db_connection, _migrate_players_table

if TYPE_CHECKING:
    from player import Player

logger = setup_logger('db.player')


def save_player_to_db(player: Player) -> None:
    """플레이어 데이터를 DB에 저장.

    Args:
        player: 저장할 Player 객체
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # 기존 테이블에 컬럼이 없을 경우 마이그레이션
    _migrate_players_table(cursor)
    data = player.get_save_data()

    # affinity 전체를 직렬화 (affinities + daily_limits + gift_history 포함)
    aff_full = {}
    aff_mgr = getattr(player, "_affinity_manager", None)
    if aff_mgr:
        aff_full = aff_mgr.to_dict()

    # affinity_full이 get_save_data()에 포함된 경우 우선 사용
    if "affinity_full" in data and data["affinity_full"]:
        aff_full = data["affinity_full"]

    # story_quest 직렬화
    story_quest_json = json.dumps(data.get("story_quest", {}), ensure_ascii=False)
    # quest_data 직렬화
    quest_data_json = json.dumps(data.get("quest_data", {}), ensure_ascii=False)
    # collection_data 직렬화
    collection_data_json = json.dumps(data.get("collection_data", {}), ensure_ascii=False)

    cursor.execute("""
        INSERT OR REPLACE INTO players
        (user_id, name, level, exp, hp, max_hp, mp, max_mp, energy, max_energy,
         gold, base_stats, inventory, equipment, keywords, affinity_data, daily_limits,
         story_quest, skill_ranks, skill_exp, titles, current_title, bags,
         last_special_encounter, rafael_contract,
         fatigue, condition, stability, costume, care_flags, quest_data, collection_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_id", 0),
        data.get("name", "모험가"),
        data.get("level", 1),
        data.get("exp", 0.0),
        data.get("hp", 100),
        data.get("max_hp", 100),
        data.get("mp", 50),
        data.get("max_mp", 50),
        data.get("energy", 100),
        data.get("max_energy", 100),
        data.get("gold", 500),
        json.dumps(data.get("base_stats", {}), ensure_ascii=False),
        json.dumps(data.get("inventory", {}), ensure_ascii=False),
        json.dumps(data.get("equipment", {}), ensure_ascii=False),
        json.dumps(data.get("keywords", ["마을", "날씨", "소문"]), ensure_ascii=False),
        json.dumps(aff_full, ensure_ascii=False),
        json.dumps(aff_full.get("daily_limits", {}), ensure_ascii=False),
        story_quest_json,
        json.dumps(data.get("skill_ranks", {"smash": "연습", "defense": "연습", "counter": "연습"}), ensure_ascii=False),
        json.dumps(data.get("skill_exp", {}), ensure_ascii=False),
        json.dumps(data.get("titles", []), ensure_ascii=False),
        data.get("current_title"),
        json.dumps(data.get("bags", ["bag_large"]), ensure_ascii=False),
        data.get("last_special_encounter"),
        json.dumps(data.get("rafael_contract"), ensure_ascii=False) if data.get("rafael_contract") else None,
        data.get("fatigue", 0),
        data.get("condition", 50),
        data.get("stability", 50),
        json.dumps(data.get("costume", {}), ensure_ascii=False),
        json.dumps(data.get("_flags", {}), ensure_ascii=False),
        quest_data_json,
        collection_data_json,
    ))
    conn.commit()
    conn.close()


def load_player_from_db(user_id: int) -> Optional[Dict[str, Any]]:
    """DB에서 플레이어 데이터 로드.

    Args:
        user_id: Discord 유저 ID

    Returns:
        플레이어 데이터 딕셔너리, 존재하지 않으면 None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    _migrate_players_table(cursor)
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    def _safe_json(val, default):
        try:
            if val is None:
                return default
            return json.loads(val)
        except Exception as e:
            logger.warning("JSON 파싱 실패 (기본값 반환): %s", e, exc_info=True)
            return default

    result = {
        "user_id":      row["user_id"],
        "name":         row["name"],
        "level":        row["level"],
        "hp":           row["hp"],
        "max_hp":       row["max_hp"],
        "mp":           row["mp"],
        "max_mp":       row["max_mp"],
        "energy":       row["energy"],
        "max_energy":   row["max_energy"],
        "gold":         row["gold"],
        "base_stats":   _safe_json(row["base_stats"], {}),
        "inventory":    _safe_json(row["inventory"], {}),
        "equipment":    _safe_json(row["equipment"], {}),
    }

    # 신규 컬럼은 없을 수도 있으므로 안전하게 접근
    try:
        result["keywords"] = _safe_json(row["keywords"], ["마을", "날씨", "소문"])
    except (IndexError, KeyError):
        result["keywords"] = ["마을", "날씨", "소문"]

    try:
        result["affinity_full"] = _safe_json(row["affinity_data"], {})
    except (IndexError, KeyError):
        result["affinity_full"] = {}

    try:
        result["story_quest"] = _safe_json(row["story_quest"], {})
    except (IndexError, KeyError):
        result["story_quest"] = {}

    try:
        result["exp"] = row["exp"] if row["exp"] is not None else 0.0
    except (IndexError, KeyError):
        result["exp"] = 0.0

    try:
        result["skill_ranks"] = _safe_json(row["skill_ranks"], {"smash": "연습", "defense": "연습", "counter": "연습"})
    except (IndexError, KeyError):
        result["skill_ranks"] = {"smash": "연습", "defense": "연습", "counter": "연습"}

    try:
        result["skill_exp"] = _safe_json(row["skill_exp"], {})
    except (IndexError, KeyError):
        result["skill_exp"] = {}

    try:
        result["titles"] = _safe_json(row["titles"], [])
    except (IndexError, KeyError):
        result["titles"] = []

    try:
        result["current_title"] = row["current_title"]
    except (IndexError, KeyError):
        result["current_title"] = None

    try:
        result["bags"] = _safe_json(row["bags"], ["bag_large"])
    except (IndexError, KeyError):
        result["bags"] = ["bag_large"]

    try:
        result["last_special_encounter"] = row["last_special_encounter"]
    except (IndexError, KeyError):
        result["last_special_encounter"] = None

    try:
        result["rafael_contract"] = _safe_json(row["rafael_contract"], None)
    except (IndexError, KeyError):
        result["rafael_contract"] = None

    try:
        result["fatigue"] = row["fatigue"] if row["fatigue"] is not None else 0
    except (IndexError, KeyError):
        result["fatigue"] = 0

    try:
        result["condition"] = row["condition"] if row["condition"] is not None else 50
    except (IndexError, KeyError):
        result["condition"] = 50

    try:
        result["stability"] = row["stability"] if row["stability"] is not None else 50
    except (IndexError, KeyError):
        result["stability"] = 50

    try:
        result["costume"] = _safe_json(row["costume"], {})
    except (IndexError, KeyError):
        result["costume"] = {}

    try:
        result["_flags"] = _safe_json(row["care_flags"], {})
    except (IndexError, KeyError):
        result["_flags"] = {}

    try:
        result["quest_data"] = _safe_json(row["quest_data"], {})
    except (IndexError, KeyError):
        result["quest_data"] = {}

    try:
        result["collection_data"] = _safe_json(row["collection_data"], {})
    except (IndexError, KeyError):
        result["collection_data"] = {}

    return result
