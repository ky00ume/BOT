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
    def choices(self, population, weights=None, k=1):
        return [population[0]]


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


def test_walk_can_bring_home_a_plausible_small_find(temp_db):
    player = Player(name="츄라이더")
    clock = WorldClock(store=EventStore(), rng=FixedRng(activity_index=0))
    now = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)

    result = clock.advance(player, now=now)

    found = result.event.payload["find"]
    assert found["item_id"] == "mat_shiny_button"
    assert player.inventory["mat_shiny_button"] == 1
    assert "반짝이 단추" in result.message


def test_non_walk_idle_life_does_not_create_loot(temp_db):
    player = Player(name="츄라이더")
    clock = WorldClock(store=EventStore(), rng=FixedRng(activity_index=2))
    result = clock.advance(player, now=datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc))
    assert result.event.payload["find"] is None
    assert not player.inventory


def test_autonomous_find_table_contains_no_legendary_or_story_items():
    from core.world_clock import _IDLE_FINDS
    from items import ALL_ITEMS
    for row in _IDLE_FINDS:
        item = ALL_ITEMS[row["item"]]
        assert item.get("grade") != "Legendary"
        assert not row["item"].startswith(("quest_", "story_"))


def test_world_life_has_time_context_without_changing_rewards():
    assert WorldClock._period(6) == "dawn"
    assert WorldClock._period(23) == "night"
    assert "새벽" in WorldClock._context_line("walk", "cloudy", "dawn")
    assert "불이 하나둘" in WorldClock._context_line("read", "cloudy", "night")


def test_weather_can_change_plausible_life_scene():
    assert "처마" in WorldClock._context_line("walk", "rain", "day")
    assert "밖으로 나가지 않고" in WorldClock._context_line("walk", "storm", "day")
    assert WorldClock._context_line("web", "rain", "day") is None
