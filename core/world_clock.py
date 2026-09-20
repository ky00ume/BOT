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
from core.agency import world_may_start
from core.activities import activity_service
from core.personality import behaviour_cue
from items import ALL_ITEMS
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
    {"kind": "read", "message": "🕷️ 츄라이더가 마을 게시판 앞에 한참 서서 새 글들을 읽었슴미댜.", "diary": "마을 게시판에 새 글이 붙어 있어서 한참 읽었슴미댜. 모르는 소식이 생기는 건 조금 신기함미댜. 📜", "exp": 3},
)


# Things Churider can plausibly come across while living an ordinary life near town.
# Rare finds are deliberately tiny probabilities; quest/story/Legendary items never appear here.
_IDLE_FINDS = (
    {"item": "mat_shiny_button", "weight": 18, "scene": "길가에서 햇빛을 반사하는 반짝이 단추 하나를 발견했슴미댜."},
    {"item": "mat_ribbon_scrap", "weight": 16, "scene": "바람에 굴러다니던 리본 조각을 주워 곱게 접어 왔슴미댜."},
    {"item": "mat_feather", "weight": 15, "scene": "마을 담장 아래 떨어진 깃털 하나를 주워 왔슴미댜."},
    {"item": "gt_flower_01", "weight": 14, "scene": "마을 앞 풀밭에서 들꽃 한 송이를 발견해 가져왔슴미댜."},
    {"item": "gt_herb_01", "weight": 14, "scene": "마을 앞 길가에서 쓸 만한 들풀을 조금 뜯어 왔슴미댜."},
    {"item": "wild_berry", "weight": 12, "scene": "산책길 덤불에서 먹음직한 야생 열매를 발견했슴미댜."},
    {"item": "scrap_branch", "weight": 9, "scene": "마을 앞에 떨어진 반듯한 잡목 가지를 하나 주워 왔슴미댜."},
    {"item": "mat_magic_thread", "weight": 1.6, "scene": "평범한 실인 줄 알고 주웠는데 희미하게 빛나는 마법실이었슴미댜."},
    {"item": "gem_ruby", "weight": 0.20, "scene": "배수로 옆에서 유난히 붉게 반짝이는 조각을 건졌는데, 닦아 보니 루비였슴미댜."},
    {"item": "gem_sapphire", "weight": 0.16, "scene": "개울가 돌틈에서 파란 빛이 보여 꺼내 왔는데 사파이어였슴미댜."},
    {"item": "gem_emerald", "weight": 0.12, "scene": "풀숲 사이에서 초록빛 돌 하나를 발견했는데 에메랄드였슴미댜."},
)
_IDLE_FIND_CHANCE = 0.22


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
        # A player-directed activity owns Churider's attention. The world may keep
        # time, but it must not make Churider nap/read/walk at the same time.
        if activity_service.current():
            return WorldTickResult(None, None, False)
        if self.rng.random() >= 0.60:
            return WorldTickResult(None, None, False)

        activity = dict(self.rng.choice(_AUTONOMOUS_ACTIVITIES))
        cue = behaviour_cue(self.store)
        if cue.idle_message and self.rng.random() < 0.25:
            activity["message"] = cue.idle_message
            activity["diary"] = cue.idle_message.replace("🕷️ ", "")
        if not world_may_start(activity["kind"]):
            return WorldTickResult(None, None, False)
        changed = self._apply_effect(player, activity)
        found = self._maybe_find_item(player, activity)
        if found:
            changed = True
            activity["message"] = f"{activity['message']}\n🎒 {found['scene']}"
            activity["diary"] = f"{activity['diary']} {found['scene']}"
        event = GameEvent(
            event_type="world.autonomous",
            subject="츄라이더",
            location="비전 타운",
            occurred_at=now_utc,
            payload={
                "activity": activity["kind"],
                "message": activity["message"],
                "diary_text": activity["diary"],
                "find": found,
            },
        )
        self.store.append(event)
        return WorldTickResult(event, activity["message"], changed)

    def _maybe_find_item(self, player, activity: dict) -> dict | None:
        # Only ordinary outside life can produce finds. Napping, reading and
        # personality flavour do not magically create loot.
        if activity.get("kind") != "walk" or self.rng.random() >= _IDLE_FIND_CHANCE:
            return None
        entry = self.rng.choices(_IDLE_FINDS, weights=[row["weight"] for row in _IDLE_FINDS], k=1)[0]
        item = ALL_ITEMS.get(entry["item"], {})
        # Defence in depth: autonomous life must never mint quest/story or
        # Legendary resources even if the table is edited later.
        if entry["item"].startswith(("quest_", "story_")) or item.get("grade") == "Legendary":
            return None
        if not player.add_item(entry["item"], 1):
            return None
        return {"item_id": entry["item"], "name": item.get("name", entry["item"]), "count": 1, "scene": entry["scene"]}

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
