import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from npc_conversation import NPCConversationView

class Player:
    keywords = ["군락", "소문"]
class Affinity:
    def check_talk_limit(self, npc): return (True, None)
    def record_talk(self, npc): pass
    def add_affinity(self, npc, points): return (0, False, "낯선이")
    def get_affinity_level(self, npc): return 0
    def get_level_name(self, npc): return "낯선이"
class Response:
    def __init__(self): self.edits=[]
    async def edit_message(self, **kwargs): self.edits.append(kwargs)
    async def send_message(self, *args, **kwargs): pass
class Interaction:
    def __init__(self): self.response=Response()

@pytest.mark.asyncio
async def test_keyword_buttons_replace_dialogue_attachment():
    view=NPCConversationView("군주 스포", Player(), Affinity())
    inter=Interaction()
    with patch("npc_conversation._render_keyword_response_image") as render, patch("npc_conversation.discord.File") as file_cls:
        from io import BytesIO
        render.return_value=BytesIO(b"x")
        file_cls.side_effect=lambda *a, **k: object()
        await view._handle_keyword(inter, "군락")
        await view._handle_keyword(inter, "소문")
    assert len(inter.response.edits)==2
    assert all(edit["attachments"] for edit in inter.response.edits)
    assert all(edit["embed"] is None for edit in inter.response.edits)
    assert render.call_args_list[0].args[1] == "군락"
    assert render.call_args_list[1].args[1] == "소문"
    assert render.call_args_list[0].args[2] != render.call_args_list[1].args[2]

def test_spaw_dialogue_has_distinct_colony_and_rumor_text():
    from npc_dialogue_db import NPC_KEYWORDS
    colony=NPC_KEYWORDS["군주 스포"]["군락"]["default"][0]
    rumor=NPC_KEYWORDS["군주 스포"]["소문"]["default"][0]
    assert colony != rumor
    assert chr(34) not in colony and chr(34) not in rumor

def test_colony_places_expose_non_npc_interactions():
    from ui.town_ui import ColonyPlaceView

    expected = {
        "마이코니드 군락 서쪽 입구": {"상인의 짐을 살핀다", "군락 바깥을 살핀다"},
        "마이코니드 군락 광명회 야영지": {"연구 장비를 살핀다", "표본 선반을 살핀다"},
        "마이코니드 군락 군주의 터": {"포자 군락을 느낀다", "의식 공간을 살핀다"},
        "마이코니드 군락 서쪽 통로": {"통로의 흔적을 살핀다", "바깥 기척을 듣는다"},
    }
    for location, labels in expected.items():
        actual = {label for label, _emoji, _observation in ColonyPlaceView.PLACE_ACTIONS[location]}
        assert labels <= actual


@pytest.mark.asyncio
async def test_colony_place_observation_edits_same_message():
    from ui.town_ui import ColonyPlaceView

    view = ColonyPlaceView.__new__(ColonyPlaceView)
    view.location = "마이코니드 군락 군주의 터"
    interaction = SimpleNamespace(
        response=SimpleNamespace(edit_message=AsyncMock())
    )
    callback = view._make_observation_callback("포자 군락을 느낀다", "기억의 잔향이 스쳐 간다.")

    await callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert kwargs["attachments"] == []
    assert kwargs["view"] is view
    assert kwargs["embed"].title == "군주의 터"
    assert kwargs["embed"].fields[0].name == "포자 군락을 느낀다"
    assert "기억의 잔향" in kwargs["embed"].fields[0].value

@pytest.mark.asyncio
async def test_tower_upper_floor_exposes_shared_living_space_and_hidden_nest():
    from ui.care_ui import TowerUpperFloorView

    class DummyCare:
        pass

    view = TowerUpperFloorView(SimpleNamespace(), DummyCare())
    labels = {item.label for item in view.children}
    assert {"책장 뒤 작은 틈", "마제스티의 자리", "카르니스의 기척", "승강기"} <= labels
    embed = view.make_embed()
    assert "마제스티와 카르니스" in embed.description
    assert "츄라이더의 방" not in embed.description
