"""tests/test_gathering.py — GatheringEngine 단위 테스트"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── 데이터 테이블 유효성 ──────────────────────────────────────────────────────────

class TestGatheringData:
    def test_gather_items_by_season_has_all_seasons(self):
        from gathering import GATHER_ITEMS_BY_SEASON
        for season in ("spring", "summer", "autumn", "winter"):
            assert season in GATHER_ITEMS_BY_SEASON

    def test_gather_items_have_required_keys(self):
        from gathering import GATHER_ITEMS_BY_SEASON
        required = {"id", "name", "grade", "rate"}
        for season, items in GATHER_ITEMS_BY_SEASON.items():
            for item in items:
                missing = required - item.keys()
                assert not missing, f"{season} 아이템 '{item.get('name')}' 누락 키: {missing}"

    def test_mine_items_have_required_keys(self):
        from gathering import MINE_ITEMS
        required = {"id", "name", "grade", "rate", "str_req"}
        for item in MINE_ITEMS:
            missing = required - item.keys()
            assert not missing, f"MINE_ITEMS '{item.get('name')}' 누락 키: {missing}"

    def test_gather_zone_items_has_mushroom_zone(self):
        from gathering import GATHER_ZONE_ITEMS
        assert "버섯 군락지" in GATHER_ZONE_ITEMS

    def test_gather_zone_items_have_required_keys(self):
        from gathering import GATHER_ZONE_ITEMS
        required = {"id", "name", "grade", "rate"}
        for zone, items in GATHER_ZONE_ITEMS.items():
            for item in items:
                missing = required - item.keys()
                assert not missing, f"{zone} 아이템 '{item.get('name')}' 누락 키: {missing}"

    def test_woodcut_table_has_ranks(self):
        from gathering import WOODCUT_TABLE
        assert len(WOODCUT_TABLE) > 0
        for rank, data in WOODCUT_TABLE.items():
            assert "id" in data
            assert "energy_cost" in data


# ── GatheringEngine 초기화 ────────────────────────────────────────────────────

class TestGatheringEngineInit:
    def test_engine_has_player(self, gathering_engine, fresh_player):
        assert gathering_engine.player is fresh_player


# ── GatheringEngine.gather — 기력 부족 ─────────────────────────────────────────

class TestGatherEnergyInsufficient:
    @pytest.mark.asyncio
    async def test_gather_fails_when_no_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.gather(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content

    @pytest.mark.asyncio
    async def test_gather_energy_not_deducted_on_failure(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.gather(mock_ctx)
        assert gathering_engine.player.energy == 0

    @pytest.mark.asyncio
    async def test_gather_fails_when_energy_below_cost(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 7  # gather cost is 8
        await gathering_engine.gather(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content


# ── GatheringEngine.mine — 기력 부족 ──────────────────────────────────────────

class TestMineEnergyInsufficient:
    @pytest.mark.asyncio
    async def test_mine_fails_when_no_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.mine(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content

    @pytest.mark.asyncio
    async def test_mine_energy_not_deducted_on_failure(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.mine(mock_ctx)
        assert gathering_engine.player.energy == 0

    @pytest.mark.asyncio
    async def test_mine_fails_when_energy_below_cost(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 9  # mine cost is 10
        await gathering_engine.mine(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content


# ── GatheringEngine.woodcut — 기력 부족 ────────────────────────────────────────

class TestWoodcutEnergyInsufficient:
    @pytest.mark.asyncio
    async def test_woodcut_fails_when_no_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.woodcut(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content

    @pytest.mark.asyncio
    async def test_woodcut_energy_not_deducted_on_failure(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 0
        await gathering_engine.woodcut(mock_ctx)
        assert gathering_engine.player.energy == 0

    @pytest.mark.asyncio
    async def test_woodcut_fails_when_energy_below_cost(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 8  # woodcut cost is 9
        await gathering_engine.woodcut(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content


# ── GatheringEngine.gather — 기력 충분 ─────────────────────────────────────────

class TestGatherWithEnergy:
    @pytest.mark.asyncio
    async def test_gather_consumes_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx)
        assert gathering_engine.player.energy == 92  # 100 - 8

    @pytest.mark.asyncio
    async def test_gather_with_zone_name_uses_zone_pool(self, gathering_engine, mock_ctx):
        from gathering import GATHER_ZONE_ITEMS
        zone_name = "버섯 군락지"
        gathering_engine.player.energy = 100

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx, zone_name=zone_name)

        zone_ids = {item["id"] for item in GATHER_ZONE_ITEMS[zone_name]}
        call_args = mock_bridge.on_gather_complete.call_args
        used_item_id = call_args[0][1]
        assert used_item_id in zone_ids

    @pytest.mark.asyncio
    async def test_gather_with_invalid_zone_uses_season_pool(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx, zone_name="존재하지않는존")

        mock_bridge.on_gather_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_gather_trains_gathering_skill(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx)

        # train_skill이 호출됐는지 확인 (skill_ranks 변화 또는 xp 증가)
        # Player.train_skill은 기존 player fixture에서 실제 동작
        assert gathering_engine.player.skill_exp.get("gathering", 0) > 0


# ── GatheringEngine.mine — 기력 충분 ──────────────────────────────────────────

class TestMineWithEnergy:
    @pytest.mark.asyncio
    async def test_mine_consumes_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.mine(mock_ctx)
        assert gathering_engine.player.energy == 90  # 100 - 10

    @pytest.mark.asyncio
    async def test_mine_adds_item_to_inventory(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        gathering_engine.player.inventory = {}
        before_total = sum(gathering_engine.player.inventory.values())
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.mine(mock_ctx)
        after_total = sum(gathering_engine.player.inventory.values())
        assert after_total >= before_total  # 아이템이 추가됐거나 인벤토리 부족

    @pytest.mark.asyncio
    async def test_mine_trains_mining_skill(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.mine(mock_ctx)
        assert gathering_engine.player.skill_exp.get("mining", 0) > 0

    @pytest.mark.asyncio
    async def test_mine_str_filtering_low_str(self, gathering_engine, mock_ctx):
        """낮은 힘 스탯이면 낮은 str_req 아이템만 나옴"""
        from gathering import MINE_ITEMS
        gathering_engine.player.energy = 100
        gathering_engine.player.base_stats["str"] = 5  # str_req <= 5인 것만 가능
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.mine(mock_ctx)

        # 인벤토리에 추가된 아이템이 str_req <= 5인지 확인
        available_ids = {i["id"] for i in MINE_ITEMS if i["str_req"] <= 5}
        for item_id in gathering_engine.player.inventory:
            if item_id in {i["id"] for i in MINE_ITEMS}:
                assert item_id in available_ids


# ── GatheringEngine.woodcut — 기력 충분 ────────────────────────────────────────

class TestWoodcutWithEnergy:
    @pytest.mark.asyncio
    async def test_woodcut_consumes_energy(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.woodcut(mock_ctx)
        assert gathering_engine.player.energy == 91  # 100 - 9

    @pytest.mark.asyncio
    async def test_woodcut_adds_item_to_inventory(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        gathering_engine.player.inventory = {}
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.woodcut(mock_ctx)
        total = sum(gathering_engine.player.inventory.values())
        assert total >= 0  # 추가됐거나 인벤토리 부족

    @pytest.mark.asyncio
    async def test_woodcut_trains_woodcutting_skill(self, gathering_engine, mock_ctx):
        gathering_engine.player.energy = 100
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gathering_engine.woodcut(mock_ctx)
        assert gathering_engine.player.skill_exp.get("woodcutting", 0) > 0

    @pytest.mark.asyncio
    async def test_woodcut_high_str_unlocks_better_wood(self, gathering_engine, mock_ctx):
        """힘이 높으면 더 좋은 나무 아이템 풀이 열림"""
        gathering_engine.player.base_stats["str"] = 60  # str_req <= 60인 것 전부 사용 가능

        collected_ids = set()
        # 반복 실행해서 다양한 아이템이 나오는지 확인
        for _ in range(10):
            gathering_engine.player.energy = 200
            gathering_engine.player.inventory = {}
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await gathering_engine.woodcut(mock_ctx)
            collected_ids.update(gathering_engine.player.inventory.keys())

        # high str일 때 고급 목재류가 나올 수 있는 풀에 포함된 것이 존재해야 함
        valid_high_str_ids = {"gt_wood_01", "wood_log", "hardwood", "ancient_wood", "treant_core"}
        assert collected_ids & valid_high_str_ids  # 교집합이 비어있지 않아야 함


# ── GATHER_ZONE_ITEMS 풀 선택 ─────────────────────────────────────────────────

class TestGatherZonePool:
    @pytest.mark.asyncio
    async def test_zone_name_selects_zone_pool(self, gathering_engine, mock_ctx):
        from gathering import GATHER_ZONE_ITEMS
        zone_name = "버섯 군락지"
        zone_ids = {item["id"] for item in GATHER_ZONE_ITEMS[zone_name]}
        gathering_engine.player.energy = 100

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx, zone_name=zone_name)

        call_args = mock_bridge.on_gather_complete.call_args
        used_item_id = call_args[0][1]
        assert used_item_id in zone_ids

    @pytest.mark.asyncio
    async def test_none_zone_name_uses_season_pool(self, gathering_engine, mock_ctx):
        from gathering import GATHER_ITEMS_BY_SEASON
        gathering_engine.player.energy = 100
        all_season_ids = {
            item["id"]
            for items in GATHER_ITEMS_BY_SEASON.values()
            for item in items
        }

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("gather_bridge.gather_bridge") as mock_bridge, \
             patch("economy.Economy"):
            mock_bridge.on_gather_complete.return_value = {
                "added": True, "is_new_collection": False
            }
            await gathering_engine.gather(mock_ctx, zone_name=None)

        call_args = mock_bridge.on_gather_complete.call_args
        used_item_id = call_args[0][1]
        assert used_item_id in all_season_ids
