import pytest

from core.activities import ActivityService
from core.directed_gathering import DirectedGatheringService
from core.events import EventStore
from core.target_gathering import TargetGatheringRunner


class FixedRng:
    def uniform(self, a, b): return 0.01
    def randint(self, a, b): return b


@pytest.mark.asyncio
async def test_target_mining_runs_silently_until_goal(monkeypatch, fresh_player, temp_db):
    fresh_player.inventory["copper_ore"] = 1
    fresh_player.energy = 100
    activities = ActivityService(store=EventStore())
    service = DirectedGatheringService(activities=activities, store=EventStore())
    activity, _ = service.start_for_recipe(fresh_player, item_id="copper_ore", required_count=5, actor_id=1)
    runner = TargetGatheringRunner(rng=FixedRng(), sleep=lambda _: _noop())
    monkeypatch.setattr("core.target_gathering.directed_gathering.activities", activities)
    monkeypatch.setattr("core.target_gathering.save_manager.save", lambda player: True)
    result = await runner.run(fresh_player, activity)
    assert result.stop_reason == "target_reached"
    assert result.final_count >= 5
    assert result.attempts == 2
    assert result.energy_spent == 20
    assert activities.current() is None


@pytest.mark.asyncio
async def test_target_gathering_stops_on_energy_without_fake_reward(monkeypatch, fresh_player, temp_db):
    fresh_player.energy = 0
    activities = ActivityService(store=EventStore())
    service = DirectedGatheringService(activities=activities, store=EventStore())
    activity, _ = service.start_for_recipe(fresh_player, item_id="copper_ore", required_count=3, actor_id=1)
    runner = TargetGatheringRunner(rng=FixedRng(), sleep=lambda _: _noop())
    monkeypatch.setattr("core.target_gathering.directed_gathering.activities", activities)
    monkeypatch.setattr("core.target_gathering.save_manager.save", lambda player: True)
    result = await runner.run(fresh_player, activity)
    assert result.stop_reason == "energy_empty"
    assert result.final_count == 0
    assert result.attempts == 0
    assert activities.current() is None


async def _noop():
    return None
