import io

import pytest

from player import Player
from skill_training import training_progress


class DummyRenderer:
    def render_battle_card(self, **kwargs):
        return io.BytesIO(b"battle")

    def render_card(self, **kwargs):
        return io.BytesIO(b"card")


def _engine(monkeypatch, *, monster_hp=500, monster_attack=20, monster_defense=0):
    import battle

    monkeypatch.setattr(battle, "get_renderer", lambda: DummyRenderer())
    monkeypatch.setattr(battle.random, "uniform", lambda a, b: 1.0)
    monkeypatch.setattr(battle.random, "random", lambda: 0.99)

    p = Player("전투수련")
    p.condition = 40
    p.stability = 50
    p.fatigue = 0
    p.hp = p.max_hp
    p.mp = p.max_mp
    engine = battle.BattleEngine(p)
    engine.in_battle = True
    engine.current_monster = {
        "id": "training_dummy",
        "name": "훈련용 골렘",
        "level": 1,
        "hp": monster_hp,
        "attack": monster_attack,
        "defense": monster_defense,
        "danger": "보통",
        "exp": 0,
        "gold": (0, 0),
        "drops": [],
        "_size": "M",
    }
    engine.monster_hp = monster_hp
    engine.turn = 1
    engine._last_size = "M"
    return engine, p


def _progress_map(player, skill_id):
    return {row["event"]: row["current"] for row in training_progress(player, skill_id)}


def test_defense_reduces_damage_and_records_training(monkeypatch):
    engine, p = _engine(monkeypatch, monster_attack=30)
    p.skill_ranks["defense"] = "F"
    hp_before = p.hp
    engine.process_turn("defense")

    assert p.hp < hp_before
    # F랭 디펜스는 순수 피격보다 8% 추가 경감한다.
    assert hp_before - p.hp < 30
    progress = _progress_map(p, "defense")
    assert progress["defense_use"] == 1
    assert _progress_map(p, "combat_mastery")["combat_action"] == 1


def test_counter_uses_counter_multiplier_and_records_training(monkeypatch):
    engine, p = _engine(monkeypatch, monster_hp=500, monster_attack=25)
    p.skill_ranks["counter"] = "F"
    before = engine.monster_hp
    engine.process_turn("counter")
    counter_damage = before - engine.monster_hp

    engine2, p2 = _engine(monkeypatch, monster_hp=500, monster_attack=25)
    p2.skill_ranks["smash"] = "F"
    before2 = engine2.monster_hp
    engine2.process_turn("smash")
    smash_damage = before2 - engine2.monster_hp

    assert counter_damage > smash_damage
    assert _progress_map(p, "counter")["counter_use"] == 1


def test_windmill_uses_aoe_multiplier_and_tracks_critless_use(monkeypatch):
    engine, p = _engine(monkeypatch, monster_hp=500)
    p.skill_ranks["windmill"] = "연습"
    p.skill_exp["windmill"] = 0.0
    before = engine.monster_hp
    engine.process_turn("windmill")
    assert 0 < before - engine.monster_hp
    progress = _progress_map(p, "windmill")
    assert progress["windmill_use"] == 1
    assert progress["windmill_crit"] == 0


def test_magic_cast_records_magic_training(monkeypatch):
    engine, p = _engine(monkeypatch, monster_hp=500)
    p.skill_ranks["firebolt"] = "연습"
    p.skill_exp["firebolt"] = 0.0
    mp_before = p.mp
    engine.process_turn("firebolt")
    assert p.mp < mp_before
    progress = _progress_map(p, "firebolt")
    assert progress["magic_cast"] == 1
    assert progress["magic_crit"] == 0


def test_healing_is_real_battle_action_and_records_low_hp_training(monkeypatch):
    engine, p = _engine(monkeypatch, monster_attack=5)
    p.skill_ranks["healing"] = "D"
    p.skill_exp["healing"] = 0.0
    p.hp = max(1, int(p.max_hp * 0.25))
    hp_before = p.hp
    mp_before = p.mp
    engine.process_turn("healing")

    assert p.mp < mp_before
    assert p.hp > hp_before
    progress = _progress_map(p, "healing")
    assert progress["healing_use"] == 1
    assert progress["healing_low_hp"] == 1


def test_combat_mastery_rank_up_applies_its_own_stat_bonus():
    p = Player()
    p.skill_ranks["combat_mastery"] = "연습"
    p.skill_exp["combat_mastery"] = 199.0
    strength_before = p.base_stats["str"]
    p.train_skill("combat_mastery", 1.0)
    assert p.skill_ranks["combat_mastery"] == "F"
    assert p.base_stats["str"] == strength_before + 2


@pytest.mark.asyncio
async def test_battle_view_exposes_learned_healing_button(monkeypatch):
    from ui.battle_view import BattleView

    engine, p = _engine(monkeypatch)
    p.skill_ranks["healing"] = "연습"
    p.skill_exp["healing"] = 0.0

    class Ctx:
        pass

    view = BattleView(engine, Ctx())
    labels = {getattr(child, "label", "") for child in view.children}
    assert any("힐링" in label for label in labels)
