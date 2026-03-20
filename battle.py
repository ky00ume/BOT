import random
import discord
from monsters_db import MONSTERS_DB, MONSTER_SIZES, roll_monster_size, apply_size_to_monster
from ui_theme import C, bar_plain, ansi, EMBED_COLOR


def _bar_text(current, max_val, width=10):
    current = max(0, current)
    if max_val <= 0:
        filled = 0
    else:
        filled = round(width * current / max_val)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


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
        """전투 시작. (성공여부, embed_or_msg) 반환."""
        zone_key = zone_name or self.current_zone
        zone = MONSTERS_DB.get(zone_key)
        if not zone:
            embed = discord.Embed(
                title="⚔ 전투 오류",
                description="사냥터를 먼저 선택하셰요! (`/사냥터`)",
                color=0xFF4444,
            )
            return False, embed

        from database import HUNTING_GROUNDS
        ground = HUNTING_GROUNDS.get(zone_key, {})
        energy_cost = ground.get("energy_cost", 5)

        if not self.player.consume_energy(energy_cost):
            embed = discord.Embed(
                title="⚔ 기력 부족",
                description=(
                    f"기력이 부족함미댜!\n"
                    f"현재 기력: **{self.player.energy}/{self.player.max_energy}**\n"
                    f"필요 기력: **{energy_cost}**"
                ),
                color=0xFF4444,
            )
            return False, embed

        monster_base = random.choice(zone["monsters"])
        size         = roll_monster_size()
        monster_data = apply_size_to_monster(monster_base, size)
        self.current_monster = monster_data
        self.monster_hp      = monster_data["hp"]
        self.in_battle       = True
        self.current_zone    = zone_key
        self.turn            = 1

        size_info  = MONSTER_SIZES[size]
        size_label = f"{size_info['icon']} [{size}]"

        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS
        mon_bar = _bar_text(self.monster_hp, monster_data["hp"])

        embed = discord.Embed(
            title="⚔ 전투 시작!",
            color=EMBED_COLOR.get("battle", 0xA01B2C),
        )
        embed.add_field(
            name=f"🐾 {monster_data['name']} Lv.{monster_data['level']} {size_label}",
            value=f"HP `{mon_bar}` {self.monster_hp}/{monster_data['hp']}",
            inline=False,
        )

        skill_lines = []
        for sid, sdata in {**COMBAT_SKILLS, **MAGIC_SKILLS, **RECOVERY_SKILLS}.items():
            rank = self.player.skill_ranks.get(sid)
            if rank is None:
                continue
            name = sdata["name"]
            mp_cost_data = sdata.get("mp_cost", 0)
            if isinstance(mp_cost_data, dict):
                mp = mp_cost_data.get(rank, "?")
                skill_lines.append(f"🕸️ **{name}** [{rank}] MP:{mp}")
            else:
                skill_lines.append(f"🕸️ **{name}** [{rank}]")

        if skill_lines:
            embed.add_field(
                name="📖 사용 가능 스킬",
                value="\n".join(skill_lines) or "없음",
                inline=False,
            )
        else:
            embed.add_field(
                name="📖 사용 가능 스킬",
                value="(보유 전투 스킬 없음 — 기본 공격만 가능)",
                inline=False,
            )

        embed.set_footer(text=f"💡 /공격 [스킬이름] 으로 공격, /도주 로 도망!")
        return True, embed

    def process_turn(self, skill_id: str = "smash") -> discord.Embed:
        if not self.in_battle or not self.current_monster:
            return discord.Embed(
                title="⚔ 전투 오류",
                description="현재 전투 중이 아님미댜!",
                color=0xFF4444,
            )

        player  = self.player
        monster = self.current_monster

        # 플레이어 공격
        base_atk = player.get_attack() if hasattr(player, "get_attack") else 10
        crit     = random.random() < (player.base_stats.get("luck", 5) * 0.01)
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
                return discord.Embed(
                    title="⚔ MP 부족",
                    description=f"MP가 부족함미댜! (필요: {mp_cost}, 보유: {player.mp})",
                    color=0xFF4444,
                )
            player.mp  -= mp_cost
            magic_dmg   = sk.get("damage", {}).get(skill_rank, 10)
            magic_atk   = player.base_stats.get("int", 10) // 2
            dmg         = int((magic_dmg + magic_atk) * random.uniform(0.85, 1.15))

        self.monster_hp -= dmg

        embed = discord.Embed(
            title=f"⚔ 턴 {self.turn} — {skill_name}",
            color=EMBED_COLOR.get("battle", 0xA01B2C),
        )

        atk_line = f"{'💥 크리티컬! ' if crit else ''}{monster['name']}에게 **{dmg}** 피해!"
        embed.add_field(name="🗡️ 공격", value=atk_line, inline=False)

        # 스킬 훈련 경험치
        rank_msg = player.train_skill(skill_id, 10.0)

        if self.monster_hp <= 0:
            self.monster_hp = 0
            self.in_battle  = False
            reward = self._calc_reward(monster)
            self._add_village_contribution_battle()

            # 라파엘 계약 처치 기록
            monster_id = monster.get("id", "")
            if monster_id:
                try:
                    from special_npc import SpecialNPCEncounterManager
                    enc_mgr = SpecialNPCEncounterManager(self.player)
                    contract_msg = enc_mgr.record_kill(monster_id)
                    if contract_msg:
                        embed.add_field(name="📜 계약 진행", value=contract_msg, inline=False)
                except Exception:
                    pass

            size      = monster.get("_size", "M")
            size_info = MONSTER_SIZES.get(size, MONSTER_SIZES["M"])
            embed.title = "🎉 전투 승리!"
            embed.color = 0x22BB55
            embed.add_field(
                name="✨ 전리품",
                value=(
                    f"💰 +**{reward['gold']}**G　　EXP +**{reward['exp']}**\n"
                    f"사이즈: {size_info['icon']} {size}"
                ),
                inline=False,
            )
            if reward.get("items"):
                from items import ALL_ITEMS
                drop_lines = []
                for item_id, cnt in reward["items"].items():
                    item_name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                    drop_lines.append(f"▸ {item_name} x{cnt}")
                embed.add_field(name="🎁 드롭 아이템", value="\n".join(drop_lines), inline=False)
            if reward.get("leveled_up"):
                gains = reward.get("level_gains", {})
                gain_lines = []
                if gains.get("max_hp"):
                    gain_lines.append(f"💖 최대 HP +{gains['max_hp']}")
                if gains.get("max_mp"):
                    gain_lines.append(f"💙 최대 MP +{gains['max_mp']}")
                if gains.get("max_energy"):
                    gain_lines.append(f"💚 최대 EN +{gains['max_energy']}")
                for stat in ("str", "int", "dex", "will", "luck"):
                    if gains.get(stat):
                        stat_names = {"str": "힘", "int": "지력", "dex": "민첩", "will": "의지", "luck": "운"}
                        gain_lines.append(f"⭐ {stat_names[stat]} +{gains[stat]}")
                embed.add_field(
                    name=f"🆙 레벨 업! Lv.{reward['old_level']} → Lv.{reward['new_level']}",
                    value="\n".join(gain_lines) if gain_lines else "능력이 향상됐슴미댜!",
                    inline=False,
                )
            if rank_msg:
                embed.set_footer(text=rank_msg)
            return embed

        # 몬스터 반격
        mon_atk = monster.get("attack", 5)
        defense = player.get_defense() if hasattr(player, "get_defense") else 0
        mon_dmg = max(1, int(mon_atk * random.uniform(0.85, 1.15)) - defense)
        player.hp -= mon_dmg
        player.hp  = max(0, player.hp)

        embed.add_field(
            name="🔴 반격",
            value=f"{monster['name']}의 반격! **-{mon_dmg} HP**",
            inline=False,
        )

        hp_bar  = _bar_text(player.hp, player.max_hp)
        mon_bar = _bar_text(self.monster_hp, monster["hp"])
        embed.add_field(
            name="📊 전투 현황",
            value=(
                f"내 HP　　 `{hp_bar}` {player.hp}/{player.max_hp}\n"
                f"{monster['name']} HP `{mon_bar}` {self.monster_hp}/{monster['hp']}"
            ),
            inline=False,
        )

        if player.hp <= 0:
            self.in_battle = False
            embed.title  = "💀 전투 패배..."
            embed.color  = 0x555555
            embed.add_field(
                name="😵 쓰러졌슴미댜...",
                value="HP를 회복하고 다시 도전하셰요!",
                inline=False,
            )
        else:
            from skills_db import COMBAT_SKILLS as CS, MAGIC_SKILLS as MS, RECOVERY_SKILLS as RS
            hint_skills = []
            for sid, sdata in {**CS, **MS, **RS}.items():
                if self.player.skill_ranks.get(sid) is not None:
                    hint_skills.append(sdata["name"])
            if hint_skills:
                embed.set_footer(text="스킬: " + " / ".join(hint_skills))

        if rank_msg:
            existing = embed.footer.text or ""
            embed.set_footer(text=f"{existing}  |  {rank_msg}".strip(" |"))

        self.turn += 1
        return embed

    def flee(self) -> discord.Embed:
        if not self.in_battle:
            return discord.Embed(
                title="⚔ 오류",
                description="현재 전투 중이 아님미댜!",
                color=0xFF4444,
            )
        success = random.random() < 0.6
        self.in_battle = False
        if success:
            return discord.Embed(
                title="🏃 도주 성공!",
                description="성공적으로 도망쳤슴미댜~",
                color=0x22BB55,
            )
        else:
            monster = self.current_monster
            mon_atk = monster.get("attack", 5) if monster else 5
            dmg     = max(1, int(mon_atk * 0.5))
            self.player.hp -= dmg
            self.player.hp  = max(0, self.player.hp)
            return discord.Embed(
                title="🏃 도주 실패!",
                description=(
                    f"{monster['name'] if monster else '몬스터'}에게 **{dmg}** 피해를 입고 "
                    f"겨우 도망쳤슴미댜..."
                ),
                color=0xFF4444,
            )

    def _calc_reward(self, monster: dict) -> dict:
        gold_range = monster.get("gold", (1, 5))
        gold       = random.randint(*gold_range)
        exp        = monster.get("exp", 1)
        self.player.gold += gold
        self.player.exp   = getattr(self.player, "exp", 0.0) + exp

        drops = {}
        for drop in monster.get("drops", []):
            if random.random() < drop["rate"]:
                item_id = drop["item"]
                if self.player.add_item(item_id):
                    drops[item_id] = drops.get(item_id, 0) + 1

        # 레벨업 체크 (exp >= level * 100)
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
