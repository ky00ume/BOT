import pytest

from ui.expiring_view import ExpiringView


class FakeMessage:
    def __init__(self):
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


@pytest.mark.asyncio
async def test_expired_view_removes_components_instead_of_leaving_dead_buttons():
    view = ExpiringView(timeout=1)
    message = FakeMessage()
    view.bind_message(message)
    await view.on_timeout()
    assert message.edits == [{"view": None}]


@pytest.mark.asyncio
async def test_unbound_expired_view_is_safe():
    view = ExpiringView(timeout=1)
    await view.on_timeout()
