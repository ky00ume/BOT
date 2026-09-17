"""Long-term affection growth for the shared Churider.

Momentary condition stays descriptive; bond is an explicit level players can raise.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from datetime import datetime, timezone
import json

from core.events import GameEvent, EventStore, event_store
from db.connection import get_db_connection

MAX_BOND_LEVEL = 100
BASE_XP = {
    "care.pet": 8,
    "care.feed": 14,
    "care.play": 18,
    "activity.fishing": 24,
    "battle.won": 28,
    "quest.completed": 45,
    "story.milestone": 60,
    "care.heal": 25,
}


@dataclass(frozen=True)
class BondState:
    level: int
    xp: int
    lifetime_xp: int

    @property
    def next_xp(self) -> int:
        return 0 if self.level >= MAX_BOND_LEVEL else xp_for_next(self.level)


def xp_for_next(level: int) -> int:
    # Friendly early levels, deliberately long tail toward 100.
    return 60 + level * 18 + (level // 10) * 40


def bond_title(level: int) -> str:
    if level >= 100: return "평생의 가족"
    if level >= 80: return "서로를 아주 잘 아는 사이"
    if level >= 60: return "없으면 허전한 사이"
    if level >= 40: return "제법 마음을 연 사이"
    if level >= 20: return "기다리게 되는 사람"
    if level >= 10: return "낯익고 반가운 사람"
    return "조금씩 알아가는 사이"


@dataclass(frozen=True)
class HabitProfile:
    primary: str | None
    description: str


def habit_profile(store: EventStore = event_store) -> HabitProfile:
    """Read recent lived experience as a soft habit, never as a punishment."""
    recent = store.recent(limit=80)
    kinds = []
    mapping = {
        "care.pet": "pet",
        "care.feed": "feed",
        "care.play": "play",
        "activity.finished": "activity",
        "battle.won": "adventure",
    }
    for event in recent:
        if event.event_type == "activity.finished" and event.payload.get("kind") == "fishing":
            kinds.append("fishing")
        elif event.event_type in mapping:
            kinds.append(mapping[event.event_type])
    if not kinds:
        return HabitProfile(None, "아직 뚜렷하게 굳은 버릇은 없습니다. 같이 지내며 조금씩 생길 것 같습니다.")
    counts = Counter(kinds)
    kind, count = counts.most_common(1)[0]
    if count < 3:
        return HabitProfile(None, "아직 한 가지 버릇으로 굳지는 않았지만, 같이 한 일들을 차곡차곡 기억하고 있습니다.")
    descriptions = {
        "pet": "쓰다듬을 좋아하게 된 모양입니다. 손이 가까이 오면 예전보다 먼저 기대어 옵니다.",
        "feed": "먹을 것을 챙겨주는 손을 유심히 보는 버릇이 생겼습니다.",
        "play": "사람이 찾아오면 혹시 놀아주려나 하고 먼저 기대하는 버릇이 생겼습니다.",
        "fishing": "낚싯대만 보여도 물가에 나가는 건가 싶어 슬쩍 따라붙는 버릇이 생겼습니다.",
        "activity": "시키신 일을 마치고 돌아와 반응을 살피는 버릇이 조금 생겼습니다.",
        "adventure": "밖에서 함께 겪은 일이 많아져, 외출 준비를 하면 먼저 눈치를 챕니다.",
    }
    return HabitProfile(kind, descriptions[kind])


class BondService:
    def __init__(self, *, store: EventStore = event_store):
        self.store = store

    def get(self) -> BondState:
        with get_db_connection() as conn:
            row = conn.execute("SELECT value FROM world_state WHERE key='bond_state'").fetchone()
        if not row:
            return BondState(1, 0, 0)
        data = json.loads(row["value"])
        return BondState(int(data.get("level", 1)), int(data.get("xp", 0)), int(data.get("lifetime_xp", 0)))

    def award(self, reason: str, *, actor_id: int | None = None, amount: int | None = None, now: datetime | None = None) -> BondState:
        base = int(amount if amount is not None else BASE_XP.get(reason, 0))
        if base <= 0:
            return self.get()
        state = self.get()
        # Repeating one interaction is still useful, but variety grows the bond faster.
        repeats = sum(1 for e in self.store.recent(limit=12) if e.event_type == "bond.gained" and e.payload.get("reason") == reason)
        multiplier = 1.0 if repeats < 2 else 0.65 if repeats < 5 else 0.35
        gained = max(1, round(base * multiplier))
        level, xp = state.level, state.xp + gained
        while level < MAX_BOND_LEVEL and xp >= xp_for_next(level):
            xp -= xp_for_next(level)
            level += 1
        if level >= MAX_BOND_LEVEL:
            xp = 0
        updated = BondState(level, xp, state.lifetime_xp + gained)
        self._save(updated, now=now)
        self.store.append(GameEvent(event_type="bond.gained", actor_id=actor_id, subject="츄라이더", occurred_at=now or datetime.now(timezone.utc), payload={"reason": reason, "xp": gained, "level": level, "lifetime_xp": updated.lifetime_xp}))
        return updated

    @staticmethod
    def _save(state: BondState, *, now: datetime | None = None) -> None:
        value = json.dumps({"level": state.level, "xp": state.xp, "lifetime_xp": state.lifetime_xp})
        stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        with get_db_connection() as conn:
            conn.execute("""INSERT INTO world_state(key,value,updated_at) VALUES('bond_state',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""", (value, stamp))


bond_service = BondService()
