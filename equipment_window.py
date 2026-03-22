import io
from bg3_renderer import get_renderer


def create_equipment_image(player) -> io.BytesIO:
    """장비창 — BG3 스타일 PIL 이미지 반환"""
    from items import ALL_ITEMS

    slot_keys = ["main", "sub", "body", "head", "hands", "feet"]
    slot_names = {
        "main": "주무기", "sub": "보조", "body": "갑옷",
        "head": "투구", "hands": "장갑", "feet": "신발",
    }

    slots = []
    for slot in slot_keys:
        eq_id = player.equipment.get(slot)
        sname = slot_names.get(slot, slot)
        if eq_id:
            item  = ALL_ITEMS.get(eq_id, {})
            name  = item.get("name", eq_id)
            grade = item.get("grade", "Normal")
            atk   = item.get("attack", 0)
            matk  = item.get("magic_attack", 0)
            defv  = item.get("defense", 0)
            parts = []
            if atk:  parts.append(f"ATK+{atk}")
            if matk: parts.append(f"MATK+{matk}")
            if defv: parts.append(f"DEF+{defv}")
            stats_text = " ".join(parts)
            slots.append({
                "slot_name": sname,
                "item_name": name,
                "grade": grade,
                "stats_text": stats_text,
            })
        else:
            slots.append({
                "slot_name": sname,
                "item_name": None,
                "grade": "Normal",
                "stats_text": "",
            })

    atk_val = player.get_attack()  if hasattr(player, "get_attack")  else 0
    def_val = player.get_defense() if hasattr(player, "get_defense") else 0
    matk_val = getattr(player, "get_magic_attack", lambda: 0)()

    return get_renderer().render_equipment_card(
        name=getattr(player, "name", "모험가"),
        slots=slots,
        attack=atk_val,
        defense=def_val,
        magic_attack=matk_val,
    )


class EquipmentWindow:
    def __init__(self, player):
        self.player = player

    def create_image(self) -> io.BytesIO:
        return create_equipment_image(self.player)
