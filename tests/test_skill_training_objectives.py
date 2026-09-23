import pytest

from blacksmith import BlacksmithEngine
from player import Player
from skill_training import record_training_event, training_objectives, training_progress
from ui.skill_ui import make_skill_detail_embed


def test_mining_training_objectives_scale_by_rank():
    practice = training_objectives("mining", "연습")
    rank_f = training_objectives("mining", "F")
    assert [row["event"] for row in practice] == ["mine_success"]
    assert {row["event"] for row in rank_f} == {"mine_success", "mine_uncommon"}
    assert rank_f[0]["target"] > practice[0]["target"]


def test_record_training_event_caps_at_target_and_is_rank_scoped():
    p = Player()
    p.skill_ranks["mining"] = "F"
    target = next(row["target"] for row in training_objectives("mining", "F") if row["event"] == "mine_uncommon")
    for _ in range(target + 5):
        record_training_event(p, "mining", "mine_uncommon")
    progress = {row["event"]: row for row in training_progress(p, "mining")}
    assert progress["mine_uncommon"]["current"] == target

    p.skill_ranks["mining"] = "E"
    assert all(row["current"] == 0 for row in training_progress(p, "mining"))


def test_rank_up_resets_training_checklist_for_new_rank():
    p = Player()
    p.skill_ranks["mining"] = "연습"
    record_training_event(p, "mining", "mine_success", 5)
    p.skill_exp["mining"] = 199
    msg = p.train_skill("mining", 1)
    assert "F" in msg
    assert p.skill_ranks["mining"] == "F"
    assert all(row["current"] == 0 for row in training_progress(p, "mining"))


def test_skill_detail_embed_shows_training_checklist():
    p = Player()
    p.skill_ranks["mining"] = "F"
    record_training_event(p, "mining", "mine_success", 3)
    record_training_event(p, "mining", "mine_uncommon", 1)
    embed = make_skill_detail_embed(p, "mining")
    field = next(field for field in embed.fields if field.name == "📋 이번 랭크 수련 항목")
    assert "광석을 채굴한다" in field.value
    assert "희귀 광물·보석을 캔다" in field.value
    assert "3/10" in field.value


class FixedRng:
    def __init__(self, values):
        self.values = iter(values)
    def randint(self, lo, hi):
        value = next(self.values)
        assert lo <= value <= hi
        return value


def test_blacksmith_quality_records_multiple_training_categories():
    p = Player("수련생")
    p.skill_ranks["blacksmith"] = "A"
    p.inventory["iron_bar"] = 3
    p.inventory["gt_wood_01"] = 1
    engine = BlacksmithEngine(p)
    session = engine.start_session("wp_sword_02")
    engine.apply_stage(session, "steady", rng=FixedRng([18]))
    engine.apply_stage(session, "steady", rng=FixedRng([16]))
    engine.apply_stage(session, "careful", rng=FixedRng([14]))
    result = engine.finish_session(session)
    assert result["quality_score"] >= 90
    progress = {row["event"]: row["current"] for row in training_progress(p, "blacksmith")}
    assert progress["forge_complete"] == 1
    assert progress["forge_fine"] == 1
    assert progress["forge_excellent"] == 1
    assert progress["forge_masterpiece"] == 1
