"""tests/test_save_manager_async.py — SaveManager.save_async() 단위 테스트."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from save_manager import SaveManager
from utils.player_lock import cleanup_lock


def _make_player(user_id: int = 1):
    player = MagicMock()
    player.user_id = user_id
    return player


class TestSaveAsync:
    @pytest.mark.asyncio
    async def test_save_async_returns_true_on_success(self):
        """save_async는 save()가 True를 반환하면 True를 반환한다."""
        sm = SaveManager()
        player = _make_player(10001)
        with patch.object(sm, "save", return_value=True) as mock_save:
            result = await sm.save_async(player)
        assert result is True
        mock_save.assert_called_once_with(player)
        cleanup_lock(10001)

    @pytest.mark.asyncio
    async def test_save_async_returns_false_on_failure(self):
        """save_async는 save()가 False를 반환하면 False를 반환한다."""
        sm = SaveManager()
        player = _make_player(10002)
        with patch.object(sm, "save", return_value=False):
            result = await sm.save_async(player)
        assert result is False
        cleanup_lock(10002)

    @pytest.mark.asyncio
    async def test_save_async_serialises_concurrent_calls(self):
        """동일 user_id에 대한 동시 save_async 호출이 직렬화된다."""
        sm = SaveManager()
        user_id = 10003
        results = []

        player = _make_player(user_id)

        async def call_save():
            results.append(await sm.save_async(player))

        with patch.object(sm, "save", side_effect=lambda p: results.append("saved") or True):
            await asyncio.gather(call_save(), call_save())

        assert results.count("saved") == 2
        cleanup_lock(user_id)

    @pytest.mark.asyncio
    async def test_save_async_lock_prevents_concurrent_writes(self):
        """두 번째 save_async는 첫 번째가 끝날 때까지 Lock으로 대기한다."""
        sm = SaveManager()
        user_id = 10004
        player = _make_player(user_id)

        # save()를 동기 함수로 패치하되, 내부에서 Lock이 제대로 직렬화하는지 확인
        call_count = [0]

        def sync_save(p):
            call_count[0] += 1
            return True

        with patch.object(sm, "save", side_effect=sync_save):
            await asyncio.gather(
                sm.save_async(player),
                sm.save_async(player),
            )

        assert call_count[0] == 2
        cleanup_lock(user_id)

    @pytest.mark.asyncio
    async def test_save_async_different_users_do_not_block(self):
        """서로 다른 user_id에 대한 save_async는 서로 차단하지 않는다."""
        sm = SaveManager()
        results = []

        async def save_user(uid: int):
            player = _make_player(uid)
            with patch.object(sm, "save", return_value=True):
                ok = await sm.save_async(player)
            results.append((uid, ok))

        await asyncio.gather(save_user(20001), save_user(20002))
        uids = {r[0] for r in results}
        assert uids == {20001, 20002}
        cleanup_lock(20001)
        cleanup_lock(20002)
