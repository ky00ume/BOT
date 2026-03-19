from items import WEAPONS, ARMORS, CONSUMABLES, COOKED_DISHES, ALL_ITEMS, TOOLS, GROCERIES
from database import BAGS
from ui_theme import C, section, divider, header_box, ansi, GRADE_ICON_PLAIN, EMBED_COLOR, FOOTERS

NPC_CATALOGS = {
    "크람":   {**WEAPONS, **ARMORS},
    "레이나": {**CONSUMABLES, **TOOLS, **GROCERIES},
    "곤트":   BAGS,
}


def find_item_by_name(name_or_id: str) -> str | None:
    """한글 이름 또는 아이템 ID로 아이템 ID를 찾습니다."""
    return _find_in_dict(ALL_ITEMS, name_or_id)


def find_item_in_catalog(catalog: dict, name_or_id: str) -> str | None:
    """NPC 카탈로그에서 한글 이름 또는 아이템 ID로 아이템 ID를 찾습니다."""
    return _find_in_dict(catalog, name_or_id)


def _find_in_dict(item_dict: dict, name_or_id: str) -> str | None:
    """아이템 딕셔너리에서 ID 또는 이름(정확/부분)으로 아이템 ID를 반환합니다."""
    # 1. 정확히 ID로 매칭
    if name_or_id in item_dict:
        return name_or_id
    # 2. 한글 이름으로 정확 매칭
    # 3. 부분 매칭 — 이름 길이가 짧은(=더 정확한) 결과 우선
    best_partial = None
    best_partial_len = float('inf')
    for item_id, item_data in item_dict.items():
        item_name = item_data.get("name", "")
        if item_name == name_or_id:
            return item_id          # 정확 매칭 즉시 반환
        if name_or_id in item_name and len(item_name) < best_partial_len:
            best_partial = item_id
            best_partial_len = len(item_name)
    return best_partial


class ShopManager:
    def __init__(self, player):
        self.player = player

    # ─── 판매목록 (플레이어 → NPC) ────────────────────────────────────────
    def show_sell_list(self) -> str:
        inventory = self.player.inventory
        if not inventory:
            return ansi(f"  {C.RED}✖ 인벤토리가 비어있슴미댜!{C.R}")

        lines = [header_box("🏪 판매 목록")]
        lines.append(f"  {C.GOLD}💰 소지금: {self.player.gold:,}G{C.R}")
        lines.append(divider())
        lines.append(section("인벤토리 아이템"))
        total = 0
        for item_id, count in inventory.items():
            item = ALL_ITEMS.get(item_id, {})
            name  = item.get("name",  item_id)
            price = item.get("price", 0)
            sell  = price // 2
            grade = item.get("grade", "Normal")
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            lines.append(
                f"  {icon} {C.WHITE}{name}{C.R} x{count}  "
                f"{C.DARK}판매가: {C.GOLD}{sell}G{C.R}"
            )
            total += sell * count

        lines.append(divider())
        lines.append(f"  {C.GOLD}예상 총액: {total:,}G{C.R}")
        lines.append(f"  {C.GREEN}/판매 [아이템이름]{C.R} 으로 판매")
        return ansi("\n".join(lines))

    # ─── 판매 확정 ────────────────────────────────────────────────────────
    def sell_item(self, name_or_id: str, count: int = 1) -> str:
        item_id = find_item_by_name(name_or_id)
        if not item_id:
            return ansi(f"  {C.RED}✖ [{name_or_id}]을(를) 찾을 수 없슴미댜!{C.R}")

        inventory = self.player.inventory
        if inventory.get(item_id, 0) < count:
            item = ALL_ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            return ansi(f"  {C.RED}✖ [{name}]이(가) 부족하거나 없슴미댜!{C.R}")

        item = ALL_ITEMS.get(item_id, {})
        name  = item.get("name",  item_id)
        price = item.get("price", 0)
        sell  = (price // 2) * count

        self.player.remove_item(item_id, count)
        self.player.gold += sell

        return ansi(
            f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} x{count} 판매 완료!\n"
            f"  {C.GOLD}+{sell}G{C.R} (현재: {self.player.gold:,}G)"
        )

    # ─── NPC 구매 목록 ────────────────────────────────────────────────────
    def show_buy_list(self, npc_name: str) -> str:
        catalog = NPC_CATALOGS.get(npc_name)
        if catalog is None:
            available = ", ".join(NPC_CATALOGS.keys())
            return ansi(
                f"  {C.RED}✖ [{npc_name}]은(는) 상점 NPC가 아님미댜!\n"
                f"  상점 NPC: {available}{C.R}"
            )

        from ui_theme import spider_scene
        lines = [spider_scene("shop"), header_box(f"🛒 {npc_name} 상점")]
        lines.append(f"  {C.GOLD}💰 소지금: {self.player.gold:,}G{C.R}")
        lines.append(divider())
        lines.append(section("판매 상품"))

        for item_id, item in catalog.items():
            grade = item.get("grade", "Normal")
            icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
            name  = item.get("name",  item_id)
            price = item.get("price", 0)
            desc  = item.get("desc",  "")
            lines.append(
                f"  {icon} {C.WHITE}{name}{C.R}  {C.GOLD}{price:,}G{C.R}"
            )
            lines.append(f"    {C.DARK}ID: {item_id}  {desc}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/구매 {npc_name} [아이템이름]{C.R} 으로 구매")
        return ansi("\n".join(lines))

    # ─── 구매 실행 ────────────────────────────────────────────────────────
    def execute_buy(self, npc_name: str, name_or_id: str, count: int = 1) -> str:
        catalog = NPC_CATALOGS.get(npc_name)
        if catalog is None:
            available = ", ".join(NPC_CATALOGS.keys())
            return ansi(
                f"  {C.RED}✖ [{npc_name}]은(는) 상점 NPC가 아님미댜!\n"
                f"  상점 NPC: {available}{C.R}"
            )

        item_id = find_item_in_catalog(catalog, name_or_id)
        item = catalog.get(item_id) if item_id else None
        if not item:
            return ansi(
                f"  {C.RED}✖ [{npc_name}] 상점에 [{name_or_id}]이(가) 없슴미댜!{C.R}"
            )

        price = item.get("price", 0)

        # 호감도 할인
        discount = 0
        if hasattr(self.player, "_affinity_manager") and self.player._affinity_manager:
            aff = self.player._affinity_manager
            discount = getattr(aff, "get_shop_discount_pct", lambda n: 0)(npc_name)
        final_price = int(price * count * (1 - discount / 100))

        # 골드 확인
        if self.player.gold < final_price:
            return ansi(
                f"  {C.RED}✖ 골드가 부족함미댜!\n"
                f"  필요: {final_price:,}G / 보유: {self.player.gold:,}G{C.R}"
            )

        # 인벤토리 공간 확인
        used, max_slots = self.player.inventory_check()
        already_have = item_id in self.player.inventory
        if not already_have and used >= max_slots:
            return ansi(
                f"  {C.RED}✖ 인벤토리가 가득 찼슴미댜! ({used}/{max_slots}){C.R}"
            )

        # 구매 처리
        self.player.gold -= final_price
        self.player.add_item(item_id, count)

        name = item.get("name", item_id)
        discount_str = f" ({discount}% 할인!)" if discount else ""
        return ansi(
            f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} x{count} 구매 완료!{discount_str}\n"
            f"  {C.RED}-{final_price:,}G{C.R} (현재: {C.GOLD}{self.player.gold:,}G{C.R})"
        )
