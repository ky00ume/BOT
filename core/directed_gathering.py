"""Goal-based gathering requested by a player.

This is deliberately not autonomous life: a player chooses the material and target
amount. Churider may repeat the mundane work until the goal or a safe stop condition.
"""
from dataclasses import dataclass

from core.activities import Activity, ActivityService, activity_service
from core.events import EventStore, event_store
from gathering import GATHER_ITEMS_BY_SEASON, GATHER_ZONE_ITEMS, MINE_ITEMS, WOODCUT_TABLE, get_current_season
from items import ALL_ITEMS


@dataclass(frozen=True)
class GatherTarget:
    item_id: str
    name: str
    mode: str
    target_count: int
    have_at_start: int

    @property
    def missing(self) -> int:
        return max(0, self.target_count - self.have_at_start)


def _all_gatherables() -> dict[str, str]:
    modes: dict[str, str] = {}
    for rows in GATHER_ITEMS_BY_SEASON.values():
        for row in rows:
            modes.setdefault(row["id"], "gather")
    for rows in GATHER_ZONE_ITEMS.values():
        for row in rows:
            modes.setdefault(row["id"], "gather")
    for row in MINE_ITEMS:
        modes[row["id"]] = "mine"
    for row in WOODCUT_TABLE.values():
        modes[row["id"]] = "woodcut"
    return modes


GATHERABLE_MODES = _all_gatherables()


def missing_recipe_ingredients(player, recipe: dict) -> list[dict]:
    """Return only recipe ingredients that have a known gathering route."""
    result = []
    for item_id, need in recipe.get("ingredients", {}).items():
        have = player.inventory.get(item_id, 0)
        missing = max(0, int(need) - int(have))
        mode = GATHERABLE_MODES.get(item_id)
        if missing and mode:
            result.append({
                "item_id": item_id,
                "name": ALL_ITEMS.get(item_id, {}).get("name", item_id),
                "have": have,
                "need": int(need),
                "missing": missing,
                "mode": mode,
            })
    return result


class DirectedGatheringService:
    def __init__(self, *, activities: ActivityService = activity_service, store: EventStore = event_store):
        self.activities = activities
        self.store = store

    def start_for_recipe(self, player, *, item_id: str, required_count: int, actor_id: int | None) -> tuple[Activity, GatherTarget]:
        mode = GATHERABLE_MODES.get(item_id)
        if not mode:
            raise ValueError("이 재료는 현재 자동 채집 경로가 없슴미댜.")
        have = player.inventory.get(item_id, 0)
        if have >= required_count:
            raise ValueError("이미 필요한 만큼 가지고 있슴미댜.")
        target = GatherTarget(item_id, ALL_ITEMS.get(item_id, {}).get("name", item_id), mode, required_count, have)
        activity = self.activities.start_directed(
            "gathering",
            actor_id=actor_id,
            context={
                "item_id": item_id,
                "item_name": target.name,
                "mode": mode,
                "target_count": required_count,
                "have_at_start": have,
                "requested_count": target.missing,
            },
        )
        return activity, target

    def progress(self, player, activity: Activity) -> tuple[int, int]:
        target = int(activity.context["target_count"])
        have = int(player.inventory.get(activity.context["item_id"], 0))
        return have, target

    def finish_if_reached(self, player, activity: Activity) -> bool:
        have, target = self.progress(player, activity)
        if have < target:
            return False
        self.activities.finish(
            activity.activity_id,
            outcome="target_reached",
            payload={"item_id": activity.context["item_id"], "target_count": target, "final_count": have},
        )
        return True


directed_gathering = DirectedGatheringService()
