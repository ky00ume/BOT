"""Economy Layer 단위 테스트.

Economy 클래스의 모든 메서드를 테스트합니다.
"""
import pytest
from economy import Economy
from player import Player


class TestEconomy:
    """Economy 클래스 테스트."""

    def test_pay_reward_adds_gold(self, economy, fresh_player):
        """보상 지급 시 골드가 증가하는지 테스트."""
        initial_gold = fresh_player.gold
        economy.pay_reward("테스트:골드보상", gold=100)
        assert fresh_player.gold == initial_gold + 100

    def test_pay_reward_adds_exp(self, economy, fresh_player):
        """보상 지급 시 경험치가 증가하는지 테스트."""
        initial_exp = fresh_player.exp
        economy.pay_reward("테스트:경험치보상", exp=50.0)
        assert fresh_player.exp == initial_exp + 50.0

    def test_pay_reward_adds_items(self, economy, fresh_player):
        """보상 지급 시 아이템이 추가되는지 테스트."""
        economy.pay_reward("테스트:아이템보상", items={"herb_01": 5, "ore_iron": 3})
        assert fresh_player.inventory.get("herb_01") == 5
        assert fresh_player.inventory.get("ore_iron") == 3

    def test_pay_reward_combined(self, economy, fresh_player):
        """골드, 경험치, 아이템을 동시에 지급하는 테스트."""
        initial_gold = fresh_player.gold
        initial_exp = fresh_player.exp

        economy.pay_reward(
            "테스트:복합보상",
            gold=200,
            exp=50.0,
            items={"potion_hp": 2}
        )

        assert fresh_player.gold == initial_gold + 200
        assert fresh_player.exp == initial_exp + 50.0
        assert fresh_player.inventory.get("potion_hp") == 2

    def test_deduct_removes_gold(self, economy, player_with_gold):
        """차감 시 골드가 감소하는지 테스트."""
        economy.deduct("테스트:골드차감", gold=300)
        assert player_with_gold.gold == 700

    def test_deduct_removes_items(self, economy, player_with_items):
        """차감 시 아이템이 제거되는지 테스트."""
        economy.deduct("테스트:아이템차감", items={"herb_01": 5, "ore_iron": 2})
        assert player_with_items.inventory.get("herb_01") == 5
        assert player_with_items.inventory.get("ore_iron") == 3

    def test_add_item_success(self, economy, fresh_player):
        """아이템 추가 성공 테스트."""
        result = economy.add_item("테스트:아이템추가", "herb_01", 10)
        assert result is True
        assert fresh_player.inventory.get("herb_01") == 10

    def test_add_item_multiple_times(self, economy, fresh_player):
        """같은 아이템을 여러 번 추가하는 테스트."""
        economy.add_item("테스트:추가1", "herb_01", 5)
        economy.add_item("테스트:추가2", "herb_01", 3)
        assert fresh_player.inventory.get("herb_01") == 8

    def test_remove_item_success(self, economy, player_with_items):
        """아이템 제거 성공 테스트."""
        result = economy.remove_item("테스트:아이템제거", "herb_01", 3)
        assert result is True
        assert player_with_items.inventory.get("herb_01") == 7

    def test_remove_item_insufficient(self, economy, player_with_items):
        """아이템 부족 시 제거 실패 테스트."""
        result = economy.remove_item("테스트:아이템부족", "herb_01", 20)
        assert result is False
        assert player_with_items.inventory.get("herb_01") == 10  # 변경 없음

    def test_remove_item_nonexistent(self, economy, fresh_player):
        """존재하지 않는 아이템 제거 시도 테스트."""
        result = economy.remove_item("테스트:없는아이템", "nonexistent_item", 1)
        assert result is False

    def test_check_item_exists(self, economy, player_with_items):
        """아이템 보유 확인 - 충분한 경우."""
        assert economy.check_item("herb_01", 5) is True
        assert economy.check_item("herb_01", 10) is True

    def test_check_item_insufficient(self, economy, player_with_items):
        """아이템 보유 확인 - 부족한 경우."""
        assert economy.check_item("herb_01", 15) is False

    def test_check_item_nonexistent(self, economy, fresh_player):
        """아이템 보유 확인 - 존재하지 않는 경우."""
        assert economy.check_item("nonexistent_item", 1) is False

    def test_check_item_zero_count(self, economy, player_with_items):
        """아이템 보유 확인 - 0개 확인 (항상 True)."""
        assert economy.check_item("herb_01", 0) is True
        assert economy.check_item("nonexistent_item", 0) is True

    def test_pay_reward_with_no_params(self, economy, fresh_player):
        """파라미터 없이 보상 지급 호출 (아무 일도 일어나지 않아야 함)."""
        initial_gold = fresh_player.gold
        initial_exp = fresh_player.exp

        economy.pay_reward("테스트:빈보상")

        assert fresh_player.gold == initial_gold
        assert fresh_player.exp == initial_exp

    def test_deduct_with_no_params(self, economy, player_with_gold):
        """파라미터 없이 차감 호출 (아무 일도 일어나지 않아야 함)."""
        initial_gold = player_with_gold.gold

        economy.deduct("테스트:빈차감")

        assert player_with_gold.gold == initial_gold
