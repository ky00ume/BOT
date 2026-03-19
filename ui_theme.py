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

EMBED_COLOR = {
    "status":    0xC9A96E,
    "equipment": 0x8B6B3D,
    "battle":    0xA01B2C,
    "shop":      0xD4AF37,
    "npc":       0x4A7856,
    "help":      0x7B5EA7,
    "save":      0x708090,
    "heal":      0xCB7BA0,
    "system":    0x2F3136,
}


def bar(current, max_val, width=10, fill_c=C.RED, empty_c=C.DARK):
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    empty = width - filled
    return f"{fill_c}{'█' * filled}{empty_c}{'░' * empty}{C.R}"


def bar_plain(current, max_val, width=10):
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    empty = width - filled
    return f"{'█' * filled}{'░' * empty}"


def section(label, width=28):
    pad = width - len(label) - 2
    left = pad // 2
    right = pad - left
    return f"{C.GOLD}{'─' * left} {label} {'─' * right}{C.R}"


def divider(width=28):
    return f"{C.DARK}{'─' * width}{C.R}"


def header_box(title, width=28):
    inner = width - 2
    pad = inner - len(title)
    left = pad // 2
    right = pad - left
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

FOOTERS = {
    "status":    "✦ 츄라이더는 성장 중임미댜! 츄아앗! ✦",
    "equipment": "✿ /스왑 으로 주·보조 슬롯을 전환하셰요 ✿",
    "battle":    "⚔ 승리를 위해 전진임미댜! ⚔",
    "shop":      "✦ 좋은 물건 많이 사셰요~ ✦",
    "npc":       "❋ 마을 사람들과 친해지셰요~ ❋",
    "help":      "✦ 모르는 게 있으면 언제든 물어봐요! ✦",
    "save":      "✿ 데이터가 안전하게 저장됐슴미댜 ✿",
    "heal":      "❋ 건강이 최고임미댜! ❋",
    "system":    "⚙ 비전 타운 봇 시스템 ⚙",
    "fishing":   "🎣 낚시는 인내임미댜~ 🎣",
    "cooking":   "🍳 요리로 힘을 키우셰요~ 🍳",
    "metallurgy": "⚒ 두드리면 강해짐미댜! ⚒",
}
