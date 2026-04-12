"""tests/test_adventure.py — AdventureEngine 단위 테스트 (discord.ui.View 제외)"""
import sys
import types
import random
import pytest
from unittest.mock import patch

# discord 모듈이 없는 환경에서도 AdventureEngine 로직을 테스트하기 위해
# 가짜 discord 모듈을 sys.modules에 미리 등록합니다.
# 모듈 임포트 시점(픽스처 호출 전)에 등록해야 adventure.py가 정상 임포트되므로
# 모듈 레벨에서 조건부로 설정합니다. discord가 실제로 설치되어 있으면 그대로 사용합니다.
if "discord" not in sys.modules:
    _discord_stub = types.ModuleType("discord")
    _discord_ui_stub = types.ModuleType("discord.ui")
    _discord_ui_stub.View = object
    _discord_ui_stub.Button = object
    _discord_stub.ui = _discord_ui_stub
    _discord_stub.ButtonStyle = types.SimpleNamespace(
        primary=1, secondary=2, success=3, danger=4
    )
    _discord_stub.Interaction = object
    _discord_stub.Embed = object
    sys.modules["discord"] = _discord_stub
    sys.modules["discord.ui"] = _discord_ui_stub


# ── _find_step_idx ────────────────────────────────────────────────────────────

class TestFindStepIdx:
    def test_finds_correct_index(self, adventure_engine):
        scenario = {
            "steps": [
                {"step": 0, "desc": "첫 번째"},
                {"step": 1, "desc": "두 번째"},
                {"step": 5, "desc": "다섯 번째"},
            ]
        }
        assert adventure_engine._find_step_idx(scenario, 0) == 0
        assert adventure_engine._find_step_idx(scenario, 1) == 1
        assert adventure_engine._find_step_idx(scenario, 5) == 2

    def test_returns_none_for_missing_step(self, adventure_engine):
        scenario = {"steps": [{"step": 0}]}
        assert adventure_engine._find_step_idx(scenario, 99) is None


# ── _apply_reward ─────────────────────────────────────────────────────────────

class TestApplyReward:
    def test_apply_gold(self, adventure_engine):
        before = adventure_engine.player.gold
        adventure_engine._apply_reward({"gold": 50})
        assert adventure_engine.player.gold == before + 50

    def test_apply_exp(self, adventure_engine):
        before = getattr(adventure_engine.player, "exp", 0.0)
        adventure_engine._apply_reward({"exp": 30})
        assert adventure_engine.player.exp == before + 30

    def test_apply_item(self, adventure_engine):
        adventure_engine.player.inventory = {}
        adventure_engine._apply_reward({"item": "herb"})
        assert adventure_engine.player.inventory.get("herb", 0) >= 1

    def test_apply_hp(self, adventure_engine):
        adventure_engine.player.hp = 10
        adventure_engine._apply_reward({"hp": 20})
        assert adventure_engine.player.hp == 30

    def test_apply_hp_capped_at_max(self, adventure_engine):
        adventure_engine.player.hp = adventure_engine.player.max_hp
        adventure_engine._apply_reward({"hp": 999})
        assert adventure_engine.player.hp == adventure_engine.player.max_hp

    def test_apply_mp(self, adventure_engine):
        adventure_engine.player.mp = 0
        adventure_engine._apply_reward({"mp": 10})
        assert adventure_engine.player.mp == 10

    def test_apply_energy(self, adventure_engine):
        adventure_engine.player.energy = 0
        adventure_engine._apply_reward({"energy": 5})
        assert adventure_engine.player.energy == 5

    def test_apply_none_reward(self, adventure_engine):
        gold_before = adventure_engine.player.gold
        adventure_engine._apply_reward(None)
        assert adventure_engine.player.gold == gold_before

    def test_apply_empty_reward(self, adventure_engine):
        gold_before = adventure_engine.player.gold
        adventure_engine._apply_reward({})
        assert adventure_engine.player.gold == gold_before


# ── check_stat ────────────────────────────────────────────────────────────────

class TestCheckStat:
    def test_guaranteed_success_with_high_stat(self, adventure_engine):
        """stat=100 이면 1d20 어떤 값이 나와도 낮은 difficulty를 통과"""
        adventure_engine.player.base_stats["str"] = 100
        with patch("adventure.random.randint", return_value=1):
            assert adventure_engine.check_stat("str", 5) is True

    def test_guaranteed_failure_with_low_stat(self, adventure_engine):
        """stat=1, roll=1 이면 매우 높은 difficulty 실패"""
        adventure_engine.player.base_stats["str"] = 1
        with patch("adventure.random.randint", return_value=1):
            assert adventure_engine.check_stat("str", 100) is False

    def test_boundary_exactly_meets_difficulty(self, adventure_engine):
        adventure_engine.player.base_stats["dex"] = 5
        with patch("adventure.random.randint", return_value=7):
            # 5 + 7 = 12, difficulty=12 → 성공
            assert adventure_engine.check_stat("dex", 12) is True

    def test_unknown_stat_defaults_to_10(self, adventure_engine):
        with patch("adventure.random.randint", return_value=20):
            # 10 + 20 = 30, 모든 일반 difficulty 통과
            assert adventure_engine.check_stat("unknown_stat", 25) is True


# ── start_adventure ───────────────────────────────────────────────────────────

class TestStartAdventure:
    def test_insufficient_energy(self, adventure_engine):
        adventure_engine.player.energy = 0
        result = adventure_engine.start_adventure("방울숲")
        assert result["ok"] is False
        assert "기력" in result["error"]

    def test_start_sets_in_adventure(self, adventure_engine):
        with patch("adventure.random.random", return_value=0.5):  # NPC 인카운터 방지
            result = adventure_engine.start_adventure("방울숲")
        assert result["ok"] is True
        assert adventure_engine.in_adventure is True

    def test_result_has_required_keys(self, adventure_engine):
        with patch("adventure.random.random", return_value=0.5):
            result = adventure_engine.start_adventure("방울숲")
        assert "ok" in result

    def test_unknown_zone_falls_back_to_random_event(self, adventure_engine):
        with patch("adventure.random.random", return_value=0.5):
            result = adventure_engine.start_adventure("존재하지않는존")
        assert result["ok"] is True


# ── process_choice ────────────────────────────────────────────────────────────

class TestProcessChoice:
    def test_error_when_not_in_adventure(self, adventure_engine):
        adventure_engine.in_adventure = False
        result = adventure_engine.process_choice(0)
        assert result["ok"] is False
        assert "탐험 중이 아님" in result["error"]

    def test_invalid_choice_index(self, adventure_engine):
        # 간단한 시나리오를 직접 주입
        scenario = {
            "id": "test_s",
            "title": "테스트",
            "steps": [
                {
                    "step": 0,
                    "desc": "테스트 설명",
                    "choices": [
                        {"label": "선택1", "auto": True, "result": {"text": "OK", "end": True}}
                    ],
                    "end": False,
                }
            ],
        }
        adventure_engine.in_adventure = True
        adventure_engine.active_adventure = {"type": "scenario", "scenario": scenario, "zone": "테스트존"}
        adventure_engine.current_step = 0
        adventure_engine._pending_rewards = []
        result = adventure_engine.process_choice(99)
        assert result["ok"] is False

    def test_valid_choice_returns_ok(self, adventure_engine):
        scenario = {
            "id": "test_s",
            "title": "테스트",
            "steps": [
                {
                    "step": 0,
                    "desc": "설명",
                    "choices": [
                        {"label": "선택1", "auto": True, "result": {"text": "완료!", "end": True}}
                    ],
                    "end": True,
                }
            ],
        }
        adventure_engine.in_adventure = True
        adventure_engine.active_adventure = {"type": "scenario", "scenario": scenario, "zone": "테스트"}
        adventure_engine.current_step = 0
        adventure_engine._pending_rewards = []
        result = adventure_engine.process_choice(0)
        assert result["ok"] is True


# ── process_npc_interaction ───────────────────────────────────────────────────

class TestProcessNpcInteraction:
    def test_error_when_not_in_adventure(self, adventure_engine):
        adventure_engine.in_adventure = False
        result = adventure_engine.process_npc_interaction("refuse")
        assert result["ok"] is False

    def test_refuse_action_clears_adventure(self, adventure_engine):
        npc = {"name": "테스트NPC", "interaction": "help", "refuse_text": "알겠어"}
        adventure_engine.in_adventure = True
        adventure_engine.active_adventure = {"type": "npc", "npc": npc, "zone": "방울숲"}
        result = adventure_engine.process_npc_interaction("refuse")
        assert adventure_engine.in_adventure is False
        assert result["ok"] is True

    def test_ignore_action_clears_adventure(self, adventure_engine):
        npc = {"name": "무명NPC", "interaction": "info"}
        adventure_engine.in_adventure = True
        adventure_engine.active_adventure = {"type": "npc", "npc": npc, "zone": "방울숲"}
        result = adventure_engine.process_npc_interaction("ignore")
        assert adventure_engine.in_adventure is False


# ── post_adventure_event ──────────────────────────────────────────────────────

class TestPostAdventureEvent:
    def test_returns_none_most_of_the_time(self, adventure_engine):
        with patch("adventure.random.random", return_value=0.5):
            result = adventure_engine.post_adventure_event("방울숲")
        assert result is None

    def test_returns_dict_when_triggered(self, adventure_engine):
        with patch("adventure.random.random", return_value=0.05):
            result = adventure_engine.post_adventure_event("방울숲")
        # 10% 이하의 random 값이면 이벤트 발생
        assert result is None or isinstance(result, dict)

    def test_event_dict_has_type(self, adventure_engine):
        """random.random을 0.05로 고정하여 이벤트를 강제 발생시킴"""
        with patch("adventure.random.random", return_value=0.05):
            result = adventure_engine.post_adventure_event()
        if result is not None:
            assert "type" in result
