"""special_npc.py — 특수 NPC 랜덤 인카운터 시스템"""
import random
import datetime
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR
from database import NPC_DATA

# ─── 특수 NPC 목록 ─────────────────────────────────────────────────────────
SPECIAL_NPCS = ["라파엘", "카르니스", "루바토"]

# 라파엘 계약 보상 아이템 풀
RAFAEL_REWARD_ITEMS = [
    "mithril_bar", "diamond", "eye_of_truth", "moonlight_dew",
    "gold_bar", "mp_crystal", "mana_herb",
]

# ─── 인카운터 확률 계산 ────────────────────────────────────────────────────
def get_encounter_chance(last_encounter_ts: float | None) -> float:
    """
    마지막 인카운터로부터 경과 시간에 따라 인카운터 확률을 반환합니다.
    - 0일: 2%
    - 1일: 8%
    - 2일: 20%
    - 3일+: 100% (확정)
    """
    if last_encounter_ts is None:
        return 0.20  # 첫 플레이 시 20%

    import time
    elapsed_days = (time.time() - last_encounter_ts) / 86400.0
    if elapsed_days >= 3.0:
        return 1.0
    elif elapsed_days >= 2.0:
        return 0.20
    elif elapsed_days >= 1.0:
        return 0.08
    else:
        return 0.02


def should_trigger_encounter(player) -> bool:
    """인카운터 발동 여부를 확률에 따라 결정합니다."""
    last_ts = getattr(player, "last_special_encounter", None)
    chance = get_encounter_chance(last_ts)
    return random.random() < chance


# ─── 인카운터 메시지 ───────────────────────────────────────────────────────
ENCOUNTER_INTROS = {
    "라파엘": [
        (
            "⚡ **불길한 기운이 스쳐간다!**\n\n"
            "어딘가 너무 완벽하게 잘생긴 인간이 허공에서 천천히 걸어 나왔다. "
            "짙은 적갈색 머리카락, 날카롭게 빛나는 눈, 완벽히 재단된 외투. "
            "보는 것만으로도 무언가 거래를 맺고 싶어지는 묘한 끌림이 있다.\n"
            "\"오, 마침 찾고 있었어. 흥미로운 제안이 있는데... 거절하기 아깝지 않겠어?\"\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔴 **라파엘**이 나타났습니다!\n"
            "`/대화 라파엘` — 대화하기\n"
            "`/특수키워드 라파엘 [키워드]` — 키워드 대화\n"
            "`/선물 라파엘 [아이템]` — 선물\n"
            "`/계약확인` — 현재 계약 확인"
        ),
    ],
    "카르니스": [
        (
            "🕷️ **어둠이 형체를 이루는 순간이 있다면, 바로 지금이다.**\n\n"
            "인간의 상반신과 거대한 거미의 하반신 — 여덟 개의 눈이 어둠 속에서 냉랭하게 빛난다. "
            "그것은 소리도, 온기도 없이 그저 거기 존재했다. 마치 처음부터 어둠의 일부였던 것처럼.\n"
            "\"...또 왔군. 하등한 미물이 어슬렁거리는 꼴이 눈에 거슬린다.\"\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🕷️ **카르니스**가 나타났습니다!\n"
            "`/대화 카르니스` — 대화하기\n"
            "`/특수키워드 카르니스 [키워드]` — 키워드 대화\n"
            "`/선물 카르니스 [아이템]` — 선물"
        ),
    ],
    "루바토": [
        (
            "🎵 **어디선가 류트 소리가 들려온다...**\n\n"
            "당근색 뿔과 갈색 망토를 두른 티플링이 나타나 흥겹게 류트를 튕기고 있었다.\n"
            "\"야호~ 오늘도 만났네! 세상 좁다고 하더니, 정말 그렇구나!\"\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎵 **루바토**가 나타났습니다!\n"
            "`/대화 루바토` — 대화하기\n"
            "`/특수키워드 루바토 [키워드]` — 키워드 대화\n"
            "`/선물 루바토 [아이템]` — 선물\n"
            "`/루바토버프` — 루바토의 노래 버프 받기"
        ),
    ],
}

DEPARTURE_MESSAGES = {
    "라파엘": "\"바쁘군. 그럼 이만... 하지만 거래는 언제든 열려 있다는 걸 잊지 마.\" *사라진다*",
    "카르니스": "\"꺼져라. 다시 눈앞에 얼씬거리지 마.\" *어둠 속으로 사라진다*",
    "루바토": "\"어이, 벌써 가버려? 뭐, 다음에 또 보자고!\" *손을 흔들며 사라진다*",
}


class SpecialNPCEncounterManager:
    """특수 NPC 인카운터를 관리하는 클래스."""

    def __init__(self, player):
        self.player = player

    def get_active_encounter(self) -> str | None:
        """현재 활성 인카운터 NPC 이름 반환."""
        return getattr(self.player, "active_encounter", None)

    def set_active_encounter(self, npc_name: str | None):
        """활성 인카운터 NPC 설정."""
        self.player.active_encounter = npc_name

    def clear_encounter(self, reason: str = "departure") -> str | None:
        """인카운터 종료 및 퇴장 메시지 반환."""
        current = self.get_active_encounter()
        if not current:
            return None
        self.set_active_encounter(None)
        msg = DEPARTURE_MESSAGES.get(current, f"{current}(이)가 사라졌습니다.")
        if reason == "departure":
            return ansi(f"  {C.DARK}💨 {msg}{C.R}")
        return None

    def trigger_encounter(self) -> str | None:
        """
        인카운터 발동. 특수 NPC 중 랜덤 1명을 선택하여
        등장 연출 메시지를 반환합니다. 인카운터가 발동되지 않으면 None 반환.
        """
        import time
        if not should_trigger_encounter(self.player):
            return None

        # 현재 이미 인카운터 중이면 중복 발동 안 함
        if self.get_active_encounter():
            return None

        npc_name = random.choice(SPECIAL_NPCS)
        self.set_active_encounter(npc_name)
        self.player.last_special_encounter = time.time()

        intros = ENCOUNTER_INTROS.get(npc_name, [f"**{npc_name}**이(가) 나타났습니다!"])
        return random.choice(intros)

    # ── 라파엘 계약 시스템 ─────────────────────────────────────────────────

    def get_rafael_contract(self) -> dict | None:
        """현재 라파엘 계약 데이터 반환."""
        return getattr(self.player, "rafael_contract", None)

    def propose_contract(self) -> str:
        """
        라파엘이 새로운 계약을 제안합니다.
        현재 존재하는 몬스터 중 랜덤으로 계약 대상을 선택합니다.
        """
        from monsters_db import MONSTERS_DB
        if not MONSTERS_DB:
            return ansi(f"  {C.RED}✖ 계약 대상 몬스터가 없슴미댜.{C.R}")

        monster_id = random.choice(list(MONSTERS_DB.keys()))
        monster = MONSTERS_DB[monster_id]
        count = random.randint(3, 10)
        reward_gold = count * random.randint(80, 200)
        reward_exp = count * random.randint(20, 60)
        reward_item = random.choice(RAFAEL_REWARD_ITEMS)

        contract = {
            "monster_id":   monster_id,
            "monster_name": monster.get("name", monster_id),
            "target_count": count,
            "killed":       0,
            "reward_gold":  reward_gold,
            "reward_exp":   reward_exp,
            "reward_item":  reward_item,
            "active":       True,
        }
        self.player.rafael_contract = contract

        from items import ALL_ITEMS
        reward_item_name = ALL_ITEMS.get(reward_item, {}).get("name", reward_item)

        lines = [
            header_box("📜 라파엘의 계약"),
            f"  {C.WHITE}\"흥미롭군. 마침 내가 원하는 게 있어.{C.R}",
            f"  {C.WHITE} 이 계약, 어때? 완수하면 충분히 보상해주지.\"",
            divider(),
            f"  {C.GOLD}🎯 목표{C.R}: {monster['name']} {count}마리 처치",
            f"  {C.GREEN}💎 보상{C.R}: {reward_gold:,}G + EXP {reward_exp:,} + {reward_item_name}",
            divider(),
            f"  {C.DARK}/계약수락 — 계약 수락{C.R}",
            f"  {C.DARK}/계약거절 — 계약 거절{C.R}",
        ]
        return ansi("\n".join(lines))

    def accept_contract(self) -> str:
        """계약 수락."""
        contract = self.get_rafael_contract()
        if not contract:
            return ansi(f"  {C.RED}✖ 현재 제안된 계약이 없슴미댜.{C.R}")
        if contract.get("active") and contract.get("killed", 0) > 0:
            return ansi(f"  {C.RED}✖ 이미 진행 중인 계약이 있슴미댜.{C.R}")
        contract["active"] = True
        return ansi(
            f"  {C.GREEN}✔ 계약 수락!{C.R}\n"
            f"  {C.WHITE}\"현명한 선택이야. 기대하고 있겠어.\" — 라파엘{C.R}\n"
            f"  {C.GOLD}목표: {contract['monster_name']} {contract['target_count']}마리 처치{C.R}"
        )

    def reject_contract(self) -> str:
        """계약 거절."""
        self.player.rafael_contract = None
        return ansi(
            f"  {C.DARK}\"...아직 준비가 안 됐군. 뭐, 다음 기회에.\" — 라파엘이 비웃으며 사라진다.{C.R}"
        )

    def check_contract_status(self) -> str:
        """계약 진행 상황 확인."""
        contract = self.get_rafael_contract()
        if not contract or not contract.get("active"):
            return ansi(f"  {C.DARK}현재 진행 중인 라파엘 계약이 없슴미댜.{C.R}")

        from items import ALL_ITEMS
        reward_item_name = ALL_ITEMS.get(contract["reward_item"], {}).get("name", contract["reward_item"])
        killed = contract.get("killed", 0)
        target = contract.get("target_count", 1)

        lines = [
            header_box("📜 라파엘 계약 현황"),
            f"  {C.GOLD}🎯 목표{C.R}: {contract['monster_name']} 처치",
            f"  {C.WHITE}진행{C.R}: {killed} / {target} 마리",
            f"  {C.GREEN}💎 보상{C.R}: {contract['reward_gold']:,}G + EXP {contract['reward_exp']:,} + {reward_item_name}",
        ]
        if killed >= target:
            lines.append(f"  {C.GREEN}✔ 완료! /계약완료 명령어로 보상을 받으셰요!{C.R}")
        return ansi("\n".join(lines))

    def record_kill(self, monster_id: str) -> str | None:
        """
        몬스터 처치 시 계약 진행도 업데이트.
        계약 완료 시 보상 메시지 반환, 아니면 None.
        """
        contract = self.get_rafael_contract()
        if not contract or not contract.get("active"):
            return None
        if contract.get("monster_id") != monster_id:
            return None

        contract["killed"] = contract.get("killed", 0) + 1
        if contract["killed"] >= contract.get("target_count", 1):
            return ansi(
                f"  {C.GOLD}✦ 라파엘 계약 달성! /계약완료 로 보상을 받으셰요!{C.R}"
            )
        remaining = contract["target_count"] - contract["killed"]
        return ansi(
            f"  {C.DARK}📜 계약 진행: {contract['killed']}/{contract['target_count']} "
            f"({remaining}마리 남음){C.R}"
        )

    def complete_contract(self) -> str:
        """계약 완료 처리 및 보상 지급."""
        contract = self.get_rafael_contract()
        if not contract or not contract.get("active"):
            return ansi(f"  {C.RED}✖ 진행 중인 계약이 없슴미댜.{C.R}")
        if contract.get("killed", 0) < contract.get("target_count", 1):
            remaining = contract["target_count"] - contract["killed"]
            return ansi(
                f"  {C.RED}✖ 아직 완료되지 않았슴미댜! "
                f"({contract['monster_name']} {remaining}마리 남음){C.R}"
            )

        # 보상 지급
        self.player.gold += contract["reward_gold"]
        self.player.exp = getattr(self.player, "exp", 0.0) + contract["reward_exp"]
        from items import ALL_ITEMS
        item_id = contract["reward_item"]
        item_name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
        self.player.add_item(item_id, 1)

        # 계약 초기화
        self.player.rafael_contract = None

        lines = [
            header_box("🎉 계약 완료!"),
            f"  {C.WHITE}\"훌륭해. 역시 흥미로운 존재야, 당신은.\"{C.R}",
            f"  {C.DARK}라파엘이 만족스러운 미소를 지으며 보상을 건넨다.{C.R}",
            divider(),
            f"  {C.GOLD}+{contract['reward_gold']:,}G{C.R}",
            f"  {C.GREEN}EXP +{contract['reward_exp']:,}{C.R}",
            f"  {C.WHITE}🎁 {item_name} x1{C.R}",
        ]
        return ansi("\n".join(lines))

    # ── 루바토 버프 시스템 ──────────────────────────────────────────────────

    def apply_lubato_buff(self) -> str:
        """루바토의 노래 버프 적용 (일시적 HP/MP 회복)."""
        if self.get_active_encounter() != "루바토":
            return ansi(f"  {C.RED}✖ 루바토가 근처에 없슴미댜.{C.R}")

        heal_hp = int(self.player.max_hp * 0.2)
        heal_mp = int(self.player.max_mp * 0.2)
        self.player.hp = min(self.player.hp + heal_hp, self.player.max_hp)
        self.player.mp = min(self.player.mp + heal_mp, self.player.max_mp)

        songs = [
            "♪ 길을 잃어도 괜찮아, 빛은 언제나 있으니 ♪",
            "♫ 상처는 흔적이 되고, 흔적은 용기가 돼 ♫",
            "♪ 오늘도 살아있으니, 그걸로 충분해 ♪",
        ]
        song = random.choice(songs)

        lines = [
            header_box("🎵 루바토의 노래"),
            f"  {C.WHITE}\"{song}\"{C.R}",
            divider(),
            f"  {C.GREEN}HP +{heal_hp} (→ {self.player.hp}/{self.player.max_hp}){C.R}",
            f"  {C.BLUE if hasattr(C, 'BLUE') else C.WHITE}MP +{heal_mp} (→ {self.player.mp}/{self.player.max_mp}){C.R}",
        ]
        return ansi("\n".join(lines))
