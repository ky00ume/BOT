"""Execution loop for player-directed, target-count gathering."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import random

from core.directed_gathering import directed_gathering
from gathering import GATHER_ITEMS_BY_SEASON, MINE_ITEMS, get_current_season
from save_manager import save_manager
from core.sound_director import sound_director


@dataclass
class TargetGatherResult:
    item_id: str
    item_name: str
    start_count: int
    final_count: int
    target_count: int
    attempts: int = 0
    energy_spent: int = 0
    stop_reason: str = "target_reached"
    finds: dict[str, int] = field(default_factory=dict)

    @property
    def gained_target(self) -> int:
        return max(0, self.final_count - self.start_count)


class TargetGatheringRunner:
    """Runs ordinary gathering silently and reports one aggregate result.

    A target item is guaranteed only when the legacy mode can actually produce it;
    other rolls are kept as by-products. This is still player-directed work and is
    bounded by energy, inventory, target amount and max attempts.
    """
    COSTS = {"gather": 8, "mine": 10, "woodcut": 9}

    def __init__(self, *, rng=None, sleep=asyncio.sleep):
        self.rng = rng or random
        self.sleep = sleep

    def _pool(self, player, mode: str):
        if mode == "mine":
            strength = player.base_stats.get("str", 10)
            rank = player.skill_ranks.get("mining", "연습")
            order = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]
            rank_i = order.index(rank) if rank in order else 0
            return [x for x in MINE_ITEMS if strength >= x["str_req"] and (not x.get("rank_req") or rank_i >= order.index(x["rank_req"]))]
        if mode == "gather":
            return list(GATHER_ITEMS_BY_SEASON[get_current_season()])
        # Recipe-driven wood targets use their requested item directly. Legacy
        # woodcut tables mix rank progression and random field drops inconsistently.
        return []

    def _roll(self, pool: list[dict]) -> dict:
        total = sum(float(x.get("rate", 1)) for x in pool)
        roll = self.rng.uniform(0, total)
        upto = 0.0
        for item in pool:
            upto += float(item.get("rate", 1))
            if roll <= upto:
                return item
        return pool[-1]

    async def run(self, player, activity, *, max_attempts: int = 40, tick_seconds: float = 1.5, on_progress=None, should_stop=None) -> TargetGatherResult:
        item_id = activity.context["item_id"]
        item_name = activity.context["item_name"]
        mode = activity.context["mode"]
        target = int(activity.context["target_count"])
        start = int(player.inventory.get(item_id, 0))
        result = TargetGatherResult(item_id, item_name, start, start, target)
        cost = self.COSTS.get(mode, 8)
        pool = self._pool(player, mode)
        target_entry = next((x for x in pool if x["id"] == item_id), None)
        if mode != "woodcut" and target_entry is None:
            result.stop_reason = "unavailable_here"
            directed_gathering.activities.finish(activity.activity_id, outcome=result.stop_reason)
            return result

        sound_director.cue({"mine": "life/mining/start", "woodcut": "life/woodcut/start", "gather": "life/gather/start"}.get(mode, "life/gather/start"))
        while player.inventory.get(item_id, 0) < target and result.attempts < max_attempts:
            if should_stop and should_stop():
                result.stop_reason = "cancelled"
                break
            if not player.consume_energy(cost):
                result.stop_reason = "energy_empty"
                break
            result.energy_spent += cost
            result.attempts += 1
            sound_director.cue({"mine": "life/mining/hit", "woodcut": "life/woodcut/hit", "gather": "life/gather/pick"}.get(mode, "life/gather/pick"))
            # Keep the legacy random-field feel. If the requested material is not
            # rolled this attempt, the by-product is still real loot.
            if mode == "woodcut":
                found = {"id": item_id, "name": item_name, "grade": "Normal"}
                count = self.rng.randint(1, 3)
            else:
                found = self._roll(pool)
                count = self.rng.randint(1, 2 if mode == "mine" else 3)
            if not player.add_item(found["id"], count):
                result.stop_reason = "inventory_full"
                break
            result.finds[found["id"]] = result.finds.get(found["id"], 0) + count
            current_target = int(player.inventory.get(item_id, 0))
            directed_gathering.activities.update_context(
                activity.activity_id,
                progress_count=current_target,
                target_count=target,
                energy=int(player.energy),
                attempts=result.attempts,
            )
            if mode == "mine":
                player.train_skill("mining", 12.0)
            elif mode == "gather":
                player.train_skill("gathering", 10.0)
            else:
                player.train_skill("woodcutting", 11.0)
            save_manager.save(player)
            if on_progress:
                maybe_awaitable = on_progress(result, current_target, target)
                if maybe_awaitable is not None:
                    await maybe_awaitable
            if tick_seconds > 0:
                await self.sleep(tick_seconds)

        result.final_count = int(player.inventory.get(item_id, 0))
        if result.final_count >= target:
            result.stop_reason = "target_reached"
        elif result.attempts >= max_attempts and result.stop_reason == "target_reached":
            result.stop_reason = "attempt_limit"
        directed_gathering.activities.finish(
            activity.activity_id,
            outcome=result.stop_reason,
            payload={"item_id": item_id, "target_count": target, "final_count": result.final_count, "attempts": result.attempts},
        )
        save_manager.save(player)
        sound_director.cue("life/gather/complete" if result.stop_reason == "target_reached" else "life/gather/stop", interrupt=True)
        return result


target_gathering_runner = TargetGatheringRunner()
