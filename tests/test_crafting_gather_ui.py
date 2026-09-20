import discord
import pytest

from ui.skill_ui import SkillMainView


@pytest.mark.asyncio
async def test_skill_main_view_is_importable_and_is_a_discord_view(fresh_player):
    view = SkillMainView(fresh_player)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_recipe_gather_callback_exists(fresh_player):
    view = SkillMainView(fresh_player)
    callback = view._make_recipe_gather_callback("crafting", "dummy", "iron_ore", 5)
    assert callable(callback)
