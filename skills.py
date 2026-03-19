from skills_db import (
    RANK_ORDER, COMBAT_SKILLS, MAGIC_SKILLS,
    RECOVERY_SKILLS, OTHER_SKILLS, MASTERY_SKILLS,
    COOKING_SKILL,
)
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS


class SkillManager:
    def __init__(self, player):
        self.player = player

    def can_cook(self, dish_id: str) -> bool:
        """현재 요리 랭크로 dish_id 조리 가능 여부 확인."""
        rank = self.player.skill_ranks.get("cooking", "연습")
        allowed = COOKING_SKILL.get(rank, [])
        return dish_id in allowed

    def use_magic(self, skill_id: str) -> tuple[bool, str]:
        """마법 스킬 사용 가능 여부 반환 (bool, message)."""
        if skill_id not in MAGIC_SKILLS:
            return False, f"[{skill_id}]은(는) 마법 스킬이 아님미댜."

        if skill_id not in self.player.skill_ranks:
            return False, f"[{skill_id}] 스킬을 보유하고 있지 않슴미댜."

        rank = self.player.skill_ranks.get(skill_id, "연습")
        sk = MAGIC_SKILLS[skill_id]
        mp_cost = sk.get("mp_cost", {}).get(rank, 5)

        if self.player.mp < mp_cost:
            return False, (
                f"{C.RED}✖ MP 부족! (보유: {self.player.mp}, 필요: {mp_cost}){C.R}"
            )

        self.player.mp -= mp_cost
        dmg = sk.get("damage", {}).get(rank, 10)
        magic_atk = self.player.base_stats.get("int", 10) // 2
        total = dmg + magic_atk
        return True, f"{sk['name']} 시전! {C.BLUE}{total}{C.R} 마법 피해."

    def show_skills(self) -> str:
        player = self.player
        lines = [header_box("✦ 스킬 목록")]

        all_skill_defs = {
            **COMBAT_SKILLS, **MAGIC_SKILLS,
            **RECOVERY_SKILLS, **OTHER_SKILLS, **MASTERY_SKILLS,
        }

        if not player.skill_ranks:
            lines.append(f"  {C.DARK}보유 스킬 없음{C.R}")
        else:
            lines.append(section("보유 스킬"))
            for skill_id, rank in player.skill_ranks.items():
                skill_def = all_skill_defs.get(skill_id, {})
                skill_name = skill_def.get("name", skill_id)
                badge = rank_badge(rank)
                acc = player.skill_exp.get(skill_id, 0.0)
                lines.append(f"  {badge} {C.WHITE}{skill_name}{C.R}  {C.DARK}({acc:.0f}){C.R}")

        return ansi("\n".join(lines))
