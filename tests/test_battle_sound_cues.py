from unittest.mock import Mock, patch

from battle import BattleEngine


def _monster():
    return {"id": "test", "name": "연습용 몬스터", "level": 1, "hp": 1, "attack": 1, "defense": 0, "danger": "낮음", "_size": "M"}


def test_victory_emits_combat_and_victory_cues(fresh_player, monkeypatch):
    engine = BattleEngine(fresh_player)
    engine.in_battle = True
    engine.current_zone = "test"
    engine.current_monster = _monster()
    engine.monster_hp = 1
    engine._last_size = "M"
    fresh_player.base_stats["luck"] = 0
    monkeypatch.setattr("battle.random.random", lambda: 0.99)
    monkeypatch.setattr("battle.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr(engine, "_calc_reward", lambda monster, grade: {"gold": 0, "exp": 0, "items": {}, "leveled_up": False})
    monkeypatch.setattr(engine, "_add_village_contribution_battle", lambda: None)
    with patch("battle.sound_director.cue") as cue:
        engine.process_turn("smash")
    names = [call.args[0] for call in cue.call_args_list]
    assert "battle/player_hit" in names
    assert "battle/victory" in names


def test_enemy_counter_emits_hit_cue(fresh_player, monkeypatch):
    engine = BattleEngine(fresh_player)
    engine.in_battle = True
    engine.current_monster = {**_monster(), "hp": 999, "attack": 2}
    engine.monster_hp = 999
    engine._last_size = "M"
    fresh_player.base_stats["luck"] = 0
    monkeypatch.setattr("battle.random.random", lambda: 0.99)
    monkeypatch.setattr("battle.random.uniform", lambda a, b: 1.0)
    with patch("battle.sound_director.cue") as cue:
        engine.process_turn("smash")
    assert any(call.args[0] == "battle/enemy_hit" for call in cue.call_args_list)
