from __future__ import annotations

import random
import io
from typing import Optional, Dict, List, Tuple, Any, TYPE_CHECKING
import discord
from bg3_renderer import get_renderer
from monsters_db import MONSTERS_DB, MONSTER_SIZES, roll_monster_size, apply_size_to_monster
from utils.logger import setup_logger
from core.sound_director import sound_director

if TYPE_CHECKING:
    from player import Player

logger = setup_logger('battle')

# E-6: 오토 전투 포션 자동 사용 HP 비율 임계값
AUTO_POTION_HP_THRESHOLD = 0.4


def _bar_text(current: int, max_val: int, width: int = 10) -> str:
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
    def __init__(self, player: Player, npc_manager: Optional[Any] = None) -> None:
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
        self.enemies         = []    # 복수 적 전투용 [{monster,hp,statuses,size}]
        self.defeated_enemies = []

    def _alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy.get("hp", 0) > 0]

    def _sync_primary_enemy(self) -> None:
        alive = self._alive_enemies()
        if not alive:
            return
        primary = alive[0]
        self.current_monster = primary["monster"]
        self.monster_hp = primary["hp"]
        self._last_size = primary.get("size", primary["monster"].get("_size", "M"))

    def _group_display_name(self) -> str:
        alive = self._alive_enemies()
        if not alive:
            return self.current_monster.get("name", "?") if self.current_monster else "?"
        name = alive[0]["monster"].get("name", "?")
        return f"{name} 외 {len(alive)-1}체" if len(alive) > 1 else name

    def _enemy_status_text(self) -> str:
        parts = []
        for enemy in self._alive_enemies():
            statuses = enemy.get("statuses", {})
            icons = []
            if statuses.get("slow", 0) > 0:
                icons.append(f"❄️둔화{statuses['slow']}")
            burn = statuses.get("burn")
            if burn and burn.get("turns", 0) > 0:
                icons.append(f"🔥화상{burn['turns']}")
            if icons:
                parts.append(f"{enemy['monster']['name']}({' '.join(icons)})")
        return " · ".join(parts)

    def _apply_status_ticks(self) -> list[str]:
        logs = []
        for enemy in self._alive_enemies():
            burn = enemy.setdefault("statuses", {}).get("burn")
            if burn and burn.get("turns", 0) > 0:
                tick = max(1, int(burn.get("damage", 1)))
                enemy["hp"] = max(0, enemy["hp"] - tick)
                burn["turns"] -= 1
                logs.append(f"🔥 {enemy['monster']['name']} 화상 -{tick}")
                if burn["turns"] <= 0:
                    enemy["statuses"].pop("burn", None)
        return logs

    def _register_newly_defeated(self) -> list[dict]:
        newly = []
        known = {id(enemy) for enemy in self.defeated_enemies}
        for enemy in self.enemies:
            if enemy.get("hp", 0) <= 0 and id(enemy) not in known:
                self.defeated_enemies.append(enemy)
                newly.append(enemy)
        return newly

    def _enemy_attack_phase(self, mods: dict, *, skip_enemy=None, counter=False) -> tuple[int, list[str]]:
        total = 0
        logs = []
        player = self.player
        defense = int((player.get_defense() if hasattr(player, "get_defense") else 0) * mods.get("def_mult", 1.0))
        for enemy in self._alive_enemies():
            if skip_enemy is enemy:
                logs.append(f"⚡ {enemy['monster']['name']}은(는) 빠른 시전에 반격하지 못했다")
                continue
            monster = enemy["monster"]
            statuses = enemy.setdefault("statuses", {})
            slow_mult = 0.65 if statuses.get("slow", 0) > 0 else 1.0
            mon_atk = int(monster.get("attack", 5) * slow_mult)
            mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - defense)
            if counter:
                mon_dmg = max(1, int(mon_dmg * 0.75))
            player.hp = max(0, player.hp - mon_dmg)
            total += mon_dmg
            slow_note = " (둔화)" if slow_mult < 1.0 else ""
            logs.append(f"{monster['name']}{slow_note} -{mon_dmg}HP")
            if statuses.get("slow", 0) > 0:
                statuses["slow"] -= 1
                if statuses["slow"] <= 0:
                    statuses.pop("slow", None)
            if player.hp <= 0:
                break
        if total:
            sound_director.cue("battle/enemy_hit")
        return total, logs

    def _finalize_group_victory(self, last_action: str, rank_msg: str = ""):
        from battle_log_data import GRADE_LABELS, VICTORY_LOGS
        grade = _calc_battle_grade(self.player.hp, self.player.max_hp)
        self._last_grade = grade
        self.in_battle = False
        sound_director.cue("battle/victory", interrupt=True)
        total_gold = 0
        total_exp = 0
        total_items = {}
        contracts = []
        leveled = False
        level_gains = {}
        old_level = self.player.level
        for enemy in self.defeated_enemies:
            monster = enemy["monster"]
            reward = self._calc_reward(monster, grade)
            total_gold += reward.get("gold", 0)
            total_exp += reward.get("exp", 0)
            leveled = leveled or reward.get("leveled_up", False)
            for key, value in reward.get("level_gains", {}).items():
                level_gains[key] = level_gains.get(key, 0) + value
            for item_id, cnt in reward.get("items", {}).items():
                total_items[item_id] = total_items.get(item_id, 0) + cnt
            monster_id = monster.get("id", "")
            if monster_id:
                try:
                    from collection import collection_manager
                    is_new, _ = collection_manager.register("몬스터", monster_id, monster.get("name", monster_id), monster.get("_size", "M"))
                    if is_new:
                        collection_manager.apply_all_bonuses(self.player, "몬스터")
                except Exception:
                    logger.warning('battle: 몬스터 도감 등록 실패', exc_info=True)
                try:
                    from special_npc import SpecialNPCEncounterManager
                    msg = SpecialNPCEncounterManager(self.player).record_kill(monster_id)
                    if msg:
                        contracts.append(msg)
                except Exception:
                    logger.warning('battle: group contract kill record failed', exc_info=True)
        try:
            from skill_training import record_training_event
            record_training_event(self.player, "combat_mastery", "combat_win", 1)
        except Exception:
            logger.warning('battle: group combat mastery win training failed', exc_info=True)
        self._add_village_contribution_battle()
        rows = [
            {"label": "행동", "value": last_action},
            {"label": "격파", "value": f"적 {len(self.defeated_enemies)}체"},
            {"label": "결과 등급", "value": GRADE_LABELS.get(grade, grade)},
            {"label": "한마디", "value": random.choice(VICTORY_LOGS.get(grade, VICTORY_LOGS["안정"]))},
            {"label": "골드", "value": f"+{total_gold}G"},
            {"label": "경험치", "value": f"+{total_exp}"},
        ]
        if total_items:
            from items import ALL_ITEMS
            rows.append({"label": "드롭", "value": ", ".join(f"{ALL_ITEMS.get(i,{}).get('name',i)} x{c}" for i,c in total_items.items())})
        if contracts:
            rows.append({"label": "계약 진행", "value": " / ".join(contracts)})
        if leveled:
            rows.append({"label": "레벨 업!", "value": f"Lv.{old_level}→Lv.{self.player.level}"})
        return get_renderer().render_card(
            title="🎉 전투 승리!" if len(self.defeated_enemies) == 1 else "🎉 다수 전투 승리!",
            rows=rows,
            grade="Legendary",
            system_key="battle_win",
            footer=rank_msg or "전투 시스템",
            h=max(380, 160 + len(rows) * 34),
        )

    def _process_group_turn(self, skill_id: str = "smash"):
        player = self.player
        alive = self._alive_enemies()
        if not alive:
            return self._finalize_group_victory("상태이상으로 마지막 적이 쓰러졌다")
        self._sync_primary_enemy()
        monster = self.current_monster
        mods = self._get_condition_modifiers()
        status_logs = self._apply_status_ticks()
        self._register_newly_defeated()
        if not self._alive_enemies():
            return self._finalize_group_victory(" · ".join(status_logs) or "상태이상으로 적을 쓰러뜨렸다")
        self._sync_primary_enemy()
        monster = self.current_monster
        primary = self._alive_enemies()[0]

        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS, RANK_ORDER
        from skill_training import record_training_event

        # 방어 / 힐링은 공격 대신 한 턴을 사용하고 모든 생존 적이 반응한다.
        if skill_id == "defense":
            rank = player.skill_ranks.get("defense", "연습")
            reduce_rate = COMBAT_SKILLS["defense"]["damage_reduce"].get(rank, 0.05)
            total_before = 0
            total_after = 0
            defense = int((player.get_defense() if hasattr(player, "get_defense") else 0) * mods.get("def_mult", 1.0))
            low_hp_before = player.hp <= max(1, int(player.max_hp * 0.35))
            attack_logs = []
            for enemy in self._alive_enemies():
                mon = enemy["monster"]
                slow_mult = 0.65 if enemy.get("statuses", {}).get("slow", 0) > 0 else 1.0
                raw = max(1, int(mon.get("attack", 5) * slow_mult * random.uniform(0.85, 1.15)) - defense)
                dealt = max(1, int(round(raw * (1.0 - reduce_rate))))
                total_before += raw
                total_after += dealt
                player.hp = max(0, player.hp - dealt)
                attack_logs.append(f"{mon['name']} -{dealt}")
                if enemy.get("statuses", {}).get("slow", 0) > 0:
                    enemy["statuses"]["slow"] -= 1
                if player.hp <= 0:
                    break
            prevented = max(0, total_before - total_after)
            record_training_event(player, "defense", "defense_use", 1)
            if prevented >= max(2, int(total_before * 0.2)):
                record_training_event(player, "defense", "defense_reduce", 1)
            if low_hp_before and player.hp > 0:
                record_training_event(player, "defense", "defense_low_hp", 1)
            record_training_event(player, "combat_mastery", "combat_action", 1)
            rank_msg = player.train_skill("defense", 10.0)
            player.train_skill("combat_mastery", 3.0)
            self.turn += 1
            if player.hp <= 0:
                self.in_battle = False
                self._last_grade = "실패"
            self._sync_primary_enemy()
            return get_renderer().render_battle_card(
                monster_name=self._group_display_name(), monster_level=monster.get("level",1),
                monster_hp=max(0,self.monster_hp), monster_max_hp=monster["hp"], danger=monster.get("danger","보통"),
                turn=self.turn, player_hp=player.hp, player_max_hp=player.max_hp, player_mp=player.mp, player_max_mp=player.max_mp,
                last_action=f"🛡 디펜스! 총 피해 {total_before} → {total_after} (-{prevented})\n" + " · ".join(attack_logs),
                last_dmg=0, is_crit=False, size_label=f"적 {len(self._alive_enemies())}체")

        if skill_id == "healing":
            rank = player.skill_ranks.get("healing", "연습")
            heal_data = RECOVERY_SKILLS["healing"]
            mp_cost = heal_data["mp_cost"].get(rank, 10)
            if player.mp < mp_cost:
                return get_renderer().render_card(title="⚔ MP 부족", rows=[{"label":"필요 MP","value":str(mp_cost)},{"label":"보유 MP","value":str(player.mp)}], system_key="battle", footer="전투 시스템")
            before = player.hp
            low = before <= max(1, int(player.max_hp*0.35))
            player.mp -= mp_cost
            player.hp = min(player.max_hp, player.hp + heal_data["heal_amount"].get(rank,20))
            healed = player.hp-before
            record_training_event(player,"healing","healing_use",1)
            if healed >= max(10,int(player.max_hp*0.2)): record_training_event(player,"healing","healing_big",1)
            if low and healed>0: record_training_event(player,"healing","healing_low_hp",1)
            record_training_event(player,"combat_mastery","combat_action",1)
            rank_msg = player.train_skill("healing",10.0); player.train_skill("combat_mastery",2.0)
            total, logs = self._enemy_attack_phase(mods)
            self.turn += 1
            if player.hp <= 0:
                self.in_battle=False; self._last_grade="실패"
            self._sync_primary_enemy()
            return get_renderer().render_battle_card(monster_name=self._group_display_name(), monster_level=monster.get("level",1), monster_hp=max(0,self.monster_hp), monster_max_hp=monster["hp"], danger=monster.get("danger","보통"), turn=self.turn, player_hp=player.hp, player_max_hp=player.max_hp, player_mp=player.mp, player_max_mp=player.max_mp, last_action=f"💚 힐링 +{healed} HP · 적 반격 총 -{total}HP\n"+" · ".join(logs), last_dmg=0, is_crit=False, size_label=f"적 {len(self._alive_enemies())}체")

        base_atk = int((player.get_attack() if hasattr(player,"get_attack") else 10) * mods["atk_mult"])
        if self._cheer_active:
            base_atk=int(base_atk*1.15); self._cheer_active=False
        crit = random.random() < (player.base_stats.get("luck",5)*0.01 + mods["crit_bonus"])
        skill_rank = player.skill_ranks.get(skill_id,"연습")
        skill_name = skill_id
        mp_cost = 0
        quick_skip = None

        if skill_id in MAGIC_SKILLS:
            sk=MAGIC_SKILLS[skill_id]; skill_name=sk["name"]
            mp_cost=sk["mp_cost"].get(skill_rank,5)
            if player.mp < mp_cost:
                return get_renderer().render_card(title="⚔ MP 부족", rows=[{"label":"필요 MP","value":str(mp_cost)},{"label":"보유 MP","value":str(player.mp)}], system_key="battle", footer="전투 시스템")
            player.mp -= mp_cost
            magic_dmg=sk["damage"].get(skill_rank,10)
            raw_base=int((magic_dmg + player.base_stats.get("int",10)//2)*mods["atk_mult"]*random.uniform(0.85,1.15))
        else:
            raw_base=int(base_atk*(1.5 if crit else 1.0)*random.uniform(0.85,1.15))

        targets = self._alive_enemies() if skill_id=="windmill" else [primary]
        hit_logs=[]; killed=0; total_damage=0
        for enemy in list(targets):
            mon=enemy["monster"]
            if skill_id in MAGIC_SKILLS:
                dmg=max(1, raw_base - mon.get("defense",0)//2)
            else:
                dmg=max(1, raw_base - mon.get("defense",0))
                if skill_id in COMBAT_SKILLS:
                    sk=COMBAT_SKILLS[skill_id]; skill_name=sk["name"]
                    if skill_id=="counter": bonus=sk["counter_multiplier"].get(skill_rank,1.5)
                    elif skill_id=="windmill": bonus=sk["aoe_multiplier"].get(skill_rank,0.8)
                    else: bonus=sk.get("damage_bonus",{}).get(skill_rank,1.0)
                    dmg=max(1,int(dmg*bonus))
            dmg, trait_note = self._apply_monster_traits(mon, dmg, skill_id)
            enemy["hp"] = max(0, enemy["hp"]-dmg)
            total_damage += dmg
            hit_logs.append(f"{mon['name']} {dmg} 피해" + (f" {trait_note}" if trait_note else ""))
            if enemy["hp"]<=0: killed += 1

        # 속성 효과
        status_note=[]
        if skill_id=="icebolt" and primary.get("hp",0)>0:
            primary.setdefault("statuses",{})["slow"] = max(primary.get("statuses",{}).get("slow",0), 2)
            status_note.append("❄️ 둔화 2턴")
        elif skill_id=="firebolt" and primary.get("hp",0)>0:
            burn_dmg=max(2,int(total_damage*0.15))
            primary.setdefault("statuses",{})["burn"]={"turns":2,"damage":burn_dmg}
            status_note.append(f"🔥 화상 2턴({burn_dmg}/턴)")
        elif skill_id=="lightningbolt" and primary.get("hp",0)>0:
            idx=RANK_ORDER.index(skill_rank) if skill_rank in RANK_ORDER else 0
            quick_chance=min(0.65, 0.25 + idx*0.025)
            if random.random() < quick_chance:
                quick_skip=primary
                status_note.append("⚡ 빠른 시전: 대상 반격 차단")

        newly=self._register_newly_defeated()
        self._sync_primary_enemy()
        if skill_id in MAGIC_SKILLS:
            sound_director.cue("battle/magic_crit" if crit else "battle/magic_hit", interrupt=crit)
        else:
            sound_director.cue("battle/crit" if crit else "battle/player_hit", interrupt=crit)

        # 수련
        if skill_id=="smash":
            record_training_event(player,"smash","smash_use",1)
            if crit: record_training_event(player,"smash","smash_crit",1)
            if killed: record_training_event(player,"smash","smash_kill",killed)
        elif skill_id=="counter":
            record_training_event(player,"counter","counter_use",1)
            if monster.get("attack",5)>=max(8,player.get_defense()+5): record_training_event(player,"counter","counter_strong",1)
            if killed: record_training_event(player,"counter","counter_kill",killed)
        elif skill_id=="windmill":
            record_training_event(player,"windmill","windmill_use",1)
            if crit: record_training_event(player,"windmill","windmill_crit",1)
            if len(targets)>=2: record_training_event(player,"windmill","windmill_multi",1)
            if killed: record_training_event(player,"windmill","windmill_kill",killed)
        elif skill_id in MAGIC_SKILLS:
            record_training_event(player,skill_id,"magic_cast",1)
            if crit: record_training_event(player,skill_id,"magic_crit",1)
            if killed: record_training_event(player,skill_id,"magic_kill",killed)
            if skill_id=="icebolt": record_training_event(player,skill_id,"ice_slow",1)
            if skill_id=="firebolt": record_training_event(player,skill_id,"fire_burn",1)
            if skill_id=="lightningbolt" and quick_skip is not None: record_training_event(player,skill_id,"lightning_quick",1)
        record_training_event(player,"combat_mastery","combat_action",1)
        rank_msg=player.train_skill(skill_id,10.0); player.train_skill("combat_mastery",3.0)

        action=f"{'💥크리티컬! ' if crit else ''}{skill_name}: " + " · ".join(hit_logs)
        if status_note: action += "\n" + " · ".join(status_note)
        if status_logs: action += "\n" + " · ".join(status_logs)

        if not self._alive_enemies():
            return self._finalize_group_victory(action, rank_msg)

        total_taken, enemy_logs=self._enemy_attack_phase(mods, skip_enemy=quick_skip, counter=(skill_id=="counter"))
        if player.hp<=0:
            self.in_battle=False; self._last_grade="실패"; sound_director.cue("battle/defeat",interrupt=True)
            return get_renderer().render_card(title="💀 전투 패배...", rows=[{"label":"행동","value":action},{"label":"적의 반격","value":" · ".join(enemy_logs)},{"label":"결과","value":"쓰러졌슴미댜..."}], system_key="battle", footer=rank_msg or "전투 시스템")
        self.turn += 1
        self._sync_primary_enemy()
        status_text=self._enemy_status_text()
        if status_text: action += "\n상태: " + status_text
        action += f"\n적 반격 총 -{total_taken}HP · " + " · ".join(enemy_logs)
        return get_renderer().render_battle_card(monster_name=self._group_display_name(), monster_level=self.current_monster.get("level",1), monster_hp=max(0,self.monster_hp), monster_max_hp=self.current_monster["hp"], danger=self.current_monster.get("danger","보통"), turn=self.turn, player_hp=player.hp, player_max_hp=player.max_hp, player_mp=player.mp, player_max_mp=player.max_mp, last_action=action, last_dmg=total_damage, is_crit=crit, size_label=f"적 {len(self._alive_enemies())}체")

    def build_battle_image(self, action_name: str = "",
                           dmg: int = 0, is_crit: bool = False) -> io.BytesIO:
        """현재 전투 상태를 BG3 스타일 이미지로 반환.

        Args:
            action_name: 수행한 행동 이름 (예: "강타", "파이어볼")
            dmg: 입힌 피해량
            is_crit: 크리티컬 여부

        Returns:
            전투 카드 이미지 BytesIO 객체, 전투 중이 아니면 None
        """
        if not self.in_battle or not self.current_monster:
            return None
        from monsters_db import MONSTER_SIZES
        size_label = ""
        if hasattr(self, '_last_size'):
            si = MONSTER_SIZES.get(self._last_size, {})
            size_label = f"{si.get('icon','')} [{self._last_size}]"
        return get_renderer().render_battle_card(
            monster_name=self._group_display_name() if self.enemies else self.current_monster.get("name","?"),
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
    def zone_list(self) -> List[str]:
        return list(MONSTERS_DB.keys())

    def enter_zone(self, zone_name: str) -> str:
        """사냥터 입장.

        Args:
            zone_name: 입장할 사냥터 이름 (예: "드레드 할로우", "폐허가 된 마을")

        Returns:
            입장 결과 메시지
        """
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

    def start_encounter(self, zone_name: Optional[str] = None) -> Tuple[bool, Any]:
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

        # A-1 fix: HP가 0 이하면 max_hp로 복원 (상태 창과 전투 HP 불일치 방지)
        if self.player.hp <= 0:
            self.player.hp = self.player.max_hp
            logger.info('battle: HP가 0 이하로 감지됨 — max_hp로 복원: %d', self.player.max_hp)

        # 지역 전투는 1~3체가 동시에 등장할 수 있다. 저레벨 지역은 단독전 비율이 높다.
        level_min, level_max = zone.get("level_range", (1, 1))
        group_roll = random.random()
        if group_roll < (0.12 if level_max <= 5 else 0.22):
            group_size = 3
        elif group_roll < (0.42 if level_max <= 5 else 0.55):
            group_size = 2
        else:
            group_size = 1
        self.enemies = []
        self.defeated_enemies = []
        for _ in range(group_size):
            monster_base = random.choice(zone["monsters"])
            size = roll_monster_size()
            monster_data = apply_size_to_monster(monster_base, size)
            self.enemies.append({"monster": monster_data, "hp": monster_data["hp"], "statuses": {}, "size": size})
        self._sync_primary_enemy()
        monster_data = self.current_monster
        size = self._last_size
        self.in_battle       = True
        self.current_zone    = zone_key
        self.turn            = 1
        self._last_size      = size
        self.cheer_count     = 0
        self._cheer_active   = False
        self._last_grade     = None
        sound_director.cue("battle/start", interrupt=True)

        size_info  = MONSTER_SIZES[size]
        size_label = f"{size_info['icon']} [{size}]"

        buf = get_renderer().render_battle_card(
            monster_name=self._group_display_name(),
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
        """응원 사용. 이번 턴 공격력 15% 상승. 최대 3회.

        Returns:
            응원 결과 메시지
        """
        if not self.in_battle:
            return "현재 전투 중이 아님미댜!"
        if self.cheer_count >= 3:
            return "이번 전투에서 응원을 모두 사용했슴미댜! (최대 3회)"
        self.cheer_count += 1
        self._cheer_active = True
        from battle_log_data import CHEER_RESPONSE_LOGS
        return random.choice(CHEER_RESPONSE_LOGS) + f" (남은 응원: {3 - self.cheer_count}회)"

    def _get_condition_modifiers(self) -> Dict[str, float]:
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

    def _attack_tags(self, skill_id: str) -> set[str]:
        """현재 공격을 몬스터 생태 특성과 비교하기 위한 최소 피해 태그."""
        if skill_id == "firebolt": return {"fire", "magic"}
        if skill_id == "icebolt": return {"cold", "magic"}
        if skill_id == "lightningbolt": return {"lightning", "magic"}
        try:
            from items import ALL_ITEMS
            wid = self.player.equipment.get("main")
            name = ALL_ITEMS.get(wid, {}).get("name", "") if wid else ""
            if any(x in name for x in ("메이스", "해머", "몽둥이")): return {"bludgeoning", "physical"}
            if "활" in name: return {"piercing", "physical"}
        except Exception:
            pass
        return {"slashing", "physical"}

    def _apply_monster_traits(self, monster: dict, dmg: int, skill_id: str) -> tuple[int, str]:
        traits = set(monster.get("traits", [])); tags = self._attack_tags(skill_id); note = ""
        mult = 1.0
        if "둔기 취약" in traits and "bludgeoning" in tags:
            mult *= 1.5; note = "💥 약점!"
        if "베기 저항" in traits and "slashing" in tags:
            mult *= 0.5; note = "🛡️ 저항"
        if "번개 저항" in traits and "lightning" in tags:
            mult *= 0.5; note = "🛡️ 저항"
        return max(1, int(round(dmg * mult))), note

    def process_turn(self, skill_id: str = "smash") -> io.BytesIO:
        """전투 턴 진행.

        Args:
            skill_id: 사용할 스킬 ID (예: "smash", "defense", "fireball")

        Returns:
            전투 결과 이미지 BytesIO 객체
        """
        if not self.in_battle or not self.current_monster:
            return get_renderer().render_card(
                title="⚔ 전투 오류",
                rows=[{"label": "상태", "value": "현재 전투 중이 아님미댜!"}],
                system_key="battle",
                footer="전투 시스템",
            )

        if self.enemies:
            return self._process_group_turn(skill_id)

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

            sound_director.cue("battle/enemy_hit")
            if player.hp <= 0:
                self.in_battle  = False
                self._last_grade = "실패"
                sound_director.cue("battle/defeat", interrupt=True)
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

        # 디펜스/힐링은 공격 대신 한 턴을 소비하는 행동이다.
        if skill_id == "defense":
            from skills_db import COMBAT_SKILLS
            from skill_training import record_training_event
            rank = player.skill_ranks.get("defense", "연습")
            reduce_rate = COMBAT_SKILLS["defense"]["damage_reduce"].get(rank, 0.05)
            mon_atk = monster.get("attack", 5)
            defense = player.get_defense() if hasattr(player, "get_defense") else 0
            raw_after_armor = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - int(defense * mods.get("def_mult", 1.0)))
            mon_dmg = max(1, int(round(raw_after_armor * (1.0 - reduce_rate))))
            prevented = max(0, raw_after_armor - mon_dmg)
            low_hp_before = player.hp <= max(1, int(player.max_hp * 0.35))
            player.hp = max(0, player.hp - mon_dmg)
            record_training_event(player, "defense", "defense_use", 1)
            if prevented >= max(2, int(raw_after_armor * 0.20)):
                record_training_event(player, "defense", "defense_reduce", 1)
            if low_hp_before and player.hp > 0:
                record_training_event(player, "defense", "defense_low_hp", 1)
            record_training_event(player, "combat_mastery", "combat_action", 1)
            rank_msg = player.train_skill("defense", 10.0)
            player.train_skill("combat_mastery", 3.0)
            self.turn += 1
            if player.hp <= 0:
                self.in_battle = False
                self._last_grade = "실패"
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
                last_action=f"🛡 디펜스! 피해 {raw_after_armor} → {mon_dmg} (-{prevented})",
                last_dmg=0,
                is_crit=False,
                size_label=getattr(self, '_last_size_label', ''),
            )

        if skill_id == "healing":
            from skills_db import RECOVERY_SKILLS
            from skill_training import record_training_event
            rank = player.skill_ranks.get("healing", "연습")
            heal_data = RECOVERY_SKILLS["healing"]
            mp_cost = heal_data["mp_cost"].get(rank, 10)
            if player.mp < mp_cost:
                return get_renderer().render_card(
                    title="⚔ MP 부족",
                    rows=[{"label": "필요 MP", "value": str(mp_cost)}, {"label": "보유 MP", "value": str(player.mp)}],
                    system_key="battle",
                    footer="전투 시스템",
                )
            hp_before = player.hp
            was_low_hp = hp_before <= max(1, int(player.max_hp * 0.35))
            player.mp -= mp_cost
            heal_amount = heal_data["heal_amount"].get(rank, 20)
            player.hp = min(player.max_hp, player.hp + heal_amount)
            healed = player.hp - hp_before
            record_training_event(player, "healing", "healing_use", 1)
            if healed >= max(10, int(player.max_hp * 0.20)):
                record_training_event(player, "healing", "healing_big", 1)
            if was_low_hp and healed > 0:
                record_training_event(player, "healing", "healing_low_hp", 1)
            record_training_event(player, "combat_mastery", "combat_action", 1)
            rank_msg = player.train_skill("healing", 10.0)
            player.train_skill("combat_mastery", 2.0)
            mon_atk = monster.get("attack", 5)
            defense = player.get_defense() if hasattr(player, "get_defense") else 0
            mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - int(defense * mods.get("def_mult", 1.0)))
            player.hp = max(0, player.hp - mon_dmg)
            self.turn += 1
            if player.hp <= 0:
                self.in_battle = False
                self._last_grade = "실패"
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
                last_action=f"💚 힐링 +{healed} HP · {monster['name']} 반격 -{mon_dmg} HP",
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
        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS
        skill_rank = player.skill_ranks.get(skill_id, "연습")
        skill_name = skill_id
        if skill_id in COMBAT_SKILLS:
            sk         = COMBAT_SKILLS[skill_id]
            skill_name = sk["name"]
            if skill_id == "counter":
                bonus = sk.get("counter_multiplier", {}).get(skill_rank, 1.5)
            elif skill_id == "windmill":
                bonus = sk.get("aoe_multiplier", {}).get(skill_rank, 0.8)
            else:
                bonus = sk.get("damage_bonus", {}).get(skill_rank, 1.0)
            dmg = max(1, int(dmg * bonus))
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

        dmg, trait_note = self._apply_monster_traits(monster, dmg, skill_id)

        # 서사화 로그 선택
        from battle_log_data import (
            PLAYER_ATTACK_LOGS, MONSTER_ATTACK_LOGS,
            PLAYER_CRIT_LOGS, VICTORY_LOGS, DEFEAT_LOGS, GRADE_MULT, GRADE_LABELS,
        )
        atk_pool = PLAYER_ATTACK_LOGS.get(skill_id, PLAYER_ATTACK_LOGS["_default"])
        atk_log  = random.choice(atk_pool).format(monster=monster["name"])
        if crit:
            atk_log = random.choice(PLAYER_CRIT_LOGS) + " " + atk_log
        if trait_note:
            atk_log += f" {trait_note}"

        self.monster_hp -= dmg
        if skill_id in MAGIC_SKILLS:
            sound_director.cue("battle/magic_crit" if crit else "battle/magic_hit", interrupt=crit)
        else:
            sound_director.cue("battle/crit" if crit else "battle/player_hit", interrupt=crit)

        # 스킬별 수련 항목 + 전투 마스터리
        try:
            from skill_training import record_training_event
            if skill_id == "smash":
                record_training_event(player, "smash", "smash_use", 1)
                if crit:
                    record_training_event(player, "smash", "smash_crit", 1)
                if self.monster_hp <= 0:
                    record_training_event(player, "smash", "smash_kill", 1)
            elif skill_id == "counter":
                record_training_event(player, "counter", "counter_use", 1)
                if monster.get("attack", 5) >= max(8, player.get_defense() + 5):
                    record_training_event(player, "counter", "counter_strong", 1)
                if self.monster_hp <= 0:
                    record_training_event(player, "counter", "counter_kill", 1)
            elif skill_id == "windmill":
                record_training_event(player, "windmill", "windmill_use", 1)
                if crit:
                    record_training_event(player, "windmill", "windmill_crit", 1)
                if self.monster_hp <= 0:
                    record_training_event(player, "windmill", "windmill_kill", 1)
            elif skill_id in MAGIC_SKILLS:
                record_training_event(player, skill_id, "magic_cast", 1)
                if crit:
                    record_training_event(player, skill_id, "magic_crit", 1)
                if self.monster_hp <= 0:
                    record_training_event(player, skill_id, "magic_kill", 1)
            record_training_event(player, "combat_mastery", "combat_action", 1)
        except Exception:
            logger.warning('battle: 전투 수련 항목 기록 실패', exc_info=True)

        rank_msg = player.train_skill(skill_id, 10.0)
        player.train_skill("combat_mastery", 3.0)

        if self.monster_hp <= 0:
            self.monster_hp = 0
            self.in_battle  = False
            grade = _calc_battle_grade(player.hp, player.max_hp)
            self._last_grade = grade
            sound_director.cue("battle/victory", interrupt=True)
            reward = self._calc_reward(monster, grade)
            try:
                from skill_training import record_training_event
                record_training_event(player, "combat_mastery", "combat_win", 1)
            except Exception:
                logger.warning('battle: 전투 마스터리 승리 수련 기록 실패', exc_info=True)
            self._add_village_contribution_battle()

            # 라파엘 계약 처치 기록
            contract_msg = ""
            monster_id = monster.get("id", "")
            if monster_id:
                try:
                    from collection import collection_manager
                    is_new, _ = collection_manager.register("몬스터", monster_id, monster.get("name", monster_id), monster.get("_size", "M"))
                    if is_new:
                        collection_manager.apply_all_bonuses(self.player, "몬스터")
                except Exception:
                    logger.warning('battle: 몬스터 도감 등록 실패', exc_info=True)
                try:
                    from special_npc import SpecialNPCEncounterManager
                    enc_mgr = SpecialNPCEncounterManager(self.player)
                    contract_msg = enc_mgr.record_kill(monster_id)
                except Exception:
                    logger.warning('battle: SpecialNPCEncounterManager.record_kill 실패', exc_info=True)

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
                grade="Legendary",
                system_key="battle_win",
                footer=footer,
                h=max(380, 160 + len(rows) * 34),
            )

        # 몬스터 반격
        mon_atk = monster.get("attack", 5)
        defense = player.get_defense() if hasattr(player, "get_defense") else 0
        defense = int(defense * mods["def_mult"])
        mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - defense)
        if skill_id == "counter":
            mon_dmg = max(1, int(mon_dmg * 0.75))

        # 몬스터 공격 서사화 로그
        mon_pool = MONSTER_ATTACK_LOGS.get(monster["name"], MONSTER_ATTACK_LOGS["_default"])
        mon_log  = random.choice(mon_pool).format(monster=monster["name"])

        player.hp -= mon_dmg
        player.hp  = max(0, player.hp)
        sound_director.cue("battle/enemy_hit")

        if player.hp <= 0:
            self.in_battle  = False
            self._last_grade = "실패"
            sound_director.cue("battle/defeat", interrupt=True)
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
        """전투에서 도주 시도.

        Returns:
            도주 결과 이미지 BytesIO 객체
        """
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
            if self.enemies:
                mon_atk = sum(enemy["monster"].get("attack", 5) for enemy in self._alive_enemies())
            else:
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

    def auto_battle(self, skill_id: str = "smash") -> Tuple[List[str], io.BytesIO]:
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

            # E-6: 오토 포션 사용 — HP가 임계값 이하일 때 포션 자동 사용
            if getattr(self.player, 'auto_use_potion', True):
                hp_ratio = self.player.hp / max(self.player.max_hp, 1)
                if hp_ratio <= AUTO_POTION_HP_THRESHOLD:
                    potion_ids = ["con_hp_potion", "con_hp_potion_small"]
                    for pid in potion_ids:
                        if self.player.inventory.get(pid, 0) > 0:
                            from items import CONSUMABLES
                            pot = CONSUMABLES.get(pid, {})
                            heal = pot.get("hp_restore", 50)
                            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                            self.player.remove_item(pid, 1)
                            pot_name = pot.get("name", pid)
                            log_lines.append(f"💊 포션 사용: {pot_name} (HP +{heal})")
                            break

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

    def _apply_event_effect(self, effect: Dict[str, Any]) -> None:
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

    def _calc_reward(self, monster: Dict[str, Any], grade: str = "안정") -> Dict[str, Any]:
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
                # 전투 드롭은 즉시 일반 인벤토리에 밀어 넣지 않고 전리품 묶음에 둔다.
                # 구형/테스트 Player와의 호환을 위해 add_loot이 없으면 기존 경로를 사용한다.
                add_loot = getattr(self.player, "add_loot", None)
                added = add_loot(item_id) if callable(add_loot) else self.player.add_item(item_id)
                if added:
                    drops[item_id] = drops.get(item_id, 0) + 1

        # 레벨업 체크 (공통 함수 사용 — 다중 레벨업 지원)
        leveled_up  = False
        level_gains = {}
        old_level   = self.player.level
        from player import check_level_up
        _ups = check_level_up(self.player)
        if _ups:
            leveled_up = True
            # 마지막 레벨업의 gains를 사용 (기존 호환)
            level_gains = _ups[-1]["gains"]

        return {
            "gold":        gold,
            "exp":         exp,
            "items":       drops,
            "leveled_up":  leveled_up,
            "level_gains": level_gains,
            "old_level":   old_level,
            "new_level":   self.player.level,
        }

    def _add_village_contribution_battle(self) -> None:
        try:
            from village import village_manager
            village_manager.add_contribution(3, "battle")
        except Exception:
            logger.warning('battle: village_manager.add_contribution 실패', exc_info=True)