"""tests/test_npcs.py — VillageNPC / ConversationManager 단위 테스트"""
import sys
import types
import warnings
import pytest
import asyncio


# ── helpers ──────────────────────────────────────────────────────────────────

def _ensure_discord_stub(monkeypatch):
    """discord가 없는 환경에서 stub을 sys.modules에 등록."""
    try:
        import discord  # noqa: F401
    except ImportError:
        _discord_stub = types.ModuleType("discord")
        _discord_ui_stub = types.ModuleType("discord.ui")

        class _StubView:
            def __init__(self, timeout=None, **kw):
                self._children = []

            def add_item(self, item):
                self._children.append(item)

            def clear_items(self):
                self._children.clear()

            async def wait(self):
                pass

        class _StubButton:
            def __init__(self, *a, **kw):
                pass

            @property
            def callback(self):
                return None

            @callback.setter
            def callback(self, fn):
                pass

        _discord_ui_stub.View = _StubView
        _discord_ui_stub.Button = _StubButton
        _discord_stub.ui = _discord_ui_stub
        _discord_stub.ButtonStyle = types.SimpleNamespace(
            primary=1, secondary=2, success=3, danger=4
        )
        _discord_stub.Interaction = object
        _discord_stub.File = lambda buf, filename=None: ("file", buf, filename)

        class _Embed:
            def __init__(self, title="", description="", color=0):
                self.title = title
                self.description = description
                self.color = color

            def set_image(self, url=None):
                pass

        _discord_stub.Embed = _Embed
        monkeypatch.setitem(sys.modules, "discord", _discord_stub)
        monkeypatch.setitem(sys.modules, "discord.ui", _discord_ui_stub)


def _make_pending_deliver_flag(
    target_npc: str = "다몬",
    deliver_item: str = "test_parcel",
    *,
    reward_gold: int = 100,
    reward_exp: float = 10.0,
    reward_skill_exp: dict | None = None,
    reward_item: str | None = None,
):
    return {
        "npc_name": "아라벨라",
        "job_name": "배달 테스트",
        "target_npc": target_npc,
        "deliver_item": deliver_item,
        "deliver_item_name": "테스트 소포",
        "reward_gold": reward_gold,
        "reward_exp": reward_exp,
        "reward_skill_exp": reward_skill_exp or {},
        "reward_item": reward_item,
    }


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def player_with_parcel(fresh_player):
    """배달 아이템을 보유한 플레이어."""
    fresh_player.inventory["test_parcel"] = 1
    return fresh_player


@pytest.fixture
def conv_manager(monkeypatch, player_with_parcel):
    """ConversationManager 픽스처 (외부 의존성 모두 mock)."""
    _ensure_discord_stub(monkeypatch)

    # stub: fishing_card
    _fc_stub = types.ModuleType("fishing_card")

    def _gen_job_card(*a, **kw):
        import io
        return io.BytesIO(b"fake_image")

    _fc_stub.generate_job_card = _gen_job_card
    monkeypatch.setitem(sys.modules, "fishing_card", _fc_stub)

    # stub: save_manager
    _sm_stub = types.ModuleType("save_manager")
    _sm_inner = types.SimpleNamespace(save=lambda p: None)
    _sm_stub.save_manager = _sm_inner
    monkeypatch.setitem(sys.modules, "save_manager", _sm_stub)

    # stub: village
    _village_stub = types.ModuleType("village")
    _village_stub.village_manager = types.SimpleNamespace(
        add_contribution=lambda amt, src: None
    )
    monkeypatch.setitem(sys.modules, "village", _village_stub)

    # stub: app_context (quest deliver_to_npc → 빈 문자열)
    _app_ctx_stub = types.ModuleType("app_context")
    _qm = types.SimpleNamespace(deliver_to_npc=lambda npc: "")
    _app_ctx_stub.get_quest_manager = lambda: _qm
    monkeypatch.setitem(sys.modules, "app_context", _app_ctx_stub)

    # stub: bg3_renderer (ConversationManager._render_greeting_image 호환)
    import io as _io
    _renderer_stub = types.ModuleType("bg3_renderer")

    class _FakeRenderer:
        def render_npc_greeting(self, *a, **kw):
            return _io.BytesIO(b"img")

        def render_npc_dialogue(self, *a, **kw):
            return _io.BytesIO(b"img")

    _renderer_stub.get_renderer = lambda: _FakeRenderer()
    _renderer_stub.C = types.SimpleNamespace(
        RED="", GREEN="", GOLD="", WHITE="", DARK="", R=""
    )
    monkeypatch.setitem(sys.modules, "bg3_renderer", _renderer_stub)

    from npc_conversation import ConversationManager
    return ConversationManager(player_with_parcel)


# ── TestDeliverJobCompletion ──────────────────────────────────────────────────

class TestDeliverJobCompletion:
    """pending_deliver 플래그 처리 통합 테스트."""

    @pytest.mark.asyncio
    async def test_deliver_complete_removes_item_and_pays_reward(
        self, conv_manager, player_with_parcel, mock_ctx
    ):
        """아이템 제거, 골드/경험치 지급, 플래그 삭제 확인."""
        player = player_with_parcel
        flag_key = "pending_deliver:test_parcel"
        player._flags = {flag_key: _make_pending_deliver_flag(reward_gold=100, reward_exp=10.0)}

        gold_before = player.gold
        exp_before = getattr(player, "exp", 0.0)

        await conv_manager.send_conversation(mock_ctx, "다몬")

        assert player.inventory.get("test_parcel", 0) == 0, "아이템이 제거되어야 함"
        assert player.gold == gold_before + 100, "골드 보상이 지급되어야 함"
        assert getattr(player, "exp", 0.0) == exp_before + 10.0, "경험치가 지급되어야 함"
        assert flag_key not in player._flags, "완료 후 플래그 삭제되어야 함"
        assert len(mock_ctx._sent) > 0, "메시지가 전송되어야 함"

    @pytest.mark.asyncio
    async def test_deliver_complete_wrong_npc_does_nothing(
        self, conv_manager, player_with_parcel, mock_ctx
    ):
        """다른 NPC에게 대화 시 pending_deliver 플래그 유지."""
        player = player_with_parcel
        flag_key = "pending_deliver:test_parcel"
        player._flags = {flag_key: _make_pending_deliver_flag(target_npc="다몬")}

        gold_before = player.gold

        # target_npc가 아닌 "몰"에게 대화
        await conv_manager.send_conversation(mock_ctx, "몰")

        assert flag_key in player._flags, "틀린 NPC에게는 플래그가 유지되어야 함"
        assert player.gold == gold_before, "보상이 지급되면 안 됨"

    @pytest.mark.asyncio
    async def test_deliver_complete_missing_item_skips_reward(
        self, conv_manager, player_with_parcel, mock_ctx
    ):
        """인벤토리에 deliver_item이 없으면 보상 미지급."""
        player = player_with_parcel
        # 아이템 제거
        del player.inventory["test_parcel"]
        flag_key = "pending_deliver:test_parcel"
        player._flags = {flag_key: _make_pending_deliver_flag(reward_gold=200)}

        gold_before = player.gold
        await conv_manager.send_conversation(mock_ctx, "다몬")

        assert player.gold == gold_before, "아이템 없으면 보상 미지급"

    @pytest.mark.asyncio
    async def test_deliver_complete_skill_exp_rewarded(
        self, conv_manager, player_with_parcel, mock_ctx, monkeypatch
    ):
        """reward_skill_exp 있으면 train_skill()이 호출되어야 함."""
        player = player_with_parcel
        flag_key = "pending_deliver:test_parcel"
        player._flags = {
            flag_key: _make_pending_deliver_flag(
                reward_skill_exp={"fishing": 5.0}
            )
        }

        called = {}

        def _mock_train(sid, amt):
            called[sid] = called.get(sid, 0.0) + amt

        monkeypatch.setattr(player, "train_skill", _mock_train)

        await conv_manager.send_conversation(mock_ctx, "다몬")

        assert "fishing" in called, "train_skill('fishing', ...) 이 호출되어야 함"
        assert called["fishing"] == 5.0

    @pytest.mark.asyncio
    async def test_deliver_complete_village_contribution(
        self, conv_manager, player_with_parcel, mock_ctx, monkeypatch
    ):
        """배달 완료 시 village_manager.add_contribution(5, 'job') 호출 확인."""
        player = player_with_parcel
        flag_key = "pending_deliver:test_parcel"
        player._flags = {flag_key: _make_pending_deliver_flag()}

        contrib_calls = []

        import types as _types
        _village_stub = _types.ModuleType("village")
        _village_stub.village_manager = _types.SimpleNamespace(
            add_contribution=lambda amt, src: contrib_calls.append((amt, src))
        )
        monkeypatch.setitem(sys.modules, "village", _village_stub)

        await conv_manager.send_conversation(mock_ctx, "다몬")

        assert any(
            amt == 5 and src == "job" for amt, src in contrib_calls
        ), "village contribution (5, 'job')이 호출되어야 함"


# ── TestStartJobDeprecated ────────────────────────────────────────────────────

class TestStartJobDeprecated:
    """start_job() 동기 메서드 deprecated 처리 테스트."""

    def test_start_job_emits_deprecation_warning(self, fresh_player):
        """start_job() 호출 시 DeprecationWarning 발생 확인."""
        from npcs import VillageNPC
        npc = VillageNPC(fresh_player)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            npc.start_job("다몬")  # NPC가 없어도 Warning은 발생해야 함

        dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(dep_warnings) == 1, "DeprecationWarning이 정확히 1번 발생해야 함"
        assert "start_job_async" in str(dep_warnings[0].message)
