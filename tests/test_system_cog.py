"""tests/test_system_cog.py — SystemCog 단위 테스트 (REMEDIATION_PLAN 1-A).

SystemCog 클래스의 기본 구조와 명령어 등록을 검증합니다.
discord 가 없는 환경에서는 자동으로 skip 된다.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# discord 가 설치되지 않은 환경(CI 테스트 컨테이너 외)에서 전체 모듈 skip
pytest.importorskip("discord")


class TestSystemCogImport:
    """SystemCog 임포트 및 초기화 검증."""

    def test_import(self):
        """cogs.system_cog 임포트가 성공해야 한다."""
        from cogs.system_cog import SystemCog
        assert SystemCog is not None

    def test_instantiation(self):
        """SystemCog 인스턴스 생성이 성공해야 한다."""
        from cogs.system_cog import SystemCog
        bot = MagicMock()
        player = MagicMock()
        save_mgr = MagicMock()
        cog = SystemCog(bot, shared_player=player, save_manager=save_mgr,
                        allowed_channel_id=12345)
        assert cog.allowed_channel_id == 12345
        assert cog.shared_player is player
        assert cog.save_manager is save_mgr

    def test_commands_registered(self):
        """SystemCog 에 모든 명령어가 등록되어 있어야 한다."""
        from cogs.system_cog import SystemCog
        command_names = {cmd.name for cmd in SystemCog.__cog_commands__}
        expected = {
            "도움말", "저장", "주사위", "날씨",
            "마을상태", "공지", "게시판", "명예의전당", "낚시순위",
        }
        assert expected.issubset(command_names)


class TestSystemCogCheckChannel:
    """_check_channel 헬퍼 검증."""

    def _make_cog(self, allowed_id: int = 9999):
        from cogs.system_cog import SystemCog
        bot = MagicMock()
        player = MagicMock()
        save_mgr = MagicMock()
        return SystemCog(bot, shared_player=player, save_manager=save_mgr,
                         allowed_channel_id=allowed_id)

    @pytest.mark.asyncio
    async def test_check_channel_allowed(self):
        """올바른 채널 ID 는 True 를 반환한다."""
        cog = self._make_cog(allowed_id=111)
        ctx = MagicMock()
        ctx.channel.id = 111
        result = await cog._check_channel(ctx)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_channel_disallowed(self):
        """잘못된 채널 ID 는 False 를 반환한다."""
        cog = self._make_cog(allowed_id=111)
        ctx = MagicMock()
        ctx.channel.id = 999
        result = await cog._check_channel(ctx)
        assert result is False


class TestDiceCmd:
    """주사위 명령어 검증."""

    def _make_cog(self):
        from cogs.system_cog import SystemCog
        bot = MagicMock()
        player = MagicMock()
        save_mgr = MagicMock()
        return SystemCog(bot, shared_player=player, save_manager=save_mgr,
                         allowed_channel_id=111)

    @pytest.mark.asyncio
    async def test_dice_result_within_range(self):
        """주사위 결과가 1~sides 범위에 있어야 한다."""
        cog = self._make_cog()
        ctx = MagicMock()
        ctx.channel.id = 111
        sent_title = []

        async def fake_send_msg_card(ctx_, title, message, **kwargs):
            sent_title.append(title)

        cog._send_msg_card = fake_send_msg_card

        for _ in range(10):
            await cog.dice_cmd.callback(cog, ctx, 6)

        assert all("6면 주사위" in t for t in sent_title)

    @pytest.mark.asyncio
    async def test_dice_sides_clamped_min(self):
        """sides 가 2 미만이면 2로 클램핑된다."""
        cog = self._make_cog()
        ctx = MagicMock()
        ctx.channel.id = 111
        sent_title = []

        async def fake_send_msg_card(ctx_, title, message, **kwargs):
            sent_title.append(title)

        cog._send_msg_card = fake_send_msg_card
        await cog.dice_cmd.callback(cog, ctx, 1)
        assert "2면 주사위" in sent_title[0]

    @pytest.mark.asyncio
    async def test_dice_channel_check_fails(self):
        """채널 검사 실패 시 메시지를 보내지 않는다."""
        cog = self._make_cog()
        ctx = MagicMock()
        ctx.channel.id = 999  # wrong channel
        ctx.send = AsyncMock()
        cog._send_msg_card = AsyncMock()
        await cog.dice_cmd.callback(cog, ctx, 6)
        cog._send_msg_card.assert_not_called()


class TestSaveCmd:
    """저장 명령어 검증."""

    def _make_cog(self):
        from cogs.system_cog import SystemCog
        bot = MagicMock()
        player = MagicMock()
        save_mgr = MagicMock()
        save_mgr.save = MagicMock(return_value=True)
        return SystemCog(bot, shared_player=player, save_manager=save_mgr,
                         allowed_channel_id=111)

    @pytest.mark.asyncio
    async def test_save_calls_save_manager(self):
        """저장 명령어 실행 시 save_manager.save() 가 호출된다."""
        cog = self._make_cog()
        ctx = MagicMock()
        ctx.channel.id = 111
        cog._send_msg_card = AsyncMock()
        await cog.save_cmd.callback(cog, ctx)
        cog.save_manager.save.assert_called_once_with(cog.shared_player)

    @pytest.mark.asyncio
    async def test_save_error_sends_message(self):
        """save_manager.save() 가 예외를 던지면 에러 메시지를 보낸다."""
        cog = self._make_cog()
        cog.save_manager.save.side_effect = RuntimeError("DB 에러")
        ctx = MagicMock()
        ctx.channel.id = 111
        ctx.send = AsyncMock()
        cog._send_msg_card = AsyncMock()
        await cog.save_cmd.callback(cog, ctx)
        ctx.send.assert_called_once()
