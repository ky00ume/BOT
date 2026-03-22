"""
ui_theme.py — 비전 타운 봇 UI 테마 (BG3 스타일 적용)

하위호환 정책:
  - 모든 기존 함수 시그니처 100% 유지
  - ANSI 색상 코드 그대로 유지 (터미널/코드블록용)
  - EMBED_COLOR / GRADE_EMBED_COLOR → BG3 팔레트로 교체
  - FOOTERS → 시스템 메시지 항목만 중립 말투 교체
             (NPC 대사·스토리 텍스트는 각 전용 파일에서 관리)
  - SPIDER_ART → 원본 유지 (캐릭터 고유 표현)
"""

ESC = "\u001b"

class C:
    R     = f"{ESC}[0m"
    B     = f"{ESC}[1m"
    DARK  = f"{ESC}[30m"
    RED   = f"{ESC}[31m"
    GREEN = f"{ESC}[32m"
    GOLD  = f"{ESC}[33m"
    BLUE  = f"{ESC}[34m"
    PINK  = f"{ESC}[35m"
    CYAN  = f"{ESC}[36m"
    WHITE = f"{ESC}[37m"
    BG_DARK = f"{ESC}[40m"
    BG_RED  = f"{ESC}[41m"
    BG_GOLD = f"{ESC}[43m"
    BG_BLUE = f"{ESC}[44m"

# ── Embed 색상 (BG3 팔레트) ──────────────────────────────────────
EMBED_COLOR = {
    "status":     0x4A7EC2,
    "equipment":  0x7A5530,
    "battle":     0x8B1A28,
    "shop":       0xB8960E,
    "npc":        0x2E7A4A,
    "help":       0x5A3E8A,
    "save":       0x4A5060,
    "heal":       0x8A4A6A,
    "system":     0x2A2438,
    "rest":       0x4A4AAA,
    "fishing":    0x1A6878,
    "cooking":    0x8A4A18,
    "metallurgy": 0x4A6878,
    "craft":      0x3A5878,
    "quest":      0x8A5818,
    "gathering":  0x2A6A3A,
}

GRADE_EMBED_COLOR = {
    "Normal":    0x7A7A7A,
    "Rare":      0x3A7ACC,
    "Epic":      0x7A3ACC,
    "Legendary": 0xC87800,
    "Fail":      0xCC2820,
}


def bar(current, max_val, width=10, fill_c=C.RED, empty_c=C.DARK):
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    empty  = width - filled
    return f"{fill_c}{'█' * filled}{empty_c}{'░' * empty}{C.R}"


def bar_plain(current, max_val, width=10):
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    empty  = width - filled
    return f"{'█' * filled}{'░' * empty}"


def section(label, width=28):
    pad   = width - len(label) - 2
    left  = pad // 2
    right = pad - left
    return f"{C.GOLD}{'─' * left} {label} {'─' * right}{C.R}"


def divider(width=28):
    return f"{C.DARK}{'─' * width}{C.R}"


def header_box(title, width=28):
    inner  = width - 2
    pad    = inner - len(title)
    left   = pad // 2
    right  = pad - left
    top    = f"{C.GOLD}╔{'═' * inner}╗{C.R}"
    middle = f"{C.GOLD}║{' ' * left}{C.B}{title}{C.R}{C.GOLD}{' ' * right}║{C.R}"
    bottom = f"{C.GOLD}╚{'═' * inner}╝{C.R}"
    return f"{top}\n{middle}\n{bottom}"


def ansi(content: str) -> str:
    return f"```ansi\n{content}\n```"


GRADE_ICON = {
    "Normal":    f"{C.WHITE}⚬{C.R}",
    "Rare":      f"{C.BLUE}◆{C.R}",
    "Epic":      f"{C.PINK}❖{C.R}",
    "Legendary": f"{C.GOLD}✦{C.R}",
}

GRADE_ICON_PLAIN = {
    "Normal":    "⚬",
    "Rare":      "◆",
    "Epic":      "❖",
    "Legendary": "✦",
}

RANK_COLOR = {
    "연습": C.DARK,
    "F": C.WHITE, "E": C.WHITE,
    "D": C.GREEN,
    "C": C.CYAN,
    "B": C.BLUE,
    "A": C.PINK,
    "9": C.PINK, "8": C.PINK, "7": C.PINK,
    "6": C.GOLD, "5": C.GOLD, "4": C.GOLD, "3": C.GOLD,
    "2": C.RED,  "1": C.RED,
}


def rank_badge(rank: str) -> str:
    color = RANK_COLOR.get(rank, C.WHITE)
    return f"{color}[{rank}]{C.R}"


STAT_DISPLAY = {
    "str":  ("힘",   "⚔"),
    "int":  ("지력", "✦"),
    "dex":  ("민첩", "◈"),
    "will": ("의지", "❋"),
    "luck": ("운",   "★"),
}

# ── 푸터 (시스템 메시지만 중립 말투 교체) ─────────────────────────
FOOTERS = {
    "status":     "✦ 상태 정보 ✦",
    "equipment":  "✦ /스왑 으로 주·보조 슬롯을 전환할 수 있습니다 ✦",
    "battle":     "⚔ 전투 진행 중 ⚔",
    "shop":       "✦ 상점 ✦",
    "npc":        "❋ 대화 ❋",
    "help":       "✦ 도움말 ✦",
    "save":       "✦ 데이터가 저장되었습니다 ✦",
    "heal":       "❋ 회복 ❋",
    "system":     "⚙ 비전 타운 시스템 ⚙",
    "fishing":    "🎣 낚시 중 🎣",
    "cooking":    "🍳 요리 중 🍳",
    "metallurgy": "⚒ 제련 중 ⚒",
    "rest":       "💤 휴식 중 💤",
    "quest":      "📜 퀘스트 ✦",
    "gathering":  "🌿 채집 중 🌿",
    "craft":      "🔨 제작 중 🔨",
}

# ── SPIDER_ART (캐릭터 고유 표현 — 원본 유지) ────────────────────
SPIDER_ART = {
    "idle": (
        "```\n"
        "    🌙 ✨         ✦\n"
        "  🌲  🕷️  🌲\n"
        "  ～ ～🕸️～ ～\n"
        " 🍃     🍃    🍃\n"
        "```"
    ),
    "happy":        "```\n   ✨ 🎉 ✨\n    \\🕷️/\n  ～🕸️🎶🕸️～\n    💕💕\n```",
    "pet":          "```\n   🤚✨\n    🕷️ ♡ ♡\n  ～🕸️～🕸️～\n    (기분 좋슴미댜~)\n```",
    "sleep":        "```\n   🌙  ⭐  ✨\n     💤🕷️💤\n  ═══🕸️═══\n   (새근새근...)\n```",
    "rest":         "```\n  🏠 ～～～\n   🕷️💤  ☕\n  ═══🕸️═══\n   (쉬는 중임미댜...)\n```",
    "battle_start": "```\n   ⚔️ 🕷️ ⚔️\n   ╔═══════╗\n   ║ VS {monster} ║\n   ╚═══════╝\n  🕸️🕸️🕸️🕸️🕸️\n```",
    "battle_win":   "```\n   🎉✨🏆✨🎉\n     \\🕷️/\n   ═🕸️═🕸️═\n   승리임미댜!!!\n```",
    "battle_lose":  "```\n      💫\n    🕷️💦\n   ～～🕸️～～\n   (으으... 아팠슴미댜...)\n```",
    "fishing_wait": "```\n   🕷️🎣        🌊\n   ｜         〰️\n  🪨～～～～～～🐟?\n```",
    "fishing_bite": "```\n   🕷️❗🎣      💥\n   ｜       🐟!!\n  🪨～～💦～～～\n```",
    "fishing_catch":"```\n  ✨🕷️✨\n   \\🎣/\n    🐟 GET!\n  🕸️═══🕸️\n```",
    "shop":         "```\n  🏪═══════🏪\n  ║ 🕷️💰     ║\n  ║  뭘 살까~  ║\n  ╚═══════╝\n```",
    "travel":       "```\n  🕷️ ─ ─ ─ → 🏘️\n  🕸️ ～～～  🌲🌲\n```",
    "levelup":      "```\n  ✨🌟✨🌟✨\n    🕷️ LEVEL UP!\n  ═🕸️═══🕸️═\n    Lv.{old} → Lv.{new}\n  💪더 강해졌슴미댜!💪\n```",
    "cooking":      "```\n  🕷️🍳 지글지글~\n   🔥🔥🔥\n  ═══🕸️═══\n```",
    "gathering":    "```\n  🌿🕷️🌿\n   ✂️ 슥슥\n  🕸️～～🕸️\n```",
    "mining":       "```\n  ⛏️🕷️💎\n   쨍! 쨍!\n  🪨🪨🪨\n```",
}


def spider_scene(scene_key: str, **kwargs) -> str:
    art = SPIDER_ART.get(scene_key, SPIDER_ART["idle"])
    try:
        return art.format(**kwargs)
    except (KeyError, IndexError):
        return art
