import pytest

from cogs.events_cog import EventsCog


class FakeAuthor:
    def __init__(self, user_id):
        self.id = user_id


class FakeMessage:
    def __init__(self, message_id, author_id, has_components=True):
        self.id = message_id
        self.author = FakeAuthor(author_id)
        self.components = [object()] if has_components else []
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


class FakeChannel:
    def __init__(self, messages):
        self.messages = messages

    def history(self, *, limit):
        assert limit == 100
        async def gen():
            for message in self.messages:
                yield message
        return gen()


class FakeCtx:
    allowed_channel_id = 123


class FakeBot:
    def __init__(self, channel):
        self.ctx = FakeCtx()
        self.user = FakeAuthor(777)
        self.channel = channel

    def get_channel(self, channel_id):
        assert channel_id == 123
        return self.channel


@pytest.mark.asyncio
async def test_startup_cleanup_closes_only_own_stale_component_windows():
    own_stale = FakeMessage(1, 777, True)
    own_plain = FakeMessage(2, 777, False)
    someone_else = FakeMessage(3, 888, True)
    cog = EventsCog(FakeBot(FakeChannel([own_stale, own_plain, someone_else])))

    closed = await cog._close_stale_interaction_windows()

    assert closed == 1
    assert own_stale.edits == [{"view": None}]
    assert own_plain.edits == []
    assert someone_else.edits == []
