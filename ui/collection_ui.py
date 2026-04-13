"""collection_ui.py — /도감 임베드+탭버튼 UI (JS 도감 시스템 참조)

JS Risulike RPG v9 의 도감 UI 구조를 Discord 봇에 맞게 이식:
  - 카테고리 탭 버튼 행 (낚시/요리/채집/채광)
  - 활성 탭: 강조 스타일, 비활성: 회색
  - 전체 수집률 progress bar
  - 등급별 그룹(Legendary → Epic → Rare → Normal) + 색상
"""
import discord
from discord.ui import View, Button
from collection import collection_manager, CATEGORY_ICONS
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
    """카테고리 도감 임베드 생성."""
    icon = CATEGORY_ICONS.get(category, "📖")
    cat_data: dict = collection_manager.to_dict().get(category, {})

    collected = len(cat_data)

    # 등급별로 묶기
    by_grade: dict[str, list] = {g: [] for g in GRADE_ORDER}
    for item_id, info in cat_data.items():
        grade = info.get("grade", "Normal")
        if grade not in by_grade:
            grade = "Normal"
        by_grade[grade].append((item_id, info))

    # 색상: 가장 높은 등급의 색 사용
    embed_color = 0x1A6878  # 기본 (낚시 색)
    for g in GRADE_ORDER:
        if by_grade[g]:
            embed_color = GRADE_EMBED_COLOR.get(g, 0x4A7EC2)
            break

    bar = _progress_bar(collected, collected)  # 전체 종 수 미확정 → 수집 수만 표시
    embed = discord.Embed(
        title=f"📖 {icon} {category} 도감",
        description=f"수집 완료: **{collected}종**\n\n",
        color=embed_color,
    )

    if not cat_data:
        embed.description = "아직 등록된 항목이 없습니다.\n게임을 통해 아이템을 발견해보세요!"
        return embed

    for grade in GRADE_ORDER:
        items = by_grade[grade]
        if not items:
            continue

        emoji = GRADE_EMOJI[grade]
        label = GRADE_LABEL[grade]

        # 항목 목록 텍스트 (한 줄에 최대 2개씩)
        lines = []
        for item_id, info in sorted(items, key=lambda x: x[1].get("name", "")):
            name = info.get("name", item_id)
            count = info.get("count", 1)
            best_size = info.get("best_size", 0)
            size_str = f" `{best_size:.1f}cm`" if best_size > 0 else ""
            lines.append(f"{emoji} **{name}**{size_str} ×{count}")

        # Discord embed field value 한도: 1024자
        value = "\n".join(lines)
        if len(value) > 1020:
            value = value[:1017] + "..."

        embed.add_field(
            name=f"{label}  ({len(items)}종)",
            value=value,
            inline=False,
        )

    embed.set_footer(text="탭 버튼으로 카테고리를 전환하세요")
    return embed


def make_collection_overview_embed() -> discord.Embed:
    """전체 카테고리 수집률 개요 임베드."""
    all_data = collection_manager.to_dict()
    total_all = sum(len(v) for v in all_data.values())

    embed = discord.Embed(
        title="📖 수집 도감",
        description=f"총 **{total_all}종** 수집 완료\n\n탭을 선택해 카테고리별 도감을 확인하세요.",
        color=0xC87800,
    )
    for cat, icon in CATEGORY_ICONS.items():
        cat_data = all_data.get(cat, {})
        count = len(cat_data)
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
            value=f"**{count}종** 수집\n{grade_summary}",
            inline=True,
        )
    embed.set_footer(text="아래 버튼으로 카테고리를 선택하세요")
    return embed


class CollectionView(View):
    """도감 탭 버튼 뷰."""

    CATEGORIES = list(CATEGORY_ICONS.keys())  # ["낚시", "요리", "채집", "채광"]

    def __init__(self, author_id: int):
        super().__init__(timeout=120.0)
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
