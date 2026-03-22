"""skill_ui.py — /스킬 통합 UI (임베드 + 드롭다운 방식)

카테고리 드롭다운:
  전투 스킬 → "전투 중에만 사용 가능합니다" 안내
  마법 스킬 → 힐링은 [사용] 버튼 제공 (전투 외 HP 회복), 나머지는 안내
  생활 스킬 → 레시피 드롭다운 → 재료 임베드 (부족=빨강) → [제작 실행] 버튼
"""
import discord
from discord.ui import View, Button, Select
from ui_theme import EMBED_COLOR
from skills_db import (
    COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS,
    OTHER_SKILLS, MASTERY_SKILLS, RANK_ORDER,
)

# 생활 스킬 ID → 엔진 종류
_LIFE_SKILL_ENGINE = {
    "cooking":    "cooking",
    "alchemy":    "alchemy",
    "crafting":   "crafting",
    "metallurgy": "metallurgy",
}

_CATEGORY_LABELS = {
    "combat": "⚔️ 전투",
    "magic":  "✨ 마법",
    "life":   "🌿 생활",
}


def _rank_badge(rank: str) -> str:
    r = {
        "연습": "🔰",
        "F": "🅵", "E": "🅴", "D": "🅳", "C": "🅲",
        "B": "🅱", "A": "🅰",
    }
    return r.get(rank, f"[{rank}]")


def make_skill_main_embed(player) -> discord.Embed:
    """메인 스킬 창 임베드 생성."""
    embed = discord.Embed(
        title="📚 스킬 창",
        description="카테고리를 선택하면 보유 스킬 목록이 표시됩니다.",
        color=EMBED_COLOR.get("help", 0x5865F2),
    )
    # 대표 스킬 랭크 요약 표시
    skill_ranks = getattr(player, "skill_ranks", {})
    combat_lines = []
    for sid, sdata in COMBAT_SKILLS.items():
        if sid in skill_ranks:
            combat_lines.append(f"• {sdata['name']} {_rank_badge(skill_ranks[sid])}")
    if combat_lines:
        embed.add_field(name="⚔️ 전투", value="\n".join(combat_lines), inline=True)

    magic_lines = []
    for sid, sdata in {**MAGIC_SKILLS, **RECOVERY_SKILLS}.items():
        if sid in skill_ranks:
            magic_lines.append(f"• {sdata['name']} {_rank_badge(skill_ranks[sid])}")
    if magic_lines:
        embed.add_field(name="✨ 마법", value="\n".join(magic_lines), inline=True)

    life_lines = []
    for sid, sdata in OTHER_SKILLS.items():
        if sid in skill_ranks:
            rank = skill_ranks[sid]
            life_lines.append(f"• {sdata['name']} {_rank_badge(rank)}")
    if life_lines:
        embed.add_field(name="🌿 생활", value="\n".join(life_lines), inline=True)
    embed.set_footer(text="아래 드롭다운에서 카테고리를 선택하세요.")
    return embed


def make_category_embed(player, category: str) -> discord.Embed:
    """카테고리별 스킬 목록 임베드."""
    skill_ranks = getattr(player, "skill_ranks", {})
    if category == "combat":
        title = "⚔️ 전투 스킬"
        lines = []
        for sid, sdata in COMBAT_SKILLS.items():
            rank = skill_ranks.get(sid)
            if rank:
                exp = getattr(player, "skill_exp", {}).get(sid, 0)
                lines.append(f"**{sdata['name']}** {_rank_badge(rank)}  EXP: {exp:.0f}\n> {sdata['desc']}")
        desc = "\n\n".join(lines) if lines else "보유한 전투 스킬이 없습니다."
        desc += "\n\n> ⚔️ 전투 스킬은 전투 중에만 사용할 수 있습니다."
        embed = discord.Embed(title=title, description=desc, color=0xFF4500)
    elif category == "magic":
        title = "✨ 마법 스킬"
        lines = []
        all_magic = {**MAGIC_SKILLS, **RECOVERY_SKILLS}
        for sid, sdata in all_magic.items():
            rank = skill_ranks.get(sid)
            if rank:
                exp = getattr(player, "skill_exp", {}).get(sid, 0)
                extra = ""
                if sid == "healing":
                    extra = "\n> 💡 힐링은 전투 외에서도 [사용] 버튼으로 HP를 회복할 수 있습니다."
                else:
                    extra = "\n> ⚠️ 공격 마법은 전투 중에만 사용 가능합니다."
                lines.append(f"**{sdata['name']}** {_rank_badge(rank)}  EXP: {exp:.0f}\n> {sdata['desc']}{extra}")
        desc = "\n\n".join(lines) if lines else "보유한 마법 스킬이 없습니다."
        embed = discord.Embed(title=title, description=desc, color=0x9B59B6)
    else:  # life
        title = "🌿 생활 스킬"
        lines = []
        for sid, sdata in OTHER_SKILLS.items():
            rank = skill_ranks.get(sid)
            if rank:
                exp = getattr(player, "skill_exp", {}).get(sid, 0)
                note = ""
                if sid in _LIFE_SKILL_ENGINE:
                    note = "\n> ✅ 스킬 선택 시 레시피 창이 열립니다."
                lines.append(f"**{sdata['name']}** {_rank_badge(rank)}  EXP: {exp:.0f}\n> {sdata['desc']}{note}")
        desc = "\n\n".join(lines) if lines else "보유한 생활 스킬이 없습니다."
        embed = discord.Embed(title=title, description=desc, color=0x2ECC71)
    embed.set_footer(text="스킬을 선택하려면 아래 드롭다운을 이용하세요.")
    return embed


def make_recipe_list_embed(player, skill_id: str, recipes: dict) -> discord.Embed:
    """레시피 목록 임베드 (드롭다운 선택 전)."""
    from skills_db import OTHER_SKILLS
    skill_name = OTHER_SKILLS.get(skill_id, {}).get("name", skill_id)
    skill_ranks = getattr(player, "skill_ranks", {})
    rank = skill_ranks.get(skill_id, "연습")
    embed = discord.Embed(
        title=f"🗂️ {skill_name} 레시피 목록 [{rank}]",
        description="레시피를 선택하면 재료 현황이 표시됩니다.",
        color=0x2ECC71,
    )
    from items import ALL_ITEMS

    for rid, recipe in list(recipes.items())[:20]:
        rank_req = recipe.get("rank_req", "연습")
        try:
            from skills_db import RANK_ORDER
            unlocked = RANK_ORDER.index(rank) >= RANK_ORDER.index(rank_req)
        except Exception:
            unlocked = True
        status = "✅" if unlocked else "🔒"
        name = recipe.get("name", rid)
        ing_parts = []
        for ing_id, cnt in recipe.get("ingredients", {}).items():
            ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
            ing_parts.append(f"{ing_name}×{cnt}")
        embed.add_field(
            name=f"{status} [{rank_req}] {name}",
            value=", ".join(ing_parts) or "재료 없음",
            inline=False,
        )
    embed.set_footer(text="아래 드롭다운에서 레시피를 선택하세요.")
    return embed


def make_recipe_detail_embed(player, recipe_id: str, recipe: dict) -> discord.Embed:
    """레시피 상세 임베드 (재료 충분 여부 표시)."""
    from items import ALL_ITEMS
    name = recipe.get("name", recipe_id)
    embed = discord.Embed(title=f"📋 {name}", color=0x2ECC71)

    desc_lines = [recipe.get("desc", "")]
    embed.description = "\n".join(desc_lines)

    # 재료 표시
    ingredients = recipe.get("ingredients", {})
    mat_lines = []
    can_craft = True
    for ing_id, need in ingredients.items():
        ing_item = ALL_ITEMS.get(ing_id, {})
        ing_name = ing_item.get("name", ing_id)
        have = player.inventory.get(ing_id, 0)
        if have >= need:
            # 충분: 녹색 (ANSI 불가이므로 이모지로 표현)
            mat_lines.append(f"✅ {ing_name}: {need}개 (보유: {have}개)")
        else:
            mat_lines.append(f"❌ {ing_name}: {need}개 (보유: {have}개 — 부족!)")
            can_craft = False

    embed.add_field(name="🧪 필요 재료", value="\n".join(mat_lines) or "없음", inline=False)

    # 도구 필요 표시
    tool_req = recipe.get("tool_req")
    if tool_req:
        tool_name = ALL_ITEMS.get(tool_req, {}).get("name", tool_req)
        have_tool = player.inventory.get(tool_req, 0)
        tool_status = "✅" if have_tool > 0 else "❌"
        embed.add_field(name="🔧 필요 도구", value=f"{tool_status} {tool_name}", inline=False)
        if have_tool == 0:
            can_craft = False

    embed.add_field(
        name="📊 제작 가능 여부",
        value="✅ 모든 재료가 충분합니다!" if can_craft else "❌ 재료가 부족합니다.",
        inline=False,
    )
    embed.set_footer(text="[제작 실행] 버튼을 눌러 제작하세요." if can_craft else "재료를 먼저 모아주세요.")
    return embed, can_craft


class SkillCategorySelect(Select):
    def __init__(self, player):
        self.player = player
        options = [
            discord.SelectOption(label="⚔️ 전투 스킬", value="combat", description="전투용 스킬 목록"),
            discord.SelectOption(label="✨ 마법 스킬", value="magic", description="마법/회복 스킬 목록"),
            discord.SelectOption(label="🌿 생활 스킬", value="life", description="요리/제작/제련/제조 등"),
        ]
        super().__init__(placeholder="카테고리를 선택하세요...", options=options, custom_id="skill_cat_select")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        view: SkillMainView = self.view
        view.current_category = category
        embed = make_category_embed(self.player, category)

        if category == "life":
            # 생활 스킬 선택 드롭다운 추가
            view.clear_items()
            view.add_item(SkillCategorySelect(self.player))
            view.add_item(LifeSkillSelect(self.player))
        elif category == "magic":
            view.clear_items()
            view.add_item(SkillCategorySelect(self.player))
            # 힐링 스킬이 있으면 [사용] 버튼 추가
            if "healing" in getattr(self.player, "skill_ranks", {}):
                btn = Button(label="힐링 사용", style=discord.ButtonStyle.success, emoji="💚")
                btn.callback = view._make_healing_callback()
                view.add_item(btn)
        else:
            view.clear_items()
            view.add_item(SkillCategorySelect(self.player))

        await interaction.response.edit_message(embed=embed, view=view)


class LifeSkillSelect(Select):
    def __init__(self, player):
        self.player = player
        skill_ranks = getattr(player, "skill_ranks", {})
        options = []
        for sid, sdata in OTHER_SKILLS.items():
            if sid in skill_ranks and sid in _LIFE_SKILL_ENGINE:
                rank = skill_ranks[sid]
                options.append(discord.SelectOption(
                    label=f"{sdata['name']} [{rank}]",
                    value=sid,
                    description=sdata.get("desc", "")[:50],
                ))
        if not options:
            options.append(discord.SelectOption(
                label="(보유 생활 스킬 없음)",
                value="none",
                description="생활 스킬이 없습니다.",
            ))
        super().__init__(placeholder="생활 스킬을 선택하세요...", options=options[:25], custom_id="life_skill_select")

    async def callback(self, interaction: discord.Interaction):
        skill_id = self.values[0]
        if skill_id == "none":
            await interaction.response.send_message("보유한 생활 스킬이 없습니다.", ephemeral=True)
            return

        view: SkillMainView = self.view
        recipes = _get_recipes_for_skill(skill_id)
        embed = make_recipe_list_embed(self.player, skill_id, recipes)
        # 레시피 드롭다운으로 교체
        view.clear_items()
        view.add_item(SkillCategorySelect(self.player))
        view.add_item(LifeSkillSelect(self.player))
        if recipes:
            view.add_item(RecipeSelect(self.player, skill_id, recipes))
        await interaction.response.edit_message(embed=embed, view=view)


class RecipeSelect(Select):
    def __init__(self, player, skill_id: str, recipes: dict):
        self.player = player
        self.skill_id = skill_id
        skill_ranks = getattr(player, "skill_ranks", {})
        rank = skill_ranks.get(skill_id, "연습")
        options = []
        for rid, recipe in list(recipes.items())[:25]:
            rank_req = recipe.get("rank_req", "연습")
            try:
                unlocked = RANK_ORDER.index(rank) >= RANK_ORDER.index(rank_req)
            except Exception:
                unlocked = True
            status = "✅" if unlocked else "🔒"
            options.append(discord.SelectOption(
                label=f"{status} {recipe.get('name', rid)}",
                value=rid,
                description=f"[{rank_req}] {recipe.get('desc','')[:40]}",
            ))
        super().__init__(placeholder="레시피를 선택하세요...", options=options, custom_id="recipe_select")

    async def callback(self, interaction: discord.Interaction):
        recipe_id = self.values[0]
        recipes = _get_recipes_for_skill(self.skill_id)
        recipe = recipes.get(recipe_id)
        if not recipe:
            await interaction.response.send_message("레시피를 찾을 수 없습니다.", ephemeral=True)
            return

        view: SkillMainView = self.view
        embed, can_craft = make_recipe_detail_embed(self.player, recipe_id, recipe)
        view.clear_items()
        view.add_item(SkillCategorySelect(self.player))
        view.add_item(LifeSkillSelect(self.player))
        view.add_item(RecipeSelect(self.player, self.skill_id, recipes))
        # [제작 실행] 버튼
        craft_btn = Button(
            label="제작 실행",
            style=discord.ButtonStyle.success if can_craft else discord.ButtonStyle.secondary,
            disabled=not can_craft,
            emoji="🔨",
            custom_id=f"craft_exec_{recipe_id}",
        )
        craft_btn.callback = view._make_craft_callback(self.skill_id, recipe_id)
        view.add_item(craft_btn)
        await interaction.response.edit_message(embed=embed, view=view)


class SkillMainView(View):
    def __init__(self, player, potion_engine=None, crafting_engine=None,
                 cooking_engine=None, metallurgy_engine=None):
        super().__init__(timeout=180.0)
        self.player = player
        self.potion_engine = potion_engine
        self.crafting_engine = crafting_engine
        self.cooking_engine = cooking_engine
        self.metallurgy_engine = metallurgy_engine
        self.current_category = None
        self.add_item(SkillCategorySelect(player))

    def _make_healing_callback(self):
        async def callback(interaction: discord.Interaction):
            from skills_db import RECOVERY_SKILLS
            rank = getattr(self.player, "skill_ranks", {}).get("healing", "연습")
            heal_data = RECOVERY_SKILLS.get("healing", {})
            heal_amount = heal_data.get("heal_amount", {}).get(rank, 20)
            mp_cost = heal_data.get("mp_cost", {}).get(rank, 10)
            if self.player.mp < mp_cost:
                await interaction.response.send_message(
                    f"❌ MP가 부족합니다! (필요: {mp_cost}, 보유: {self.player.mp})",
                    ephemeral=True,
                )
                return
            self.player.mp -= mp_cost
            old_hp = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
            healed = self.player.hp - old_hp
            embed = discord.Embed(
                title="💚 힐링",
                description=(
                    f"HP +{healed} 회복! ({old_hp} → {self.player.hp}/{self.player.max_hp})\n"
                    f"MP -{mp_cost} 소모 (현재: {self.player.mp}/{self.player.max_mp})"
                ),
                color=0x2ECC71,
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        return callback

    def _make_craft_callback(self, skill_id: str, recipe_id: str):
        async def callback(interaction: discord.Interaction):
            result = ""
            if skill_id == "alchemy" and self.potion_engine:
                result = self.potion_engine.craft(recipe_id)
            elif skill_id == "crafting" and self.crafting_engine:
                result = self.crafting_engine.craft(recipe_id)
            elif skill_id == "cooking" and self.cooking_engine:
                result = self.cooking_engine.cook(recipe_id)
            elif skill_id == "metallurgy" and self.metallurgy_engine:
                result = self.metallurgy_engine.smelt(recipe_id)
            else:
                result = "❌ 제작 엔진을 찾을 수 없습니다."

            # 제작 후 임베드 갱신
            recipes = _get_recipes_for_skill(skill_id)
            recipe = recipes.get(recipe_id, {})
            new_embed, can_craft = make_recipe_detail_embed(self.player, recipe_id, recipe)
            # 버튼 상태 갱신
            for child in self.children:
                if hasattr(child, "custom_id") and child.custom_id and child.custom_id.startswith("craft_exec_"):
                    child.disabled = not can_craft
                    child.style = discord.ButtonStyle.success if can_craft else discord.ButtonStyle.secondary

            await interaction.response.edit_message(embed=new_embed, view=self)
            await interaction.followup.send(result, ephemeral=False)
        return callback


def _get_recipes_for_skill(skill_id: str) -> dict:
    """스킬 ID에 따라 레시피 딕셔너리 반환."""
    if skill_id == "alchemy":
        from potion import POTION_RECIPES
        return POTION_RECIPES
    elif skill_id == "crafting":
        from crafting import CRAFTING_RECIPES
        return CRAFTING_RECIPES
    elif skill_id == "cooking":
        from cooking_db import RECIPES
        return RECIPES
    elif skill_id == "metallurgy":
        from metallurgy import SMELT_RECIPES
        return SMELT_RECIPES
    return {}
