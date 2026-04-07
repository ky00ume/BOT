"""Player 클래스 단위 테스트.

Player 클래스의 주요 메서드를 테스트합니다.
"""
import pytest
from player import Player


class TestPlayer:
    """Player 클래스 테스트."""

    def test_player_initialization(self):
        """플레이어 초기화 테스트."""
        player = Player(name="초기화테스트")
        assert player.name == "초기화테스트"
        assert player.level == 1
        assert player.gold == 500
        assert player.hp > 0
        assert player.max_hp > 0
        assert isinstance(player.inventory, dict)
        assert isinstance(player.equipment, dict)

    def test_add_item_new(self, fresh_player):
        """새 아이템 추가 테스트."""
        fresh_player.add_item("herb_01", 5)
        assert fresh_player.inventory.get("herb_01") == 5

    def test_add_item_existing(self, fresh_player):
        """기존 아이템에 추가 테스트."""
        fresh_player.inventory["herb_01"] = 10
        fresh_player.add_item("herb_01", 5)
        assert fresh_player.inventory.get("herb_01") == 15

    def test_add_item_zero_count(self, fresh_player):
        """0개 추가 시도 테스트."""
        fresh_player.add_item("herb_01", 0)
        # 0개 추가는 아무 일도 일어나지 않거나 무시될 수 있음
        assert fresh_player.inventory.get("herb_01", 0) == 0

    def test_remove_item_success(self, player_with_items):
        """아이템 제거 성공 테스트."""
        result = player_with_items.remove_item("herb_01", 3)
        assert result is True
        assert player_with_items.inventory.get("herb_01") == 7

    def test_remove_item_all(self, player_with_items):
        """아이템 전부 제거 테스트."""
        count = player_with_items.inventory.get("ore_iron")
        result = player_with_items.remove_item("ore_iron", count)
        assert result is True
        # 전부 제거되면 0이거나 키가 삭제될 수 있음
        assert player_with_items.inventory.get("ore_iron", 0) == 0

    def test_remove_item_insufficient(self, player_with_items):
        """아이템 부족 시 제거 실패 테스트."""
        initial_count = player_with_items.inventory.get("herb_01")
        result = player_with_items.remove_item("herb_01", 100)
        assert result is False
        # 실패 시 수량 변경 없음
        assert player_with_items.inventory.get("herb_01") == initial_count

    def test_remove_item_nonexistent(self, fresh_player):
        """존재하지 않는 아이템 제거 시도."""
        result = fresh_player.remove_item("nonexistent_item", 1)
        assert result is False

    def test_equip_item(self, fresh_player):
        """장비 착용 테스트."""
        fresh_player.equip_item("wp_sword_01")
        assert fresh_player.equipment.get("main") == "wp_sword_01"

    def test_equip_item_replace(self, fresh_player):
        """기존 장비 교체 테스트."""
        fresh_player.equip_item("wp_sword_01")
        fresh_player.equip_item("wp_sword_02")
        assert fresh_player.equipment.get("main") == "wp_sword_02"

    def test_unequip_item(self, fresh_player):
        """장비 해제 테스트."""
        fresh_player.equip_item("wp_sword_01")
        fresh_player.unequip_item("main")
        assert fresh_player.equipment.get("main") is None

    def test_take_damage(self, fresh_player):
        """피해 받기 테스트."""
        initial_hp = fresh_player.hp
        fresh_player.take_damage(20)
        assert fresh_player.hp == initial_hp - 20

    def test_take_damage_overkill(self, fresh_player):
        """HP보다 큰 피해 받기 테스트 (0 이하로 내려가야 함)."""
        fresh_player.take_damage(fresh_player.hp + 100)
        assert fresh_player.hp <= 0

    def test_heal(self, fresh_player):
        """HP 회복 테스트."""
        fresh_player.hp = fresh_player.max_hp // 2
        fresh_player.heal(20)
        assert fresh_player.hp == (fresh_player.max_hp // 2) + 20

    def test_heal_max_cap(self, fresh_player):
        """HP 회복 시 최대값 제한 테스트."""
        fresh_player.hp = fresh_player.max_hp - 10
        fresh_player.heal(50)
        assert fresh_player.hp == fresh_player.max_hp

    def test_use_energy(self, fresh_player):
        """기력 소모 테스트."""
        initial_energy = fresh_player.energy
        result = fresh_player.use_energy(20)
        assert result is True
        assert fresh_player.energy == initial_energy - 20

    def test_use_energy_insufficient(self, fresh_player):
        """기력 부족 시 소모 실패 테스트."""
        fresh_player.energy = 10
        result = fresh_player.use_energy(20)
        assert result is False
        assert fresh_player.energy == 10  # 변경 없음

    def test_restore_energy(self, fresh_player):
        """기력 회복 테스트."""
        fresh_player.energy = 50
        fresh_player.restore_energy(30)
        assert fresh_player.energy == 80

    def test_restore_energy_max_cap(self, fresh_player):
        """기력 회복 시 최대값 제한 테스트."""
        fresh_player.energy = fresh_player.max_energy - 5
        fresh_player.restore_energy(100)
        assert fresh_player.energy == fresh_player.max_energy

    def test_get_total_slots(self, fresh_player):
        """총 인벤토리 슬롯 수 계산 테스트."""
        slots = fresh_player.get_total_slots()
        assert isinstance(slots, int)
        assert slots >= 10  # 기본 슬롯 수

    def test_inventory_not_shared(self):
        """플레이어 간 인벤토리 독립성 테스트."""
        player1 = Player(name="플레이어1")
        player2 = Player(name="플레이어2")

        player1.add_item("herb_01", 10)

        assert player1.inventory.get("herb_01") == 10
        assert player2.inventory.get("herb_01") is None

    def test_gold_operations(self, fresh_player):
        """골드 증감 테스트."""
        fresh_player.gold = 100
        assert fresh_player.gold == 100

        fresh_player.gold += 50
        assert fresh_player.gold == 150

        fresh_player.gold -= 30
        assert fresh_player.gold == 120
