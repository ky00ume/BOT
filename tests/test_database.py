"""Database 저장/로드 기능 테스트.

save_player_to_db, load_player_from_db 함수를 테스트합니다.
"""
import pytest
from player import Player
from database import save_player_to_db, load_player_from_db, init_db


class TestDatabase:
    """Database 저장/로드 테스트."""

    def test_save_and_load_basic(self, temp_db):
        """기본 플레이어 데이터 저장 및 로드."""
        player = Player(name="저장테스트")
        player.gold = 500
        player.level = 5
        player.hp = 80
        player.max_hp = 100

        # 저장
        save_player_to_db(123456, player)

        # 로드
        loaded = load_player_from_db(123456)

        assert loaded is not None
        assert loaded.gold == 500
        assert loaded.level == 5
        assert loaded.hp == 80
        assert loaded.max_hp == 100

    def test_save_preserves_inventory(self, temp_db):
        """인벤토리 데이터 보존 테스트."""
        player = Player(name="인벤토리테스트")
        player.inventory = {
            "herb_01": 10,
            "ore_iron": 5,
            "potion_hp": 3,
        }

        save_player_to_db(123456, player)
        loaded = load_player_from_db(123456)

        assert loaded.inventory.get("herb_01") == 10
        assert loaded.inventory.get("ore_iron") == 5
        assert loaded.inventory.get("potion_hp") == 3

    def test_save_preserves_equipment(self, temp_db):
        """장비 데이터 보존 테스트."""
        player = Player(name="장비테스트")
        player.equipment = {
            "main": "wp_sword_01",
            "sub": "wp_shield_01",
            "body": "armor_plate_01",
            "head": None,
            "hands": None,
            "feet": None,
        }

        save_player_to_db(123456, player)
        loaded = load_player_from_db(123456)

        assert loaded.equipment.get("main") == "wp_sword_01"
        assert loaded.equipment.get("sub") == "wp_shield_01"
        assert loaded.equipment.get("body") == "armor_plate_01"
        assert loaded.equipment.get("head") is None

    def test_save_update_existing(self, temp_db):
        """기존 플레이어 데이터 업데이트 테스트."""
        player = Player(name="업데이트테스트")
        player.gold = 100

        # 첫 번째 저장
        save_player_to_db(123456, player)

        # 데이터 변경
        player.gold = 500
        player.level = 10

        # 두 번째 저장 (업데이트)
        save_player_to_db(123456, player)

        # 로드 후 확인
        loaded = load_player_from_db(123456)
        assert loaded.gold == 500
        assert loaded.level == 10

    def test_load_nonexistent_player(self, temp_db):
        """존재하지 않는 플레이어 로드 시도."""
        loaded = load_player_from_db(999999)
        assert loaded is None

    def test_multiple_players(self, temp_db):
        """여러 플레이어 동시 저장/로드."""
        player1 = Player(name="플레이어1")
        player1.gold = 100
        player1.level = 5

        player2 = Player(name="플레이어2")
        player2.gold = 200
        player2.level = 10

        player3 = Player(name="플레이어3")
        player3.gold = 300
        player3.level = 15

        # 저장
        save_player_to_db(111111, player1)
        save_player_to_db(222222, player2)
        save_player_to_db(333333, player3)

        # 로드 및 확인
        loaded1 = load_player_from_db(111111)
        loaded2 = load_player_from_db(222222)
        loaded3 = load_player_from_db(333333)

        assert loaded1.gold == 100 and loaded1.level == 5
        assert loaded2.gold == 200 and loaded2.level == 10
        assert loaded3.gold == 300 and loaded3.level == 15

    def test_save_empty_inventory(self, temp_db):
        """빈 인벤토리 저장 테스트."""
        player = Player(name="빈인벤토리")
        player.inventory = {}

        save_player_to_db(123456, player)
        loaded = load_player_from_db(123456)

        assert isinstance(loaded.inventory, dict)
        assert len(loaded.inventory) == 0

    def test_save_large_inventory(self, temp_db):
        """큰 인벤토리 저장 테스트."""
        player = Player(name="큰인벤토리")

        # 많은 아이템 추가
        for i in range(50):
            player.inventory[f"item_{i}"] = i * 10

        save_player_to_db(123456, player)
        loaded = load_player_from_db(123456)

        assert len(loaded.inventory) == 50
        for i in range(50):
            assert loaded.inventory.get(f"item_{i}") == i * 10

    def test_save_preserves_stats(self, temp_db):
        """스탯 데이터 보존 테스트."""
        player = Player(name="스탯테스트")
        player.base_stats = {
            "str": 15,
            "int": 20,
            "dex": 10,
            "will": 12,
            "luck": 8,
        }

        save_player_to_db(123456, player)
        loaded = load_player_from_db(123456)

        assert loaded.base_stats.get("str") == 15
        assert loaded.base_stats.get("int") == 20
        assert loaded.base_stats.get("dex") == 10
        assert loaded.base_stats.get("will") == 12
        assert loaded.base_stats.get("luck") == 8
