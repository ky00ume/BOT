"""Persistent current activity for the shared Churider character."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import uuid

from core.agency import AgencyLevel, rule_for
from core.events import GameEvent, EventStore, event_store
from db.connection import get_db_connection


@dataclass(frozen=True)
class Activity:
    activity_id: str
    kind: str
    agency: AgencyLevel
    status: str
    started_at: datetime
    actor_id: int | None
    location: str | None
    context: dict


class ActivityService:
    def __init__(self, *, store: EventStore = event_store):
        self.store = store

    def current(self) -> Activity | None:
        with get_db_connection() as conn:
            row = conn.execute("SELECT value FROM world_state WHERE key='current_activity'").fetchone()
        if not row:
            return None
        return self._decode(json.loads(row["value"]))

    def start_directed(self, kind: str, *, actor_id: int, location: str | None = None, context: dict | None = None, now: datetime | None = None) -> Activity:
        rule = rule_for(kind)
        if rule.level is not AgencyLevel.DIRECTED:
            raise ValueError(f"{kind} is {rule.level.value}, not a directed activity")
        if self.current() is not None:
            raise RuntimeError("Churider is already busy")
        activity = Activity(uuid.uuid4().hex, kind, rule.level, "active", (now or datetime.now(timezone.utc)).astimezone(timezone.utc), actor_id, location, context or {})
        self._save(activity)
        self.store.append(GameEvent(event_type="activity.started", actor_id=actor_id, subject="츄라이더", location=location, occurred_at=activity.started_at, payload={"activity_id": activity.activity_id, "kind": kind, "agency": rule.level.value, **activity.context}))
        return activity

    def reconcile(self, *, now: datetime | None = None, stale_after: timedelta = timedelta(minutes=15)) -> Activity | None:
        """Close an interaction activity whose Discord UI could not survive a restart.

        We do not invent a catch/reward. The durable fact is only that the old
        interaction was interrupted and Churider is available again.
        """
        activity = self.current()
        if activity is None:
            return None
        now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if now_utc - activity.started_at < stale_after:
            return None
        return self.finish(
            activity.activity_id,
            outcome="interrupted",
            payload={"reason": "restart_or_stale_interaction"},
            now=now_utc,
        )

    def finish(self, activity_id: str, *, outcome: str, payload: dict | None = None, now: datetime | None = None) -> Activity | None:
        activity = self.current()
        if activity is None or activity.activity_id != activity_id:
            return None
        ended_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with get_db_connection() as conn:
            conn.execute("DELETE FROM world_state WHERE key='current_activity'")
        self.store.append(GameEvent(event_type="activity.finished", actor_id=activity.actor_id, subject="츄라이더", location=activity.location, occurred_at=ended_at, payload={"activity_id": activity.activity_id, "kind": activity.kind, "outcome": outcome, **(payload or {})}))
        return activity

    def _save(self, activity: Activity) -> None:
        value = json.dumps({"activity_id": activity.activity_id, "kind": activity.kind, "agency": activity.agency.value, "status": activity.status, "started_at": activity.started_at.isoformat(), "actor_id": activity.actor_id, "location": activity.location, "context": activity.context}, ensure_ascii=False)
        with get_db_connection() as conn:
            conn.execute("""INSERT INTO world_state(key,value,updated_at) VALUES('current_activity',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""", (value, datetime.now(timezone.utc).isoformat()))

    @staticmethod
    def _decode(data: dict) -> Activity:
        return Activity(data["activity_id"], data["kind"], AgencyLevel(data["agency"]), data["status"], datetime.fromisoformat(data["started_at"]), data.get("actor_id"), data.get("location"), data.get("context") or {})


activity_service = ActivityService()
