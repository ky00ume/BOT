import discord
from ui_theme import C, EMBED_COLOR


def make_intro_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏘 비전 타운에 오신 걸 환영합니다!",
        description=(
            "저는 **비전 타운**을 안내하는 봇임미댜~\n\n"
            "비전 타운은 모험, 전투, 요리, 낚시, 제련 등 다양한 활동을 즐길 수 있는 판타지 마을임미댜!\n\n"
            "아래 명령어로 다양한 콘텐츠를 즐겨보셰요 ✨"
        ),
        color=EMBED_COLOR["npc"],
    )
    embed.add_field(
        name="📌 기본 안내",
        value=(
            "• `/상태창` — 캐릭터 상태 확인\n"
            "• `/장비` — 장비창 확인\n"
            "• `/도움말` — 전체 명령어 목록\n"
            "• `/공지` — 이 공지를 다시 보기"
        ),
        inline=False,
    )
    embed.set_footer(text="✦ 비전 타운 봇 — 즐거운 모험 되셰요! ✦")
    return embed


def make_npc_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧑‍🤝‍🧑 마을 NPC 안내",
        description="비전 타운에는 다양한 NPC들이 살고 있슴미댜!",
        color=EMBED_COLOR["npc"],
    )
    npcs = [
        ("크람",   "대장장이", "무기·방어구 상점"),
        ("레이나", "약초상",   "소모품·도구 상점"),
        ("곤트",   "상인",     "가방 상점"),
        ("엘리",   "마법사",   "마법 연구소"),
        ("그레고", "경비병",   "마을 성문"),
        ("마리",   "요리사",   "마을 식당"),
        ("피터",   "낚시꾼",   "마을 강가"),
        ("루카스", "음악가",   "마을 광장"),
        ("나디아", "길드 마스터", "모험가 길드"),
    ]
    npc_text = "\n".join(f"• **{name}** [{role}] — {loc}" for name, role, loc in npcs)
    embed.add_field(name="NPC 목록", value=npc_text, inline=False)
    embed.add_field(
        name="💬 대화 방법",
        value="`/대화 [NPC이름]` — NPC와 대화\n`/알바 [NPC이름]` — NPC 알바 진행",
        inline=False,
    )
    embed.set_footer(text="✦ NPC와 친해지면 특별한 혜택이 있을지도~ ✦")
    return embed


def make_commands_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📖 전체 명령어 목록",
        color=EMBED_COLOR["help"],
    )
    embed.add_field(
        name="👤 캐릭터",
        value=(
            "`/상태창` `/장비` `/스왑`\n"
            "`/치료` `/먹기 [ID]`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🏘 마을",
        value=(
            "`/마을` `/대화 [NPC]`\n"
            "`/알바 [NPC]` `/공지`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🛒 상점",
        value=(
            "`/구매목록 [NPC]`\n"
            "`/구매 [NPC] [ID]`\n"
            "`/판매목록` `/판매 [ID]`"
        ),
        inline=True,
    )
    embed.add_field(
        name="⚔ 전투",
        value=(
            "`/사냥터` `/사냥 [구역]`\n"
            "`/공격 [스킬]` `/도주`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎣 낚시",
        value="`/낚시` `/낚시목록`",
        inline=True,
    )
    embed.add_field(
        name="🍳 요리 & ⚒ 제련",
        value=(
            "`/요리 [ID]` `/레시피`\n"
            "`/제련 [ID]` `/제련목록`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎲 기타",
        value="`/주사위 [면수]` `/저장` `/도움말`",
        inline=True,
    )
    embed.set_footer(text="✦ 비전 타운 봇 — 모든 명령어 ✦")
    return embed


async def send_town_notice(channel):
    """채널에 마을 공지 3장을 전송합니다."""
    await channel.send(embed=make_intro_embed())
    await channel.send(embed=make_npc_embed())
    await channel.send(embed=make_commands_embed())
