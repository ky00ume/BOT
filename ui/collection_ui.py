"""collection_ui.py — /도감 임베드+탭버튼 UI (JS 도감 시스템 참조)

JS Risulike RPG v9 의 도감 UI 구조를 Discord 봇에 맞게 이식:
  - 카테고리 탭 버튼 행 (낚시/요리/채집/채광)
  - 활성 탭: 강조 스타일, 비활성: 회색
  - 전체 수집률 progress bar
  - 등급별 그룹(Legendary → Epic → Rare → Normal) + 색상
"""
import discord
from ui.view_timeouts import GAME_VIEW_TIMEOUT
from discord.ui import View, Button
from collection import collection_manager, CATEGORY_ICONS, COLLECTION_MILESTONES, CATEGORY_MILESTONES, get_collection_catalog
from ui.ui_theme import GRADE_EMBED_COLOR

GRADE_ORDER = ["Legendary", "Epic", "Rare", "Normal"]
GRADE_LABEL = {
    "Legendary": "✦ 전설",
    "Epic":      "❖ 영웅",
    "Rare":      "◆ 희귀",
    "Normal":    "⚬ 일반",
}
GRADE_EMOJI = {"Legendary": "✦", "Epic": "❖", "Rare": "◆", "Normal": "⚬"}


def _progress_bar(collected: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return f"{'░' * width}  0%"
    ratio = collected / total
    filled = round(ratio * width)
    return f"{'█' * filled}{'░' * (width - filled)}  {int(ratio * 100)}%"


def make_collection_embed(category: str) -> discord.Embed:
    """실제 DB 전체 슬롯을 기준으로 발견/미발견을 함께 보여준다."""
    icon = CATEGORY_ICONS.get(category, "📖")
    cat_data: dict = collection_manager.to_dict().get(category, {})
    catalog = get_collection_catalog(category)
    collected = len({row["id"] for row in catalog if row["id"] in cat_data})
    total = len(catalog)
    embed = discord.Embed(
        title=f"📖 {icon} {category} 도감",
        description=f"**{collected} / {total}종** 발견\n{_progress_bar(collected, total)}",
        color=0x1A6878,
    )
    targets = CATEGORY_MILESTONES.get(category, ())
    nxt = next((n for n in targets if collected < n), None)
    if nxt:
        embed.add_field(name="🎁 다음 카테고리 보상", value=f"**{nxt}종**까지 앞으로 **{nxt-collected}종**", inline=False)
    elif targets:
        embed.add_field(name="🏆 카테고리 완성", value="모든 수집 보상을 달성했습니다.", inline=False)

    if category == "몬스터":
        zones: dict[str, list[dict]] = {}
        for row in catalog: zones.setdefault(row.get("zone", "기타"), []).append(row)
        for zone, rows in zones.items():
            found = sum(r["id"] in cat_data for r in rows)
            complete = found == len(rows)
            lines = [f"{'✅' if r['id'] in cat_data else '❔'} **{r['name']}**" if r['id'] in cat_data else "❔ ???" for r in rows]
            if complete:
                lines.append("🏆 **지역 완성 보상:** 기력 최대치 +1")
            else:
                lines.append(f"🎁 완성까지 **{len(rows)-found}종** · 보상: 기력 최대치 +1")
            embed.add_field(name=f"{'🏆' if complete else '🗺️'} {zone}  {found}/{len(rows)}", value="\n".join(lines), inline=False)
    else:
        by_grade: dict[str, list[dict]] = {g: [] for g in GRADE_ORDER}
        for row in catalog: by_grade.setdefault(row.get("grade", "Normal"), []).append(row)
        for grade in GRADE_ORDER:
            rows = by_grade.get(grade, [])
            if not rows: continue
            found = sum(r["id"] in cat_data for r in rows)
            lines=[]
            for r in rows:
                info=cat_data.get(r["id"])
                if info:
                    size=info.get("best_size",0); extra=f" `{size:.1f}cm`" if size else ""
                    lines.append(f"{GRADE_EMOJI[grade]} **{info.get('name',r['name'])}**{extra}")
                else: lines.append("❔ ???")
            value="\n".join(lines); value=value if len(value)<=1020 else value[:1017]+"..."
            embed.add_field(name=f"{GRADE_LABEL[grade]}  {found}/{len(rows)}", value=value, inline=False)
    embed.set_footer(text="???를 발견해 도감을 채우세요 · 발견 종수에 따라 영구 보상이 열립니다")
    return embed


def make_collection_overview_embed() -> discord.Embed:
    """전체 카테고리 수집률 개요 임베드."""
    all_data = collection_manager.to_dict()
    total_all = sum(len(v) for v in all_data.values())

    embed = discord.Embed(
        title="📖 수집 도감",
        description=f"총 **{total_all}종** 수집 완료\n\n새로운 종류를 발견할수록 영구 보너스가 열립니다.",
        color=0xC87800,
    )
    for cat, icon in CATEGORY_ICONS.items():
        cat_data = all_data.get(cat, {})
        catalog = get_collection_catalog(cat)
        total = len(catalog)
        count = sum(row["id"] in cat_data for row in catalog)
        by_grade = {g: 0 for g in GRADE_ORDER}
        for info in cat_data.values():
            g = info.get("grade", "Normal")
            if g in by_grade:
                by_grade[g] += 1

        grade_summary = "  ".join(
            f"{GRADE_EMOJI[g]}×{by_grade[g]}"
            for g in GRADE_ORDER
            if by_grade[g] > 0
        ) or "—"
        embed.add_field(
            name=f"{icon} {cat}",
            value=f"**{count}/{total}종** · {_progress_bar(count, total, 6)}\n{grade_summary}",
            inline=True,
        )
    next_m = collection_manager.next_milestone()
    if next_m:
        remain = next_m["count"] - total_all
        embed.add_field(name="🎁 다음 수집 보너스", value=f"**{next_m['count']}종 · {next_m['label']}**\n{next_m['bonus']}  ·  앞으로 **{remain}종**", inline=False)
    else:
        embed.add_field(name="🏆 수집 보너스", value="모든 수집 마일스톤을 달성했습니다!", inline=False)
    unlocked = [m for m in COLLECTION_MILESTONES if total_all >= m["count"]]
    if unlocked:
        embed.add_field(name="✨ 획득한 보너스", value="\n".join(f"✅ {m['count']}종 · {m['bonus']}" for m in unlocked[-4:]), inline=False)
    embed.set_footer(text="카테고리를 눌러 발견 기록을 확인하세요 · 새 종류 수집이 핵심입니다")
    return embed


class CollectionView(View):
    """도감 탭 버튼 뷰."""

    CATEGORIES = list(CATEGORY_ICONS.keys())  # ["낚시", "요리", "채집", "채광"]

    def __init__(self, author_id: int):
        super().__init__(timeout=GAME_VIEW_TIMEOUT)
        self.author_id = author_id
        self._active: str | None = None  # 현재 선택된 카테고리
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for cat in self.CATEGORIES:
            icon = CATEGORY_ICONS[cat]
            is_active = self._active == cat
            btn = Button(
                label=f"{icon} {cat}",
                style=discord.ButtonStyle.primary if is_active else discord.ButtonStyle.secondary,
                custom_id=f"col_tab_{cat}",
                row=0,
            )
            btn.callback = self._make_callback(cat)
            self.add_item(btn)

    def _make_callback(self, category: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("이 도감은 다른 사용자의 것입니다.", ephemeral=True)
                return
            self._active = category
            self._build_buttons()
            embed = make_collection_embed(category)
            await interaction.response.edit_message(embed=embed, view=self)
        return callback
