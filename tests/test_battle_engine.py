"""battle.py — BattleEngine 유닛 테스트 (REMEDIATION_PLAN 4-C 확장).

discord / bg3_renderer 에 직접 의존하지 않는 계층을 집중 테스트한다:

- enter_zone   : 레벨/존재 여부 검증 로직
- use_cheer    : 응원 상태 관리 (최대 3회, 전투 외 사용 차단)
- _calc_reward : 등급별 골드·경험치 배율 검증
- _apply_event_effect : HP/MP 변화 + 경계 클램핑
- zone_list    : MONSTERS_DB 모든 키 반환

discord 및 PIL 이 없는 환경에서는 자동으로 skip 된다.
"""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest


# ────────────────────────────────────────────────────────────────────────────
# Fixture: battle 모듈 lazy import (discord + PIL 없으면 skip)
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def battle_module():
    pytest.importorskip("discord")
    pytest.importorskip("PIL")
    import battle  # noqa: WPS433
    return battle


@pytest.fixture
def player():
    from player import Player
    return Player(name="전투테스트")


@pytest.fixture
def engine(battle_module, player):
    """npc_manager 없이 BattleEngine 생성."""
    return battle_module.BattleEngine(player, npc_manager=None)


# ────────────────────────────────────────────────────────────────────────────
# enter_zone
# ────────────────────────────────────────────────────────────────────────────

class TestEnterZone:
    def test_invalid_zone_returns_error(self, engine):
        result = engine.enter_zone("존재하지않는사냥터XYZ")
        assert "존재하지 않는" in result

    def test_valid_zone_low_level_player_blocked(self, engine, player):
        """레벨 0 플레이어는 Lv.1 이상 요구 구역에 입장 불가."""
        player.level = 0
        result = engine.enter_zone("방울숲")
        assert "입장에는" in result
        assert "필요" in result

    def test_valid_zone_sufficient_level_enters(self, engine, player):
        """충분한 레벨이면 입장 메시지 반환."""
        player.level = 1
        result = engine.enter_zone("방울숲")
        assert "입장했슴미댜" in result

    def test_enter_zone_sets_current_zone(self, engine, player):
        player.level = 10
        engine.enter_zone("방울숲")
        assert engine.current_zone == "방울숲"

    def test_enter_zone_message_contains_zone_name(self, engine, player):
        player.level = 10
        result = engine.enter_zone("방울숲")
        assert "방울숲" in result


# ────────────────────────────────────────────────────────────────────────────
# zone_list
# ────────────────────────────────────────────────────────────────────────────

class TestZoneList:
    def test_zone_list_is_nonempty(self, engine):
        assert len(engine.zone_list) > 0

    def test_zone_list_contains_known_zones(self, engine):
        from monsters_db import MONSTERS_DB
        assert set(engine.zone_list) == set(MONSTERS_DB.keys())


# ────────────────────────────────────────────────────────────────────────────
# use_cheer
# ────────────────────────────────────────────────────────────────────────────

class TestUseCheer:
    def test_cheer_outside_battle_blocked(self, engine):
        engine.in_battle = False
        result = engine.use_cheer()
        assert "전투 중이 아님" in result

    def test_cheer_increments_count(self, engine):
        engine.in_battle = True
        engine.cheer_count = 0
        engine.use_cheer()
        assert engine.cheer_count == 1

    def test_three_cheers_allowed(self, engine):
        engine.in_battle = True
        engine.cheer_count = 0
        for _ in range(3):
            result = engine.use_cheer()
            assert "모두 사용" not in result

    def test_fourth_cheer_blocked(self, engine):
        engine.in_battle = True
        engine.cheer_count = 3
        result = engine.use_cheer()
        assert "모두 사용" in result

    def test_cheer_sets_active_flag(self, engine):
        engine.in_battle = True
        engine.cheer_count = 0
        engine._cheer_active = False
        engine.use_cheer()
        assert engine._cheer_active is True

    def test_cheer_reports_remaining(self, engine):
        engine.in_battle = True
        engine.cheer_count = 0
        result = engine.use_cheer()
        assert "남은 응원" in result


# ────────────────────────────────────────────────────────────────────────────
# _calc_reward
# ────────────────────────────────────────────────────────────────────────────

_BASE_MONSTER = {
    "name": "슬라임",
    "level": 1,
    "hp": 30,
    "attack": 5,
    "defense": 1,
    "exp": 10,
    "gold": (10, 10),  # 고정값으로 테스트 용이
    "drops": [],
}


class TestCalcReward:
    def test_failure_grade_gives_zero_reward(self, engine):
        result = engine._calc_reward(_BASE_MONSTER, "실패")
        assert result["gold"] == 0
        assert result["exp"] == 0
        assert result["items"] == {}

    def test_stable_grade_gives_base_reward(self, engine, player):
        before_gold = player.gold
        before_exp = player.exp
        result = engine._calc_reward(_BASE_MONSTER, "안정")
        # gold range (10,10) * mult 1.0 = 10
        assert result["gold"] == 10
        assert result["exp"] == 10
        assert player.gold == before_gold + 10
        assert player.exp == pytest.approx(before_exp + 10)

    def test_perfect_grade_gives_bonus(self, engine, player):
        before_gold = player.gold
        result = engine._calc_reward(_BASE_MONSTER, "완벽")
        # mult = 1.3, gold = round(10 * 1.3) = 13
        assert result["gold"] == 13

    def test_close_grade_gives_less(self, engine, player):
        result = engine._calc_reward(_BASE_MONSTER, "아슬아슬")
        # mult = 0.7, gold = round(10 * 0.7) = 7
        assert result["gold"] == 7

    def test_reward_returns_level_info(self, engine):
        result = engine._calc_reward(_BASE_MONSTER, "안정")
        assert "old_level" in result
        assert "new_level" in result

    def test_failure_does_not_change_gold(self, engine, player):
        before_gold = player.gold
        engine._calc_reward(_BASE_MONSTER, "실패")
        assert player.gold == before_gold


# ────────────────────────────────────────────────────────────────────────────
# _apply_event_effect
# ────────────────────────────────────────────────────────────────────────────

class TestApplyEventEffect:
    def test_heal_hp_increases_hp(self, engine, player):
        player.hp = 50
        player.max_hp = 100
        engine._apply_event_effect({"heal_hp": 20})
        assert player.hp == 70

    def test_heal_hp_capped_at_max(self, engine, player):
        player.hp = 90
        player.max_hp = 100
        engine._apply_event_effect({"heal_hp": 50})
        assert player.hp == 100

    def test_take_damage_reduces_hp(self, engine, player):
        player.hp = 80
        player.max_hp = 100
        engine._apply_event_effect({"take_damage": 30})
        assert player.hp == 50

    def test_take_damage_clamped_at_zero(self, engine, player):
        player.hp = 10
        player.max_hp = 100
        engine._apply_event_effect({"take_damage": 999})
        assert player.hp == 0

    def test_heal_mp_increases_mp(self, engine, player):
        player.mp = 20
        player.max_mp = 100
        engine._apply_event_effect({"heal_mp": 30})
        assert player.mp == 50

    def test_heal_mp_capped_at_max(self, engine, player):
        player.mp = 95
        player.max_mp = 100
        engine._apply_event_effect({"heal_mp": 100})
        assert player.mp == 100

    def test_mp_cost_reduces_mp(self, engine, player):
        player.mp = 60
        player.max_mp = 100
        engine._apply_event_effect({"mp_cost": 20})
        assert player.mp == 40

    def test_mp_cost_clamped_at_zero(self, engine, player):
        player.mp = 5
        player.max_mp = 100
        engine._apply_event_effect({"mp_cost": 999})
        assert player.mp == 0

    def test_empty_effect_no_change(self, engine, player):
        hp_before = player.hp
        mp_before = player.mp
        engine._apply_event_effect({})
        assert player.hp == hp_before
        assert player.mp == mp_before
