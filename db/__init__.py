"""db 패키지 — 기존 import 호환 re-export."""
from __future__ import annotations

from db.connection import DB_PATH, get_db_connection, init_db, _migrate_players_table
from db.constants import STATS_INFO, BAGS, EQUIPMENT, HUNTING_GROUNDS, NPC_DATA
from db.player import save_player_to_db, load_player_from_db
from db.village import save_village_data, load_village_data
from db.music import save_sheet_music, load_sheet_music, load_sheet_music_list, delete_sheet_music

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
