import discord
from ui_theme import C, EMBED_COLOR


def make_intro_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏘 비전 타운에 오신 걸 환영합니다!",
        description=(
            "저는 **비전 타운**을 안내하는 봇임미댜~\n\n"
            "비전 타운은 모험, 전투, 요리, 낚시, 채집, 채광, 제련 등 "
            "다양한 활동을 즐길 수 있는 판타지 마을임미댜!\n\n"
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
    embed.add_field(
        name="🏘 마을 레벨 시스템",
        value=(
            "마을 기여도가 쌓이면 마을이 레벨업됨미댜!\n"
            "• Lv1: 기본 마을\n"
            "• Lv2 (500pt): 알바 보너스 +10%, 드랍 +5%\n"
            "• Lv3 (1200pt): 알바 +15%, 드랍 +8%, 요리품질 +1\n"
            "• Lv4 (2500pt): 알바 +20%, 드랍 +12%\n"
            "• Lv5 (4500pt): 알바 +30%, 드랍 +20%, 요리품질 +2\n"
            "기여도: 알바(+5), 제련(+4), 전투(+3), 요리(+2), 채집(+2), 낚시(+1)"
        ),
        inline=False,
    )
    embed.set_footer(text="✦ 비전 타운 봇 — 즐거운 모험 되셰요! ✦")
    return embed


def make_npc_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧑‍🤝‍🧑 마을 NPC & 알바 안내",
        description="비전 타운에는 다양한 NPC들이 살고 있슴미댜!",
        color=EMBED_COLOR["npc"],
    )
    npcs = [
        ("다몬",       "대장장이",     "무기·방어구 상점 / 단조 보조 알바"),
        ("오멜룸",     "약초상",       "소모품·도구 상점 / 약초 채집 알바"),
        ("몰",         "상인",         "가방 상점 / 짐 운반 알바"),
        ("아라벨라",   "마법사",       "마법 연구소 / 실험 보조 알바"),
        ("제블로어",   "경비대장",     "마을 성문 / 순찰 보조 알바"),
        ("브룩샤",     "요리사",       "마을 식당 / 주방 보조 알바"),
        ("실렌",       "낚시꾼",       "강가 / 낚시 보조 알바"),
        ("알피라",     "음유시인",     "마을 광장 / 공연 보조 알바"),
        ("엘레라신",   "길드 마스터",  "모험가 길드 / 길드 업무 알바"),
        ("게일의 환영","마법학교 교수","마법학교 / 수업 보조 알바"),
        ("카엘릭",     "교관",         "훈련소 / 훈련 보조 알바"),
    ]
    npc_text = "\n".join(f"• **{name}** [{role}] — {desc}" for name, role, desc in npcs)
    embed.add_field(name="NPC 목록", value=npc_text, inline=False)
    embed.add_field(
        name="💬 대화 & 알바",
        value=(
            "`/대화 [NPC이름]` — NPC와 대화\n"
            "`/알바 [NPC이름]` — NPC 알바 진행 (기력 소모, 골드·EXP 획득)"
        ),
        inline=False,
    )
    embed.set_footer(text="✦ NPC와 친해지면 특별한 혜택이 있을지도~ ✦")
    return embed


def make_life_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌿 생활 시스템 안내",
        description="비전 타운의 다양한 생활 콘텐츠임미댜!",
        color=0x4a9e5c,
    )
    embed.add_field(
        name="🎣 낚시",
        value=(
            "`/낚시` — 타이밍 게임 (버튼 클릭)\n"
            "`/낚시터정보` — 낚시터·물고기 정보\n"
            "날씨에 따라 확률 변화! 비 오면 확률 +20%"
        ),
        inline=True,
    )
    embed.add_field(
        name="🌿 채집 & ⛏ 채광",
        value=(
            "`/채집` — 계절별 허브·버섯 채집 (기력 15)\n"
            "`/채광` — 힘(STR)에 따라 광석 채광 (기력 20)"
        ),
        inline=True,
    )
    embed.add_field(
        name="🍳 요리",
        value=(
            "`/요리 [레시피ID]` — 요리 (도구 필요)\n"
            "`/레시피` — 레시피 목록\n"
            "도구: 냄비·팬·절구·반죽틀·발효통"
        ),
        inline=True,
    )
    embed.add_field(
        name="⚒ 제련",
        value=(
            "`/제련 [광석ID]` — 광석 → 주괴\n"
            "`/제련목록` — 제련 목록"
        ),
        inline=True,
    )
    embed.add_field(
        name="⚗ 포션 제조",
        value=(
            "`/제조 [레시피ID]` — 포션 제조\n"
            "절구 도구 필요, DEX 기반 성공률"
        ),
        inline=True,
    )
    embed.add_field(
        name="☀️ 날씨",
        value=(
            "`/날씨` — 현재 날씨 확인\n"
            "맑음·흐림·비·폭풍·눈·안개\n"
            "6시간마다 변화"
        ),
        inline=True,
    )
    embed.set_footer(text="🌿 생활 스킬을 올려서 더 좋은 결과를 얻으셰요!")
    return embed


def make_commands_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📖 전체 명령어 목록",
        color=EMBED_COLOR["help"],
    )
    embed.add_field(
        name="👤 캐릭터 & 상태",
        value="`/상태창` `/장비` `/스왑`\n`/치료` `/먹기 [ID]`",
        inline=True,
    )
    embed.add_field(
        name="🏘 마을 & NPC",
        value=(
            "`/마을` `/대화 [NPC]`\n"
            "`/알바 [NPC]` `/공지`\n"
            "`/마을상태`"
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
        value="`/사냥터` `/사냥 [구역]`\n`/공격 [스킬]` `/도주`",
        inline=True,
    )
    embed.add_field(
        name="🎣 낚시 & 생활",
        value=(
            "`/낚시` `/낚시터정보`\n"
            "`/채집` `/채광`\n"
            "`/요리 [ID]` `/레시피`\n"
            "`/제련 [ID]` `/제련목록`\n"
            "`/제조 [ID]` `/날씨`"
        ),
        inline=True,
    )
    embed.add_field(
        name="📋 퀘스트 & 소셜",
        value=(
            "`/퀘스트` `/퀘스트수락 [ID]`\n"
            "`/퀘스트완료 [ID]`\n"
            "`/뽑기` `/뽑기10`\n"
            "`/작곡` `/연주 [ID]`\n"
            "`/게시판` `/명예의전당`\n"
            "`/낚시순위`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎲 기타",
        value="`/주사위 [면수]` `/저장`\n`/공지` `/도움말`",
        inline=True,
    )
    embed.set_footer(text="✦ 비전 타운 봇 — 모든 명령어 ✦")
    return embed


async def send_town_notice(channel):
    """채널에 마을 공지 4장을 전송합니다."""
    await channel.send(embed=make_intro_embed())
    await channel.send(embed=make_npc_embed())
    await channel.send(embed=make_life_embed())
    await channel.send(embed=make_commands_embed())
