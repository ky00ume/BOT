# utils/discord_helpers.py
"""Discord 전송 헬퍼 — 모든 Cog에서 공유"""

import discord
from bg3_renderer import get_renderer


async def send_image(ctx, buf, filename: str = "ui.png"):
    buf.seek(0)
    await ctx.send(file=discord.File(fp=buf, filename=filename))


async def send_image_with_text(ctx, buf, text: str = None, filename: str = "ui.png"):
    buf.seek(0)
    await ctx.send(content=text, file=discord.File(fp=buf, filename=filename))


async def send_msg_card(ctx, title, message, system_key="system", grade="Normal"):
    buf = get_renderer().render_result_card(
        title=title,
        rows=[{"label": "내용", "value": str(message)}],
        system_key=system_key,
        grade=grade,
    )
    await send_image(ctx, buf, 'message.png')


async def send_encounter(ctx, enc_msg: str, bot_ctx):
    from special_npc import render_encounter_image
    from ui.special_npc_ui import SpecialNPCView
    npc_name = bot_ctx.encounter_manager.get_active_encounter()
    buf = render_encounter_image(npc_name, enc_msg)
    if buf:
        buf.seek(0)
        view = SpecialNPCView(
            npc_name, bot_ctx.player,
            getattr(bot_ctx.player, "_affinity_manager", None),
            None,
            bot_ctx.encounter_manager,
        )
        await ctx.send(file=discord.File(fp=buf, filename="encounter.png"), view=view)
    else:
        await ctx.send(enc_msg)


async def check_channel(ctx, allowed_channel_id: int) -> bool:
    return ctx.channel.id == allowed_channel_id
