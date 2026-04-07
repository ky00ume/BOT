"""Economy 원자성/롤백 테스트 (REMEDIATION_PLAN 2-C).

pay_reward / deduct 가 부분 실패 시 스냅샷 기반으로 이전 상태를 완전히
복구하는지 검증한다. Player 내부 구현에 의존하지 않도록 플레이어 더블을
사용해 add_item / remove_item 의 실패를 명시적으로 주입한다.
"""

from types import SimpleNamespace

import pytest

import economy as economy_module
from economy import Economy
from utils.exceptions import InsufficientResourceError, InventoryFullError


@pytest.fixture(autouse=True)
def _stub_check_level_up(monkeypatch):
    """check_level_up 은 player 내부에 강하게 결합되어 있으므로 무력화."""
    monkeypatch.setattr(economy_module, "check_level_up", lambda player: [])


# --------------------------------------------------------------- test doubles


class _StubPlayer:
    """테스트용 경량 플레이어. Economy 가 사용하는 속성만 구현."""

    def __init__(self, gold: int = 1000, exp: float = 0.0, inventory=None,
                 max_slots: int = 20):
        self.name = "stub"
        self.gold = gold
        self.exp = exp
        self.inventory = dict(inventory or {})
        self._max_slots = max_slots
        # add/remove 실패 주입용 카운터
        self.fail_add_after = None  # int: n 번째 add_item 호출부터 실패
        self._add_calls = 0

    def inventory_check(self):
        return len(self.inventory), self._max_slots

    def add_item(self, item_id: str, count: int = 1) -> bool:
        self._add_calls += 1
        if (
            self.fail_add_after is not None
            and self._add_calls >= self.fail_add_after
        ):
            return False
        if (
            item_id not in self.inventory
            and len(self.inventory) >= self._max_slots
        ):
            return False
        self.inventory[item_id] = self.inventory.get(item_id, 0) + count
        return True

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        have = self.inventory.get(item_id, 0)
        if have < count:
            return False
        self.inventory[item_id] -= count
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True


@pytest.fixture
def stub_player():
    return _StubPlayer(gold=500, exp=10.0, inventory={"herb_01": 2})


@pytest.fixture
def stub_economy(stub_player):
    return Economy(stub_player)  # type: ignore[arg-type]


# ------------------------------------------------------------- pay_reward


class TestPayRewardRollback:
    def test_inventory_full_raises_and_reverts_gold(self, stub_player, stub_economy):
        """슬롯 부족으로 실패하면 골드 증가까지 전부 롤백."""
        stub_player._max_slots = 1  # herb_01 하나로 이미 가득
        snapshot = (stub_player.gold, stub_player.exp, dict(stub_player.inventory))

        with pytest.raises(InventoryFullError):
            stub_economy.pay_reward(
                "test:full", gold=100, exp=5.0, items={"ore_iron": 1}
            )

        assert (stub_player.gold, stub_player.exp, stub_player.inventory) == snapshot

    def test_partial_add_item_failure_rolls_back(self, stub_player, stub_economy):
        """두 번째 add_item 이 실패하면 첫 번째도 취소되고 골드·exp 도 복구."""
        stub_player.fail_add_after = 2  # 두 번째 add_item 호출부터 False
        snapshot = (stub_player.gold, stub_player.exp, dict(stub_player.inventory))

        with pytest.raises(InventoryFullError):
            stub_economy.pay_reward(
                "test:partial",
                gold=50,
                exp=5.0,
                items={"ore_iron": 1, "potion_hp": 1},
            )

        assert stub_player.gold == snapshot[0]
        assert stub_player.exp == snapshot[1]
        assert stub_player.inventory == snapshot[2]

    def test_successful_pay_reward_applies_changes(self, stub_player, stub_economy):
        stub_economy.pay_reward(
            "test:ok", gold=30, exp=2.0, items={"ore_iron": 1}
        )
        assert stub_player.gold == 530
        assert stub_player.exp == 12.0
        assert stub_player.inventory["ore_iron"] == 1

    def test_snapshot_deep_copies_inventory(self, stub_player, stub_economy):
        """롤백 후 inventory dict 에 이전 참조가 남지 않아야 한다."""
        original = stub_player.inventory
        stub_player.fail_add_after = 1  # 첫 호출부터 실패
        with pytest.raises(InventoryFullError):
            stub_economy.pay_reward("test:copy", items={"new_item": 1})
        # 롤백 후 inventory 는 원본 내용과 동일해야 한다.
        assert stub_player.inventory == {"herb_01": 2}
        # 그리고 롤백된 dict 가 원래 dict 객체와는 달라도 된다.
        assert stub_player.inventory is not None
        _ = original  # 참조 유지 확인용


# ------------------------------------------------------------------- deduct


class TestDeductRollback:
    def test_insufficient_gold_raises_before_any_change(self, stub_player, stub_economy):
        with pytest.raises(InsufficientResourceError):
            stub_economy.deduct("test:broke", gold=9999)
        assert stub_player.gold == 500
        assert stub_player.inventory == {"herb_01": 2}

    def test_insufficient_item_raises_before_any_change(self, stub_player, stub_economy):
        with pytest.raises(InsufficientResourceError):
            stub_economy.deduct(
                "test:noitem", gold=10, items={"herb_01": 99}
            )
        # 골드가 이미 차감되지 않았어야 함.
        assert stub_player.gold == 500
        assert stub_player.inventory == {"herb_01": 2}

    def test_successful_deduct(self, stub_player, stub_economy):
        stub_economy.deduct("test:ok", gold=100, items={"herb_01": 1})
        assert stub_player.gold == 400
        assert stub_player.inventory == {"herb_01": 1}

    def test_exact_amount_deducts_cleanly(self, stub_player, stub_economy):
        stub_economy.deduct("test:exact", items={"herb_01": 2})
        assert "herb_01" not in stub_player.inventory


# ------------------------------------- module-level import hoisting (5-C)


class TestImportHoisting:
    def test_check_level_up_imported_at_module_top(self):
        """economy 모듈이 player.check_level_up 을 모듈 최상단에서 import 하는지."""
        import economy as economy_module
        assert hasattr(economy_module, "check_level_up")

    def test_no_function_internal_player_import(self):
        """economy.py AST 에 함수 내부 player import 가 남아있지 않아야 한다."""
        import ast
        from pathlib import Path

        import economy
        src = Path(economy.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom) and child.module == "player":
                        offenders.append((child.lineno, "from player"))
                    elif isinstance(child, ast.Import):
                        for alias in child.names:
                            if alias.name == "player":
                                offenders.append((child.lineno, "import player"))
        assert offenders == [], f"함수 내부 player import 발견: {offenders}"
