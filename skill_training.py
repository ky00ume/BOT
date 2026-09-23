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

    if skill_id == "smash":
        rows = [
            {"event": "smash_use", "label": "스매시를 사용한다", "target": 8 + idx * 2},
            {"event": "smash_crit", "label": "스매시로 크리티컬을 낸다", "target": 2 + idx // 3},
        ]
        if idx >= 3:
            rows.append({"event": "smash_kill", "label": "스매시로 적을 쓰러뜨린다", "target": 2 + idx // 4})
        return rows

    if skill_id == "defense":
        rows = [
            {"event": "defense_use", "label": "디펜스로 공격을 받아낸다", "target": 8 + idx * 2},
            {"event": "defense_reduce", "label": "피해를 크게 경감한다", "target": 3 + idx // 3},
        ]
        if idx >= 4:
            rows.append({"event": "defense_low_hp", "label": "위기 상태에서 방어에 성공한다", "target": 1 + idx // 5})
        return rows

    if skill_id == "counter":
        rows = [
            {"event": "counter_use", "label": "카운터를 성공시킨다", "target": 6 + idx * 2},
            {"event": "counter_strong", "label": "강한 공격을 받아치고 반격한다", "target": 2 + idx // 3},
        ]
        if idx >= 3:
            rows.append({"event": "counter_kill", "label": "카운터로 적을 쓰러뜨린다", "target": 1 + idx // 5})
        return rows

    if skill_id == "windmill":
        rows = [
            {"event": "windmill_use", "label": "윈드밀을 사용한다", "target": 8 + idx * 2},
            {"event": "windmill_crit", "label": "윈드밀로 크리티컬을 낸다", "target": 2 + idx // 3},
        ]
        rows.append({"event": "windmill_multi", "label": "윈드밀로 여러 적을 동시에 맞힌다", "target": 2 + idx // 3})
        if idx >= 3:
            rows.append({"event": "windmill_kill", "label": "윈드밀로 적을 쓰러뜨린다", "target": 2 + idx // 4})
        return rows

    if skill_id in {"firebolt", "icebolt", "lightningbolt"}:
        rows = [
            {"event": "magic_cast", "label": "볼트 마법을 시전한다", "target": 8 + idx * 2},
            {"event": "magic_crit", "label": "마법으로 크리티컬을 낸다", "target": 2 + idx // 3},
        ]
        if skill_id == "icebolt":
            rows.append({"event": "ice_slow", "label": "아이스볼트로 적을 둔화시킨다", "target": 3 + idx // 3})
        elif skill_id == "firebolt":
            rows.append({"event": "fire_burn", "label": "파이어볼트로 화상을 건다", "target": 3 + idx // 3})
        elif skill_id == "lightningbolt":
            rows.append({"event": "lightning_quick", "label": "빠른 시전으로 반격 틈을 끊는다", "target": 2 + idx // 4})
        if idx >= 3:
            rows.append({"event": "magic_kill", "label": "마법으로 적을 쓰러뜨린다", "target": 2 + idx // 4})
        return rows

    if skill_id == "healing":
        rows = [
            {"event": "healing_use", "label": "힐링으로 체력을 회복한다", "target": 6 + idx * 2},
            {"event": "healing_big", "label": "한 번에 큰 체력을 회복한다", "target": 2 + idx // 3},
        ]
        if idx >= 3:
            rows.append({"event": "healing_low_hp", "label": "위기 상태에서 힐링한다", "target": 1 + idx // 5})
        return rows

    if skill_id == "combat_mastery":
        rows = [
            {"event": "combat_action", "label": "전투 행동을 수행한다", "target": 15 + idx * 3},
            {"event": "combat_win", "label": "전투에서 승리한다", "target": 3 + idx // 2},
        ]
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
