"""Pytest configuration and fixtures.

이 파일은 모든 테스트에서 사용할 수 있는 공통 fixture들을 정의합니다.
"""
import pytest
import os
import tempfile
from typing import Generator


# ── Discord Mock Classes ─────────────────────────────────────────────────────

class MockUser:
    """Discord User mock"""
    def __init__(self, id=12345, name="TestUser", bot=False):
        self.id = id
        self.name = name
        self.display_name = name
        self.bot = bot
        self.mention = f"<@{id}>"


class MockChannel:
    """Discord TextChannel mock"""
    def __init__(self, id=99999, name="test-channel"):
        self.id = id
        self.name = name
        self.mention = f"<#{id}>"
        self._sent_messages = []

    async def send(self, content=None, *, embed=None, view=None, file=None):
        msg = MockMessage(content=content, embed=embed)
        self._sent_messages.append(msg)
        return msg


class MockMessage:
    """Discord Message mock"""
    def __init__(self, content=None, embed=None, author=None, channel=None):
        self.content = content
        self.embed = embed
        self.author = author or MockUser()
        self.channel = channel or MockChannel()
        self._edited = False

    async def edit(self, content=None, embed=None, view=None):
        if content:
            self.content = content
        if embed:
            self.embed = embed
        self._edited = True


class MockInteractionResponse:
    async def defer(self, ephemeral=False):
        pass

    async def send_message(self, content=None, embed=None, view=None, ephemeral=False):
        pass


class MockFollowup:
    def __init__(self, channel=None):
        self.channel = channel or MockChannel()
        self._messages = []

    async def send(self, content=None, embed=None, view=None, ephemeral=False):
        msg = MockMessage(content=content, embed=embed)
        self._messages.append(msg)
        return msg


class MockInteraction:
    """Discord Interaction mock"""
    def __init__(self, user=None, channel=None):
        self.user = user or MockUser()
        self.channel = channel or MockChannel()
        self.response = MockInteractionResponse()
        self.followup = MockFollowup(channel=self.channel)
        self._responded = False


class MockContext:
    """commands.Context mock"""
    def __init__(self, author=None, channel=None, bot=None):
        self.author = author or MockUser()
        self.channel = channel or MockChannel()
        self.bot = bot
        self._sent = []

    async def send(self, content=None, *, embed=None, view=None, file=None):
        msg = MockMessage(content=content, embed=embed)
        self._sent.append(msg)
        return msg

    async def reply(self, content=None, *, embed=None, mention_author=False):
        return await self.send(content, embed=embed)


@pytest.fixture
def fresh_player():
    """테스트용 새 플레이어 인스턴스.

    Returns:
        초기 상태의 Player 객체
    """
    from player import Player
    return Player(name="테스트플레이어")


@pytest.fixture
def player_with_gold(fresh_player):
    """골드를 보유한 플레이어.

    Returns:
        1000 골드를 보유한 Player 객체
    """
    fresh_player.gold = 1000
    return fresh_player


@pytest.fixture
def player_with_items(fresh_player):
    """아이템을 보유한 플레이어.

    Returns:
        여러 아이템을 보유한 Player 객체
    """
    fresh_player.inventory = {
        "herb_01": 10,
        "ore_iron": 5,
        "potion_hp": 3,
    }
    return fresh_player


@pytest.fixture
def economy(fresh_player):
    """Economy 인스턴스.

    Returns:
        fresh_player와 연결된 Economy 객체
    """
    from economy import Economy
    return Economy(fresh_player)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """임시 데이터베이스 fixture.

    테스트용 임시 DB 파일을 생성하고 테스트 후 삭제합니다.

    Yields:
        임시 DB 파일 경로
    """
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # DB 환경변수 설정
    old_db = os.environ.get('DB_PATH')
    os.environ['DB_PATH'] = path

    # DB 초기화
    from database import init_db
    init_db()

    yield path

    # 정리
    if old_db:
        os.environ['DB_PATH'] = old_db
    else:
        if 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']

    # 파일 삭제
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def quest_manager(fresh_player):
    """QuestManager 인스턴스.

    Returns:
        fresh_player와 연결된 QuestManager 객체
    """
    from quest import QuestManager
    return QuestManager(fresh_player)


@pytest.fixture
def shop_manager(fresh_player):
    """ShopManager 인스턴스.

    Returns:
        fresh_player와 연결된 ShopManager 객체
    """
    from shop import ShopManager
    return ShopManager(fresh_player)


@pytest.fixture
def crafting_engine(fresh_player):
    """CraftingEngine 인스턴스.

    Returns:
        fresh_player와 연결된 CraftingEngine 객체
    """
    from crafting import CraftingEngine
    return CraftingEngine(fresh_player)


@pytest.fixture
def adventure_engine(fresh_player, monkeypatch):
    """AdventureEngine 인스턴스.

    discord가 설치되지 않은 환경에서는 monkeypatch로 sys.modules에 stub을
    일시 등록하고 테스트 후 자동 복원합니다.

    Returns:
        fresh_player와 연결된 AdventureEngine 객체
    """
    import sys
    import types

    try:
        import discord  # noqa: F401
    except ImportError:
        _discord_stub = types.ModuleType("discord")
        _discord_ui_stub = types.ModuleType("discord.ui")
        _discord_ui_stub.View = object
        _discord_ui_stub.Button = object
        _discord_stub.ui = _discord_ui_stub
        _discord_stub.ButtonStyle = types.SimpleNamespace(
            primary=1, secondary=2, success=3, danger=4
        )
        _discord_stub.Interaction = object
        _discord_stub.Embed = object
        monkeypatch.setitem(sys.modules, "discord", _discord_stub)
        monkeypatch.setitem(sys.modules, "discord.ui", _discord_ui_stub)

    from adventure import AdventureEngine
    return AdventureEngine(fresh_player)


@pytest.fixture
def story_quest_manager(fresh_player):
    """StoryQuestManager 인스턴스.

    Returns:
        fresh_player와 연결된 StoryQuestManager 객체
    """
    from story_quest import StoryQuestManager
    return StoryQuestManager(fresh_player)


@pytest.fixture
def mock_user():
    return MockUser()


@pytest.fixture
def mock_channel():
    return MockChannel()


@pytest.fixture
def mock_ctx():
    return MockContext()


@pytest.fixture
def mock_interaction():
    return MockInteraction()


@pytest.fixture
def fishing_engine(fresh_player, monkeypatch):
    """FishingEngine 인스턴스.

    discord가 설치되지 않은 환경에서는 monkeypatch로 sys.modules에 stub을
    일시 등록하고 테스트 후 자동 복원합니다.

    Returns:
        fresh_player와 연결된 FishingEngine 객체
    """
    import sys
    import types

    try:
        import discord  # noqa: F401
    except ImportError:
        _discord_stub = types.ModuleType("discord")
        _discord_ui_stub = types.ModuleType("discord.ui")
        _discord_ui_stub.View = object
        _discord_ui_stub.Button = object
        _discord_stub.ui = _discord_ui_stub
        _discord_stub.ButtonStyle = types.SimpleNamespace(
            primary=1, secondary=2, success=3, danger=4
        )
        _discord_stub.Interaction = object
        _discord_stub.Embed = object
        _discord_stub.File = object
        monkeypatch.setitem(sys.modules, "discord", _discord_stub)
        monkeypatch.setitem(sys.modules, "discord.ui", _discord_ui_stub)

    from fishing import FishingEngine
    return FishingEngine(fresh_player)


@pytest.fixture
def gathering_engine(fresh_player, monkeypatch):
    """GatheringEngine 인스턴스.

    discord가 설치되지 않은 환경에서는 monkeypatch로 sys.modules에 stub을
    일시 등록하고 테스트 후 자동 복원합니다.

    Returns:
        fresh_player와 연결된 GatheringEngine 객체
    """
    import sys
    import types

    try:
        import discord  # noqa: F401
    except ImportError:
        _discord_stub = types.ModuleType("discord")
        _discord_ui_stub = types.ModuleType("discord.ui")
        _discord_ui_stub.View = object
        _discord_ui_stub.Button = object
        _discord_stub.ui = _discord_ui_stub
        _discord_stub.ButtonStyle = types.SimpleNamespace(
            primary=1, secondary=2, success=3, danger=4
        )
        _discord_stub.Interaction = object
        _discord_stub.Embed = object
        _discord_stub.File = object
        monkeypatch.setitem(sys.modules, "discord", _discord_stub)
        monkeypatch.setitem(sys.modules, "discord.ui", _discord_ui_stub)

    from gathering import GatheringEngine
    return GatheringEngine(fresh_player)


@pytest.fixture(autouse=True)
def reset_singletons():
    """각 테스트마다 싱글톤 인스턴스 리셋.

    Config 등의 싱글톤 객체가 테스트 간 영향을 주지 않도록 합니다.
    """
    from utils.config import Config

    # Config 싱글톤 리셋
    Config._instance = None

    yield

    # 테스트 후 정리
    Config._instance = None
