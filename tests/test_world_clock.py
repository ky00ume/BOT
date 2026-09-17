"""World clock tests: autonomous life must be durable, paced, and stateful."""
from datetime import datetime, timedelta, timezone
import random

from core.events import EventStore
from core.world_clock import WorldClock
from player import Player


class FixedRng:
    def __init__(self, activity_index=2):
        self.activity_index = activity_index
    def random(self):
        return 0.0
    def choice(self, seq):
        return seq[self.activity_index]


def test_world_clock_records_real_autonomous_event(temp_db):
    player = Player(name="츄라이더")
    player.energy = 50
    clock = WorldClock(store=EventStore(), rng=FixedRng(activity_index=2))
    now = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    result = clock.advance(player, now=now)

    assert result.event is not None
    assert result.event.event_type == "world.autonomous"
    assert result.event.payload["activity"] == "rest"
    assert player.energy == 55
    assert EventStore().recent(limit=1)[0].event_id == result.event.event_id


def test_world_clock_does_not_repeat_same_interval(temp_db):
    player = Player(name="츄라이더")
    clock = WorldClock(store=EventStore(), rng=FixedRng())
    now = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    first = clock.advance(player, now=now)
    second = clock.advance(player, now=now + timedelta(minutes=10))

    assert first.event is not None
    assert second.event is None
    assert len(EventStore().recent()) == 1


def test_world_clock_advances_again_after_thirty_minutes(temp_db):
    player = Player(name="츄라이더")
    clock = WorldClock(store=EventStore(), rng=FixedRng())
    now = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    clock.advance(player, now=now)
    result = clock.advance(player, now=now + timedelta(minutes=30))

    assert result.event is not None
    assert len(EventStore().recent()) == 2
