from items import WEAPONS, ARMORS, CONSUMABLES, COOKED_DISHES, ALL_ITEMS
from database import BAGS
from ui_theme import C, section, divider, header_box, ansi, GRADE_ICON_PLAIN, EMBED_COLOR, FOOTERS

TOOLS = {
    "tool_pot": {
        "name":  "나무 냄비",
        "type":  "tool",
        "grade": "Normal",
        "price": 500,
        "desc":  "삶기·끓이기·찌기용",
    },
    "tool_pan": {
        "name":  "프라이팬",
        "type":  "tool",
        "grade": "Normal",
        "price": 800,
        "desc":  "굽기·볶기·튀김용",
    },
    "tool_mortar": {
        "name":  "절구",
        "type":  "tool",
        "grade": "Normal",
        "price": 300,
        "desc":  "약초 가공·포션 제조용",
    },
    "tool_dough": {
        "name":  "반죽 틀",
        "type":  "tool",
        "grade": "Normal",
        "price": 600,
        "desc":  "반죽·굽기용",
    },
    "tool_ferment": {
        "name":  "발효통",
        "type":  "tool",
        "grade": "Rare",
        "price": 2000,
        "desc":  "발효 요리 전용",
    },
}

NPC_CATALOGS = {
    "크람":   {**WEAPONS, **ARMORS},
    "레이나": {**CONSUMABLES, **TOOLS},
    "곤트":   BAGS,
}


class ShopManager:
    def __init__(self, player):
        self.player = player

    # ─── 판매목록 (플레이어 → NPC) ────────────────────────────────────────
    def show_sell_list(self) -> str:
        inventory = self.player.inventory
        if not inventory:
            return ansi(f"  {C.RED}✖ 인벤토리가 비어있슴미댜!{C.R}")

        lines = [header_box("🏪 판매 목록"), section("인벤토리 아이템")]
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
        lines.append(f"  {C.GREEN}/판매 [아이템ID]{C.R} 으로 판매")
        return ansi("\n".join(lines))

    # ─── 판매 확정 ────────────────────────────────────────────────────────
    def sell_item(self, item_id: str, count: int = 1) -> str:
        inventory = self.player.inventory
        if inventory.get(item_id, 0) < count:
            return ansi(f"  {C.RED}✖ [{item_id}]이(가) 부족하거나 없슴미댜!{C.R}")

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

        lines = [header_box(f"🛒 {npc_name} 상점")]
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
        lines.append(f"  {C.GREEN}/구매 {npc_name} [아이템ID]{C.R} 으로 구매")
        return ansi("\n".join(lines))

    # ─── 구매 실행 ────────────────────────────────────────────────────────
    def execute_buy(self, npc_name: str, item_id: str, count: int = 1) -> str:
        catalog = NPC_CATALOGS.get(npc_name)
        if catalog is None:
            available = ", ".join(NPC_CATALOGS.keys())
            return ansi(
                f"  {C.RED}✖ [{npc_name}]은(는) 상점 NPC가 아님미댜!\n"
                f"  상점 NPC: {available}{C.R}"
            )

        item = catalog.get(item_id)
        if not item:
            return ansi(
                f"  {C.RED}✖ [{npc_name}] 상점에 [{item_id}]이(가) 없슴미댜!{C.R}"
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
