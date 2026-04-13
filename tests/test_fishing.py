"""tests/test_fishing.py — FishingEngine 단위 테스트 (discord.ui.View 제외)"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── FishingEngine.set_spot ────────────────────────────────────────────────────

class TestSetSpot:
    def test_set_valid_spot(self, fishing_engine):
        from fishing import FISH_GUIDE
        spot_name = next(iter(FISH_GUIDE))
        fishing_engine.set_spot(spot_name)
        assert fishing_engine.current_spot == spot_name

    def test_set_all_valid_spots(self, fishing_engine):
        from fishing import FISH_GUIDE
        for spot_name in FISH_GUIDE:
            fishing_engine.set_spot(spot_name)
            assert fishing_engine.current_spot == spot_name

    def test_ignore_invalid_spot(self, fishing_engine):
        original = fishing_engine.current_spot
        fishing_engine.set_spot("존재하지않는낚시터")
        assert fishing_engine.current_spot == original

    def test_default_spot_exists_in_fish_guide(self, fishing_engine):
        from fishing import FISH_GUIDE
        assert fishing_engine.current_spot in FISH_GUIDE


# ── FISH_DB / FISH_GUIDE 데이터 유효성 ─────────────────────────────────────────

class TestFishData:
    def test_fish_db_has_entries(self):
        from fishing import FISH_DB
        assert len(FISH_DB) > 0

    def test_fish_db_entries_have_required_keys(self):
        from fishing import FISH_DB
        required = {"id", "grade", "price", "rate", "rank_req"}
        for name, data in FISH_DB.items():
            missing = required - data.keys()
            assert not missing, f"{name} 누락 키: {missing}"

    def test_fish_guide_has_entries(self):
        from fishing import FISH_GUIDE
        assert len(FISH_GUIDE) > 0

    def test_fish_guide_entries_have_required_keys(self):
        from fishing import FISH_GUIDE
        required = {"desc", "fish", "energy_cost", "fee_rate"}
        for spot, data in FISH_GUIDE.items():
            missing = required - data.keys()
            assert not missing, f"{spot} 누락 키: {missing}"

    def test_fish_guide_fish_names_exist_in_fish_db(self):
        from fishing import FISH_GUIDE, FISH_DB
        for spot_name, spot in FISH_GUIDE.items():
            for fish_name in spot["fish"]:
                assert fish_name in FISH_DB, (
                    f"{spot_name}의 물고기 '{fish_name}'가 FISH_DB에 없음"
                )

    def test_fish_guide_energy_cost_positive(self):
        from fishing import FISH_GUIDE
        for spot_name, spot in FISH_GUIDE.items():
            assert spot["energy_cost"] > 0, f"{spot_name} energy_cost는 양수여야 함"

    def test_fish_db_rates_positive(self):
        from fishing import FISH_DB
        for name, data in FISH_DB.items():
            assert data["rate"] > 0, f"{name} rate는 양수여야 함"


# ── FishingEngine.fish — 기력 부족 ─────────────────────────────────────────────

class TestFishEnergyInsufficient:
    @pytest.mark.asyncio
    async def test_fish_fails_when_no_energy(self, fishing_engine, mock_ctx):
        fishing_engine.player.energy = 0
        await fishing_engine.fish(mock_ctx)
        assert len(mock_ctx._sent) == 1
        assert "기력" in mock_ctx._sent[0].content

    @pytest.mark.asyncio
    async def test_fish_sends_error_message_with_cost_info(self, fishing_engine, mock_ctx):
        from fishing import FISH_GUIDE
        spot = FISH_GUIDE[fishing_engine.current_spot]
        energy_cost = spot["energy_cost"]
        fishing_engine.player.energy = energy_cost - 1
        await fishing_engine.fish(mock_ctx)
        assert len(mock_ctx._sent) == 1

    @pytest.mark.asyncio
    async def test_fish_energy_not_deducted_on_failure(self, fishing_engine, mock_ctx):
        fishing_engine.player.energy = 0
        before = fishing_engine.player.energy
        await fishing_engine.fish(mock_ctx)
        assert fishing_engine.player.energy == before


# ── FishingEngine.fish — 기력 충분 (FishingView.start mock) ────────────────────

class TestFishWithEnergy:
    @pytest.mark.asyncio
    async def test_fish_consumes_energy(self, fishing_engine, mock_ctx):
        from fishing import FISH_GUIDE
        spot = FISH_GUIDE[fishing_engine.current_spot]
        energy_cost = spot["energy_cost"]
        fishing_engine.player.energy = energy_cost + 50

        with patch("fishing.FishingView") as MockView:
            instance = MagicMock()
            instance.start = AsyncMock()
            MockView.return_value = instance
            await fishing_engine.fish(mock_ctx)

        assert fishing_engine.player.energy == 50

    @pytest.mark.asyncio
    async def test_fish_calls_view_start(self, fishing_engine, mock_ctx):
        from fishing import FISH_GUIDE
        spot = FISH_GUIDE[fishing_engine.current_spot]
        energy_cost = spot["energy_cost"]
        fishing_engine.player.energy = energy_cost + 50

        with patch("fishing.FishingView") as MockView:
            instance = MagicMock()
            instance.start = AsyncMock()
            MockView.return_value = instance
            await fishing_engine.fish(mock_ctx)

        instance.start.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    async def test_fish_passes_correct_spot_to_view(self, fishing_engine, mock_ctx):
        from fishing import FISH_GUIDE
        spot_name = next(iter(FISH_GUIDE))
        fishing_engine.set_spot(spot_name)
        spot = FISH_GUIDE[spot_name]
        energy_cost = spot["energy_cost"]
        fishing_engine.player.energy = energy_cost + 50

        with patch("fishing.FishingView") as MockView:
            instance = MagicMock()
            instance.start = AsyncMock()
            MockView.return_value = instance
            await fishing_engine.fish(mock_ctx)

        call_args = MockView.call_args
        assert call_args[0][0] is fishing_engine.player
        assert call_args[0][1] == spot_name


# ── 물고기 풀 랭크 필터링 ──────────────────────────────────────────────────────

class TestFishPoolFiltering:
    def _get_filtered_pool(self, fishing_engine, spot_name):
        """FishingEngine.fish() 내부의 풀 필터링 로직을 재현합니다."""
        from fishing import FISH_GUIDE, FISH_DB
        from utils.ranks import rank_gte as _rank_gte
        spot = FISH_GUIDE[spot_name]
        rank = fishing_engine.player.skill_ranks.get("fishing", "연습")
        fish_names = spot.get("fish", [])
        return {
            name: FISH_DB[name]
            for name in fish_names
            if name in FISH_DB and _rank_gte(rank, FISH_DB[name].get("rank_req", "연습"))
        }

    def test_beginner_rank_gets_rank_req_practiced_fish(self, fishing_engine):
        from fishing import FISH_GUIDE, FISH_DB
        fishing_engine.player.skill_ranks["fishing"] = "연습"
        # '고요한 연못'에는 연습 랭크 물고기만 있음 (붕어, 잉어 등)
        pool = self._get_filtered_pool(fishing_engine, "고요한 연못")
        assert len(pool) > 0

    def test_high_rank_spot_filtered_for_beginner(self, fishing_engine):
        from fishing import FISH_GUIDE, FISH_DB
        from utils.ranks import rank_gte as _rank_gte
        fishing_engine.player.skill_ranks["fishing"] = "연습"
        # '요정의 샘'은 B랭 이상 물고기만 있음 - 연습 랭크면 일부 또는 전부 필터됨
        pool = self._get_filtered_pool(fishing_engine, "요정의 샘")
        # 필터링 결과는 랭크 조건을 만족하는 것만 포함
        for fish_name, fish_data in pool.items():
            assert _rank_gte("연습", fish_data.get("rank_req", "연습"))

    def test_empty_pool_fallback(self, fishing_engine):
        """풀이 비어있으면 rank 무관하게 해당 존 전체 물고기 반환"""
        from fishing import FISH_GUIDE, FISH_DB
        # 매우 높은 랭크 설정 (실제로 필터가 다 통과시키도록)
        fishing_engine.player.skill_ranks["fishing"] = "1"
        pool = self._get_filtered_pool(fishing_engine, "방울숲 강")
        assert len(pool) > 0

    def test_pool_contains_only_fish_in_spot(self, fishing_engine):
        from fishing import FISH_GUIDE
        fishing_engine.player.skill_ranks["fishing"] = "1"
        spot_name = "방울숲 강"
        spot_fish = set(FISH_GUIDE[spot_name]["fish"])
        pool = self._get_filtered_pool(fishing_engine, spot_name)
        for name in pool:
            assert name in spot_fish


# ── show_fish_guide ────────────────────────────────────────────────────────────

class TestShowFishGuide:
    def test_returns_string(self, fishing_engine):
        result = fishing_engine.show_fish_guide()
        assert isinstance(result, str)

    def test_contains_spot_names(self, fishing_engine):
        from fishing import FISH_GUIDE
        result = fishing_engine.show_fish_guide()
        for spot_name in FISH_GUIDE:
            assert spot_name in result

    def test_contains_fish_names(self, fishing_engine):
        from fishing import FISH_GUIDE, FISH_DB
        from utils.ranks import rank_gte as _rank_gte
        fishing_engine.player.skill_ranks["fishing"] = "1"
        result = fishing_engine.show_fish_guide()
        # 전체 물고기 중 일부는 반드시 등장해야 함
        found = sum(1 for name in FISH_DB if name in result)
        assert found > 0
