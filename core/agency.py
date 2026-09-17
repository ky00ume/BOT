"""Agency boundaries between Churider, the world, and human players."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgencyLevel(str, Enum):
    AUTONOMOUS = "autonomous"
    DIRECTED = "directed"
    PLAYER_CONTROLLED = "player_controlled"
    FORBIDDEN_AUTONOMY = "forbidden_autonomy"


@dataclass(frozen=True)
class AgencyRule:
    activity: str
    level: AgencyLevel
    reason: str


_RULES = {
    "rest": AgencyRule("rest", AgencyLevel.AUTONOMOUS, "ordinary self-care"),
    "walk": AgencyRule("walk", AgencyLevel.AUTONOMOUS, "ordinary daily life"),
    "web": AgencyRule("web", AgencyLevel.AUTONOMOUS, "ordinary daily life"),
    "read": AgencyRule("read", AgencyLevel.AUTONOMOUS, "ordinary daily life"),
    "fishing": AgencyRule("fishing", AgencyLevel.DIRECTED, "player starts the fishing game"),
    "gathering": AgencyRule("gathering", AgencyLevel.DIRECTED, "player chooses to spend time/resources"),
    "crafting": AgencyRule("crafting", AgencyLevel.DIRECTED, "player chooses recipe/resources"),
    "battle": AgencyRule("battle", AgencyLevel.PLAYER_CONTROLLED, "combat decisions belong to the player"),
    "quest": AgencyRule("quest", AgencyLevel.PLAYER_CONTROLLED, "quest choices belong to the player"),
    "story": AgencyRule("story", AgencyLevel.PLAYER_CONTROLLED, "story decisions belong to the player"),
    "relationship_commitment": AgencyRule("relationship_commitment", AgencyLevel.FORBIDDEN_AUTONOMY, "irreversible relationship choices require a player"),
    "contract": AgencyRule("contract", AgencyLevel.FORBIDDEN_AUTONOMY, "contracts require explicit player choice"),
    "rare_resource_spend": AgencyRule("rare_resource_spend", AgencyLevel.FORBIDDEN_AUTONOMY, "valuable resources are never auto-spent"),
}


def rule_for(activity: str) -> AgencyRule:
    # Unknown gameplay is conservative by default: the world may not play it.
    return _RULES.get(activity, AgencyRule(activity, AgencyLevel.PLAYER_CONTROLLED, "unclassified gameplay defaults to player control"))


def world_may_start(activity: str) -> bool:
    return rule_for(activity).level is AgencyLevel.AUTONOMOUS


def player_may_direct(activity: str) -> bool:
    return rule_for(activity).level in {AgencyLevel.DIRECTED, AgencyLevel.PLAYER_CONTROLLED, AgencyLevel.FORBIDDEN_AUTONOMY}
