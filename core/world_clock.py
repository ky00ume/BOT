"""Server-owned world clock and autonomous Churider activity.

Discord is only the presentation surface. The clock decides when the world may
advance, persists its own cursor, mutates authoritative player state, and records
what actually happened as GameEvents.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import random
from typing import Callable

from core.events import GameEvent, EventStore, event_store
from db.connection import get_db_connection

KST = timezone(timedelta(hours=9))
TICK_MINUTES = 30


@dataclass(frozen=True)
class WorldTickResult:
    event: GameEvent | None
    message: str | None
    changed_state: bool = False


_AUTONOMOUS_ACTIVITIES = (
    {"kind": "walk", "message": "🕷️ 츄라이더가 마을을 한 바퀴 천천히 산책하고 돌아왔슴미댜.", "diary": "마을을 천천히 한 바퀴 걸었슴미댜. 바람이 괜히 좋아서 조금 더 걷고 싶었슴미댜. 🍃"},
    {"kind": "web", "message": "🕷️ 츄라이더가 느슨해진 거미줄을 다시 팽팽하게 손봤슴미댜.", "diary": "느슨해진 거미줄을 다시 손봤슴미댜. 반듯해진 걸 보니까 괜히 뿌듯했슴미댜. 🕸️"},
    {"kind": "rest", "message": "🕷️ 츄라이더가 거미줄 해먹에서 잠깐 낮잠을 잤슴미댜.", "diary": "거미줄 해먹에서 잠깐 졸았슴미댜. 눈을 뜨니까 몸이 조금 가벼워졌슴미댜. 💤", "energy": 5},
    {"kind": "gather", "message": "🕷️ 츄라이더가 산책길에서 약초 한 포기를 발견해 챙겨왔슴미댜. 🌿", "diary": "산책하다가 약초 한 포기를 발견했슴미댜. 그냥 지나칠까 하다가 잘 챙겨왔슴미댜. 🌿", "item": "herb"},
    {"kind": "read", "message": "🕷️ 츄라이더가 마을 게시판 앞에 한참 서서 새 글들을 읽었슴미댜.", "diary": "마을 게시판에 새 글이 붙어 있어서 한참 읽었슴미댜. 모르는 소식이 생기는 건 조금 신기함미댜. 📜", "exp": 3},
)


class WorldClock:
    def __init__(self, *, store: EventStore = event_store, rng: random.Random | None = None):
        self.store = store
        self.rng = rng or random.Random()

    def advance(self, player, *, now: datetime | None = None) -> WorldTickResult:
        now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        last_tick = self._load_cursor()
        if last_tick and now_utc - last_tick < timedelta(minutes=TICK_MINUTES):
            return WorldTickResult(None, None, False)

        # Advance the cursor even when the world is quiet. Reconnects therefore do
        # not replay the same interval or manufacture a backlog of fake history.
        self._save_cursor(now_utc)
        if self.rng.random() >= 0.60:
            return WorldTickResult(None, None, False)

        activity = dict(self.rng.choice(_AUTONOMOUS_ACTIVITIES))
        changed = self._apply_effect(player, activity)
        event = GameEvent(
            event_type="world.autonomous",
            subject="츄라이더",
            location="비전 타운",
            occurred_at=now_utc,
            payload={
                "activity": activity["kind"],
                "message": activity["message"],
                "diary_text": activity["diary"],
            },
        )
        self.store.append(event)
        return WorldTickResult(event, activity["message"], changed)

    @staticmethod
    def _apply_effect(player, activity: dict) -> bool:
        if "energy" in activity:
            before = player.energy
            player.restore_energy(activity["energy"])
            return player.energy != before
        if "item" in activity:
            player.add_item(activity["item"], 1)
            return True
        if "exp" in activity:
            player.exp += activity["exp"]
            return True
        return False

    @staticmethod
    def _load_cursor() -> datetime | None:
        with get_db_connection() as conn:
            row = conn.execute("SELECT value FROM world_state WHERE key = 'last_tick_at'").fetchone()
        if not row:
            return None
        return datetime.fromisoformat(json.loads(row["value"])).astimezone(timezone.utc)

    @staticmethod
    def _save_cursor(now_utc: datetime) -> None:
        value = json.dumps(now_utc.isoformat())
        with get_db_connection() as conn:
            conn.execute(
                """INSERT INTO world_state(key, value, updated_at) VALUES('last_tick_at', ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (value, now_utc.isoformat()),
            )


world_clock = WorldClock()
