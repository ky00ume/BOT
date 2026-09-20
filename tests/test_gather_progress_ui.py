import pytest

from core.activities import ActivityService
from core.directed_gathering import DirectedGatheringService
from core.events import EventStore
from core.target_gathering import TargetGatheringRunner
from renderer.cards import BG3Renderer


class FixedRng:
    def uniform(self, a, b): return 0.01
    def randint(self, a, b): return b


@pytest.mark.asyncio
async def test_progress_callback_sees_persisted_counts(monkeypatch, fresh_player, temp_db):
    fresh_player.inventory["copper_ore"] = 1
    fresh_player.energy = 100
    activities = ActivityService(store=EventStore())
    service = DirectedGatheringService(activities=activities, store=EventStore())
    activity, _ = service.start_for_recipe(fresh_player, item_id="copper_ore", required_count=5, actor_id=1)
    runner = TargetGatheringRunner(rng=FixedRng(), sleep=lambda _: _noop())
    monkeypatch.setattr("core.target_gathering.directed_gathering.activities", activities)
    monkeypatch.setattr("core.target_gathering.save_manager.save", lambda player: True)
    seen = []
    async def progress(result, current, target):
        persisted = activities.current()
        seen.append((current, target, persisted.context["progress_count"], fresh_player.energy))
    result = await runner.run(fresh_player, activity, tick_seconds=0, on_progress=progress)
    assert result.stop_reason == "target_reached"
    assert seen == [(3, 5, 3, 90), (5, 5, 5, 80)]


@pytest.mark.asyncio
async def test_cancel_stops_before_spending_more_energy(monkeypatch, fresh_player, temp_db):
    fresh_player.energy = 100
    activities = ActivityService(store=EventStore())
    service = DirectedGatheringService(activities=activities, store=EventStore())
    activity, _ = service.start_for_recipe(fresh_player, item_id="copper_ore", required_count=9, actor_id=1)
    runner = TargetGatheringRunner(rng=FixedRng(), sleep=lambda _: _noop())
    monkeypatch.setattr("core.target_gathering.directed_gathering.activities", activities)
    monkeypatch.setattr("core.target_gathering.save_manager.save", lambda player: True)
    cancelled = False
    async def progress(result, current, target):
        nonlocal cancelled
        cancelled = True
    result = await runner.run(fresh_player, activity, tick_seconds=0, on_progress=progress, should_stop=lambda: cancelled)
    assert result.stop_reason == "cancelled"
    assert result.attempts == 1
    assert fresh_player.energy == 90
    assert activities.current() is None


def test_progress_card_renders_png():
    buf = BG3Renderer().render_gather_progress("철광석", 2, 5, energy=72, max_energy=100)
    assert buf.getvalue()[:4] == bytes([137, 80, 78, 71])


async def _noop():
    return None


