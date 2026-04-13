"""database.py — 하위 호환성 유지를 위한 re-export 래퍼.

실제 구현은 db/ 패키지의 각 서브모듈에 있습니다:
  db/connection.py  — DB 연결·초기화·마이그레이션
  db/constants.py   — STATS_INFO, BAGS, EQUIPMENT, HUNTING_GROUNDS, NPC_DATA
  db/player.py      — save_player_to_db, load_player_from_db
  db/village.py     — save_village_data, load_village_data
  db/music.py       — save/load/list/delete sheet_music
"""
from __future__ import annotations

from db.connection import (  # noqa: F401
    DB_PATH,
    get_db_connection,
    init_db,
    _migrate_players_table,
)
from db.constants import (  # noqa: F401
    STATS_INFO,
    BAGS,
    EQUIPMENT,
    HUNTING_GROUNDS,
    NPC_DATA,
)
from db.player import (  # noqa: F401
    save_player_to_db,
    load_player_from_db,
)
from db.village import (  # noqa: F401
    save_village_data,
    load_village_data,
)
from db.music import (  # noqa: F401
    save_sheet_music,
    load_sheet_music,
    load_sheet_music_list,
    delete_sheet_music,
)

__all__ = [
    "DB_PATH",
    "get_db_connection",
    "init_db",
    "_migrate_players_table",
    "STATS_INFO",
    "BAGS",
    "EQUIPMENT",
    "HUNTING_GROUNDS",
    "NPC_DATA",
    "save_player_to_db",
    "load_player_from_db",
    "save_village_data",
    "load_village_data",
    "save_sheet_music",
    "load_sheet_music",
    "load_sheet_music_list",
    "delete_sheet_music",
]
