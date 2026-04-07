"""tests/test_player_lock.py — utils.player_lock 단위 테스트."""

import asyncio
import pytest

from utils.player_lock import cleanup_lock, get_player_lock


class TestGetPlayerLock:
    def test_returns_asyncio_lock(self):
        """get_player_lock은 asyncio.Lock 인스턴스를 반환한다."""
        lock = get_player_lock(1001)
        assert isinstance(lock, asyncio.Lock)
        cleanup_lock(1001)

    def test_same_user_id_returns_same_lock(self):
        """동일 user_id에 대해 항상 같은 Lock 객체를 반환한다."""
        lock_a = get_player_lock(2001)
        lock_b = get_player_lock(2001)
        assert lock_a is lock_b
        cleanup_lock(2001)

    def test_different_user_ids_return_different_locks(self):
        """서로 다른 user_id는 서로 다른 Lock 객체를 반환한다."""
        lock_x = get_player_lock(3001)
        lock_y = get_player_lock(3002)
        assert lock_x is not lock_y
        cleanup_lock(3001)
        cleanup_lock(3002)

    def test_lock_not_held_initially(self):
        """새로 생성된 Lock은 잠겨있지 않다."""
        lock = get_player_lock(4001)
        assert not lock.locked()
        cleanup_lock(4001)


class TestCleanupLock:
    def test_cleanup_removes_lock(self):
        """cleanup_lock 후 새로 요청하면 다른 Lock 객체가 반환된다."""
        lock_before = get_player_lock(5001)
        cleanup_lock(5001)
        lock_after = get_player_lock(5001)
        assert lock_before is not lock_after
        cleanup_lock(5001)

    def test_cleanup_nonexistent_user_no_error(self):
        """존재하지 않는 user_id를 cleanup해도 오류가 발생하지 않는다."""
        cleanup_lock(99999)  # should not raise


class TestLockConcurrency:
    @pytest.mark.asyncio
    async def test_lock_blocks_concurrent_access(self):
        """Lock이 실제로 동시 접근을 차단하는지 검증."""
        results = []

        async def task_a():
            async with get_player_lock(6001):
                results.append("a_start")
                await asyncio.sleep(0.05)
                results.append("a_end")

        async def task_b():
            # task_a가 먼저 Lock을 획득하도록 잠시 대기
            await asyncio.sleep(0.01)
            async with get_player_lock(6001):
                results.append("b_start")
                await asyncio.sleep(0.01)
                results.append("b_end")

        await asyncio.gather(task_a(), task_b())
        # task_a가 완전히 끝난 후 task_b가 실행되어야 한다
        assert results == ["a_start", "a_end", "b_start", "b_end"]
        cleanup_lock(6001)

    @pytest.mark.asyncio
    async def test_different_users_do_not_block_each_other(self):
        """서로 다른 user_id의 Lock은 서로 차단하지 않는다."""
        results = []

        async def task_user1():
            async with get_player_lock(7001):
                results.append("u1_start")
                await asyncio.sleep(0.05)
                results.append("u1_end")

        async def task_user2():
            async with get_player_lock(7002):
                results.append("u2_start")
                await asyncio.sleep(0.05)
                results.append("u2_end")

        await asyncio.gather(task_user1(), task_user2())
        # 두 태스크가 동시에 실행되어야 하므로 각 "_start"가 "_end" 전에 모두 나온다
        assert results.index("u1_start") < results.index("u1_end")
        assert results.index("u2_start") < results.index("u2_end")
        # 두 태스크가 겹쳐서 실행됨: u1_end 전에 u2_start가 나타나야 한다
        assert results.index("u2_start") < results.index("u1_end")
        cleanup_lock(7001)
        cleanup_lock(7002)

    @pytest.mark.asyncio
    async def test_locked_check_returns_true_while_held(self):
        """Lock이 점유 중일 때 lock.locked()가 True를 반환한다."""
        lock = get_player_lock(8001)
        acquired = asyncio.Event()
        release = asyncio.Event()

        async def holder():
            async with lock:
                acquired.set()
                await release.wait()

        task = asyncio.create_task(holder())
        await acquired.wait()
        assert lock.locked()
        release.set()
        await task
        assert not lock.locked()
        cleanup_lock(8001)
