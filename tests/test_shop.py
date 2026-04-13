"""tests/test_shop.py — ShopManager 단위 테스트"""
import pytest


# ── show_sell_list ───────────────────────────────────────────────────────────

class TestShowSellList:
    def test_empty_inventory_returns_error(self, shop_manager):
        shop_manager.player.inventory = {}
        result = shop_manager.show_sell_list()
        assert "비어있" in result

    def test_with_items_shows_list(self, shop_manager):
        shop_manager.player.inventory = {"iron_ore": 3}
        result = shop_manager.show_sell_list()
        assert "판매" in result
        assert isinstance(result, str)


# ── sell_item ────────────────────────────────────────────────────────────────

class TestSellItem:
    def test_sell_valid_item(self, shop_manager):
        shop_manager.player.inventory = {"iron_ore": 5}
        shop_manager.player.gold = 0
        result = shop_manager.sell_item("iron_ore", 3)
        assert "판매 완료" in result
        assert shop_manager.player.gold > 0
        assert shop_manager.player.inventory.get("iron_ore", 0) == 2

    def test_sell_unknown_item(self, shop_manager):
        result = shop_manager.sell_item("totally_fake_item_xyz", 1)
        assert "찾을 수 없" in result

    def test_sell_insufficient_quantity(self, shop_manager):
        shop_manager.player.inventory = {"iron_ore": 1}
        result = shop_manager.sell_item("iron_ore", 10)
        assert "부족" in result or "없" in result

    def test_sell_by_korean_name(self, shop_manager):
        from items import ALL_ITEMS
        # Find an item with Korean name in inventory
        item_id = "iron_ore"
        name = ALL_ITEMS.get(item_id, {}).get("name", "철광석")
        shop_manager.player.inventory = {item_id: 5}
        shop_manager.player.gold = 0
        result = shop_manager.sell_item(name, 1)
        assert "판매 완료" in result


# ── show_buy_list ────────────────────────────────────────────────────────────

class TestShowBuyList:
    def test_valid_npc(self, shop_manager):
        from shop import NPC_CATALOGS
        npc_name = next(iter(NPC_CATALOGS))
        result = shop_manager.show_buy_list(npc_name)
        assert "상점" in result or npc_name in result

    def test_invalid_npc(self, shop_manager):
        result = shop_manager.show_buy_list("존재하지않는NPC123")
        assert "상점 NPC가 아님" in result or "NPC" in result


# ── execute_buy ──────────────────────────────────────────────────────────────

class TestExecuteBuy:
    def _get_cheap_item(self, npc_name: str):
        """NPC 카탈로그에서 가장 저렴한 아이템 id와 데이터를 반환합니다."""
        from shop import NPC_CATALOGS
        catalog = NPC_CATALOGS[npc_name]
        # bag 타입 제외하고 가장 저렴한 아이템
        non_bag = {k: v for k, v in catalog.items() if v.get("type") != "bag"}
        if not non_bag:
            return next(iter(catalog.items()))
        return min(non_bag.items(), key=lambda x: x[1].get("price", 0))

    def test_buy_valid_item(self, shop_manager):
        from shop import NPC_CATALOGS
        npc_name = "오멜룸"
        if npc_name not in NPC_CATALOGS:
            npc_name = next(iter(NPC_CATALOGS))
        item_id, item = self._get_cheap_item(npc_name)
        price = item.get("price", 0)
        shop_manager.player.gold = price + 1000
        result = shop_manager.execute_buy(npc_name, item_id, 1)
        assert "구매 완료" in result

    def test_buy_insufficient_gold(self, shop_manager):
        from shop import NPC_CATALOGS
        npc_name = next(iter(NPC_CATALOGS))
        item_id, item = self._get_cheap_item(npc_name)
        shop_manager.player.gold = 0
        shop_manager.player.inventory = {}
        price = item.get("price", 0)
        if price == 0:
            pytest.skip("무료 아이템은 이 테스트에 적합하지 않음")
        result = shop_manager.execute_buy(npc_name, item_id, 1)
        assert "골드가 부족" in result

    def test_buy_full_inventory(self, shop_manager):
        from shop import NPC_CATALOGS
        npc_name = "오멜룸"
        if npc_name not in NPC_CATALOGS:
            npc_name = next(iter(NPC_CATALOGS))
        item_id, item = self._get_cheap_item(npc_name)
        if item.get("type") == "bag":
            pytest.skip("가방 아이템은 인벤토리 슬롯 규칙이 다름")
        price = item.get("price", 0)
        shop_manager.player.gold = price * 100 + 9999
        # 슬롯을 다 채움 (item_id가 인벤토리에 없어야 함)
        used, max_slots = shop_manager.player.inventory_check()
        filler = {f"fake_fill_{i}": 1 for i in range(max_slots - used)}
        shop_manager.player.inventory.update(filler)
        # item_id를 인벤토리에서 제거
        shop_manager.player.inventory.pop(item_id, None)
        result = shop_manager.execute_buy(npc_name, item_id, 1)
        assert "가득" in result or "인벤토리" in result

    def test_buy_invalid_npc(self, shop_manager):
        result = shop_manager.execute_buy("존재하지않는NPC", "iron_ore", 1)
        assert "상점 NPC가 아님" in result

    def test_buy_item_not_in_catalog(self, shop_manager):
        from shop import NPC_CATALOGS
        npc_name = next(iter(NPC_CATALOGS))
        shop_manager.player.gold = 99999
        result = shop_manager.execute_buy(npc_name, "completely_fake_item_xyz_123", 1)
        assert "없슴미댜" in result

    def test_buy_bag_appended_to_player(self, shop_manager):
        from shop import NPC_CATALOGS
        from database import BAGS
        npc_name = "몰"
        if npc_name not in NPC_CATALOGS:
            pytest.skip("몰 NPC 없음")
        catalog = NPC_CATALOGS[npc_name]
        bag_items = {k: v for k, v in catalog.items() if v.get("type") == "bag"}
        if not bag_items:
            pytest.skip("몰 카탈로그에 가방 없음")

        # 현재 플레이어 가방보다 슬롯이 많은 가방 찾기
        current_bags = getattr(shop_manager.player, "bags", [])
        current_max = max(
            (BAGS.get(b, {}).get("slots", 0) for b in current_bags),
            default=0
        )
        target_id = None
        for bid, bdata in bag_items.items():
            if bdata.get("slots", 0) > current_max and bid not in current_bags:
                target_id = bid
                break

        if target_id is None:
            pytest.skip("더 큰 가방 없음")

        price = bag_items[target_id].get("price", 0)
        shop_manager.player.gold = price + 9999
        result = shop_manager.execute_buy(npc_name, target_id, 1)
        assert "가방 추가" in result or "구매 완료" in result
        assert target_id in shop_manager.player.bags


# ── find_item_by_name ────────────────────────────────────────────────────────

class TestFindItemByName:
    def test_find_by_id(self):
        from shop import find_item_by_name
        assert find_item_by_name("iron_ore") == "iron_ore"

    def test_find_by_exact_korean_name(self):
        from shop import find_item_by_name
        from items import ALL_ITEMS
        item_id = "iron_ore"
        name = ALL_ITEMS.get(item_id, {}).get("name")
        if not name:
            pytest.skip("iron_ore 한글명 없음")
        assert find_item_by_name(name) == item_id

    def test_find_partial_match(self):
        from shop import find_item_by_name
        # '철광' 이 포함된 아이템이 있어야 함
        result = find_item_by_name("철광")
        assert result is not None

    def test_unknown_returns_none(self):
        from shop import find_item_by_name
        assert find_item_by_name("xxxx_totally_unknown_item") is None


# ── find_item_in_catalog ─────────────────────────────────────────────────────

class TestFindItemInCatalog:
    def test_find_by_id_in_catalog(self):
        from shop import find_item_in_catalog, NPC_CATALOGS
        npc_name = next(iter(NPC_CATALOGS))
        catalog = NPC_CATALOGS[npc_name]
        item_id = next(iter(catalog))
        assert find_item_in_catalog(catalog, item_id) == item_id

    def test_unknown_item_returns_none(self):
        from shop import find_item_in_catalog, NPC_CATALOGS
        npc_name = next(iter(NPC_CATALOGS))
        catalog = NPC_CATALOGS[npc_name]
        assert find_item_in_catalog(catalog, "zzz_impossible_item") is None
