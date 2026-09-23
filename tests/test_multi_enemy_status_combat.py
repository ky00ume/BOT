import io

from player import Player
from skill_training import training_progress


class DummyRenderer:
    def __init__(self):
        self.last_battle = None
        self.last_card = None

    def render_battle_card(self, **kwargs):
        self.last_battle = kwargs
        return io.BytesIO(b"battle")

    def render_card(self, **kwargs):
        self.last_card = kwargs
        return io.BytesIO(b"card")


def _monster(name, hp=100, attack=20, defense=0):
    return {
        "id": name,
        "name": name,
        "level": 3,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "danger": "보통",
        "exp": 0,
        "gold": (0, 0),
        "drops": [],
        "_size": "M",
    }


def _group_engine(monkeypatch, count=3, hp=100, attack=20):
    import battle

    renderer = DummyRenderer()
    monkeypatch.setattr(battle, "get_renderer", lambda: renderer)
    monkeypatch.setattr(battle.random, "uniform", lambda a, b: 1.0)
    monkeypatch.setattr(battle.random, "random", lambda: 0.99)

    p = Player("복수전투")
    p.condition = 40
    p.stability = 50
    p.fatigue = 0
    p.hp = p.max_hp = 500
    p.mp = p.max_mp = 500
    engine = battle.BattleEngine(p)
    engine.in_battle = True
    engine.turn = 1
    engine.enemies = []
    for idx in range(count):
        mon = _monster(f"적{idx+1}", hp=hp, attack=attack)
        engine.enemies.append({"monster": mon, "hp": hp, "statuses": {}, "size": "M"})
    engine.defeated_enemies = []
    engine._sync_primary_enemy()
    return engine, p, renderer


def _progress(player, skill_id):
    return {row["event"]: row["current"] for row in training_progress(player, skill_id)}


def test_windmill_hits_every_alive_enemy_and_trains_multi_target(monkeypatch):
    engine, p, renderer = _group_engine(monkeypatch, count=3, hp=250, attack=1)
    p.skill_ranks["windmill"] = "F"
    before = [enemy["hp"] for enemy in engine.enemies]

    engine.process_turn("windmill")

    after = [enemy["hp"] for enemy in engine.enemies]
    assert all(a < b for a, b in zip(after, before))
    assert _progress(p, "windmill")["windmill_multi"] == 1
    assert "적 3체" in renderer.last_battle["size_label"]


def test_icebolt_applies_two_turn_slow_and_reduces_enemy_attack(monkeypatch):
    engine, p, renderer = _group_engine(monkeypatch, count=1, hp=500, attack=40)
    p.skill_ranks["icebolt"] = "F"
    hp_before = p.hp

    engine.process_turn("icebolt")

    # 둔화가 걸린 바로 그 반격부터 공격력 65%가 적용되고, 한 턴이 소모된다.
    assert p.hp > hp_before - 40
    status = engine.enemies[0]["statuses"].get("slow", 0)
    assert status == 1
    assert _progress(p, "icebolt")["ice_slow"] == 1
    assert "둔화" in renderer.last_battle["last_action"]


def test_firebolt_burn_ticks_on_next_player_turn(monkeypatch):
    engine, p, renderer = _group_engine(monkeypatch, count=1, hp=500, attack=1)
    p.skill_ranks["firebolt"] = "F"

    engine.process_turn("firebolt")
    hp_after_cast = engine.enemies[0]["hp"]
    burn = dict(engine.enemies[0]["statuses"]["burn"])

    engine.process_turn("smash")

    # 두 번째 턴 시작 전에 화상 피해가 별도로 들어간다.
    assert engine.enemies[0]["hp"] <= hp_after_cast - burn["damage"] - 1
    assert _progress(p, "firebolt")["fire_burn"] == 1


def test_lightning_quick_cast_can_cancel_primary_counterattack(monkeypatch):
    import battle

    engine, p, renderer = _group_engine(monkeypatch, count=2, hp=1200, attack=30)
    p.skill_ranks["lightningbolt"] = "1"
    # crit 판정은 실패, quick-cast 판정은 성공.
    rolls = iter([0.99, 0.0])
    monkeypatch.setattr(battle.random, "random", lambda: next(rolls))
    hp_before = p.hp

    engine.process_turn("lightningbolt")

    # 두 적 중 주 대상은 반격하지 못하고 나머지 한 체만 때린다.
    damage_taken = hp_before - p.hp
    assert 0 < damage_taken < 60
    assert _progress(p, "lightningbolt")["lightning_quick"] == 1
    assert "반격 차단" in renderer.last_battle["last_action"]


def test_single_enemy_group_path_uses_single_victory_title_and_victory_theme(monkeypatch):
    engine, p, renderer = _group_engine(monkeypatch, count=1, hp=15, attack=1)
    p.skill_ranks["smash"] = "1"

    engine.process_turn("smash")

    assert engine.in_battle is False
    assert len(engine.defeated_enemies) == 1
    assert renderer.last_card["title"] == "🎉 전투 승리!"
    assert renderer.last_card["grade"] == "Legendary"
    assert renderer.last_card["system_key"] == "battle_win"


def test_group_victory_waits_until_all_enemies_are_defeated(monkeypatch):
    engine, p, renderer = _group_engine(monkeypatch, count=2, hp=15, attack=1)
    p.skill_ranks["smash"] = "1"

    # 스매시는 한 대상만 치므로 첫 적이 죽어도 두 번째 적이 남아 전투는 계속된다.
    engine.process_turn("smash")
    assert engine.in_battle is True
    assert len(engine._alive_enemies()) == 1

    engine.process_turn("smash")
    assert engine.in_battle is False
    assert len(engine.defeated_enemies) == 2
    assert renderer.last_card["title"] == "🎉 다수 전투 승리!"
