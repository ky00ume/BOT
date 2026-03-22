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
            "• `/장착 [아이템이름]` — 장비 장착\n"
            "• `/벗기 [슬롯]` — 장비 탈착\n"
            "• `/비전타운` — 마을 이동·NPC 대화·탐험 (임베드+버튼 UI)\n"
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
            "`/비전타운` → NPC 버튼으로 대화 (버튼+임베드 UI)\n"
            "~~`/대화 [NPC이름]`~~ — 삭제됨 → `/비전타운` 사용\n"
            "`/대화` (단독) — NPC 목록 확인은 유지\n"
            "`/알바 [NPC이름]` — NPC 알바 진행 (기력 소모, 골드·EXP 획득)\n"
            "⚠️ 호감도 일일 한도 달성 시 대화는 계속 가능 (대화 차단 없음)"
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
            "`/낚시터정보` `/낚시도감` — 낚시터·물고기 정보\n"
            "`/낚시순위` — 주간 낚시 대회 순위\n"
            "날씨에 따라 확률 변화! 비 오면 확률 +20%"
        ),
        inline=True,
    )
    embed.add_field(
        name="🌿 채집 & ⛏ 채광 & 🪓 벌목",
        value=(
            "`/채집` — 계절별 허브·버섯 채집 (기력 15)\n"
            "`/채광` — 힘(STR)에 따라 광석 채광 (기력 20)\n"
            "`/벌목` — 나무 획득 (기력 18)\n"
            "`/채집도감` — 채집 가능 아이템 목록"
        ),
        inline=True,
    )
    embed.add_field(
        name="🍳 요리 & ⚒ 제련",
        value=(
            "`/스킬` → **생활 스킬** 드롭다운 → **요리** 선택\n"
            "→ 레시피 선택 → 재료 확인 → **[제작 실행]**\n"
            "제련도 동일: `/스킬` → **제련** 선택\n"
            "도구: 냄비·팬·절구·반죽틀·발효통"
        ),
        inline=True,
    )
    embed.add_field(
        name="⚗ 포션 제조 & 🔨 장비 제작",
        value=(
            "`/스킬` → **생활 스킬** 드롭다운\n"
            "→ **연금술** (포션) 또는 **제작** (장비) 선택\n"
            "→ 레시피 선택 → **[제작 실행]**"
        ),
        inline=True,
    )
    embed.add_field(
        name="💧 물뜨기 & 🛡 장비",
        value=(
            "`/물뜨기 [수량]` — 빈 병으로 물 뜨기\n"
            "`/장착 [아이템이름]` — 장비 장착\n"
            "`/벗기 [슬롯]` — 장비 탈착\n"
            "`/스왑` — 주·보조 무기 교환"
        ),
        inline=True,
    )
    embed.add_field(
        name="☀️ 날씨 & 🗺 이동",
        value=(
            "`/날씨` — 현재 날씨 확인\n"
            "맑음·흐림·비·폭풍·눈·안개 / 6시간마다 변화\n"
            "`/이동 [장소]` — 맵 이동 (3분 쿨타임)"
        ),
        inline=True,
    )
    embed.add_field(
        name="📖 수련 & 스킬",
        value=(
            "`/수련 [스탯]` — 훈련소 스탯 수련 (`/훈련소` `/학교`)\n"
            "`/스킬` — 스킬 창 (드롭다운+버튼 UI)\n"
            "  └ 카테고리 선택 → 스킬 버튼 → 상세 정보 조회\n"
            "`/업적` — 업적 목록\n"
            "`/타이틀 [이름]` — 보유 타이틀 목록/장착"
        ),
        inline=True,
    )
    embed.add_field(
        name="📦 보관함",
        value=(
            "`/보관함` — 보관함 보기\n"
            "`/보관함넣기 [아이템] [수량]` — 넣기\n"
            "`/보관함꺼내기 [아이템] [수량]` — 꺼내기\n"
            "`/보관함업그레이드` — 용량 확장"
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
        value=(
            "`/상태창` `/장비` `/스왑`\n"
            "`/장착 [아이템]` `/벗기 [슬롯]`\n"
            "`/치료` `/먹기 [ID]` `/버리기 [ID]`\n"
            "`/타이틀` `/업적` `/도감`\n"
            "`/일기` `/아이템목록`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🏘 마을 & NPC",
        value=(
            "`/비전타운` — 마을·월드맵·NPC 통합 UI\n"
            "`/대화` — NPC 목록 확인\n"
            "`/알바 [NPC]` `/공지`\n"
            "`/마을상태` `/이동 [장소]`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🛒 상점 & 보관함",
        value=(
            "NPC 대화 창 **[구매]** 버튼 — NPC 상점\n"
            "인벤토리 **[판매]** 버튼 — 아이템 판매\n"
            "`/보관함` `/보관함넣기`\n"
            "`/보관함꺼내기` `/보관함업그레이드`"
        ),
        inline=True,
    )
    embed.add_field(
        name="⚔ 전투 & 스킬",
        value=(
            "`/사냥터` `/사냥 [구역]`\n"
            "`/공격 [스킬]` `/도주`\n"
            "`/스킬` — 스킬 창 (드롭다운+버튼 UI)\n"
            "`/수련 [스탯]`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎣 낚시 & 생활",
        value=(
            "`/낚시` `/낚시터정보` `/낚시도감`\n"
            "`/채집` `/채광` `/벌목` `/채집도감`\n"
            "`/스킬` → 생활 스킬 → 요리/제련/포션/제작\n"
            "`/물뜨기` `/날씨`"
        ),
        inline=True,
    )
    embed.add_field(
        name="📋 퀘스트 & 소셜",
        value=(
            "`/퀘스트` — 퀘스트 목록 (채집·처치·전달형)\n"
            "`/퀘스트수락 [ID]` `/퀘스트완료 [ID]`\n"
            "`/뽑기` `/뽑기10`\n"
            "`/작곡` `/연주 [ID]`\n"
            "`/게시판` `/명예의전당`\n"
            "`/낚시순위`"
        ),
        inline=True,
    )
    embed.add_field(
        name="📖 스토리",
        value=(
            "`/스토리` `/스토리퀘스트`\n"
            "`/스토리탐색` `/스토리수집`\n"
            "`/스토리힌트` `/그림자`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎲 기타",
        value=(
            "`/주사위 [면수]` `/저장`\n"
            "`/공지` `/도움말`"
        ),
        inline=True,
    )
    embed.set_footer(text="✦ 비전 타운 봇 — 모든 명령어 ✦")
    return embed


def make_patchnote_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛠️ 패치노트 — v0.5.1 (2026-03-22)",
        description="비전 타운 봇 대규모 업데이트 내용임미댜!",
        color=0xf0a500,
    )
    embed.add_field(
        name="🏙️ 마을·탐험 시스템 전면 개편",
        value=(
            "• `/마을` 삭제 → **`/비전타운`** 으로 교체\n"
            "• 마을·월드맵 임베드+버튼 UI 통합\n"
            "• 사냥터·채집터·낚시터 버튼 이동 지원\n"
            "• 실렌 낚시터에서 `[실렌]` 버튼으로 NPC 대화 연결"
        ),
        inline=False,
    )
    embed.add_field(
        name="💬 NPC 대화 시스템 개편",
        value=(
            "• `/대화 [NPC이름]` 형식 **삭제** → `/비전타운` 버튼 사용\n"
            "• NPC 대화 전면 임베드+버튼 UI로 교체\n"
            "• 호감도 하루 한도 달성 시 대화 차단 없음 → 임베드 경고 표시로 변경\n"
            "• 모든 NPC 키워드 대사 **5가지 바리에이션** 적용 (랜덤 선택)"
        ),
        inline=False,
    )
    embed.add_field(
        name="📋 퀘스트 시스템 전면 재설계",
        value=(
            "• 퀘스트 타입 3종: **채집형 / 처치형 / 전달형**\n"
            "• 36개 퀘스트 추가 (NPC 4인 × 타입 3 × 난이도 3)\n"
            "• 전달형 퀘스트 아이템(`sq_` 접두사) — 버리기·판매·장착 불가\n"
            "• 퀘스트 UI → 셀렉트 메뉴+버튼 기반으로 개편"
        ),
        inline=False,
    )
    embed.add_field(
        name="🛒 상점 배분 변경",
        value=(
            "• **오멜룸** 상점: 식료품 제거 → 소비품 + 도구\n"
            "• **브룩샤** 상점 신설: 식료품 + 기초 요리 4종\n"
            "• 상점 진입: NPC 대화 창 **[구매]** 버튼\n"
            "• 판매: 인벤토리 **[판매]** 버튼"
        ),
        inline=True,
    )
    embed.add_field(
        name="🪓 벌목 시스템 업데이트",
        value=(
            "• 목재 7등급 아이템 추가\n"
            "  잡목 가지(F) ~ 전설의 고목(1)\n"
            "• 등급별 기력 소모 및 경험치 적용"
        ),
        inline=True,
    )
    embed.add_field(
        name="🗣️ /쓰담·/훈육 대사 개편",
        value=(
            "• 캐릭터 ID별 맞춤 대사로 분기\n"
            "  (HYNESS 10종 / MAJESTY 10종 / DRIDER 5종)"
        ),
        inline=True,
    )
    embed.add_field(
        name="💼 알바 시스템 개편 (난이도 3단계)",
        value=(
            "• NPC당 9개 알바 풀 (쉬움/보통/어려움 × 3)\n"
            "• 알바 유형: **채집형 / 처치형 / 전달형**\n"
            "• 전달형: 퀘스트 아이템 수령 → 대상 NPC에 전달\n"
            "• 스킬 경험치 보상 추가"
        ),
        inline=False,
    )
    embed.add_field(
        name="📚 /스킬 창 스킬 상세 조회",
        value=(
            "• 카테고리 선택 후 **[ℹ️ 스킬이름]** 버튼 표시\n"
            "• 버튼 클릭 시 스킬 상세 임베드 (설명·랭크 수치)\n"
            "• 현재 랭크 배지 + 다음 랭크까지 게이지 표시"
        ),
        inline=True,
    )
    embed.add_field(
        name="🔧 기타 수정",
        value=(
            "• 채팅 자연어 반응 완전 제거\n"
            "• 인벤토리 슬롯에서 가방 이름 미표시\n"
            "• `/공지` 명령어 안내 갱신 (구버전 명령어 제거)\n"
            "• [핫픽스] `/저장` 오류 수정 — `current_title` 컬럼 누락 버그 해결"
        ),
        inline=False,
    )
    embed.set_footer(text="✦ 비전 타운 봇 v0.5.1 패치노트 ✦")
    return embed


async def send_town_notice(channel):
    """채널에 마을 공지 5장을 전송합니다."""
    await channel.send(embed=make_intro_embed())
    await channel.send(embed=make_npc_embed())
    await channel.send(embed=make_life_embed())
    await channel.send(embed=make_commands_embed())
    await channel.send(embed=make_patchnote_embed())
