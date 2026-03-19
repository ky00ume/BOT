import random
from monsters_db import MONSTERS_DB
from ui_theme import C, bar, section, divider, header_box, ansi, EMBED_COLOR, FOOTERS


class BattleEngine:
    def __init__(self, player, npc_manager=None):
        self.player      = player
        self.npc_manager = npc_manager
        self.in_battle   = False
        self.current_zone    = None
        self.current_monster = None
        self.monster_hp      = 0
        self.turn            = 0

    @property
    def zone_list(self):
        return list(MONSTERS_DB.keys())

    def enter_zone(self, zone_name: str) -> str:
        zone = MONSTERS_DB.get(zone_name)
        if not zone:
            return f"{C.RED}✖ [{zone_name}]은(는) 존재하지 않는 사냥터임미댜!{C.R}"

        level_min, level_max = zone["level_range"]
        if self.player.level < level_min:
            return (
                f"{C.RED}✖ [{zone_name}] 입장에는 Lv.{level_min} 이상이 필요함미댜!{C.R}\n"
                f"  현재 레벨: {C.WHITE}Lv.{self.player.level}{C.R}"
            )

        self.current_zone = zone_name
        return (
            f"{C.GOLD}✦ {zone['name']}{C.R}에 입장했슴미댜!\n"
            f"  {C.DARK}{zone.get('desc', '')} (Lv.{level_min}~{level_max}){C.R}\n"
            f"  {C.GREEN}/사냥 {zone_name}{C.R} 으로 전투를 시작하셰요!"
        )

    def start_encounter(self, zone_name: str = None) -> tuple[bool, str]:
        """전투 시작. (성공여부, 메시지) 반환."""
        zone_key = zone_name or self.current_zone
        zone = MONSTERS_DB.get(zone_key)
        if not zone:
            return False, f"{C.RED}✖ 사냥터를 먼저 선택하셰요! (/사냥터){C.R}"

        from database import HUNTING_GROUNDS
        ground = HUNTING_GROUNDS.get(zone_key, {})
        energy_cost = ground.get("energy_cost", 10)

        if not self.player.consume_energy(energy_cost):
            return False, (
                f"{C.RED}✖ 기력이 부족함미댜!{C.R}\n"
                f"  현재 기력: {C.WHITE}{self.player.energy}/{self.player.max_energy}{C.R}\n"
                f"  필요 기력: {C.WHITE}{energy_cost}{C.R}"
            )

        monster_data = random.choice(zone["monsters"])
        self.current_monster = dict(monster_data)
        self.monster_hp      = monster_data["hp"]
        self.in_battle       = True
        self.current_zone    = zone_key
        self.turn            = 1

        msg = (
            f"{header_box('⚔ 전투 시작!')}\n"
            f"  {C.RED}{monster_data['name']}{C.R} {C.DARK}Lv.{monster_data['level']}{C.R}이(가) 나타났슴미댜!\n"
            f"  {C.RED}HP{C.R} {bar(self.monster_hp, monster_data['hp'])} "
            f"{C.WHITE}{self.monster_hp}/{monster_data['hp']}{C.R}\n"
            f"{divider()}\n"
            f"  {C.GREEN}/공격 [스킬]{C.R} 으로 공격, {C.GOLD}/도주{C.R} 로 도망!"
        )
        return True, msg

    def process_turn(self, skill_id: str = "smash") -> str:
        if not self.in_battle or not self.current_monster:
            return f"{C.RED}✖ 현재 전투 중이 아님미댜!{C.R}"

        player = self.player
        monster = self.current_monster

        # 플레이어 공격
        base_atk = player.get_attack() if hasattr(player, "get_attack") else 10
        crit = random.random() < (player.base_stats.get("luck", 5) * 0.01)
        dmg  = int(base_atk * (1.5 if crit else 1.0) * random.uniform(0.85, 1.15))
        dmg  = max(1, dmg - monster.get("defense", 0))

        # 스킬 보너스
        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS
        skill_rank = player.skill_ranks.get(skill_id, "연습")
        if skill_id in COMBAT_SKILLS:
            sk = COMBAT_SKILLS[skill_id]
            bonus = sk.get("damage_bonus", {}).get(skill_rank, 1.0)
            dmg = int(dmg * bonus)
        elif skill_id in MAGIC_SKILLS:
            sk = MAGIC_SKILLS[skill_id]
            mp_cost = sk.get("mp_cost", {}).get(skill_rank, 5)
            if player.mp < mp_cost:
                return f"{C.RED}✖ MP가 부족함미댜! (필요: {mp_cost}){C.R}"
            player.mp -= mp_cost
            magic_dmg = sk.get("damage", {}).get(skill_rank, 10)
            magic_atk = player.base_stats.get("int", 10) // 2
            dmg = int((magic_dmg + magic_atk) * random.uniform(0.85, 1.15))

        self.monster_hp -= dmg

        lines = [
            f"{divider()}",
            f"  {C.B}[턴 {self.turn}]{C.R}",
            f"  {C.CYAN}{'크리티컬!' if crit else ''}{C.R}",
            f"  {C.WHITE}{monster['name']}{C.R}에게 {C.RED}{dmg}{C.R} 피해를 입혔슴미댜!",
        ]

        # 스킬 훈련 경험치
        train_msg = player.train_skill(skill_id, 10.0)
        if train_msg:
            lines.append(f"  {C.GOLD}{train_msg}{C.R}")

        # 몬스터 사망 처리
        if self.monster_hp <= 0:
            self.monster_hp = 0
            self.in_battle  = False
            reward = self._calc_reward(monster)
            lines.append(f"\n{header_box('🎉 전투 승리!')}")
            lines.append(f"  {C.GOLD}💰 +{reward['gold']}G{C.R}  {C.GREEN}EXP +{reward['exp']}{C.R}")
            for item_id, cnt in reward["items"].items():
                from items import ALL_ITEMS
                item_name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                lines.append(f"  {C.CYAN}▸ {item_name} x{cnt}{C.R}")
            return ansi("\n".join(l for l in lines if l.strip()))

        # 몬스터 반격
        mon_atk = monster.get("attack", 5)
        defense = player.get_defense() if hasattr(player, "get_defense") else 0
        mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - defense)
        player.hp -= mon_dmg
        player.hp  = max(0, player.hp)

        lines.append(f"  {C.RED}{monster['name']}{C.R}이(가) 반격! {C.RED}-{mon_dmg} HP{C.R}")

        hp_bar = bar(player.hp, player.max_hp)
        mon_bar = bar(self.monster_hp, monster["hp"])
        lines.append(f"\n  {C.WHITE}내 HP{C.R} {hp_bar} {player.hp}/{player.max_hp}")
        lines.append(f"  {C.RED}{monster['name']} HP{C.R} {mon_bar} {self.monster_hp}/{monster['hp']}")

        if player.hp <= 0:
            self.in_battle = False
            lines.append(f"\n{C.RED}💀 쓰러졌슴미댜...{C.R} HP를 회복하고 다시 도전하셰요!")

        self.turn += 1
        return ansi("\n".join(l for l in lines if l is not None))

    def flee(self) -> str:
        if not self.in_battle:
            return f"{C.RED}✖ 현재 전투 중이 아님미댜!{C.R}"
        success = random.random() < 0.6
        self.in_battle = False
        if success:
            return ansi(f"  {C.GREEN}✔ 성공적으로 도망쳤슴미댜~{C.R}")
        else:
            monster = self.current_monster
            mon_atk = monster.get("attack", 5) if monster else 5
            dmg = max(1, int(mon_atk * 0.5))
            self.player.hp -= dmg
            self.player.hp = max(0, self.player.hp)
            return ansi(
                f"  {C.RED}✖ 도주 실패! {monster['name'] if monster else '몬스터'}에게 {dmg} 피해를 입고 겨우 도망쳤슴미댜...{C.R}"
            )

    def _calc_reward(self, monster: dict) -> dict:
        gold_range = monster.get("gold", (1, 5))
        gold = random.randint(*gold_range)
        exp  = monster.get("exp", 1)
        self.player.gold += gold
        self.player.exp  = getattr(self.player, "exp", 0.0) + exp

        drops = {}
        for drop in monster.get("drops", []):
            if random.random() < drop["rate"]:
                item_id = drop["item"]
                added = self.player.add_item(item_id)
                if added:
                    drops[item_id] = drops.get(item_id, 0) + 1

        # 레벨업 체크 (간단: exp >= level*100)
        level_thresh = self.player.level * 100
        if self.player.exp >= level_thresh:
            self.player.exp  -= level_thresh
            self.player.level += 1
            self.player.max_hp += 10
            self.player.hp    = self.player.max_hp
            self.player.max_mp += 5
            self.player.mp    = self.player.max_mp

        return {"gold": gold, "exp": exp, "items": drops}
