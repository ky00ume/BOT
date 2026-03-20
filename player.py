from skills_db import (
    RANK_ORDER, RANK_UP_THRESHOLD, MASTERY_SKILLS,
    COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS,
)

BASE_INVENTORY_SLOTS = 10


class Player:
    def __init__(self, name="모험가"):
        self.name           = name
        self.level          = 1
        self.exp            = 0.0
        self.hp             = 100
        self.max_hp         = 100
        self.mp             = 50
        self.max_mp         = 50
        self.energy         = 100
        self.max_energy     = 100
        self.gold           = 500
        self.fatigue        = 0
        self.current_title  = "비전의 탑 신입"
        self.talent         = "초보 모험가"
        self.titles         = ["비전의 탑 신입"]

        self.base_stats = {
            "str":  10,
            "int":  10,
            "dex":  10,
            "will": 10,
            "luck": 5,
        }

        self.equipment = {
            "main":  None,
            "sub":   None,
            "body":  None,
            "head":  None,
            "hands": None,
            "feet":  None,
        }

        self.inventory = {}
        self.bags = []

        self.skill_ranks = {}
        self.skill_exp   = {}

        self._affinity_manager = None

    def get_max_slots(self):
        extra = 0
        from database import BAGS
        for bag_id in self.bags:
            bag = BAGS.get(bag_id)
            if bag:
                extra += bag["slots"]
        return BASE_INVENTORY_SLOTS + extra

    def add_item(self, item_id: str, count: int = 1) -> bool:
        """인벤토리에 아이템 추가. 공간 부족 시 False 반환."""
        current_unique = len(self.inventory)
        already_have   = item_id in self.inventory
        max_slots      = self.get_max_slots()

        if not already_have and current_unique >= max_slots:
            return False

        self.inventory[item_id] = self.inventory.get(item_id, 0) + count
        return True

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """인벤토리에서 아이템 제거. 부족 시 False 반환."""
        if self.inventory.get(item_id, 0) < count:
            return False
        self.inventory[item_id] -= count
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def consume_energy(self, amount: int) -> bool:
        """에너지 소비. 부족 시 False 반환."""
        if self.energy < amount:
            return False
        self.energy -= amount
        return True

    def has_skill_auth(self, skill_id: str) -> bool:
        return skill_id in self.skill_ranks

    def inventory_check(self):
        used = len(self.inventory)
        max_slots = self.get_max_slots()
        return used, max_slots

    def equip_item(self, item_id: str) -> str:
        from items import ALL_ITEMS
        item = ALL_ITEMS.get(item_id)
        if not item:
            return f"[{item_id}] 아이템을 찾을 수 없슴미댜."

        item_type = item.get("type")
        if item_type not in ("weapon", "armor"):
            return f"[{item.get('name', item_id)}]은(는) 장착할 수 없는 아이템임미댜."

        slot = item.get("slot")
        if not slot:
            return f"[{item.get('name', item_id)}]의 슬롯 정보가 없슴미댜."

        prev = self.equipment.get(slot)
        if prev:
            self.add_item(prev)

        if item_id in self.inventory:
            self.remove_item(item_id)

        self.equipment[slot] = item_id
        return f"[{item.get('name', item_id)}]을(를) 장착했슴미댜!"

    def swap_weapons(self) -> str:
        main = self.equipment.get("main")
        sub  = self.equipment.get("sub")
        self.equipment["main"] = sub
        self.equipment["sub"]  = main
        return "주·보조 슬롯을 교환했슴미댜!"

    def train_skill(self, skill_id: str, amount: float) -> str:
        if skill_id not in self.skill_ranks:
            self.skill_ranks[skill_id] = "연습"

        self.skill_exp[skill_id] = self.skill_exp.get(skill_id, 0.0) + amount

        current_rank = self.skill_ranks[skill_id]
        messages = []

        while True:
            threshold = RANK_UP_THRESHOLD.get(current_rank)
            if threshold is None:
                break
            if self.skill_exp[skill_id] < threshold:
                break

            rank_idx = RANK_ORDER.index(current_rank)
            if rank_idx + 1 >= len(RANK_ORDER):
                break

            next_rank = RANK_ORDER[rank_idx + 1]
            self.skill_exp[skill_id] -= threshold
            self.skill_ranks[skill_id] = next_rank
            current_rank = next_rank

            mastery_key = f"{skill_id}_mastery"
            mastery = MASTERY_SKILLS.get(mastery_key)
            if mastery:
                bonus = mastery["stat_bonus"].get(next_rank, {})
                for stat, val in bonus.items():
                    if stat == "max_hp":
                        self.max_hp += val
                        self.hp = min(self.hp, self.max_hp)
                    elif stat == "max_mp":
                        self.max_mp += val
                        self.mp = min(self.mp, self.max_mp)
                    elif stat in self.base_stats:
                        self.base_stats[stat] += val

            messages.append(
                f"✦ [{skill_id}] 랭크 업! {current_rank} 달성임미댜! ✦"
            )

        return "\n".join(messages) if messages else ""

    def get_save_data(self) -> dict:
        return {
            "user_id":       0,
            "name":          self.name,
            "level":         self.level,
            "hp":            self.hp,
            "max_hp":        self.max_hp,
            "mp":            self.mp,
            "max_mp":        self.max_mp,
            "energy":        self.energy,
            "max_energy":    self.max_energy,
            "gold":          self.gold,
            "base_stats":    self.base_stats,
            "inventory":     self.inventory,
            "equipment":     self.equipment,
            "titles":        self.titles,
            "current_title": self.current_title,
        }

    def load_from_dict(self, data: dict):
        self.name          = data.get("name",          self.name)
        self.level         = data.get("level",         self.level)
        self.hp            = data.get("hp",            self.hp)
        self.max_hp        = data.get("max_hp",        self.max_hp)
        self.mp            = data.get("mp",            self.mp)
        self.max_mp        = data.get("max_mp",        self.max_mp)
        self.energy        = data.get("energy",        self.energy)
        self.max_energy    = data.get("max_energy",    self.max_energy)
        self.gold          = data.get("gold",          self.gold)
        self.current_title = data.get("current_title", self.current_title)

        if "titles" in data and isinstance(data["titles"], list):
            self.titles = data["titles"]

        if "base_stats" in data and isinstance(data["base_stats"], dict):
            self.base_stats.update(data["base_stats"])

        if "inventory" in data and isinstance(data["inventory"], dict):
            self.inventory = data["inventory"]

        if "equipment" in data and isinstance(data["equipment"], dict):
            for slot, val in data["equipment"].items():
                if slot in self.equipment:
                    self.equipment[slot] = val

    def get_attack(self) -> int:
        base = 5 + self.base_stats.get("str", 10) // 2
        from items import ALL_ITEMS
        main_id = self.equipment.get("main")
        if main_id:
            weapon = ALL_ITEMS.get(main_id, {})
            base += weapon.get("attack", 0)
        return base

    def get_defense(self) -> int:
        base = self.base_stats.get("will", 10) // 5
        from items import ALL_ITEMS
        for slot in ("sub", "body", "head", "hands", "feet"):
            eq_id = self.equipment.get(slot)
            if eq_id:
                armor = ALL_ITEMS.get(eq_id, {})
                base += armor.get("defense", 0)
        return base
