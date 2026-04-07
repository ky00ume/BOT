"""battle.py — 순수 함수 & 컨디션 보정식 회귀 테스트 (REMEDIATION_PLAN 4-C).

battle.py 는 discord / bg3_renderer 에 의존하는 대형 모듈이라 전체를 import
하기 어렵다. 이 테스트는 다음 두 계층만 목표로 한다:

1) 모듈 최상단의 순수 함수 (``_bar_text``, ``_calc_battle_grade``)
2) ``BattleEngine._get_condition_modifiers`` — player 더미만으로 검증 가능

이를 통해 컨디션/안정감/피로도 보정이 밸런스 문서와 어긋나는 순간을
감지할 수 있다.
"""

from types import SimpleNamespace

import pytest


# --------------------------------------------------------- pure helper tests


@pytest.fixture
def battle_module():
    pytest.importorskip("discord")
    pytest.importorskip("PIL")
    import battle  # noqa: WPS433 — lazy import to skip cleanly
    return battle


class TestBarText:
    def test_full_bar(self, battle_module):
        assert battle_module._bar_text(10, 10, width=10) == "█" * 10

    def test_empty_bar(self, battle_module):
        assert battle_module._bar_text(0, 10, width=10) == "░" * 10

    def test_half_bar(self, battle_module):
        bar = battle_module._bar_text(5, 10, width=10)
        assert bar.count("█") == 5
        assert bar.count("░") == 5

    def test_negative_current_clamped(self, battle_module):
        bar = battle_module._bar_text(-50, 10, width=10)
        assert bar == "░" * 10

    def test_zero_max_does_not_crash(self, battle_module):
        bar = battle_module._bar_text(5, 0, width=10)
        assert len(bar) == 10

    def test_width_is_respected(self, battle_module):
        assert len(battle_module._bar_text(3, 10, width=7)) == 7


class TestBattleGrade:
    def test_dead_player_is_failure(self, battle_module):
        assert battle_module._calc_battle_grade(0, 100) == "실패"
        assert battle_module._calc_battle_grade(-5, 100) == "실패"

    @pytest.mark.parametrize(
        "hp,max_hp,expected",
        [
            (100, 100, "완벽"),   # 1.00
            (61, 100, "완벽"),    # 0.61
            (60, 100, "안정"),    # 0.60 — 경계
            (16, 100, "안정"),    # 0.16
            (14, 100, "아슬아슬"),  # 0.14
            (1, 100, "아슬아슬"),   # 0.01
        ],
    )
    def test_boundary_grades(self, battle_module, hp, max_hp, expected):
        assert battle_module._calc_battle_grade(hp, max_hp) == expected

    def test_max_hp_zero_treated_as_one(self, battle_module):
        # 분모 0 방어 — 현재 HP 가 양수면 비율 >= 1 이므로 "완벽".
        assert battle_module._calc_battle_grade(1, 0) == "완벽"


# ------------------------------------------------- condition modifier tests


def _mk_engine(battle_module, *, condition=50, stability=50, fatigue=0):
    """BattleEngine 을 부분적으로 초기화. __init__ 이 많은 기본값을 설정하므로
    실제 생성자를 거치되 외부 의존(npc_manager)은 None 으로 둔다."""
    player = SimpleNamespace(
        name="test",
        hp=100, max_hp=100,
        condition=condition,
        stability=stability,
        fatigue=fatigue,
    )
    return battle_module.BattleEngine(player, npc_manager=None)


class TestConditionModifiers:
    def test_neutral_values_are_baseline(self, battle_module):
        engine = _mk_engine(battle_module, condition=50, stability=50, fatigue=0)
        mods = engine._get_condition_modifiers()
        # condition==50 은 임계값: bonus = 0.05 + 0*0.05 = 0.05
        assert mods["atk_mult"] == pytest.approx(1.05, abs=1e-9)
        assert mods["def_mult"] == pytest.approx(1.05, abs=1e-9)
        assert mods["crit_bonus"] == pytest.approx(0.0)
        assert mods["flee_bonus"] == pytest.approx(0.0)
        assert mods["miss_chance"] == pytest.approx(0.0)

    def test_max_condition_gives_ten_percent_bonus(self, battle_module):
        engine = _mk_engine(battle_module, condition=100)
        mods = engine._get_condition_modifiers()
        assert mods["atk_mult"] == pytest.approx(1.10, abs=1e-9)
        assert mods["def_mult"] == pytest.approx(1.10, abs=1e-9)

    def test_low_condition_applies_penalty(self, battle_module):
        engine = _mk_engine(battle_module, condition=20)
        mods = engine._get_condition_modifiers()
        assert mods["atk_mult"] == pytest.approx(0.90, abs=1e-9)
        assert mods["def_mult"] == pytest.approx(0.90, abs=1e-9)

    def test_mid_condition_no_change(self, battle_module):
        # 31..49 는 보너스/패널티 모두 해당 없음
        engine = _mk_engine(battle_module, condition=35)
        mods = engine._get_condition_modifiers()
        assert mods["atk_mult"] == pytest.approx(1.0)
        assert mods["def_mult"] == pytest.approx(1.0)

    def test_high_stability_gives_crit_bonus(self, battle_module):
        engine = _mk_engine(battle_module, stability=80)
        mods = engine._get_condition_modifiers()
        assert mods["crit_bonus"] == pytest.approx(0.05)

    def test_low_stability_reduces_flee(self, battle_module):
        engine = _mk_engine(battle_module, stability=10)
        mods = engine._get_condition_modifiers()
        assert mods["flee_bonus"] == pytest.approx(-0.15)

    def test_high_fatigue_hits_attack_and_miss(self, battle_module):
        engine = _mk_engine(battle_module, fatigue=90)
        mods = engine._get_condition_modifiers()
        # cond 50 -> +0.05 bonus, fatigue 90 -> -0.15
        assert mods["atk_mult"] == pytest.approx(1.05 - 0.15, abs=1e-9)
        assert mods["miss_chance"] == pytest.approx(0.15)

    def test_moderate_fatigue_only_reduces_attack(self, battle_module):
        engine = _mk_engine(battle_module, fatigue=60)
        mods = engine._get_condition_modifiers()
        assert mods["atk_mult"] == pytest.approx(1.05 - 0.10, abs=1e-9)
        assert mods["miss_chance"] == pytest.approx(0.0)
