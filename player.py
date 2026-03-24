from skills_db import (
    RANK_ORDER, RANK_UP_THRESHOLD, SKILL_RANK_THRESHOLD, MASTERY_SKILLS,
    COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS,
)

# ─── 레벨업 스탯 증가 테이블 ─────────────────────────────────────────────
LEVEL_UP_TABLE = {
    1:  {"max_hp": 10, "max_mp": 5,  "max_energy": 3, "str": 1},
    2:  {"max_hp": 10, "max_mp": 5,  "max_energy": 3, "int": 1},
    3:  {"max_hp": 12, "max_mp": 6,  "max_energy": 3, "dex": 1},
    4:  {"max_hp": 12, "max_mp": 6,  "max_energy": 4, "will": 1},
    5:  {"max_hp": 15, "max_mp": 8,  "max_energy": 4, "str": 1, "int": 1},
    6:  {"max_hp": 15, "max_mp": 8,  "max_energy": 4, "dex": 1},
    7:  {"max_hp": 18, "max_mp": 10, "max_energy": 5, "will": 1},
    8:  {"max_hp": 18, "max_mp": 10, "max_energy": 5, "str": 1},
    9:  {"max_hp": 20, "max_mp": 12, "max_energy": 5, "int": 1},
    10: {"max_hp": 25, "max_mp": 15, "max_energy": 6, "str": 1, "int": 1, "dex": 1},
    "_default": {"max_hp": 20, "max_mp": 12, "max_energy": 5, "str": 1},
}


def apply_level_up(player) -> dict:
    """레벨업 시 스탯 증가를 적용하고 증가 내역 반환."""
    gains = LEVEL_UP_TABLE.get(player.level, LEVEL_UP_TABLE["_default"])
    result = {}
    if "max_hp" in gains:
        v = gains["max_hp"]
        player.max_hp += v
        player.hp = player.max_hp
        result["max_hp"] = v
    if "max_mp" in gains:
        v = gains["max_mp"]
        player.max_mp += v
        player.mp = player.max_mp
        result["max_mp"] = v
    if "max_energy" in gains:
        v = gains["max_energy"]
        player.max_energy += v
        player.energy = min(player.energy + v, player.max_energy)
        result["max_energy"] = v
    for stat in ("str", "int", "dex", "will", "luck"):
        if stat in gains:
            v = gains[stat]
            player.base_stats[stat] = player.base_stats.get(stat, 0) + v
            result[stat] = v
    return result

BASE_INVENTORY_SLOTS = 10

_SLOT_NAMES = {
    "main":  "주무기",
    "sub":   "보조",
    "body":  "갑옷",
    "head":  "투구",
    "hands": "장갑",
    "feet":  "신발",
}


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
        self.condition      = 50   # 컨디션 0~100, 기본 50
        self.stability      = 50   # 안정감 0~100, 기본 50
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

        self.costume = {
            "toy":       None,  # 장난감
            "hat":       None,  # 모자
            "outfit":    None,  # 의상
            "shoes":     None,  # 신발
            "accessory": None,  # 악세사리
        }

        self.inventory = {}
        self.bags = ["bag_large"]  # 기본 가방

        # 기본 전투 스킬은 처음부터 연습 랭크로 습득
        self.skill_ranks = {
            "smash":   "연습",
            "defense": "연습",
            "counter": "연습",
        }
        self.skill_exp = {
            "smash":   0.0,
            "defense": 0.0,
            "counter": 0.0,
        }

        self._affinity_manager = None

        self.keywords = ["마을", "날씨", "소문"]  # 기본 키워드 3개로 시작

        self._story_quest_manager = None  # StoryQuestManager (main.py에서 주입)
        self._quest_manager = None  # QuestManager (main.py에서 주입)
        self._flags: dict = {}  # 1회성 이벤트 플래그 (예: levelup_potion_granted)

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

    def unequip_item(self, slot: str) -> str:
        from items import ALL_ITEMS
        if slot not in self.equipment:
            return f"[{slot}]은(는) 올바른 슬롯이 아님미댜. (main/sub/body/head/hands/feet)"
        eq_id = self.equipment.get(slot)
        if not eq_id:
            return f"[{_SLOT_NAMES.get(slot, slot)}] 슬롯이 비어있슴미댜."
        item = ALL_ITEMS.get(eq_id, {})
        self.add_item(eq_id)
        self.equipment[slot] = None
        return f"[{item.get('name', eq_id)}]을(를) 벗었슴미댜!"

    def swap_weapons(self) -> str:
        main = self.equipment.get("main")
        sub  = self.equipment.get("sub")
        self.equipment["main"] = sub
        self.equipment["sub"]  = main
        return "주·보조 슬롯을 교환했슴미댜!"

    # ─── 의장(코스튬) 슬롯 ─────────────────────────────────────────────────
    _COSTUME_SLOT_MAP = {
        # 영문 키
        "toy":       "toy",
        "hat":       "hat",
        "outfit":    "outfit",
        "shoes":     "shoes",
        "accessory": "accessory",
        # 한글 alias
        "장난감": "toy",
        "모자":   "hat",
        "의상":   "outfit",
        "신발":   "shoes",
        "악세사리": "accessory",
    }
    _COSTUME_SLOT_NAMES = {
        "toy":       "장난감",
        "hat":       "모자",
        "outfit":    "의상",
        "shoes":     "신발",
        "accessory": "악세사리",
    }

    def equip_costume(self, item_id: str) -> str:
        from items import ALL_ITEMS
        item = ALL_ITEMS.get(item_id)
        if not item:
            return f"[{item_id}] 아이템을 찾을 수 없슴미댜."

        item_type = item.get("type")
        if item_type != "costume":
            return f"[{item.get('name', item_id)}]은(는) 의장 아이템이 아님미댜."

        eq_slot = item.get("slot")
        if not eq_slot:
            return f"[{item.get('name', item_id)}]의 슬롯 정보가 없슴미댜."

        costume_slot = self._COSTUME_SLOT_MAP.get(eq_slot)
        if not costume_slot:
            return f"[{eq_slot}]에 대응하는 의장 슬롯이 없슴미댜."

        prev = self.costume.get(costume_slot)
        if prev:
            self.add_item(prev)

        if item_id in self.inventory:
            self.remove_item(item_id)

        self.costume[costume_slot] = item_id
        slot_name = self._COSTUME_SLOT_NAMES.get(costume_slot, costume_slot)
        return f"[{item.get('name', item_id)}]을(를) {slot_name} 슬롯에 장착했슴미댜!"

    def unequip_costume(self, slot_input: str) -> str:
        from items import ALL_ITEMS
        slot = self._COSTUME_SLOT_MAP.get(slot_input)
        if slot is None:
            valid = "toy(장난감) / hat(모자) / outfit(의상) / shoes(신발) / accessory(악세사리)"
            return f"[{slot_input}]은(는) 올바른 의장 슬롯이 아님미댜.\n슬롯: {valid}"
        eq_id = self.costume.get(slot)
        if not eq_id:
            slot_name = self._COSTUME_SLOT_NAMES.get(slot, slot)
            return f"[{slot_name}] 슬롯이 비어있슴미댜."
        item = ALL_ITEMS.get(eq_id, {})
        self.add_item(eq_id)
        self.costume[slot] = None
        slot_name = self._COSTUME_SLOT_NAMES.get(slot, slot)
        return f"[{item.get('name', eq_id)}]을(를) {slot_name} 슬롯에서 해제했슴미댜!"

    def train_skill(self, skill_id: str, amount: float) -> str:
        if skill_id not in self.skill_ranks:
            self.skill_ranks[skill_id] = "연습"

        self.skill_exp[skill_id] = self.skill_exp.get(skill_id, 0.0) + amount

        current_rank = self.skill_ranks[skill_id]
        messages = []

        # 스킬별 threshold 조회 (없으면 공통 RANK_UP_THRESHOLD 폴백)
        skill_thresholds = SKILL_RANK_THRESHOLD.get(skill_id, RANK_UP_THRESHOLD)

        while True:
            threshold = skill_thresholds.get(current_rank, RANK_UP_THRESHOLD.get(current_rank))
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
        data = {
            "user_id":       0,
            "name":          self.name,
            "level":         self.level,
            "exp":           self.exp,
            "hp":            self.hp,
            "max_hp":        self.max_hp,
            "mp":            self.mp,
            "max_mp":        self.max_mp,
            "energy":        self.energy,
            "max_energy":    self.max_energy,
            "gold":          self.gold,
            "fatigue":       self.fatigue,
            "condition":     self.condition,
            "stability":     self.stability,
            "base_stats":    self.base_stats,
            "inventory":     self.inventory,
            "bags":          self.bags,
            "equipment":     self.equipment,
            "costume":       self.costume,
            "titles":        self.titles,
            "current_title": self.current_title,
            "keywords":      self.keywords,
            "skill_ranks":   self.skill_ranks,
            "skill_exp":     self.skill_exp,
            "last_special_encounter": getattr(self, "last_special_encounter", None),
            "rafael_contract": getattr(self, "rafael_contract", None),
            "_flags": getattr(self, "_flags", {}),
        }
        # 스토리 퀘스트 데이터 포함
        sq_mgr = getattr(self, "_story_quest_manager", None)
        if sq_mgr is not None:
            data["story_quest"] = sq_mgr.to_dict()
        # 퀘스트 데이터 포함
        qm = getattr(self, "_quest_manager", None)
        if qm is not None:
            data["quest_data"] = qm.to_dict()
        return data

    def load_from_dict(self, data: dict):
        self.name          = data.get("name",          self.name)
        self.level         = data.get("level",         self.level)
        self.exp           = data.get("exp",           self.exp)
        self.hp            = data.get("hp",            self.hp)
        self.max_hp        = data.get("max_hp",        self.max_hp)
        self.mp            = data.get("mp",            self.mp)
        self.max_mp        = data.get("max_mp",        self.max_mp)
        self.energy        = data.get("energy",        self.energy)
        self.max_energy    = data.get("max_energy",    self.max_energy)
        self.gold          = data.get("gold",          self.gold)
        self.fatigue       = data.get("fatigue",       getattr(self, "fatigue", 0))
        self.condition     = data.get("condition",     getattr(self, "condition", 50))
        self.stability     = data.get("stability",     getattr(self, "stability", 50))
        self.current_title = data.get("current_title", self.current_title)

        if "titles" in data and isinstance(data["titles"], list):
            self.titles = data["titles"]

        if "base_stats" in data and isinstance(data["base_stats"], dict):
            self.base_stats.update(data["base_stats"])

        if "inventory" in data and isinstance(data["inventory"], dict):
            self.inventory = data["inventory"]

        if "bags" in data and isinstance(data["bags"], list):
            self.bags = data["bags"]
        elif not self.bags:
            # 기존 데이터: bag_large 기본값 (가장 큰 가방)
            self.bags = ["bag_large"]

        if "equipment" in data and isinstance(data["equipment"], dict):
            for slot, val in data["equipment"].items():
                if slot in self.equipment:
                    self.equipment[slot] = val

        if "costume" in data and isinstance(data["costume"], dict):
            # 구버전 6슬롯 키(costume_main 등)는 새 5슬롯에 없으므로 자동으로 무시됨
            for slot, val in data["costume"].items():
                if slot in self.costume:
                    self.costume[slot] = val

        if "keywords" in data and isinstance(data["keywords"], list):
            self.keywords = data["keywords"]
        elif not hasattr(self, "keywords") or self.keywords is None:
            self.keywords = ["마을", "날씨", "소문"]

        if "skill_ranks" in data and isinstance(data["skill_ranks"], dict):
            # 기본 스킬은 항상 최소 연습 랭크 보장
            merged = {"smash": "연습", "defense": "연습", "counter": "연습"}
            merged.update(data["skill_ranks"])
            self.skill_ranks = merged
        if "skill_exp" in data and isinstance(data["skill_exp"], dict):
            self.skill_exp.update(data["skill_exp"])

        # 스토리 퀘스트 복원
        if "story_quest" in data and isinstance(data["story_quest"], dict):
            sq_mgr = getattr(self, "_story_quest_manager", None)
            if sq_mgr is not None:
                sq_mgr.from_dict(data["story_quest"])

        # 퀘스트 복원
        if "quest_data" in data and isinstance(data["quest_data"], dict):
            qm = getattr(self, "_quest_manager", None)
            if qm is not None:
                qm.from_dict(data["quest_data"])

        # 인카운터 관련 데이터 복원
        if "last_special_encounter" in data:
            self.last_special_encounter = data["last_special_encounter"]
        if "rafael_contract" in data:
            self.rafael_contract = data["rafael_contract"]
        # 1회성 플래그 복원
        if "_flags" in data and isinstance(data["_flags"], dict):
            self._flags = data["_flags"]

    def get_attack(self) -> int:
        base = 5 + self.base_stats.get("str", 10) // 2
        from items import ALL_ITEMS
        main_id = self.equipment.get("main")
        if main_id:
            weapon = ALL_ITEMS.get(main_id, {})
            base += weapon.get("attack", 0)
        # 의장 장난감 슬롯 공격력 합산
        toy_id = self.costume.get("toy")
        if toy_id:
            toy_item = ALL_ITEMS.get(toy_id, {})
            base += toy_item.get("attack", 0)
        # 타이틀 효과
        try:
            from title_data import get_title_effects
            eff = get_title_effects(self.current_title)
            base += eff.get("atk_bonus", 0)
            base += eff.get("stat_bonus", {}).get("str", 0) // 2
        except Exception:
            pass
        return base

    def get_defense(self) -> int:
        base = self.base_stats.get("will", 10) // 5
        from items import ALL_ITEMS
        for slot in ("sub", "body", "head", "hands", "feet"):
            eq_id = self.equipment.get(slot)
            if eq_id:
                armor = ALL_ITEMS.get(eq_id, {})
                base += armor.get("defense", 0)
        # 의장 방어구 방어력 합산 (모든 의장 슬롯)
        for cslot in ("toy", "hat", "outfit", "shoes", "accessory"):
            ceq_id = self.costume.get(cslot)
            if ceq_id:
                citem = ALL_ITEMS.get(ceq_id, {})
                base += citem.get("defense", 0)
        # 타이틀 효과
        try:
            from title_data import get_title_effects
            eff = get_title_effects(self.current_title)
            base += eff.get("def_bonus", 0)
        except Exception:
            pass
        return base
