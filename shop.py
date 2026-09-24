from items import WEAPONS, ARMORS, CONSUMABLES, COOKED_DISHES, ALL_ITEMS, TOOLS, GROCERIES
from database import BAGS
from economy import Economy
from ui_theme import C, section, divider, header_box, ansi, GRADE_ICON_PLAIN, EMBED_COLOR, FOOTERS

# 스킬북 아이템 임포트 (있으면)
try:
    from items import SKILL_BOOKS
except ImportError:
    SKILL_BOOKS = {}

# ── 마이코니드 군락 상점 역할 ───────────────────────────────────────────────
# 데리스: 버섯/연금술 재료와 생활 물자. 오멜룸: 포션/연금술.
# 블러그: 연구 도구와 탐험 장비. NPC 역할과 무관한 옛 마을 카탈로그는 제거한다.
_DERRyth_MATERIAL_IDS = {
    "herb", "mana_herb", "healing_root", "mana_flower", "energy_leaf",
    "antidote_herb", "moonlight_dew", "mushroom", "pine_mushroom",
}
_DERRyth_CATALOG = {
    k: v for k, v in ALL_ITEMS.items()
    if k in _DERRyth_MATERIAL_IDS or (v.get("type") == "gathering" and "버섯" in v.get("name", ""))
}
_DERRyth_CATALOG.update({k: v for k, v in GROCERIES.items() if k not in {"empty_bottle"}})

_OMELUM_EXCLUDE = {"con_bread", "con_milk"}
_OMELUM_CATALOG = {k: v for k, v in CONSUMABLES.items() if k not in _OMELUM_EXCLUDE}
_OMELUM_CATALOG.update({
    k: v for k, v in ALL_ITEMS.items()
    if v.get("type") == "gathering" and k in {
        "herb", "mana_herb", "water", "healing_root", "mana_flower",
        "energy_leaf", "antidote_herb", "moonlight_dew",
    }
})

_BLURG_CATALOG = {**TOOLS}
_BLURG_CATALOG["empty_bottle"] = GROCERIES["empty_bottle"]
_BLURG_CATALOG.update(BAGS)
_BLURG_CATALOG.update({k: v for k, v in SKILL_BOOKS.items() if v.get("npc") == "블러그"})

NPC_CATALOGS = {
    "데리스 본클록": _DERRyth_CATALOG,
    "오멜룸": _OMELUM_CATALOG,
    "블러그": _BLURG_CATALOG,
}



def find_item_by_name(name_or_id: str) -> str | None:
    """한글 이름 또는 아이템 ID로 아이템 ID를 찾습니다."""
    return _find_in_dict(ALL_ITEMS, name_or_id)


def find_item_in_catalog(catalog: dict, name_or_id: str) -> str | None:
    """NPC 카탈로그에서 한글 이름 또는 아이템 ID로 아이템 ID를 찾습니다."""
    return _find_in_dict(catalog, name_or_id)


def _find_in_dict(item_dict: dict, name_or_id: str) -> str | None:
    """아이템 딕셔너리에서 ID 또는 이름으로 아이템 ID를 반환합니다.

    검색 우선순위:
    1. ID 정확 매칭
    2. 이름 정확 매칭
    3. 이름 공백 제거 후 정확 매칭
    4. 모든 검색어 키워드가 아이템명에 포함되는 경우 (AND 매칭, 이름 짧은 것 우선)
    5. 단일 키워드 부분 매칭 (이름 짧은 것 우선)
    """
    name_or_id = name_or_id.strip()
    keywords = name_or_id.split()
    # 공백 제거 버전
    normalized = name_or_id.replace(" ", "")

    # 1. ID 정확 매칭
    if name_or_id in item_dict:
        return name_or_id

    # 2. 이름 정확 매칭
    for item_id, item_data in item_dict.items():
        if item_data.get("name", "") == name_or_id:
            return item_id

    # 3. 이름 공백 제거 후 정확 매칭 (예: "철주괴" → "철 주괴")
    for item_id, item_data in item_dict.items():
        item_name = item_data.get("name", "")
        if item_name.replace(" ", "") == normalized:
            return item_id

    # 4. 모든 키워드 AND 매칭 (이름이 짧을수록 우선)
    if keywords:
        best_and = None
        best_and_len = float('inf')
        for item_id, item_data in item_dict.items():
            item_name = item_data.get("name", "")
            if all(kw in item_name for kw in keywords):
                if len(item_name) < best_and_len:
                    best_and = item_id
                    best_and_len = len(item_name)
        if best_and:
            return best_and

    # 5. 단일 부분 매칭 (이름이 짧을수록 우선)
    best_partial = None
    best_partial_len = float('inf')
    for item_id, item_data in item_dict.items():
        item_name = item_data.get("name", "")
        if name_or_id in item_name and len(item_name) < best_partial_len:
            best_partial = item_id
            best_partial_len = len(item_name)
    return best_partial


class ShopManager:
    def __init__(self, player):
        self.player = player

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
        if item.get("sellable") is False:
            return ansi(f"  {C.RED}✖ [{name}]은(는) 비전의 탑 전시용 유일품이라 판매할 수 없슴미댜!{C.R}")
        price = item.get("price", 0)
        sell  = (price // 2) * count

        economy = Economy(self.player)
        economy.remove_item(f"판매:{name}", item_id, count)
        economy.pay_reward(source=f"판매:{name}", gold=sell)

        return ansi(
            f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} x{count} 판매 완료!\n"
            f"  {C.GOLD}+{sell}G{C.R} (현재: {self.player.gold:,}G)"
        )

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
            extra = ""
            if item.get("type") == "bag":
                extra = f"  (+{item.get('slots', 0)}칸)"
            lines.append(
                f"  {icon} {C.WHITE}{name}{C.R}  {C.GOLD}{price:,}G{C.R}{extra}"
            )
            if desc:
                lines.append(f"    {C.DARK}{desc}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}[구매]{C.R} 버튼으로 드롭다운 구매")
        return ansi("\n".join(lines))

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

        discount = 0
        if hasattr(self.player, "_affinity_manager") and self.player._affinity_manager:
            aff = self.player._affinity_manager
            discount = getattr(aff, "get_shop_discount_pct", lambda n: 0)(npc_name)
        final_price = int(price * count * (1 - discount / 100))

        if self.player.gold < final_price:
            return ansi(
                f"  {C.RED}✖ 골드가 부족함미댜!\n"
                f"  필요: {final_price:,}G / 보유: {self.player.gold:,}G{C.R}"
            )

        name = item.get("name", item_id)
        discount_str = f" ({discount}% 할인!)" if discount else ""

        economy = Economy(self.player)

        # ── 가방 특별 처리 ──────────────────────────────────────────────
        if item.get("type") == "bag":
            new_slots = item.get("slots", 0)
            current_bags = getattr(self.player, "bags", [])
            # C-2 fix: 이미 같은 가방을 보유한 경우 중복 구매 방지
            if item_id in current_bags:
                return ansi(
                    f"  {C.RED}✖ 이미 같은 가방을 가지고 있슴미댜! "
                    f"({name}, +{new_slots}칸){C.R}"
                )
            # C-2 fix: 기존에 보유한 가방보다 작은 가방은 경고
            for cur_bag_id in current_bags:
                cur_bag = BAGS.get(cur_bag_id, {})
                cur_slots = cur_bag.get("slots", 0)
                if new_slots <= cur_slots:
                    return ansi(
                        f"  {C.RED}✖ 이미 더 좋은 가방을 가지고 있슴미댜! "
                        f"({cur_bag.get('name', cur_bag_id)}, +{cur_slots}칸){C.R}"
                    )
            economy.deduct(source=f"구매:{name}", gold=final_price)
            # C-2 fix: 기존 가방 유지하면서 새 가방 추가 (여러 가방 동시 보유)
            self.player.bags.append(item_id)
            total_extra = sum(BAGS.get(b, {}).get("slots", 0) for b in self.player.bags)
            return ansi(
                f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} 구매 완료!{discount_str}\n"
                f"  {C.RED}-{final_price:,}G{C.R} (현재: {C.GOLD}{self.player.gold:,}G{C.R})\n"
                f"  {C.GOLD}🎒 가방 추가: {name} (+{new_slots}칸) | 총 추가 슬롯: +{total_extra}칸{C.R}"
            )
        # ──────────────────────────────────────────────────────────────────

        used, max_slots = self.player.inventory_check()
        already_have = item_id in self.player.inventory
        if not already_have and used >= max_slots:
            return ansi(
                f"  {C.RED}✖ 인벤토리가 가득 찼슴미댜! ({used}/{max_slots}){C.R}"
            )

        economy.deduct(source=f"구매:{name}", gold=final_price)
        economy.add_item(source=f"구매:{name}", item_id=item_id, count=count)

        return ansi(
            f"  {C.GREEN}✔{C.R} {C.WHITE}{name}{C.R} x{count} 구매 완료!{discount_str}\n"
            f"  {C.RED}-{final_price:,}G{C.R} (현재: {C.GOLD}{self.player.gold:,}G{C.R})"
        )
