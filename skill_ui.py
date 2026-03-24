"""skill_ui.py — /스킬 통합 UI (임베드 + 드롭다운 방식)

카테고리 드롭다운:
  전투 스킬 → 보유 스킬마다 [ℹ️ 스킬이름] 버튼 + 랭크 배지 + 경험치 게이지
  마법 스킬 → 동일 + 힐링은 [사용] 버튼 추가
  생활 스킬 → 레시피 드롭다운 → 재료 임베드 (부족=빨강) → [제작 실행] 버튼
"""
import discord
from discord.ui import View, Button, Select
from ui_theme import EMBED_COLOR
from skills_db import (
    COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS,
    OTHER_SKILLS, MASTERY_SKILLS, RANK_ORDER,
    RANK_UP_THRESHOLD, SKILL_RANK_THRESHOLD,
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

# 버튼 당 최대 표시 스킬 수 (카테고리 select 1 + 버튼들, Discord 한계 25)
_MAX_SKILL_BUTTONS = 20


def _rank_badge(rank: str) -> str:
    r = {
        "연습": "🔰",
        "F": "🅵", "E": "🅴", "D": "🅳", "C": "🅲",
        "B": "🅱", "A": "🅰",
    }
    return r.get(rank, f"[{rank}]")


def _exp_gauge(skill_id: str, rank: str, current_exp: float) -> str:
    """다음 랭크까지 경험치 게이지 문자열 반환."""
    threshold_map = SKILL_RANK_THRESHOLD.get(skill_id, RANK_UP_THRESHOLD)
    threshold = threshold_map.get(rank)
    if threshold is None or threshold == 0:
        return "▓▓▓▓▓ MAX"
    ratio = min(1.0, current_exp / threshold)
    filled = int(ratio * 5)
    bar = "▓" * filled + "░" * (5 - filled)
    pct = int(ratio * 100)
    return f"{bar} {pct}%"


def make_skill_detail_embed(player, skill_id: str) -> discord.Embed:
    """스킬 상세 임베드 생성."""
    skill_ranks = getattr(player, "skill_ranks", {})
    skill_exp   = getattr(player, "skill_exp", {})
    rank = skill_ranks.get(skill_id, "연습")
    exp  = skill_exp.get(skill_id, 0.0)

    # 스킬 정의 찾기
    all_skill_dbs = [
        COMBAT_SKILLS, MAGIC_SKILLS, RECOVERY_SKILLS,
        OTHER_SKILLS, MASTERY_SKILLS,
    ]
    sdata = None
    for db in all_skill_dbs:
        if skill_id in db:
            sdata = db[skill_id]
            break
    if sdata is None:
        return discord.Embed(title="❌ 스킬 정보 없음", color=0xFF0000)

    name = sdata.get("name", skill_id)
    desc = sdata.get("desc", "")

    # 게이지
    gauge = _exp_gauge(skill_id, rank, exp)
    rank_badge = _rank_badge(rank)

    # 다음 랭크
    try:
        rank_idx = RANK_ORDER.index(rank)
        next_rank = RANK_ORDER[rank_idx + 1] if rank_idx + 1 < len(RANK_ORDER) else None
    except ValueError:
        next_rank = None

    embed = discord.Embed(
        title=f"📖 {name}",
        description=f"*{desc}*",
        color=0x5865F2,
    )
    embed.add_field(
        name="현재 랭크",
        value=f"{rank_badge} **{rank}**  EXP: {exp:.0f}\n📊 {gauge}",
        inline=False,
    )
    if next_rank:
        embed.add_field(name="다음 랭크", value=f"**{next_rank}**", inline=True)

    # 스킬 종류별 수치
    if skill_id in COMBAT_SKILLS:
        # 전투 스킬
        stats = []
        if "damage_bonus" in sdata:
            val = sdata["damage_bonus"].get(rank, "?")
            stats.append(f"⚔️ 피해 배율: **×{val}**")
        if "damage_reduce" in sdata:
            val = sdata["damage_reduce"].get(rank, "?")
            stats.append(f"🛡️ 피해 감소: **{int(val*100)}%**")
        if "counter_multiplier" in sdata:
            val = sdata["counter_multiplier"].get(rank, "?")
            stats.append(f"🔄 반격 배율: **×{val}**")
        if "aoe_multiplier" in sdata:
            val = sdata["aoe_multiplier"].get(rank, "?")
            stats.append(f"💥 광역 배율: **×{val}**")
        if stats:
            embed.add_field(name="📈 현재 수치", value="\n".join(stats), inline=False)

    elif skill_id in MAGIC_SKILLS:
        stats = []
        mp_cost = sdata.get("mp_cost", {}).get(rank, "?")
        damage  = sdata.get("damage", {}).get(rank, "?")
        stats.append(f"🔮 MP 소모: **{mp_cost}**")
        stats.append(f"✨ 마법 피해: **{damage}**")
        embed.add_field(name="📈 현재 수치", value="\n".join(stats), inline=False)

    elif skill_id in RECOVERY_SKILLS:
        stats = []
        mp_cost    = sdata.get("mp_cost", {}).get(rank, "?")
        heal_amount = sdata.get("heal_amount", {}).get(rank, "?")
        stats.append(f"🔮 MP 소모: **{mp_cost}**")
        stats.append(f"💚 회복량: **{heal_amount}**")
        embed.add_field(name="📈 현재 수치", value="\n".join(stats), inline=False)

    elif skill_id in MASTERY_SKILLS:
        stat_bonus = sdata.get("stat_bonus", {}).get(rank, {})
        if stat_bonus:
            _stat_names = {"str": "힘", "int": "지력", "dex": "민첩",
                           "will": "의지", "luck": "운",
                           "max_hp": "최대HP", "max_energy": "최대기력"}
            bonus_str = "  ".join(
                f"{_stat_names.get(k, k)} +{v}" for k, v in stat_bonus.items()
            )
            embed.add_field(name="📈 랭크 보너스", value=bonus_str, inline=False)

    elif skill_id in OTHER_SKILLS:
        if skill_id in _LIFE_SKILL_ENGINE:
            embed.add_field(
                name="💡 사용법",
                value="`/스킬` → 생활 스킬 드롭다운 → 이 스킬 선택 → 레시피 제작",
                inline=False,
            )

    embed.set_footer(text=f"스킬 ID: {skill_id}")
    return embed


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
    skill_exp   = getattr(player, "skill_exp", {})

    if category == "combat":
        title = "⚔️ 전투 스킬"
        lines = []
        for sid, sdata in COMBAT_SKILLS.items():
            rank = skill_ranks.get(sid)
            if rank:
                exp = skill_exp.get(sid, 0)
                gauge = _exp_gauge(sid, rank, exp)
                lines.append(
                    f"**{sdata['name']}** {_rank_badge(rank)}\n"
                    f"> {gauge}  EXP: {exp:.0f}\n"
                    f"> {sdata['desc']}"
                )
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
                exp = skill_exp.get(sid, 0)
                gauge = _exp_gauge(sid, rank, exp)
                extra = ""
                if sid == "healing":
                    extra = "\n> 💡 힐링은 전투 외에서도 [사용] 버튼으로 HP를 회복할 수 있습니다."
                else:
                    extra = "\n> ⚠️ 공격 마법은 전투 중에만 사용 가능합니다."
                lines.append(
                    f"**{sdata['name']}** {_rank_badge(rank)}\n"
                    f"> {gauge}  EXP: {exp:.0f}\n"
                    f"> {sdata['desc']}{extra}"
                )
        desc = "\n\n".join(lines) if lines else "보유한 마법 스킬이 없습니다."
        embed = discord.Embed(title=title, description=desc, color=0x9B59B6)

    else:  # life
        title = "🌿 생활 스킬"
        lines = []
        for sid, sdata in OTHER_SKILLS.items():
            rank = skill_ranks.get(sid)
            if rank:
                exp = skill_exp.get(sid, 0)
                gauge = _exp_gauge(sid, rank, exp)
                note = ""
                if sid in _LIFE_SKILL_ENGINE:
                    note = "\n> ✅ 스킬 선택 시 레시피 창이 열립니다."
                lines.append(
                    f"**{sdata['name']}** {_rank_badge(rank)}\n"
                    f"> {gauge}  EXP: {exp:.0f}\n"
                    f"> {sdata['desc']}{note}"
                )
        desc = "\n\n".join(lines) if lines else "보유한 생활 스킬이 없습니다."
        embed = discord.Embed(title=title, description=desc, color=0x2ECC71)

    embed.set_footer(text="아래 버튼을 눌러 스킬 상세 정보를 확인하세요.")
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

        view.clear_items()
        view.add_item(SkillCategorySelect(self.player))

        if category == "life":
            view.add_item(LifeSkillSelect(self.player))
        elif category == "magic":
            # 마법 스킬 정보 버튼 추가
            _add_skill_info_buttons(view, self.player, {**MAGIC_SKILLS, **RECOVERY_SKILLS})
            # 힐링 스킬이 있으면 [사용] 버튼 추가
            if "healing" in getattr(self.player, "skill_ranks", {}):
                if len(view.children) < 24:
                    btn = Button(label="힐링 사용", style=discord.ButtonStyle.success, emoji="💚")
                    btn.callback = view._make_healing_callback()
                    view.add_item(btn)
        else:  # combat
            _add_skill_info_buttons(view, self.player, COMBAT_SKILLS)

        await interaction.response.edit_message(embed=embed, view=view)


def _add_skill_info_buttons(view: "SkillMainView", player, skill_db: dict):
    """보유 스킬마다 [ℹ️ 스킬이름] 정보 버튼을 view에 추가한다."""
    skill_ranks = getattr(player, "skill_ranks", {})
    skill_exp   = getattr(player, "skill_exp", {})
    count = 0
    for sid, sdata in skill_db.items():
        if sid not in skill_ranks:
            continue
        if len(view.children) >= 24:  # Discord 25개 한계 (select 1개 포함)
            break
        rank = skill_ranks[sid]
        exp  = skill_exp.get(sid, 0.0)
        gauge = _exp_gauge(sid, rank, exp)
        label = f"ℹ️ {sdata['name']} [{rank}] {gauge}"
        # Discord 버튼 label 최대 80자
        if len(label) > 80:
            label = label[:79]
        btn = Button(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"skill_info_{sid}",
        )
        btn.callback = view._make_skill_detail_callback(sid)
        view.add_item(btn)
        count += 1


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
        view.clear_items()
        view.add_item(SkillCategorySelect(self.player))
        view.add_item(LifeSkillSelect(self.player))
        if recipes:
            view.add_item(RecipeSelect(self.player, skill_id, recipes))

        try:
            from bg3_renderer import get_renderer, render_async
            skill_name = OTHER_SKILLS.get(skill_id, {}).get("name", skill_id)
            rank = getattr(self.player, "skill_ranks", {}).get(skill_id, "연습")
            recipes_info = []
            for rid, recipe in list(recipes.items())[:12]:
                rank_req = recipe.get("rank_req", "연습")
                try:
                    unlocked = RANK_ORDER.index(rank) >= RANK_ORDER.index(rank_req)
                except Exception:
                    unlocked = True
                recipes_info.append((recipe.get("name", rid), rank_req, unlocked))
            r = get_renderer()
            buf = await render_async(r.render_recipe_list, skill_name, rank, recipes_info)
            await interaction.response.edit_message(
                attachments=[discord.File(buf, filename="recipe_list.png")],
                embed=None,
                view=view,
            )
        except Exception:
            embed = make_recipe_list_embed(self.player, skill_id, recipes)
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
        # 재료 현황 계산
        from items import ALL_ITEMS
        can_craft = True
        rows = []
        for ing_id, need in recipe.get("ingredients", {}).items():
            ing_name = ALL_ITEMS.get(ing_id, {}).get("name", ing_id)
            have = self.player.inventory.get(ing_id, 0)
            ok = have >= need
            if not ok:
                can_craft = False
            rows.append({"label": f"[{'O' if ok else 'X'}] {ing_name}", "value": f"{have}/{need}개"})
        tool_req = recipe.get("tool_req")
        if tool_req:
            tool_name = ALL_ITEMS.get(tool_req, {}).get("name", tool_req)
            have_tool = self.player.inventory.get(tool_req, 0)
            if have_tool == 0:
                can_craft = False
            rows.append({"label": f"[{'O' if have_tool else 'X'}] 도구", "value": tool_name})

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

        try:
            from bg3_renderer import get_renderer, render_async
            r = get_renderer()
            grade    = "Normal" if can_craft else "Fail"
            subtitle = "✅ 제작 가능!" if can_craft else "❌ 재료 부족"
            footer   = "[제작 실행] 버튼으로 제작하세요." if can_craft else "재료를 먼저 모아주세요."
            buf = await render_async(
                r.render_card,
                recipe.get("name", recipe_id),
                rows,
                grade=grade,
                subtitle=subtitle,
                system_key="craft",
                footer=footer,
            )
            await interaction.response.edit_message(
                attachments=[discord.File(buf, filename="recipe_detail.png")],
                embed=None,
                view=view,
            )
        except Exception:
            embed, _ = make_recipe_detail_embed(self.player, recipe_id, recipe)
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

    def _make_skill_detail_callback(self, skill_id: str):
        async def callback(interaction: discord.Interaction):
            embed = make_skill_detail_embed(self.player, skill_id)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        return callback

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
            try:
                from save_manager import save_manager
                save_manager.save(self.player)
            except Exception:
                pass
        return callback

    def _make_craft_callback(self, skill_id: str, recipe_id: str):
        async def callback(interaction: discord.Interaction):
            result = None
            if skill_id == "alchemy" and self.potion_engine:
                result = self.potion_engine.craft(recipe_id)
            elif skill_id == "crafting" and self.crafting_engine:
                result = self.crafting_engine.craft(recipe_id)
            elif skill_id == "cooking" and self.cooking_engine:
                result = self.cooking_engine.cook(recipe_id)
            elif skill_id == "metallurgy" and self.metallurgy_engine:
                result = self.metallurgy_engine.smelt(recipe_id)

            if result is None:
                await interaction.response.send_message("제작 엔진을 찾을 수 없습니다.", ephemeral=True)
                return

            # 제작 후 재료 현황 갱신
            recipes = _get_recipes_for_skill(skill_id)
            recipe = recipes.get(recipe_id, {})
            from items import ALL_ITEMS as _AI
            can_craft = True
            detail_rows = []
            for ing_id, need in recipe.get("ingredients", {}).items():
                ing_name = _AI.get(ing_id, {}).get("name", ing_id)
                have = self.player.inventory.get(ing_id, 0)
                ok = have >= need
                if not ok:
                    can_craft = False
                detail_rows.append({"label": f"[{'O' if ok else 'X'}] {ing_name}", "value": f"{have}/{need}개"})
            for child in self.children:
                if hasattr(child, "custom_id") and child.custom_id and child.custom_id.startswith("craft_exec_"):
                    child.disabled = not can_craft
                    child.style = discord.ButtonStyle.success if can_craft else discord.ButtonStyle.secondary

            try:
                from bg3_renderer import get_renderer, render_async
                _r = get_renderer()
                _grade  = "Normal" if can_craft else "Fail"
                _sub    = "✅ 제작 가능!" if can_craft else "❌ 재료 부족"
                _footer = "[제작 실행] 버튼으로 제작하세요." if can_craft else "재료를 먼저 모아주세요."
                _buf = await render_async(
                    _r.render_card,
                    recipe.get("name", recipe_id),
                    detail_rows,
                    grade=_grade,
                    subtitle=_sub,
                    system_key="craft",
                    footer=_footer,
                )
                await interaction.response.edit_message(
                    attachments=[discord.File(_buf, filename="recipe_detail.png")],
                    embed=None,
                    view=self,
                )
            except Exception:
                new_embed, _ = make_recipe_detail_embed(self.player, recipe_id, recipe)
                await interaction.response.edit_message(embed=new_embed, view=self)

            # BG3 스타일 이미지 결과 카드 전송
            try:
                from bg3_renderer import get_renderer, render_async
                r = get_renderer()
                if isinstance(result, dict):
                    if result.get("success"):
                        buf = await render_async(
                            r.render_craft_result,
                            recipe_name=result.get("recipe_name", "제작"),
                            result_item_name=result.get("result_name", "???"),
                            result_grade=result.get("result_grade", "Normal"),
                            ingredients=result.get("ingredients"),
                            exp_gained=result.get("exp", 0),
                            rank_up_msg=result.get("rank_up_msg", ""),
                            system_key=result.get("system_key", "craft"),
                            footer="제작 완료!" if result.get("system_key") == "craft" else "완료!",
                        )
                    else:
                        buf = await render_async(
                            r.render_craft_fail,
                            recipe_name=result.get("recipe_name", "제작"),
                            reason=result.get("error", "알 수 없는 오류"),
                            exp_gained=result.get("exp", 0),
                            rank_up_msg=result.get("rank_up_msg", ""),
                            system_key=result.get("system_key", "craft"),
                            footer="제작 실패" if not result.get("crafted_but_failed") else "실패...",
                        )
                    await interaction.followup.send(
                        file=discord.File(fp=buf, filename="craft_result.png"),
                        ephemeral=False,
                    )
                else:
                    # fallback: 문자열 결과 (호환)
                    await interaction.followup.send(str(result), ephemeral=False)
            except Exception:
                # PIL 미설치 등 폴백: 텍스트로 전송
                if isinstance(result, dict):
                    msg = result.get("result_name") or result.get("error", "결과 없음")
                    await interaction.followup.send(f"결과: {msg}", ephemeral=False)
                else:
                    await interaction.followup.send(str(result), ephemeral=False)
            try:
                from save_manager import save_manager
                save_manager.save(self.player)
            except Exception:
                pass
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

