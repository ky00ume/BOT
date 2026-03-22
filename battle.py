import random
import io
import discord
from bg3_renderer import get_renderer
from monsters_db import MONSTERS_DB, MONSTER_SIZES, roll_monster_size, apply_size_to_monster


def _bar_text(current, max_val, width=10):
    current = max(0, current)
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _calc_battle_grade(player_hp: int, player_max_hp: int) -> str:
    """남은 HP 비율에 따라 4단계 전투 등급 반환"""
    if player_hp <= 0:
        return "실패"
    ratio = player_hp / max(1, player_max_hp)
    if ratio < 0.15:
        return "아슬아슬"
    elif ratio <= 0.60:
        return "안정"
    else:
        return "완벽"


class BattleEngine:
    def __init__(self, player, npc_manager=None):
        self.player      = player
        self.npc_manager = npc_manager
        self.in_battle   = False
        self.current_zone    = None
        self.current_monster = None
        self.monster_hp      = 0
        self.turn            = 0
        self.cheer_count     = 0   # 응원 사용 횟수 (최대 3회)
        self._cheer_active   = False  # 이번 턴 응원 활성화 여부
        self._last_size      = "M"
        self._last_grade     = None  # 마지막 전투 결과 등급

    def build_battle_image(self, action_name: str = "",
                           dmg: int = 0, is_crit: bool = False) -> io.BytesIO:
        """현재 전투 상태를 BG3 스타일 이미지로 반환"""
        if not self.in_battle or not self.current_monster:
            return None
        from monsters_db import MONSTER_SIZES
        size_label = ""
        if hasattr(self, '_last_size'):
            si = MONSTER_SIZES.get(self._last_size, {})
            size_label = f"{si.get('icon','')} [{self._last_size}]"
        return get_renderer().render_battle_card(
            monster_name=self.current_monster.get("name","?"),
            monster_level=self.current_monster.get("level",1),
            monster_hp=max(0,self.monster_hp),
            monster_max_hp=self.current_monster.get("hp",1),
            danger=self.current_monster.get("danger","보통"),
            turn=self.turn,
            player_hp=self.player.hp,
            player_max_hp=self.player.max_hp,
            player_mp=self.player.mp,
            player_max_mp=self.player.max_mp,
            last_action=action_name,
            last_dmg=dmg,
            is_crit=is_crit,
            size_label=size_label,
        )

    @property
    def zone_list(self):
        return list(MONSTERS_DB.keys())

    def enter_zone(self, zone_name: str) -> str:
        zone = MONSTERS_DB.get(zone_name)
        if not zone:
            return f"[{zone_name}]은(는) 존재하지 않는 사냥터임미댜!"

        level_min, level_max = zone["level_range"]
        if self.player.level < level_min:
            return (
                f"[{zone_name}] 입장에는 Lv.{level_min} 이상이 필요함미댜!\n"
                f"현재 레벨: Lv.{self.player.level}"
            )

        self.current_zone = zone_name
        return (
            f"{zone['name']}에 입장했슴미댜!\n"
            f"{zone.get('desc', '')} (Lv.{level_min}~{level_max})\n"
            f"/사냥 {zone_name} 으로 전투를 시작하셰요!"
        )

    def start_encounter(self, zone_name: str = None) -> tuple:
        """전투 시작. (성공여부, image_buf_or_error_str) 반환."""
        zone_key = zone_name or self.current_zone
        zone = MONSTERS_DB.get(zone_key)
        if not zone:
            return False, "사냥터를 먼저 선택하셰요! (`/사냥터`)"

        from database import HUNTING_GROUNDS
        ground = HUNTING_GROUNDS.get(zone_key, {})
        energy_cost = ground.get("energy_cost", 5)

        if not self.player.consume_energy(energy_cost):
            return False, (
                f"기력이 부족함미댜!\n"
                f"현재 기력: {self.player.energy}/{self.player.max_energy}\n"
                f"필요 기력: {energy_cost}"
            )

        monster_base = random.choice(zone["monsters"])
        size         = roll_monster_size()
        monster_data = apply_size_to_monster(monster_base, size)
        self.current_monster = monster_data
        self.monster_hp      = monster_data["hp"]
        self.in_battle       = True
        self.current_zone    = zone_key
        self.turn            = 1
        self._last_size      = size
        self.cheer_count     = 0
        self._cheer_active   = False
        self._last_grade     = None

        size_info  = MONSTER_SIZES[size]
        size_label = f"{size_info['icon']} [{size}]"

        buf = get_renderer().render_battle_card(
            monster_name=monster_data["name"],
            monster_level=monster_data["level"],
            monster_hp=self.monster_hp,
            monster_max_hp=monster_data["hp"],
            danger=monster_data.get("danger", "보통"),
            turn=self.turn,
            player_hp=self.player.hp,
            player_max_hp=self.player.max_hp,
            player_mp=self.player.mp,
            player_max_mp=self.player.max_mp,
            last_action="전투 시작!",
            last_dmg=0,
            is_crit=False,
            size_label=size_label,
        )
        return True, buf

    def use_cheer(self) -> str:
        """응원 사용. 이번 턴 공격력 15% 상승. 최대 3회."""
        if not self.in_battle:
            return "현재 전투 중이 아님미댜!"
        if self.cheer_count >= 3:
            return "이번 전투에서 응원을 모두 사용했슴미댜! (최대 3회)"
        self.cheer_count += 1
        self._cheer_active = True
        from battle_log_data import CHEER_RESPONSE_LOGS
        return random.choice(CHEER_RESPONSE_LOGS) + f" (남은 응원: {3 - self.cheer_count}회)"

    def _get_condition_modifiers(self) -> dict:
        """돌봄 상태(컨디션/안정감/피로도)에 따른 전투 보정값 반환"""
        mods = {
            "atk_mult":    1.0,
            "def_mult":    1.0,
            "crit_bonus":  0.0,
            "flee_bonus":  0.0,
            "miss_chance": 0.0,
        }
        player = self.player
        cond      = getattr(player, "condition",  50)
        stability = getattr(player, "stability",  50)
        fatigue   = getattr(player, "fatigue",     0)

        # 컨디션 보정
        if cond >= 50:
            bonus = 0.05 + (cond - 50) / 50 * 0.05  # 50~100 → +5%~+10%
            mods["atk_mult"] += bonus
            mods["def_mult"] += bonus
        elif cond <= 30:
            mods["atk_mult"] -= 0.10
            mods["def_mult"] -= 0.10

        # 안정감 보정
        if stability >= 60:
            mods["crit_bonus"] += 0.05
        elif stability <= 20:
            mods["flee_bonus"] -= 0.15

        # 피로도 보정
        if fatigue >= 80:
            mods["atk_mult"] -= 0.15
            mods["miss_chance"] += 0.15
        elif fatigue >= 50:
            mods["atk_mult"] -= 0.10

        return mods

    def process_turn(self, skill_id: str = "smash") -> io.BytesIO:
        if not self.in_battle or not self.current_monster:
            return get_renderer().render_card(
                title="⚔ 전투 오류",
                rows=[{"label": "상태", "value": "현재 전투 중이 아님미댜!"}],
                system_key="battle",
                footer="전투 시스템",
            )

        player  = self.player
        monster = self.current_monster

        # 돌봄 상태 보정
        mods = self._get_condition_modifiers()

        # 피로도에 의한 행동 스킵
        if mods["miss_chance"] > 0 and random.random() < mods["miss_chance"]:
            from battle_log_data import MONSTER_ATTACK_LOGS
            mon_atk = monster.get("attack", 5)
            defense = player.get_defense() if hasattr(player, "get_defense") else 0
            mon_def_mult = mods.get("def_mult", 1.0)
            mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - int(defense * mon_def_mult))
            player.hp -= mon_dmg
            player.hp  = max(0, player.hp)
            self.turn += 1

            if player.hp <= 0:
                self.in_battle  = False
                self._last_grade = "실패"
                return get_renderer().render_card(
                    title="💀 전투 패배...",
                    rows=[
                        {"label": "행동", "value": "피로로 인해 행동을 할 수 없었다!"},
                        {"label": "반격", "value": f"{monster['name']}의 반격! -{mon_dmg} HP"},
                        {"label": "결과", "value": "쓰러졌슴미댜... HP를 회복하고 다시 도전하셰요!"},
                    ],
                    system_key="battle",
                    footer="전투 시스템",
                )

            return get_renderer().render_battle_card(
                monster_name=monster["name"],
                monster_level=monster.get("level", 1),
                monster_hp=max(0, self.monster_hp),
                monster_max_hp=monster["hp"],
                danger=monster.get("danger", "보통"),
                turn=self.turn,
                player_hp=player.hp,
                player_max_hp=player.max_hp,
                player_mp=player.mp,
                player_max_mp=player.max_mp,
                last_action=f"피로로 행동 불가! {monster['name']}의 반격 -{mon_dmg}HP",
                last_dmg=0,
                is_crit=False,
                size_label=getattr(self, '_last_size_label', ''),
            )

        # 플레이어 공격
        base_atk = player.get_attack() if hasattr(player, "get_attack") else 10
        base_atk = int(base_atk * mods["atk_mult"])

        # 응원 보너스
        if self._cheer_active:
            base_atk = int(base_atk * 1.15)
            self._cheer_active = False

        crit_chance = player.base_stats.get("luck", 5) * 0.01 + mods["crit_bonus"]
        crit     = random.random() < crit_chance
        dmg      = int(base_atk * (1.5 if crit else 1.0) * random.uniform(0.85, 1.15))
        dmg      = max(1, dmg - monster.get("defense", 0))

        # 스킬 보너스
        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS
        skill_rank = player.skill_ranks.get(skill_id, "연습")
        skill_name = skill_id
        if skill_id in COMBAT_SKILLS:
            sk         = COMBAT_SKILLS[skill_id]
            skill_name = sk["name"]
            bonus      = sk.get("damage_bonus", {}).get(skill_rank, 1.0)
            dmg        = int(dmg * bonus)
        elif skill_id in MAGIC_SKILLS:
            sk         = MAGIC_SKILLS[skill_id]
            skill_name = sk["name"]
            mp_cost    = sk.get("mp_cost", {}).get(skill_rank, 5)
            if player.mp < mp_cost:
                return get_renderer().render_card(
                    title="⚔ MP 부족",
                    rows=[
                        {"label": "필요 MP", "value": str(mp_cost)},
                        {"label": "보유 MP", "value": str(player.mp)},
                    ],
                    system_key="battle",
                    footer="전투 시스템",
                )
            player.mp  -= mp_cost
            magic_dmg   = sk.get("damage", {}).get(skill_rank, 10)
            magic_atk   = player.base_stats.get("int", 10) // 2
            dmg         = int((magic_dmg + magic_atk) * mods["atk_mult"] * random.uniform(0.85, 1.15))

        # 서사화 로그 선택
        from battle_log_data import (
            PLAYER_ATTACK_LOGS, MONSTER_ATTACK_LOGS,
            PLAYER_CRIT_LOGS, VICTORY_LOGS, DEFEAT_LOGS, GRADE_MULT, GRADE_LABELS,
        )
        atk_pool = PLAYER_ATTACK_LOGS.get(skill_id, PLAYER_ATTACK_LOGS["_default"])
        atk_log  = random.choice(atk_pool).format(monster=monster["name"])
        if crit:
            atk_log = random.choice(PLAYER_CRIT_LOGS) + " " + atk_log

        self.monster_hp -= dmg

        # 스킬 훈련 경험치
        rank_msg = player.train_skill(skill_id, 10.0)

        if self.monster_hp <= 0:
            self.monster_hp = 0
            self.in_battle  = False
            grade = _calc_battle_grade(player.hp, player.max_hp)
            self._last_grade = grade
            reward = self._calc_reward(monster, grade)
            self._add_village_contribution_battle()

            # 라파엘 계약 처치 기록
            contract_msg = ""
            monster_id = monster.get("id", "")
            if monster_id:
                try:
                    from special_npc import SpecialNPCEncounterManager
                    enc_mgr = SpecialNPCEncounterManager(self.player)
                    contract_msg = enc_mgr.record_kill(monster_id)
                except Exception:
                    pass

            size      = monster.get("_size", "M")
            size_info = MONSTER_SIZES.get(size, MONSTER_SIZES["M"])

            grade_label  = GRADE_LABELS.get(grade, grade)
            victory_log  = random.choice(VICTORY_LOGS.get(grade, VICTORY_LOGS["안정"]))

            rows = [
                {"label": "행동", "value": atk_log},
                {"label": "결과 등급", "value": grade_label},
                {"label": "한마디", "value": victory_log},
                {"label": "골드", "value": f"+{reward['gold']}G"},
                {"label": "경험치", "value": f"+{reward['exp']}"},
                {"label": "사이즈", "value": f"{size_info['icon']} {size}"},
            ]

            if contract_msg:
                rows.append({"label": "계약 진행", "value": contract_msg})

            if reward.get("items"):
                from items import ALL_ITEMS
                drop_lines = []
                for item_id, cnt in reward["items"].items():
                    item_name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                    drop_lines.append(f"{item_name} x{cnt}")
                rows.append({"label": "드롭", "value": ", ".join(drop_lines)})

            if reward.get("leveled_up"):
                gains = reward.get("level_gains", {})
                gain_parts = []
                if gains.get("max_hp"):
                    gain_parts.append(f"HP+{gains['max_hp']}")
                if gains.get("max_mp"):
                    gain_parts.append(f"MP+{gains['max_mp']}")
                if gains.get("max_energy"):
                    gain_parts.append(f"EN+{gains['max_energy']}")
                for stat in ("str", "int", "dex", "will", "luck"):
                    if gains.get(stat):
                        stat_names = {"str": "힘", "int": "지력", "dex": "민첩", "will": "의지", "luck": "운"}
                        gain_parts.append(f"{stat_names[stat]}+{gains[stat]}")
                rows.append({
                    "label": "레벨 업!",
                    "value": f"Lv.{reward['old_level']}→Lv.{reward['new_level']}  {' '.join(gain_parts)}"
                })

            footer = rank_msg if rank_msg else "전투 시스템"
            return get_renderer().render_card(
                title="🎉 전투 승리!",
                rows=rows,
                system_key="battle",
                footer=footer,
                h=max(380, 160 + len(rows) * 34),
            )

        # 몬스터 반격
        mon_atk = monster.get("attack", 5)
        defense = player.get_defense() if hasattr(player, "get_defense") else 0
        defense = int(defense * mods["def_mult"])
        mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - defense)

        # 몬스터 공격 서사화 로그
        mon_pool = MONSTER_ATTACK_LOGS.get(monster["name"], MONSTER_ATTACK_LOGS["_default"])
        mon_log  = random.choice(mon_pool).format(monster=monster["name"])

        player.hp -= mon_dmg
        player.hp  = max(0, player.hp)

        if player.hp <= 0:
            self.in_battle  = False
            self._last_grade = "실패"
            defeat_log = random.choice(DEFEAT_LOGS)
            rows = [
                {"label": "행동", "value": atk_log},
                {"label": "반격", "value": f"{mon_log} -{mon_dmg} HP"},
                {"label": "결과", "value": defeat_log},
            ]
            footer = rank_msg if rank_msg else "전투 시스템"
            return get_renderer().render_card(
                title="💀 전투 패배...",
                rows=rows,
                system_key="battle",
                footer=footer,
            )

        # 전투 계속 — 전투 카드 이미지
        self.turn += 1
        size_info = MONSTER_SIZES.get(self._last_size, MONSTER_SIZES["M"])
        size_label = f"{size_info['icon']} [{self._last_size}]"
        action_text = (
            f"{'💥크리티컬! ' if crit else ''}{atk_log}  →  {dmg} 피해\n"
            f"{mon_log}  →  -{mon_dmg}HP"
        )
        buf = get_renderer().render_battle_card(
            monster_name=monster["name"],
            monster_level=monster.get("level", 1),
            monster_hp=max(0, self.monster_hp),
            monster_max_hp=monster["hp"],
            danger=monster.get("danger", "보통"),
            turn=self.turn,
            player_hp=player.hp,
            player_max_hp=player.max_hp,
            player_mp=player.mp,
            player_max_mp=player.max_mp,
            last_action=action_text,
            last_dmg=dmg,
            is_crit=crit,
            size_label=size_label,
        )
        return buf

    def flee(self) -> io.BytesIO:
        if not self.in_battle:
            return get_renderer().render_card(
                title="⚔ 오류",
                rows=[{"label": "상태", "value": "현재 전투 중이 아님미댜!"}],
                system_key="battle",
                footer="전투 시스템",
            )
        # 안정감이 낮으면 도주 확률 감소
        mods = self._get_condition_modifiers()
        flee_rate = 0.6 + mods.get("flee_bonus", 0.0)
        flee_rate = max(0.1, min(0.95, flee_rate))
        success = random.random() < flee_rate
        self.in_battle = False
        if success:
            return get_renderer().render_card(
                title="🏃 도주 성공!",
                rows=[{"label": "결과", "value": "성공적으로 도망쳤슴미댜~"}],
                system_key="battle",
                grade="Normal",
                footer="전투 시스템",
            )
        else:
            monster = self.current_monster
            mon_atk = monster.get("attack", 5) if monster else 5
            dmg     = max(1, int(mon_atk * 0.5))
            self.player.hp -= dmg
            self.player.hp  = max(0, self.player.hp)
            mon_name = monster['name'] if monster else '몬스터'
            return get_renderer().render_card(
                title="🏃 도주 실패!",
                rows=[
                    {"label": "피해", "value": f"{mon_name}에게 {dmg} 피해를 입음"},
                    {"label": "결과", "value": "겨우 도망쳤슴미댜..."},
                    {"label": "남은 HP", "value": f"{self.player.hp}/{self.player.max_hp}"},
                ],
                system_key="battle",
                footer="전투 시스템",
            )

    def auto_battle(self, skill_id: str = "smash") -> tuple:
        """
        전투가 끝날 때까지 자동으로 턴을 진행하고 전체 로그 + 최종 결과 반환.
        Returns: (log_lines: list[str], final_result: io.BytesIO)
        """
        if not self.in_battle:
            result_card = get_renderer().render_card(
                title="⚔ 오류",
                rows=[{"label": "상태", "value": "현재 전투 중이 아님미댜!"}],
                system_key="battle",
                footer="전투 시스템",
            )
            return [], result_card

        log_lines = []
        final_result = None
        max_turns = 50  # 무한 루프 방지

        while self.in_battle and max_turns > 0:
            max_turns -= 1
            # 이벤트 처리 (자동: 첫 번째 선택지)
            from battle_event_data import BATTLE_EVENTS
            if random.random() < 0.20:
                event = random.choice(BATTLE_EVENTS)
                choice = event["choices"][0]
                log_lines.append(f"⚡ **[이벤트]** {event['desc']}")
                log_lines.append(f"→ {choice['result_text']}")
                self._apply_event_effect(choice["effect"])

            result = self.process_turn(skill_id)
            # process_turn이 BytesIO(render_battle_card)나 render_card를 반환
            if not self.in_battle:
                final_result = result
            else:
                log_lines.append(f"턴 {self.turn - 1}: {skill_id} 공격")

        if final_result is None:
            final_result = get_renderer().render_card(
                title="⚔ Auto 전투 종료",
                rows=[{"label": "상태", "value": "전투가 종료됐슴미댜!"}],
                system_key="battle",
                footer="전투 시스템",
            )
        return log_lines, final_result

    def _apply_event_effect(self, effect: dict):
        """전투 이벤트 효과 적용 (즉시 적용 가능한 것만)"""
        player = self.player
        monster = self.current_monster

        if "heal_hp" in effect:
            player.hp = min(player.max_hp, player.hp + effect["heal_hp"])
        if "heal_mp" in effect:
            player.mp = min(player.max_mp, player.mp + effect["heal_mp"])
        if "take_damage" in effect:
            player.hp = max(0, player.hp - effect["take_damage"])
        if "mp_cost" in effect:
            player.mp = max(0, player.mp - effect["mp_cost"])
        if "item_find" in effect and effect["item_find"]:
            # 랜덤 아이템 드랍 (소모품 중 하나)
            from items import ALL_ITEMS
            candidates = [iid for iid, idata in ALL_ITEMS.items()
                          if idata.get("type") in ("consumable", "material")]
            if candidates:
                player.add_item(random.choice(candidates))

    def _calc_reward(self, monster: dict, grade: str = "안정") -> dict:
        from battle_log_data import GRADE_MULT
        mult = GRADE_MULT.get(grade, 1.0)

        if mult == 0:
            # 실패: 보상 없음
            return {
                "gold": 0, "exp": 0, "items": {},
                "leveled_up": False, "level_gains": {},
                "old_level": self.player.level, "new_level": self.player.level,
            }

        gold_range = monster.get("gold", (1, 5))
        gold       = int(random.randint(*gold_range) * mult)
        exp        = int(monster.get("exp", 1) * mult)
        self.player.gold += gold
        self.player.exp   = getattr(self.player, "exp", 0.0) + exp

        drops = {}
        for drop in monster.get("drops", []):
            drop_rate = drop["rate"] * mult
            if random.random() < drop_rate:
                item_id = drop["item"]
                if self.player.add_item(item_id):
                    drops[item_id] = drops.get(item_id, 0) + 1

        # 레벨업 체크
        leveled_up  = False
        level_gains = {}
        old_level   = self.player.level
        level_thresh = self.player.level * 100
        if self.player.exp >= level_thresh:
            self.player.exp   -= level_thresh
            self.player.level += 1
            from player import apply_level_up
            level_gains = apply_level_up(self.player)
            leveled_up  = True

        return {
            "gold":        gold,
            "exp":         exp,
            "items":       drops,
            "leveled_up":  leveled_up,
            "level_gains": level_gains,
            "old_level":   old_level,
            "new_level":   self.player.level,
        }

    def _add_village_contribution_battle(self):
        try:
            from village import village_manager
            village_manager.add_contribution(3, "battle")
        except Exception:
            pass

