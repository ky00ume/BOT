"""app_context.py — 전역 공유 객체 레지스트리 (순환 import 방지)

main.py / config/bot_config.py 에서 초기화 시 register() 로 등록하면,
다른 모듈에서 from main import X 대신 app_context.get_X() 로 접근합니다.
"""
from __future__ import annotations
from typing import Any

_store: dict[str, Any] = {}


def register(key: str, obj: Any) -> None:
    _store[key] = obj


def get(key: str) -> Any:
    return _store.get(key)


# Typed convenience accessors
def get_player():
    return _store.get("shared_player")


def get_save_manager():
    return _store.get("save_manager")


def get_battle_engine():
    return _store.get("battle_engine")


def get_encounter_manager():
    return _store.get("encounter_manager")


def get_quest_manager():
    return _store.get("quest_manager")


def get_story_quest_manager():
    return _store.get("story_quest_manager")


def get_achievement_manager():
    return _store.get("achievement_manager")


def get_diary_manager():
    return _store.get("diary_manager")


def get_npc_manager():
    return _store.get("npc_manager")


def get_affinity_manager():
    return _store.get("affinity_manager")


def get_gathering_engine():
    return _store.get("gathering_engine")


def get_fishing_engine():
    return _store.get("fishing_engine")
