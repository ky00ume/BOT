import uuid
from typing import Dict, List, Optional, Any
from utils.logger import setup_logger
from skills_db import (
    RANK_ORDER, RANK_UP_THRESHOLD, SKILL_RANK_THRESHOLD, MASTERY_SKILLS,
    COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, OTHER_SKILLS,
)

logger = setup_logger('player')

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


def apply_level_up(player: 'Player') -> Dict[str, int]:
    """레벨업 시 스탯 증가를 적용하고 증가 내역 반환.

    Args:
        player: 플레이어 인스턴스

    Returns:
        증가된 스탯 딕셔너리
    """
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


def check_level_up(player: 'Player') -> List[Dict[str, Any]]:
    """EXP가 레벨업 기준(level*100)을 초과하면 레벨업 처리.

    여러 레벨을 한 번에 올릴 수 있다.

    Args:
        player: 플레이어 인스턴스

    Returns:
        [{old_level, new_level, gains}, ...] 레벨업 내역 리스트 (없으면 빈 리스트)
    """
    results = []
    while True:
        threshold = player.level * 100
        if player.exp < threshold:
            break
        old_level = player.level
        player.exp -= threshold
        player.level += 1
        gains = apply_level_up(player)
        results.append({
            "old_level": old_level,
            "new_level": player.level,
            "gains": gains,
        })
    return results

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
    """플레이어 캐릭터 데이터 클래스."""

    def __init__(self, name: str = "모험가") -> None:
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

        # 휴대품 가방. 기존 저장/시스템 호환을 위해 inventory 이름은 유지한다.
        self.inventory: dict = {}
        self.bags = ["bag_large"]  # 휴대 가방 확장
        # 장비 가방 / 전투 전리품 임시 묶음 / 비전의 탑 보관함.
        self.gear_inventory: dict = {}
        self.loot_buffer: dict = {}
        self.home_storage: dict = {}
        self.gear_bag_slots = 8
        self.home_storage_slots = 120
        # 수서 발전기와 비전의 탑 설비 복구 상태. 기존 세이브는 모두 꺼진 상태로 시작한다.
        self.tower_state = {"generator_online": False, "facilities": {}}

        # 기본 전투 스킬은 처음부터 연습 랭크로 습득
        self.skill_ranks = {
            "smash":      "연습",
            "defense":    "연습",
            "counter":    "연습",
            "mining":     "연습",
            "metallurgy": "연습",
            "blacksmith": "연습",
        }
        self.skill_exp = {
            "smash":      0.0,
            "defense":    0.0,
            "counter":    0.0,
            "mining":     0.0,
            "metallurgy": 0.0,
            "blacksmith": 0.0,
        }

        self._affinity_manager = None

        self.keywords = ["군락", "날씨", "소문"]  # 기본 키워드 3개로 시작
        self.current_location = "비전의 탑"

        self._story_quest_manager = None  # StoryQuestManager (main.py에서 주입)
        self._quest_manager = None  # QuestManager (main.py에서 주입)
        self._flags: dict = {}  # 1회성 이벤트 플래그 (예: levelup_potion_granted)
        self.auto_use_potion = True  # E-6: 오토 전투 시 포션 자동 사용 설정

    def get_max_slots(self) -> int:
        """최대 인벤토리 슬롯 수 계산.

        Returns:
            기본 슬롯 + 가방 슬롯 합계
        """
        extra = 0
        from database import BAGS
        for bag_id in self.bags:
            bag = BAGS.get(bag_id)
            if bag:
                extra += bag["slots"]  # type: ignore[operator]
        return BASE_INVENTORY_SLOTS + extra

    def add_item(self, item_id: str, count: int = 1) -> bool:
        """인벤토리에 아이템 추가.

        Args:
            item_id: 아이템 ID
            count: 추가할 수량

        Returns:
            공간이 있어 추가 성공 시 True, 실패 시 False
        """
        current_unique = len(self.inventory)
        already_have   = item_id in self.inventory
        max_slots      = self.get_max_slots()

        if not already_have and current_unique >= max_slots:
            logger.warning(
                f"인벤토리 가득 찼음: player={self.name}, "
                f"current={current_unique}, max={max_slots}, item={item_id}"
            )
            return False

        self.inventory[item_id] = self.inventory.get(item_id, 0) + count
        logger.debug(f"아이템 추가: player={self.name}, item={item_id}, count={count}")
        return True

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """인벤토리에서 아이템 제거.

        Args:
            item_id: 아이템 ID
            count: 제거할 수량

        Returns:
            충분한 수량이 있어 제거 성공 시 True, 실패 시 False
        """
        current = self.inventory.get(item_id, 0)
        if current < count:
            logger.warning(
                f"아이템 부족: player={self.name}, item={item_id}, "
                f"필요={count}, 보유={current}"
            )
            return False

        self.inventory[item_id] -= count
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]

        logger.debug(f"아이템 제거: player={self.name}, item={item_id}, count={count}")
        return True

    def _gear_instance_store(self) -> dict:
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        return self._flags.setdefault("gear_instances", {})

    def _equipped_instance_store(self) -> dict:
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        return self._flags.setdefault("equipped_gear_instances", {})

    def _make_gear_instance(self, item_id: str, *, quality_score: int = 50,
                            quality_key: str = "Normal", quality_label: str = "⚒️ 보통",
                            crafted_by=None, source: str = "loot", uid: str | None = None) -> dict:
        max_durability_by_quality = {
            "Rough": 90, "Normal": 100, "Fine": 105,
            "Excellent": 110, "Masterpiece": 120,
        }
        max_durability = max_durability_by_quality.get(quality_key, 100)
        return {
            "uid": uid or uuid.uuid4().hex,
            "item_id": item_id,
            "quality_score": max(0, min(100, int(quality_score))),
            "quality_key": quality_key,
            "quality_label": quality_label,
            "durability": max_durability,
            "max_durability": max_durability,
            "crafted_by": crafted_by,
            "source": source,
        }

    def ensure_gear_instances(self) -> None:
        """기존 수량형 장비 저장을 개별 인스턴스로 안전하게 보강한다."""
        store = self._gear_instance_store()
        equipped_store = self._equipped_instance_store()
        counts = {}
        for inst in store.values():
            item_id = inst.get("item_id")
            if item_id:
                counts[item_id] = counts.get(item_id, 0) + 1
        for item_id, count in list(self.gear_inventory.items()):
            missing = max(0, int(count) - counts.get(item_id, 0))
            for _ in range(missing):
                inst = self._make_gear_instance(item_id, source="legacy")
                store[inst["uid"]] = inst
        for slot, item_id in self.equipment.items():
            if item_id and slot not in equipped_store:
                inst = self._make_gear_instance(item_id, source="legacy_equipped")
                equipped_store[slot] = inst

    def get_gear_instances(self, item_id: str | None = None) -> list[dict]:
        self.ensure_gear_instances()
        rows = list(self._gear_instance_store().values())
        if item_id is not None:
            rows = [row for row in rows if row.get("item_id") == item_id]
        return rows

    def get_equipped_gear_instance(self, slot: str):
        self.ensure_gear_instances()
        inst = self._equipped_instance_store().get(slot)
        return dict(inst) if inst else None

    def _quality_stat_multiplier(self, instance: dict | None) -> float:
        if not instance:
            return 1.0
        return {
            "Rough": 0.90,
            "Normal": 1.00,
            "Fine": 1.05,
            "Excellent": 1.10,
            "Masterpiece": 1.15,
        }.get(instance.get("quality_key", "Normal"), 1.0)

    def add_gear_item(self, item_id: str, count: int = 1, *, quality_score: int = 50,
                      quality_key: str = "Normal", quality_label: str = "⚒️ 보통",
                      crafted_by=None, source: str = "loot") -> bool:
        """장비를 개별 인스턴스로 생성해 장비 가방에 넣는다."""
        from inventory_domains import is_equipment
        if not is_equipment(item_id) or count <= 0:
            return False
        if item_id not in self.gear_inventory and len(self.gear_inventory) >= self.gear_bag_slots:
            return False
        store = self._gear_instance_store()
        for _ in range(count):
            inst = self._make_gear_instance(
                item_id,
                quality_score=quality_score,
                quality_key=quality_key,
                quality_label=quality_label,
                crafted_by=crafted_by,
                source=source,
            )
            store[inst["uid"]] = inst
        self.gear_inventory[item_id] = self.gear_inventory.get(item_id, 0) + count
        return True

    def add_loot(self, item_id: str, count: int = 1) -> bool:
        """전투 중 획득물을 임시 전리품 묶음에 보관한다."""
        if count <= 0:
            return False
        self.loot_buffer[item_id] = self.loot_buffer.get(item_id, 0) + count
        return True

    def claim_loot(self, item_id: str, count: int = 1) -> bool:
        """전리품을 종류에 맞는 휴대 가방으로 옮긴다."""
        if count <= 0 or self.loot_buffer.get(item_id, 0) < count:
            return False
        from inventory_domains import is_equipment
        added = self.add_gear_item(item_id, count) if is_equipment(item_id) else self.add_item(item_id, count)
        if not added:
            return False
        self.loot_buffer[item_id] -= count
        if self.loot_buffer[item_id] <= 0:
            del self.loot_buffer[item_id]
        return True

    def store_at_home(self, item_id: str, count: int = 1, *, from_gear: bool = False) -> bool:
        """휴대품/장비 가방의 물건을 비전의 탑 보관함으로 옮긴다."""
        source = self.gear_inventory if from_gear else self.inventory
        if count <= 0 or source.get(item_id, 0) < count:
            return False
        if item_id not in self.home_storage and len(self.home_storage) >= self.home_storage_slots:
            return False
        source[item_id] -= count
        if source[item_id] <= 0:
            del source[item_id]
        self.home_storage[item_id] = self.home_storage.get(item_id, 0) + count
        return True

    def store_all_loot_at_home(self) -> dict[str, int]:
        """안전 귀환 시 남은 전리품을 탑 보관함으로 자동 수납한다."""
        moved = {}
        for item_id, count in list(self.loot_buffer.items()):
            if item_id not in self.home_storage and len(self.home_storage) >= self.home_storage_slots:
                continue
            self.home_storage[item_id] = self.home_storage.get(item_id, 0) + count
            moved[item_id] = count
            del self.loot_buffer[item_id]
        return moved

    def add_hyness_item(self, item_id: str, count: int = 1) -> None:
        """하이네스 방 전용 인벤토리에 아이템 추가.

        Args:
            item_id: 아이템 ID
            count: 추가할 수량
        """
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        inv = self._flags.setdefault("hyness_inventory", {})
        inv[item_id] = inv.get(item_id, 0) + count

    def remove_hyness_item(self, item_id: str, count: int = 1) -> bool:
        """하이네스 방 전용 인벤토리에서 아이템 제거."""
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        inv = self._flags.get("hyness_inventory", {})
        if inv.get(item_id, 0) < count:
            return False
        inv[item_id] -= count
        if inv[item_id] <= 0:
            del inv[item_id]
        return True

    def get_hyness_inventory(self) -> Dict[str, int]:
        """하이네스 방 전용 인벤토리 반환."""
        if not hasattr(self, "_flags") or self._flags is None:
            return {}
        return self._flags.get("hyness_inventory", {})  # type: ignore[return-value]

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

    def get_total_slots(self) -> int:
        """최대 인벤토리 슬롯 수 반환 (get_max_slots 별칭)."""
        return self.get_max_slots()

    def take_damage(self, amount: int) -> None:
        """HP를 amount만큼 감소시킨다 (0 이하로 내려갈 수 있음)."""
        self.hp -= amount

    def heal(self, amount: int) -> None:
        """HP를 amount만큼 회복한다 (max_hp를 초과하지 않는다)."""
        self.hp = min(self.max_hp, self.hp + amount)

    def use_energy(self, amount: int) -> bool:
        """기력을 amount만큼 소모한다.

        Returns:
            소모 성공 시 True, 기력 부족 시 False (상태 변경 없음).
        """
        if amount < 0 or self.energy < amount:
            return False
        self.energy -= amount
        return True

    def restore_energy(self, amount: int) -> None:
        """기력을 amount만큼 회복한다 (max_energy를 초과하지 않는다)."""
        self.energy = min(self.max_energy, self.energy + amount)

    def equip_item(self, item_id: str, instance_uid: str | None = None) -> str:
        from items import ALL_ITEMS
        item = ALL_ITEMS.get(item_id)
        if not item:
            return f"[{item_id}] 아이템을 찾을 수 없슴미댜."
        if item.get("type") not in ("weapon", "armor"):
            return f"[{item.get('name', item_id)}]은(는) 장착할 수 없는 아이템임미댜."
        slot = item.get("slot")
        if not slot:
            return f"[{item.get('name', item_id)}]의 슬롯 정보가 없슴미댜."

        self.ensure_gear_instances()
        candidates = self.get_gear_instances(item_id)
        if instance_uid:
            candidates = [row for row in candidates if row.get("uid") == instance_uid]
        if not candidates:
            # 구버전 일반 인벤토리에 남은 장비는 이 시점에 Normal 인스턴스로 이관한다.
            if self.inventory.get(item_id, 0) > 0:
                self.remove_item(item_id, 1)
                self.add_gear_item(item_id, 1, source="legacy_inventory")
                candidates = self.get_gear_instances(item_id)
            if not candidates:
                # equip_item()은 오래된 내부 호출/tests와의 호환을 위해 직접 호출 시
                # 암묵적 Normal 개체를 허용한다. 실제 Discord 명령은 소유 여부를 먼저 검사한다.
                self.add_gear_item(item_id, 1, source="legacy_direct_equip")
                candidates = self.get_gear_instances(item_id)
        # 이름만 지정했을 때는 가장 품질이 높은 개체를 선택한다.
        chosen = max(candidates, key=lambda row: (row.get("quality_score", 50), row.get("durability", 0)))

        prev = self.equipment.get(slot)
        if prev:
            prev_inst = self._equipped_instance_store().pop(slot, None)
            if prev_inst:
                self._gear_instance_store()[prev_inst["uid"]] = prev_inst
                self.gear_inventory[prev] = self.gear_inventory.get(prev, 0) + 1
            else:
                self.add_gear_item(prev, source="legacy_equipped")

        self._gear_instance_store().pop(chosen["uid"], None)
        self.gear_inventory[item_id] = max(0, self.gear_inventory.get(item_id, 0) - 1)
        if self.gear_inventory[item_id] <= 0:
            self.gear_inventory.pop(item_id, None)
        self.equipment[slot] = item_id
        self._equipped_instance_store()[slot] = chosen
        quality = chosen.get("quality_label", "⚒️ 보통")
        return f"[{item.get('name', item_id)}]을(를) 장착했슴미댜! · {quality}"

    def unequip_item(self, slot: str) -> str:
        from items import ALL_ITEMS
        if slot not in self.equipment:
            return f"[{slot}]은(는) 올바른 슬롯이 아님미댜. (main/sub/body/head/hands/feet)"
        eq_id = self.equipment.get(slot)
        if not eq_id:
            return f"[{_SLOT_NAMES.get(slot, slot)}] 슬롯이 비어있슴미댜."
        if eq_id not in self.gear_inventory and len(self.gear_inventory) >= self.gear_bag_slots:
            return "장비 가방이 가득 차서 벗을 수 없슴미댜."
        self.ensure_gear_instances()
        inst = self._equipped_instance_store().pop(slot, None)
        if not inst:
            inst = self._make_gear_instance(eq_id, source="legacy_equipped")
        self._gear_instance_store()[inst["uid"]] = inst
        self.gear_inventory[eq_id] = self.gear_inventory.get(eq_id, 0) + 1
        self.equipment[slot] = None
        item = ALL_ITEMS.get(eq_id, {})
        return f"[{item.get('name', eq_id)}]을(를) 벗었슴미댜!"

    def swap_weapons(self) -> str:
        main = self.equipment.get("main")
        sub  = self.equipment.get("sub")
        self.equipment["main"] = sub
        self.equipment["sub"]  = main
        self.ensure_gear_instances()
        inst = self._equipped_instance_store()
        main_inst = inst.pop("main", None)
        sub_inst = inst.pop("sub", None)
        if sub_inst:
            inst["main"] = sub_inst
        if main_inst:
            inst["sub"] = main_inst
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

    def get_featured_costume(self):
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        item_id = self._flags.get("featured_costume")
        if item_id and item_id in self.costume.values():
            return item_id
        if item_id:
            self._flags["featured_costume"] = None
        return None

    def set_featured_costume(self, item_id: str | None) -> bool:
        if not hasattr(self, "_flags") or self._flags is None:
            self._flags = {}
        if item_id is None:
            self._flags["featured_costume"] = None
            return True
        if item_id not in self.costume.values():
            return False
        self._flags["featured_costume"] = item_id
        return True

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
            if self.get_featured_costume() == prev:
                self.set_featured_costume(None)
            self.add_hyness_item(prev)

        h_inv = self.get_hyness_inventory()
        if item_id in h_inv:
            self.remove_hyness_item(item_id)

        self.costume[costume_slot] = item_id  # type: ignore[assignment]
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
        self.add_hyness_item(eq_id)
        if self.get_featured_costume() == eq_id:
            self.set_featured_costume(None)
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
            "user_id":       getattr(self, "user_id", 0),
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
            "gear_inventory": self.gear_inventory,
            "loot_buffer":    self.loot_buffer,
            "home_storage":   self.home_storage,
            "gear_bag_slots": self.gear_bag_slots,
            "home_storage_slots": self.home_storage_slots,
            "tower_state":    self.tower_state,
            "equipment":     self.equipment,
            "costume":       self.costume,
            "titles":        self.titles,
            "current_title": self.current_title,
            "keywords":      self.keywords,
            "current_location": self.current_location,
            "skill_ranks":   self.skill_ranks,
            "skill_exp":     self.skill_exp,
            "last_special_encounter": getattr(self, "last_special_encounter", None),
            "rafael_contract": getattr(self, "rafael_contract", None),
            "_flags": getattr(self, "_flags", {}),
            "auto_use_potion": getattr(self, "auto_use_potion", True),
        }
        # 스토리 퀘스트 데이터 포함
        sq_mgr = getattr(self, "_story_quest_manager", None)
        if sq_mgr is not None:
            data["story_quest"] = sq_mgr.to_dict()
        # 퀘스트 데이터 포함
        qm = getattr(self, "_quest_manager", None)
        if qm is not None:
            data["quest_data"] = qm.to_dict()
        # 호감도 데이터 포함
        aff_mgr = getattr(self, "_affinity_manager", None)
        if aff_mgr is not None:
            data["affinity_full"] = aff_mgr.to_dict()
        # 도감 데이터 포함
        col_mgr = getattr(self, "_collection_manager", None)
        if col_mgr is not None:
            data["collection_data"] = col_mgr.to_dict()
        return data

    def load_from_dict(self, data: dict):
        self.name          = data.get("name",          self.name)
        self.level         = data.get("level",         self.level)
        self.exp           = data.get("exp",           self.exp)
        # A-1: max 값을 먼저 로드해야 hp/mp 유효성 검증에 올바른 참조값 사용 가능
        self.max_hp        = data.get("max_hp",        self.max_hp)
        self.hp            = data.get("hp",            self.hp)
        self.max_mp        = data.get("max_mp",        self.max_mp)
        self.mp            = data.get("mp",            self.mp)
        self.energy        = data.get("energy",        self.energy)
        self.max_energy    = data.get("max_energy",    self.max_energy)
        self.gold          = data.get("gold",          self.gold)
        self.fatigue       = data.get("fatigue",       getattr(self, "fatigue", 0))
        self.condition     = data.get("condition",     getattr(self, "condition", 50))
        self.stability     = data.get("stability",     getattr(self, "stability", 50))
        self.current_title = data.get("current_title", self.current_title)
        self.current_location = data.get("current_location", getattr(self, "current_location", "비전의 탑"))

        # A-1 fix: HP/MP 값 유효성 보정 (0 이하이면 최대값으로 복원, max 초과 방지)
        if self.hp <= 0:
            self.hp = self.max_hp
        elif self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.mp < 0:
            self.mp = self.max_mp
        elif self.mp > self.max_mp:
            self.mp = self.max_mp

        if "titles" in data and isinstance(data["titles"], list):
            self.titles = data["titles"]

        if "base_stats" in data and isinstance(data["base_stats"], dict):
            self.base_stats.update(data["base_stats"])

        if "inventory" in data and isinstance(data["inventory"], dict):
            self.inventory = data["inventory"]

        if "gear_inventory" in data and isinstance(data["gear_inventory"], dict):
            self.gear_inventory = data["gear_inventory"]
        if "loot_buffer" in data and isinstance(data["loot_buffer"], dict):
            self.loot_buffer = data["loot_buffer"]
        if "home_storage" in data and isinstance(data["home_storage"], dict):
            self.home_storage = data["home_storage"]
        self.gear_bag_slots = int(data.get("gear_bag_slots", self.gear_bag_slots))
        self.home_storage_slots = int(data.get("home_storage_slots", self.home_storage_slots))
        if "tower_state" in data and isinstance(data["tower_state"], dict):
            self.tower_state = data["tower_state"]
        from tower_power import ensure_tower_state, recalculate_storage
        ensure_tower_state(self)
        recalculate_storage(self)

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
            self.keywords = ["군락", "날씨", "소문"]

        if "skill_ranks" in data and isinstance(data["skill_ranks"], dict):
            # 기본 스킬은 항상 최소 연습 랭크 보장
            merged = {"smash": "연습", "defense": "연습", "counter": "연습", "mining": "연습", "metallurgy": "연습", "blacksmith": "연습"}
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
        self.ensure_gear_instances()

        # E-6: 오토 전투 포션 자동 사용 설정 복원
        self.auto_use_potion = data.get("auto_use_potion", True)

    def get_attack(self) -> int:
        base = 5 + self.base_stats.get("str", 10) // 2
        from items import ALL_ITEMS
        main_id = self.equipment.get("main")
        if main_id:
            weapon = ALL_ITEMS.get(main_id, {})
            inst = self.get_equipped_gear_instance("main")
            base += round(weapon.get("attack", 0) * self._quality_stat_multiplier(inst))
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
            logger.warning('player: get_attack title_data 로드 실패', exc_info=True)
        return base

    def get_defense(self) -> int:
        base = self.base_stats.get("will", 10) // 5
        from items import ALL_ITEMS
        for slot in ("sub", "body", "head", "hands", "feet"):
            eq_id = self.equipment.get(slot)
            if eq_id:
                armor = ALL_ITEMS.get(eq_id, {})
                inst = self.get_equipped_gear_instance(slot)
                base += round(armor.get("defense", 0) * self._quality_stat_multiplier(inst))
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
            logger.warning('player: get_defense title_data 로드 실패', exc_info=True)
        return base
