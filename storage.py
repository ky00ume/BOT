"""storage.py — 보관함 시스템 (하이네스의 방)"""
import json
from database import get_db_connection
from ui_theme import C, ansi, header_box, divider, GRADE_ICON_PLAIN
from items import ALL_ITEMS

UPGRADE_TABLE = {
    20: 3000,
    30: 6000,
    40: 10000,
    50: 18000,
    60: 30000,
    70: 50000,
    80: 80000,
    90: 120000,
}
MAX_CAPACITY = 100


class StorageEngine:
    def __init__(self, player):
        self.player       = player
        self.items        = {}
        self.max_capacity = 20
        self._load()

    def _load(self):
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT items, max_capacity FROM storage WHERE user_id = ?", (0,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.items        = json.loads(row["items"])
                self.max_capacity = row["max_capacity"]
        except Exception:
            pass

    def _save(self):
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO storage (user_id, items, max_capacity)
                VALUES (?, ?, ?)
            """, (0, json.dumps(self.items, ensure_ascii=False), self.max_capacity))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def show(self) -> str:
        lines = [header_box("🗄 하이네스의 보관함")]
        lines.append(f"  {C.GOLD}용량: {len(self.items)}/{self.max_capacity}{C.R}")
        lines.append(divider())
        if not self.items:
            lines.append(f"  {C.DARK}보관함이 비어 있슴미댜.{C.R}")
        else:
            for item_id, count in self.items.items():
                item  = ALL_ITEMS.get(item_id, {})
                name  = item.get("name", item_id)
                grade = item.get("grade", "Normal")
                icon  = GRADE_ICON_PLAIN.get(grade, "⚬")
                lines.append(f"  {icon} {C.WHITE}{name}{C.R} x{count}")
        lines.append(divider())
        next_cap = self.max_capacity + 10
        cost     = UPGRADE_TABLE.get(self.max_capacity)
        if cost:
            lines.append(f"  {C.GREEN}/보관함업그레이드{C.R}  → {next_cap}칸  {C.GOLD}{cost:,}G{C.R}")
        else:
            lines.append(f"  {C.GOLD}최대 용량 달성!{C.R}")
        return ansi("\n".join(lines))

    def deposit(self, item_id: str, count: int) -> str:
        inventory = self.player.inventory
        have = inventory.get(item_id, 0)
        if have < count:
            item = ALL_ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            return ansi(f"  {C.RED}✖ [{name}] 인벤토리에 {count}개가 없슴미댜! (보유: {have}){C.R}")

        already = item_id in self.items
        if not already and len(self.items) >= self.max_capacity:
            return ansi(f"  {C.RED}✖ 보관함이 가득 찼슴미댜! ({len(self.items)}/{self.max_capacity}){C.R}")

        self.player.remove_item(item_id, count)
        self.items[item_id] = self.items.get(item_id, 0) + count
        self._save()

        item = ALL_ITEMS.get(item_id, {})
        name = item.get("name", item_id)
        return ansi(
            f"  {C.GREEN}✔ {name} x{count} 보관함에 넣었슴미댜!{C.R}\n"
            f"  {C.DARK}보관함: {len(self.items)}/{self.max_capacity}{C.R}"
        )

    def withdraw(self, item_id: str, count: int) -> str:
        have = self.items.get(item_id, 0)
        if have < count:
            item = ALL_ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            return ansi(f"  {C.RED}✖ [{name}] 보관함에 {count}개가 없슴미댜! (보유: {have}){C.R}")

        used, max_slots = self.player.inventory_check()
        already = item_id in self.player.inventory
        if not already and used >= max_slots:
            return ansi(f"  {C.RED}✖ 인벤토리가 가득 찼슴미댜! ({used}/{max_slots}){C.R}")

        self.items[item_id] -= count
        if self.items[item_id] <= 0:
            del self.items[item_id]
        self.player.add_item(item_id, count)
        self._save()

        item = ALL_ITEMS.get(item_id, {})
        name = item.get("name", item_id)
        return ansi(
            f"  {C.GREEN}✔ {name} x{count} 꺼냈슴미댜!{C.R}\n"
            f"  {C.DARK}보관함: {len(self.items)}/{self.max_capacity}{C.R}"
        )

    def upgrade(self) -> str:
        cost = UPGRADE_TABLE.get(self.max_capacity)
        if cost is None:
            return ansi(f"  {C.GOLD}✔ 이미 최대 용량({MAX_CAPACITY}칸)임미댜!{C.R}")

        if self.player.gold < cost:
            return ansi(
                f"  {C.RED}✖ 골드가 부족함미댜!\n"
                f"  필요: {cost:,}G / 보유: {self.player.gold:,}G{C.R}"
            )

        self.player.gold  -= cost
        self.max_capacity += 10
        self._save()
        return ansi(
            f"  {C.GREEN}✔ 보관함 업그레이드 완료!{C.R}\n"
            f"  {C.WHITE}용량: {self.max_capacity - 10} → {self.max_capacity}칸{C.R}\n"
            f"  {C.RED}-{cost:,}G{C.R} (현재: {self.player.gold:,}G)"
        )
