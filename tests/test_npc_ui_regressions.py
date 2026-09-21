import pytest
from unittest.mock import patch

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
