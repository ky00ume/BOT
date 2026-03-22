import discord
import io
from bg3_renderer import get_renderer
from ui_theme import C, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS, GRADE_ICON_PLAIN


def _slot_name(slot: str) -> str:
    names = {
        "main":  "주무기",
        "sub":   "보조",
        "body":  "갑옷",
        "head":  "투구",
        "hands": "장갑",
        "feet":  "신발",
    }
    return names.get(slot, slot)


def create_equipment_image(player) -> io.BytesIO:
    """장비창 — BG3 스타일 PIL 이미지 반환"""
    from items import ALL_ITEMS
    slots = ["main","sub","body","head","hands","feet"]
    slot_names = {
        "main":"주무기","sub":"보조","body":"갑옷",
        "head":"투구","hands":"장갑","feet":"신발"
    }
    rows = []
    for slot in slots:
        eq_id = player.equipment.get(slot)
        sname = slot_names.get(slot, slot)
        if eq_id:
            item  = ALL_ITEMS.get(eq_id, {})
            name  = item.get("name", eq_id)
            grade = item.get("grade", "Normal")
            atk   = item.get("attack",0)
            matk  = item.get("magic_attack",0)
            defv  = item.get("defense",0)
            stat_str = name
            if atk:  stat_str += f" ATK+{atk}"
            if matk: stat_str += f" MATK+{matk}"
            if defv: stat_str += f" DEF+{defv}"
            from bg3_renderer import C
            col = C.RARITY.get(grade,(155,155,155))
            rows.append({"label":sname,"value":stat_str,"color":col})
        else:
            rows.append({"label":sname,"value":"— 비어있음 —"})
    atk_val  = player.get_attack()  if hasattr(player,"get_attack")  else 0
    def_val  = player.get_defense() if hasattr(player,"get_defense") else 0
    rows.append({"label":"공격력","value":str(atk_val)})
    rows.append({"label":"방어력","value":str(def_val)})
    return get_renderer().render_card(
        title="장비창", rows=rows,
        system_key="equipment", footer="✦ 장비 정보 ✦",
        w=560, h=380,
    )


class EquipmentWindow:
    def __init__(self, player):
        self.player = player

    def create_embed(self) -> discord.Embed:
        player = self.player
        from items import ALL_ITEMS

        lines = []
        lines.append(header_box("⚔ 장비창"))
        lines.append(section("착용 장비"))

        slots = ["main", "sub", "body", "head", "hands", "feet"]
        for slot in slots:
            eq_id = player.equipment.get(slot)
            slot_label = _slot_name(slot)
            if eq_id:
                item = ALL_ITEMS.get(eq_id, {})
                item_name  = item.get("name", eq_id)
                grade      = item.get("grade", "Normal")
                grade_icon = GRADE_ICON_PLAIN.get(grade, "⚬")
                atk = item.get("attack",       0)
                matk= item.get("magic_attack", 0)
                defv= item.get("defense",      0)
                stat_str = ""
                if atk:
                    stat_str += f" ATK+{atk}"
                if matk:
                    stat_str += f" MATK+{matk}"
                if defv:
                    stat_str += f" DEF+{defv}"
                lines.append(
                    f"  {C.GOLD}[{slot_label}]{C.R} {grade_icon}{C.WHITE}{item_name}{C.R}{C.DARK}{stat_str}{C.R}"
                )
            else:
                lines.append(f"  {C.DARK}[{slot_label}]{C.R} {C.DARK}— 비어있음 —{C.R}")

        lines.append(divider())
        lines.append(section("전투 스탯"))
        atk = player.get_attack()  if hasattr(player, "get_attack")  else 0
        defv= player.get_defense() if hasattr(player, "get_defense") else 0
        lines.append(f"  {C.RED}공격력{C.R}  {C.WHITE}{atk}{C.R}")
        lines.append(f"  {C.BLUE}방어력{C.R}  {C.WHITE}{defv}{C.R}")

        embed = discord.Embed(
            title="🛡 장비창",
            description=ansi("\n".join(lines)),
            color=EMBED_COLOR["equipment"],
        )
        embed.set_footer(text=FOOTERS["equipment"])
        return embed
