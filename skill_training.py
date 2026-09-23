"""생활 스킬 수련 항목 진행도.

랭크업 자체는 기존 EXP 게이지를 유지하고, 이 모듈은 '어떤 행동으로 수련했는지'를
랭크별 체크리스트로 남긴다. 랭크가 오르면 해당 랭크의 항목 진행도는 새로 시작한다.
"""

from skills_db import RANK_ORDER


def _rank_index(rank: str) -> int:
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return 0


def training_objectives(skill_id: str, rank: str) -> list[dict]:
    idx = _rank_index(rank)

    if skill_id == "mining":
        rows = [
            {"event": "mine_success", "label": "광석을 채굴한다", "target": 8 + idx * 2},
        ]
        if idx >= 1:
            rows.append({"event": "mine_uncommon", "label": "희귀 광물·보석을 캔다", "target": 2 + idx // 3})
        if idx >= 4:
            rows.append({"event": "mine_precious", "label": "귀금속·고급 광물을 캔다", "target": 1 + idx // 4})
        return rows

    if skill_id == "metallurgy":
        rows = [
            {"event": "smelt_attempt", "label": "제련을 시도한다", "target": 8 + idx * 2},
            {"event": "smelt_success", "label": "제련에 성공한다", "target": 5 + idx},
        ]
        if idx <= 5:
            rows.append({"event": "smelt_failure", "label": "제련 실패에서 배운다", "target": 2})
        if idx >= 4:
            rows.append({"event": "smelt_advanced", "label": "고급 금속을 제련한다", "target": 1 + idx // 4})
        return rows

    if skill_id == "blacksmith":
        rows = [
            {"event": "forge_complete", "label": "장비를 완성한다", "target": 4 + idx},
            {"event": "forge_fine", "label": "양호 이상 품질로 완성한다", "target": 2 + idx // 3},
        ]
        if idx >= 3:
            rows.append({"event": "forge_excellent", "label": "훌륭함 이상으로 완성한다", "target": 1 + idx // 4})
        if idx >= 6:
            rows.append({"event": "forge_masterpiece", "label": "걸작을 만든다", "target": 1})
        return rows

    return []


def training_progress(player, skill_id: str, rank: str | None = None) -> list[dict]:
    rank = rank or player.skill_ranks.get(skill_id, "연습")
    flags = getattr(player, "_flags", {}) or {}
    bucket = flags.get("skill_training", {}).get(skill_id, {})
    # 다른 랭크의 진행도는 다음 랭크에 들고 가지 않는다.
    progress = bucket.get("progress", {}) if bucket.get("rank") == rank else {}
    result = []
    for row in training_objectives(skill_id, rank):
        item = dict(row)
        item["current"] = min(int(progress.get(row["event"], 0)), int(row["target"]))
        result.append(item)
    return result


def record_training_event(player, skill_id: str, event: str, count: int = 1) -> int:
    if count <= 0:
        return 0
    rank = player.skill_ranks.get(skill_id, "연습")
    objectives = {row["event"]: row for row in training_objectives(skill_id, rank)}
    if event not in objectives:
        return 0
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    all_training = player._flags.setdefault("skill_training", {})
    bucket = all_training.setdefault(skill_id, {"rank": rank, "progress": {}})
    if bucket.get("rank") != rank:
        bucket.clear()
        bucket.update({"rank": rank, "progress": {}})
    progress = bucket.setdefault("progress", {})
    target = int(objectives[event]["target"])
    progress[event] = min(target, int(progress.get(event, 0)) + int(count))
    return progress[event]


def clear_training_for_new_rank(player, skill_id: str, rank: str) -> None:
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    training = player._flags.setdefault("skill_training", {})
    training[skill_id] = {"rank": rank, "progress": {}}
