import discord
from ui_theme import C, bar, bar_plain, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS, STAT_DISPLAY, rank_badge


def create_status_embed(player) -> discord.Embed:
    name  = getattr(player, "name",         "모험가")
    level = getattr(player, "level",        1)
    title = getattr(player, "current_title","비전의 탑 신입")
    talent= getattr(player, "talent",       "초보 모험가")

    hp     = getattr(player, "hp",         100)
    max_hp = getattr(player, "max_hp",     100)
    mp     = getattr(player, "mp",         50)
    max_mp = getattr(player, "max_mp",     50)
    en     = getattr(player, "energy",     100)
    max_en = getattr(player, "max_energy", 100)
    gold   = getattr(player, "gold",       0)
    stats  = getattr(player, "base_stats", {})

    used, max_slots = player.inventory_check() if hasattr(player, "inventory_check") else (0, 10)

    lines = []
    lines.append(header_box(f"✦ {name} ✦"))
    lines.append(f"  {C.GOLD}Lv.{level}{C.R}  {C.CYAN}{title}{C.R}")
    lines.append(f"  {C.DARK}재능: {C.WHITE}{talent}{C.R}")
    lines.append(divider())

    lines.append(section("생명력 / 마나 / 기력"))
    hp_bar = bar(hp, max_hp, fill_c=C.RED,  empty_c=C.DARK)
    mp_bar = bar(mp, max_mp, fill_c=C.BLUE, empty_c=C.DARK)
    en_bar = bar(en, max_en, fill_c=C.GREEN, empty_c=C.DARK)
    lines.append(f"  {C.RED}HP{C.R} {hp_bar} {C.WHITE}{hp}/{max_hp}{C.R}")
    lines.append(f"  {C.BLUE}MP{C.R} {mp_bar} {C.WHITE}{mp}/{max_mp}{C.R}")
    lines.append(f"  {C.GREEN}EN{C.R} {en_bar} {C.WHITE}{en}/{max_en}{C.R}")
    lines.append(divider())

    lines.append(section("기본 스탯"))
    for stat_key, (stat_name, stat_icon) in STAT_DISPLAY.items():
        val = stats.get(stat_key, 0)
        lines.append(f"  {C.GOLD}{stat_icon}{C.R} {C.WHITE}{stat_name}{C.R}  {C.CYAN}{val}{C.R}")
    lines.append(divider())

    lines.append(f"  {C.GOLD}💰{C.R} {C.WHITE}골드{C.R}  {C.GOLD}{gold:,}G{C.R}")
    lines.append(f"  {C.DARK}인벤토리{C.R} {C.WHITE}{used}/{max_slots}{C.R}")

    embed = discord.Embed(
        title=f"📋 {name}의 상태창",
        description=ansi("\n".join(lines)),
        color=EMBED_COLOR["status"],
    )
    embed.set_footer(text=FOOTERS["status"])
    return embed


def create_party_status_embed(player) -> discord.Embed:
    name  = getattr(player, "name",     "모험가")
    level = getattr(player, "level",    1)
    hp    = getattr(player, "hp",       100)
    max_hp= getattr(player, "max_hp",   100)
    mp    = getattr(player, "mp",       50)
    max_mp= getattr(player, "max_mp",   50)
    en    = getattr(player, "energy",   100)
    max_en= getattr(player, "max_energy",100)

    hp_bar = bar_plain(hp, max_hp, width=8)
    mp_bar = bar_plain(mp, max_mp, width=8)
    en_bar = bar_plain(en, max_en, width=8)

    desc = (
        f"**Lv.{level}** {name}\n"
        f"❤ `{hp_bar}` {hp}/{max_hp}\n"
        f"💙 `{mp_bar}` {mp}/{max_mp}\n"
        f"💚 `{en_bar}` {en}/{max_en}"
    )

    embed = discord.Embed(
        title="⚔ 파티 상태",
        description=desc,
        color=EMBED_COLOR["status"],
    )
    return embed
