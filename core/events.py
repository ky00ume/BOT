"""Durable facts produced by player and world actions.

The event log is intentionally not the source of truth yet. Existing game state
continues to work while new systems (memory, diary, traces) consume durable facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
import json
import sqlite3
import uuid

from db.connection import get_db_connection


@dataclass(frozen=True)
class GameEvent:
    event_type: str
    actor_id: int | None = None
    subject: str | None = None
    location: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)


class EventStore:
    """Append/read boundary for durable world facts."""

    def append(self, event: GameEvent) -> GameEvent:
        payload_json = json.dumps(dict(event.payload), ensure_ascii=False, separators=(",", ":"))
        with get_db_connection() as conn:
            conn.execute(
                """INSERT INTO game_events
                   (event_id, occurred_at, event_type, actor_id, subject, location, payload)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.occurred_at.astimezone(timezone.utc).isoformat(),
                    event.event_type,
                    event.actor_id,
                    event.subject,
                    event.location,
                    payload_json,
                ),
            )
        return event

    def recent(self, *, limit: int = 100, event_type: str | None = None) -> list[GameEvent]:
        if limit < 1:
            return []
        sql = "SELECT * FROM game_events"
        params: list[Any] = []
        if event_type is not None:
            sql += " WHERE event_type = ?"
            params.append(event_type)
        sql += " ORDER BY occurred_at DESC, rowid DESC LIMIT ?"
        params.append(limit)
        with get_db_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._from_row(row) for row in rows]

    def between(self, start: datetime, end: datetime) -> list[GameEvent]:
        """Return events in a UTC-normalized half-open time window."""
        start_utc = start.astimezone(timezone.utc).isoformat()
        end_utc = end.astimezone(timezone.utc).isoformat()
        with get_db_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM game_events
                   WHERE occurred_at >= ? AND occurred_at < ?
                   ORDER BY occurred_at ASC, rowid ASC""",
                (start_utc, end_utc),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> GameEvent:
        return GameEvent(
            event_id=row["event_id"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            event_type=row["event_type"],
            actor_id=row["actor_id"],
            subject=row["subject"],
            location=row["location"],
            payload=json.loads(row["payload"] or "{}"),
        )


event_store = EventStore()
