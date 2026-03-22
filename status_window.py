import discord
import io
from ui_theme import bar_plain, EMBED_COLOR, FOOTERS, STAT_DISPLAY
from bg3_renderer import get_renderer


def create_status_image(player) -> io.BytesIO:
    """상태창 — BG3 스타일 PIL 이미지 반환"""
    name   = getattr(player, 'name',          '모험가')
    level  = getattr(player, 'level',         1)
    title  = getattr(player, 'current_title', '비전의 탑 신입')
    hp     = getattr(player, 'hp',            100)
    max_hp = getattr(player, 'max_hp',        100)
    mp     = getattr(player, 'mp',            50)
    max_mp = getattr(player, 'max_mp',        50)
    en     = getattr(player, 'energy',        100)
    max_en = getattr(player, 'max_energy',    100)
    gold   = getattr(player, 'gold',          0)
    exp    = getattr(player, 'exp',           0.0)
    stats  = getattr(player, 'base_stats',    {})
    used, max_slots = (player.inventory_check()
                       if hasattr(player, 'inventory_check') else (0, 10))
    return get_renderer().render_status_card(
        name=name, level=level, title_str=title,
        hp=hp, max_hp=max_hp, mp=mp, max_mp=max_mp,
        en=en, max_en=max_en, gold=gold,
        exp=float(exp), exp_needed=level*100,
        stats=stats, inv_used=used, inv_max=max_slots,
    )




def create_status_embed(player) -> discord.Embed:
    """상태창 — Discord Embed 필드 기반 (모바일 호환)"""
    name  = getattr(player, "name",         "모험가")
    level = getattr(player, "level",        1)
    exp   = getattr(player, "exp",          0.0)
    title = getattr(player, "current_title","비전의 탑 신입")
    talent= getattr(player, "talent",       "초보 모험가")
    hp    = getattr(player, "hp",           100)
    max_hp= getattr(player, "max_hp",       100)
    mp    = getattr(player, "mp",           50)
    max_mp= getattr(player, "max_mp",       50)
    en    = getattr(player, "energy",       100)
    max_en= getattr(player, "max_energy",   100)
    gold  = getattr(player, "gold",         0)
    stats = getattr(player, "base_stats",   {})
    used, max_slots = player.inventory_check() if hasattr(player, "inventory_check") else (0, 10)
    bags = getattr(player, "bags", [])
    bag_name = ""
    if bags:
        try:
            from database import BAGS
            b = BAGS.get(bags[0], {})
            bag_name = f"\n🎒 {b.get('name', bags[0])} (+{b.get('slots',0)}칸)"
        except Exception:
            pass

    exp_needed = level * 100
    exp_bar_width = 10
    exp_filled = round(exp_bar_width * min(exp, exp_needed) / exp_needed) if exp_needed > 0 else 0
    exp_bar = "█" * exp_filled + "░" * (exp_bar_width - exp_filled)

    hp_bar  = bar_plain(hp,  max_hp,  width=10)
    mp_bar  = bar_plain(mp,  max_mp,  width=10)
    en_bar  = bar_plain(en,  max_en,  width=10)

    embed = discord.Embed(
        title=f"📋 {name}의 상태창",
        description=f"✦ **{title}** | 재능: {talent}",
        color=EMBED_COLOR["status"],
    )

    embed.add_field(
        name="⭐ 레벨 / 경험치",
        value=f"**Lv.{level}**\n`{exp_bar}` {int(exp):,} / {exp_needed:,}",
        inline=True,
    )

    hp_val  = f"❤️ `{hp_bar}` {hp}/{max_hp}"
    mp_val  = f"💙 `{mp_bar}` {mp}/{max_mp}"
    en_val  = f"💚 `{en_bar}` {en}/{max_en}"
    embed.add_field(name="💗 생명력 / 마나 / 기력", value=f"{hp_val}\n{mp_val}\n{en_val}", inline=True)

    stat_lines = []
    for stat_key, (stat_name, stat_icon) in STAT_DISPLAY.items():
        val = stats.get(stat_key, 0)
        stat_lines.append(f"{stat_icon} {stat_name}: **{val}**")
    embed.add_field(name="📊 기본 스탯", value="\n".join(stat_lines), inline=True)

    embed.add_field(
        name="💰 소지금 / 인벤토리",
        value=f"💰 **{gold:,}G**\n🎒 {used}/{max_slots} 슬롯",
        inline=True,
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
