"""care_ui.py — 비전의 탑 상층 · 츄라이더의 숨은 보금자리 돌봄 UI"""
import asyncio
import discord
from ui.view_timeouts import CARE_VIEW_TIMEOUT
from ui.expiring_view import ExpiringView
import random
import time as _time
from utils.logger import setup_logger
logger = setup_logger('care_ui')
from bg3_renderer import get_renderer
from costume_data import (
    COSTUME_ITEMS, COSTUME_FLAVOR, SNACK_ITEMS, SNACK_RECIPES, COSTUME_RECIPES,
    GRADE_EMOJI, GRADE_LABELS,
)
from database import save_player_to_db
from core.events import GameEvent, event_store
from core.bond import bond_service
from core.pet_state import observe_pet
from care import get_care_state, CHURIDER_SPEECH


# ── 헬퍼: stat bar ──────────────────────────────────────────────────────────
def _bar(value: int, max_val: int = 100, length: int = 10) -> str:
    filled = round(value / max_val * length)
    return "█" * filled + "░" * (length - filled)


def _make_room_card(player):
    """마제스티와 카르니스의 생활권 한구석에 만든 츄라이더의 보금자리를 보여준다."""
    obs = observe_pet(player)
    rows = [
        {"label": "🕷️ 지금", "value": obs.headline},
        {"label": "👀 모습", "value": obs.body},
        {"label": "💗 기분", "value": obs.mood},
        {"label": "💤 기운", "value": obs.energy},
        {"label": "🫶 기억", "value": obs.care_memory},
        {"label": "🧵 인연", "value": obs.relationship},
        {"label": "🌱 버릇", "value": obs.habit},
    ]
    buf = get_renderer().render_card(title="🕷️ 츄라이더 · 책장 뒤 작은 틈", rows=rows, system_key="system", grade="Normal", footer="비전의 탑 상층 · 숨은 보금자리")
    return discord.File(buf, filename="care_room.png")


def _band_word(value, low, mid, high):
    if value < 34:
        return low
    if value < 67:
        return mid
    return high


def _status_line(player) -> str:
    state = get_care_state(player)
    hunger = _band_word(state["hunger"], "든든함", "보통", "배고픔")
    clean = _band_word(state["cleanliness"], "더러움", "보통", "깨끗함")
    fatigue = _band_word(player.fatigue, "멀쩡함", "조금 피곤", "많이 피곤")
    mood = _band_word(player.stability, "예민함", "평온함", "좋음")
    return f"🍖 {hunger}　🫧 {clean}　💤 {fatigue}　✨ {mood}"


def _nest_trace(player) -> str:
    state = get_care_state(player)
    if state["boredom"] >= 70:
        return "실뭉치가 여기저기 풀려 있고 작은 물건 몇 개가 자리를 옮겨 놓았습니다. 혼자 꽤 부산하게 놀았던 모양입니다."
    if state["cleanliness"] < 35:
        return "담요 가장자리와 바닥에 마른 흙자국이 이어집니다. 들어오기 전에 몸을 제대로 털지 않은 모양입니다."
    return "담요 조각과 실, 주워 온 작은 물건들이 츄라이더 나름의 순서로 모여 있습니다."


def _observation_details(player) -> list[str]:
    state = get_care_state(player)
    details = []
    if state["hunger"] >= 70:
        details.append("배 쪽을 한 번 내려다본 뒤 먹을거리 냄새가 나는 쪽으로 시선이 자꾸 갑니다.")
    elif state["hunger"] <= 20:
        details.append("배가 찬 모양인지 먹을거리 쪽은 힐끗 보고도 금세 관심을 거둡니다.")
    else:
        details.append("배가 고파 보이지도, 특별히 든든해 보이지도 않습니다. 지금은 먹을 것보다 주변에 더 관심이 많습니다.")
    if state["cleanliness"] < 35:
        details.append("거미 복부와 다리 관절 사이에 먼지와 마른 얼룩이 꽤 남아 있습니다.")
    elif state["cleanliness"] >= 85:
        details.append("흰 피부의 드로우 상체와 검은 거미 복부·여덟 다리가 막 닦아낸 듯 말끔합니다.")
    else:
        details.append("다리 끝 몇 군데에 생활 먼지가 조금 묻어 있지만 당장 씻길 정도는 아닙니다.")
    if player.fatigue >= 65:
        details.append("상체를 낮게 기대고 복부도 바닥 가까이 붙였습니다. 여덟 다리가 평소보다 넓게 퍼져 있습니다.")
    elif player.fatigue <= 30:
        details.append("앞다리를 가볍게 들었다 놓으며 주변 소리에 바로 반응합니다. 아직 기운이 남아 있습니다.")
    else:
        details.append("앞다리 하나를 접었다 폈다 하며 편한 자세를 찾고 있습니다.")
    equipped_flavor = []
    for item_id in getattr(player, "costume", {}).values():
        if item_id:
            flavor = COSTUME_FLAVOR.get(item_id, {}).get("observe")
            if flavor:
                equipped_flavor.append(flavor)
    details.extend(equipped_flavor)

    traces = state.get("traces", [])
    if traces:
        details.append(traces[-1].get("text", ""))
    details.append(_nest_trace(player))
    return [detail for detail in details if detail]


def _featured_costume(player):
    try:
        item_id = player.get_featured_costume()
    except Exception:
        item_id = getattr(player, "_flags", {}).get("featured_costume")
    if not item_id:
        return None, None
    return item_id, COSTUME_ITEMS.get(item_id, {})


def _churider_mark(player) -> str:
    _item_id, item = _featured_costume(player)
    if not item:
        return "🕷️"
    return f"🕷️ {item.get('emoji', '✨')}"


def _make_room_embed(player):
    """Compact home surface: status is visible; details belong to interactions."""
    try:
        from app_context import get_care_manager
        get_care_manager().finish_rest_if_ready(player)
    except Exception:
        pass
    obs = observe_pet(player)
    rest = None
    try:
        # Caller normally owns the manager; this is only a visual hint from persisted state.
        state = get_care_state(player)
        until = float(state.get("rest_until", 0) or 0)
        if until > _time.time():
            remaining = int(until - _time.time())
            rest = f"🕷️💤 쉬는 중 · {remaining // 60}분 {remaining % 60:02d}초"
    except Exception:
        rest = None
    description = rest or obs.headline
    embed = discord.Embed(
        title=f"{_churider_mark(player)} 츄라이더",
        description=description,
        color=0x544766,
    )
    embed.add_field(name="상태", value=_status_line(player), inline=False)
    equipped = []
    slot_labels = {"toy": "🪄", "hat": "🎀", "outfit": "👗", "shoes": "👢", "accessory": "💎"}
    for slot in ("toy", "hat", "outfit", "shoes", "accessory"):
        item_id = getattr(player, "costume", {}).get(slot)
        if item_id:
            item = COSTUME_ITEMS.get(item_id, {})
            star = "⭐ " if item_id == getattr(player, "get_featured_costume", lambda: None)() else ""
            equipped.append(f"{star}{slot_labels[slot]} {item.get('name', item_id)}")
    if equipped:
        embed.add_field(name="의장", value=" · ".join(equipped), inline=False)
    featured_id, featured = _featured_costume(player)
    if featured_id and featured:
        embed.add_field(name="⭐ 대표 의장", value=f"{featured.get('emoji', '✨')} {featured.get('name', featured_id)}", inline=False)
    return embed


def _result_card(title, rows, grade="Normal"):
    buf = get_renderer().render_card(
        title=title,
        rows=rows,
        system_key="system",
        grade=grade,
        footer="돌봄 시스템",
    )
    return discord.File(buf, filename="care_result.png")


# ── 의장 관리 서브 View ──────────────────────────────────────────────────────
class CostumeManageView(ExpiringView):
    SLOT_LABELS = {
        "toy":       "🪄 장난감",
        "hat":       "🎀 모자",
        "outfit":    "👗 의상",
        "shoes":     "👢 신발",
        "accessory": "💎 악세사리",
    }

    def __init__(self, player, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player      = player
        self.parent_view = parent_view
        self._message    = None
        self._equip_slot = None   # 장착할 때 선택된 슬롯
        self._selected_item = None

        # 장착 버튼 (슬롯별)
        for slot, label in self.SLOT_LABELS.items():
            btn = discord.ui.Button(
                label=f"{label} 장착",
                style=discord.ButtonStyle.primary,
                custom_id=f"equip_{slot}",
                row=0 if slot in ("toy", "hat") else 1 if slot in ("outfit", "shoes") else 2,
            )
            btn.callback = self._make_equip_cb(slot)
            self.add_item(btn)

        # 해제 버튼
        unequip_btn = discord.ui.Button(
            label="🗑️ 해제",
            style=discord.ButtonStyle.danger,
            custom_id="unequip_costume",
            row=2,
        )
        unequip_btn.callback = self._on_unequip_select
        self.add_item(unequip_btn)

        featured_btn = discord.ui.Button(
            label="⭐ 대표 의장",
            style=discord.ButtonStyle.success,
            custom_id="featured_costume",
            row=3,
        )
        featured_btn.callback = self._on_featured_select
        self.add_item(featured_btn)

        # 뒤로 가기
        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_costume",
            row=4,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    def _make_equip_cb(self, slot: str):
        async def cb(interaction: discord.Interaction):
            self._equip_slot = slot
            # 해당 슬롯 의장 아이템 목록을 인벤에서 검색
            from items import ALL_ITEMS
            options = []
            h_inv = self.player.get_hyness_inventory()
            for item_id, count in h_inv.items():
                item = ALL_ITEMS.get(item_id, {})
                if item.get("type") == "costume" and item.get("slot") == slot:
                    grade = item.get("grade", "일반")
                    icon  = GRADE_EMOJI.get(grade, "⚬")
                    options.append(discord.SelectOption(
                        label=f"{icon} {item.get('name', item_id)} x{count}",
                        value=item_id,
                        description=item.get("description", "")[:50],
                    ))

            if not options:
                slot_label = self.SLOT_LABELS.get(slot, slot)
                file = _result_card(
                    "의장 장착",
                    [{"label": "안내", "value": f"{slot_label}에 장착 가능한 의장 아이템이 없습니다."}],
                    grade="Fail",
                )
                await interaction.response.send_message(file=file, ephemeral=True)
                return

            select = discord.ui.Select(
                placeholder=f"{self.SLOT_LABELS.get(slot, slot)} 슬롯에 장착할 의장 선택...",
                options=options[:25],
                custom_id=f"equip_item_select_{slot}",
            )
            select_view = _ItemSelectView(select, self._on_equip_confirm)
            await interaction.response.send_message(
                content=f"**{self.SLOT_LABELS.get(slot, slot)} 슬롯 장착**\n장착할 의장을 선택합니다.",
                view=select_view,
                ephemeral=True,
            )
        return cb

    async def _on_equip_confirm(self, interaction: discord.Interaction, item_id: str):
        msg = self.player.equip_costume(item_id)
        from items import ALL_ITEMS
        item = ALL_ITEMS.get(item_id, {})
        grade_key = item.get("grade", "일반")
        grade_eng = GRADE_LABELS.get(grade_key, "Normal")
        try:
            save_player_to_db(self.player)
        except Exception as e:
            logger.error("의장 장착 후 저장 실패: %s", e, exc_info=True)
        flavor = COSTUME_FLAVOR.get(item_id, {})
        embed = discord.Embed(
            title=f"{item.get('emoji', '👗')} {item.get('name', item_id)} 장착",
            description=flavor.get("equip") or item.get("description", msg),
            color=0x6D596E,
        )
        embed.add_field(name="기본 설명", value=item.get("description", ""), inline=False)
        await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=None)

    async def _on_unequip_select(self, interaction: discord.Interaction):
        # 장착된 의장 슬롯 목록 표시
        options = []
        for slot, label in self.SLOT_LABELS.items():
            equipped_id = self.player.costume.get(slot)
            if equipped_id:
                from items import ALL_ITEMS
                item = ALL_ITEMS.get(equipped_id, {})
                options.append(discord.SelectOption(
                    label=f"{label}: {item.get('name', equipped_id)}",
                    value=slot,
                ))

        if not options:
            file = _result_card(
                "의장 해제",
                [{"label": "안내", "value": "장착된 의장이 없습니다."}],
                grade="Fail",
            )
            await interaction.response.send_message(file=file, ephemeral=True)
            return

        async def unequip_confirm(inter: discord.Interaction, slot_chosen: str):
            msg = self.player.unequip_costume(slot_chosen)
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("의장 해제 후 저장 실패: %s", e, exc_info=True)
            await inter.response.edit_message(content=None, attachments=[file], view=None)

        select = discord.ui.Select(
            placeholder="해제할 의장 슬롯 선택...",
            options=options,
            custom_id="unequip_slot_select",
        )
        select_view = _ItemSelectView(select, unequip_confirm)
        await interaction.response.send_message(
            content="해제할 의장 슬롯을 선택합니다.",
            view=select_view,
            ephemeral=True,
        )

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=None, attachments=[], embed=_make_room_embed(self.player), view=self.parent_view
        )

    def _build_status_rows(self):
        rows = []
        for slot, label in self.SLOT_LABELS.items():
            equipped_id = self.player.costume.get(slot)
            if equipped_id:
                from items import ALL_ITEMS
                item = ALL_ITEMS.get(equipped_id, {})
                rows.append({"label": label, "value": item.get("name", equipped_id)})
            else:
                rows.append({"label": label, "value": "(없음)"})
        return rows


# ── 간식 주기 서브 View ──────────────────────────────────────────────────────
class SnackFeedView(ExpiringView):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view

        from items import ALL_ITEMS
        options = []

        # Real portable food first: cooked dishes, caught fish, groceries.
        for item_id, count, item in care_manager.available_foods(player):
            grade = item.get("grade", "Normal")
            icon = GRADE_EMOJI.get(grade, "⚬")
            item_type = item.get("type", "")
            kind = "요리" if item_type == "cooked" else "생선" if item_type == "fish" else "먹을거리"
            options.append(discord.SelectOption(
                label=f"{icon} {item.get('name', item_id)} x{count}",
                value=f"food:{item_id}",
                description=f"{kind} · 가방에서 1개 먹입니다."[:50],
            ))

        # Existing crafted treats remain valid and use the dedicated room inventory.
        h_inv = player.get_hyness_inventory()
        for item_id, count in h_inv.items():
            item = ALL_ITEMS.get(item_id, {})
            if item.get("type") == "snack":
                grade = item.get("grade", "Normal")
                icon = GRADE_EMOJI.get(grade, "⚬")
                options.append(discord.SelectOption(
                    label=f"{icon} {item.get('name', item_id)} x{count}",
                    value=f"snack:{item_id}",
                    description="간식 · 돌봄 보관함에서 1개 먹입니다.",
                ))

        if options:
            select = discord.ui.Select(
                placeholder="츄라이더에게 먹일 것을 고릅니다...",
                options=options[:25],
                custom_id="food_select",
            )
            select.callback = self._on_food_select
            self.add_item(select)
        else:
            btn = discord.ui.Button(
                label="지금 먹일 수 있는 음식이 없어요",
                style=discord.ButtonStyle.secondary,
                disabled=True,
            )
            self.add_item(btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_food",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_food_select(self, interaction: discord.Interaction):
        value = interaction.data["values"][0]
        kind, item_id = value.split(":", 1)
        if kind == "food":
            result = self.care_manager.feed_food(self.player, item_id)
        else:
            result = self.care_manager.feed_snack(self.player, item_id)

        if result.get("success"):
            event_store.append(GameEvent(
                event_type="care.feed",
                actor_id=interaction.user.id,
                subject="츄라이더",
                location="비전의 탑",
                payload={"food": result.get("item_name", item_id), "kind": kind},
            ))
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("먹이기 후 저장 실패: %s", e, exc_info=True)

        embed = discord.Embed(
            title="🕷️🍖 먹이기",
            description=result["message"],
            color=0x7B6545 if result.get("success") else 0x6B5C5C,
        )
        if result.get("success") and "hunger_recovery" in result:
            embed.add_field(name="배부름", value=f"허기 -{result['hunger_recovery']:g}", inline=True)
        # Rebuild so consumed items/counts update immediately.
        view = SnackFeedView(self.player, self.care_manager, self.parent_view)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=view)

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=None, attachments=[], embed=_make_room_embed(self.player), view=self.parent_view
        )

class ObserveView(ExpiringView):
    def __init__(self, player, parent_view, *, index=0):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.parent_view = parent_view
        self.index = index
        more = discord.ui.Button(label="👀 조금 더 본다", style=discord.ButtonStyle.primary)
        more.callback = self._more
        self.add_item(more)
        done = discord.ui.Button(label="그만 본다", style=discord.ButtonStyle.secondary)
        done.callback = self._done
        self.add_item(done)

    def make_embed(self):
        details = _observation_details(self.player)
        detail = details[self.index % len(details)]
        embed = discord.Embed(title="🕷️👀 관찰", description=detail, color=0x5E596B)
        embed.add_field(name="상태", value=_status_line(self.player), inline=False)
        return embed

    async def _more(self, interaction):
        details = _observation_details(self.player)
        self.index = (self.index + 1) % len(details)
        view = ObserveView(self.player, self.parent_view, index=self.index)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

    async def _done(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


class PettingView(ExpiringView):
    MAX_STROKES = 3
    SPOTS = [
        ("🫳 머리", "head"),
        ("🤍 배", "belly"),
        ("🕷️ 꼬리", "tail"),
        ("🦵 다리", "legs"),
        ("🤝 손", "hand"),
        ("💨 전부", "all"),
    ]
    # Each spot has several variants per stroke depth. The same three-click session can
    # therefore play differently even when the player chooses the same body part.
    REACTIONS = {
        "head": [
            [
                "흰 머리카락 사이를 천천히 쓸어내립니다. 츄라이더가 눈만 들어 손을 확인합니다.",
                "정수리를 손바닥으로 가볍게 눌러 쓸어줍니다. 귀 끝이 잠깐 움직이고 시선이 손끝을 따라옵니다.",
                "앞머리를 넘겨주듯 쓰다듬자 고개를 아주 조금 숙입니다. 거미 다리는 아직 경계하듯 가지런히 서 있습니다.",
                "머리 위에 손을 올리자 처음에는 굳어 있다가, 손길이 움직이자 슬쩍 눈을 감았다 뜹니다.\n“조금만 하셰요...”",
            ],
            [
                "정수리부터 귀 뒤까지 다시 쓰다듬자 어깨의 힘이 풀리고 고개가 손바닥 쪽으로 조금 기웁니다.",
                "귀 뒤쪽을 손끝으로 살살 긁어주자 앞다리 하나가 바닥을 두 번 두드리고 멈춥니다.",
                "머리카락을 결대로 천천히 정리해주자 눈꺼풀이 점점 무거워집니다.\n“거긴 괜찮슴미댜.”",
                "이번에는 먼저 고개가 손쪽으로 옵니다. 드로우 상체는 태연하지만 복부가 바닥 가까이 내려갑니다.",
            ],
            [
                "세 번째 손길에는 아예 눈을 반쯤 감고 머리를 손바닥에 맡깁니다. 앞다리도 몸 안쪽으로 편하게 접힙니다.",
                "손을 떼려는 순간 고개가 아주 조금 따라옵니다. 잠깐 더 있으라는 듯 손바닥 아래에 그대로 머뭅니다.",
                "머리카락이 잔뜩 흐트러졌는데도 고칠 생각이 없습니다. 대신 이마를 손바닥에 살짝 기대고 가만히 있습니다.",
                "마지막으로 귀 뒤를 긁어주자 눈을 완전히 감습니다.\n“이건... 더 해도 됩니댜.”",
            ],
        ],
        "belly": [
            [
                "거미 복부 위를 조심스럽게 쓸자 여덟 다리가 순간 굳었다가 곧 다시 바닥을 짚습니다.",
                "복부 옆면을 손바닥으로 살짝 쓸어줍니다. 츄라이더가 몸을 반 박자 늦게 움찔합니다.",
                "복부 위에 손을 얹자 앞다리 둘이 동시에 들립니다. 몇 초 지나자 천천히 다시 내려놓습니다.",
                "손끝이 복부에 닿자 뒤를 힐끗 돌아봅니다.\n“거긴 갑자기 만지면 놀람미댜.”",
            ],
            [
                "복부 옆을 둥글게 쓰다듬자 앞다리 두 개가 바닥을 짧게 꿈질거립니다.",
                "이번에는 복부 아래쪽을 천천히 쓸어줍니다. 여덟 다리의 힘이 조금씩 풀립니다.",
                "손바닥 전체로 부드럽게 원을 그리자 복부가 바닥에 더 편하게 내려앉습니다.\n“이상한데 싫진 않슴미댜.”",
                "두 번째에는 피하지 않습니다. 대신 앞다리가 손목 근처에서 가만히 방향을 바꿉니다.",
            ],
            [
                "익숙해졌는지 복부를 조금 더 내려놓습니다. 드로우 상체는 아무렇지 않은 척하지만 다리 끝이 느슨해집니다.",
                "세 번째에는 아예 몸을 맡기듯 복부를 바닥에 붙입니다. 여덟 다리가 사방으로 편하게 퍼집니다.",
                "손이 멈추자 복부 끝이 한 번 작게 흔들립니다. 다시 움직이라는 뜻처럼 보입니다.",
                "복부를 마지막으로 길게 쓸어주자 눈을 가늘게 뜨고 돌아봅니다.\n“이번에는 잘했슴미댜.”",
            ],
        ],
        "tail": [
            [
                "복부 끝, 꼬리처럼 보이는 부분을 손끝으로 살짝 쓸자 츄라이더가 홱 뒤를 돌아봅니다.",
                "복부 끝을 손가락 하나로 건드리자 뒷다리 둘이 동시에 움찔합니다. 표정에는 '왜 거기?'가 그대로 드러납니다.",
                "꼬리처럼 보이는 끝부분을 살살 문지르자 몸 전체가 아주 짧게 들썩입니다.",
                "복부 끝에 손이 닿자 바로 뒤를 돌아봅니다.\n“거기 만질 줄은 몰랐슴미댜.”",
            ],
            [
                "이번에는 놀라지 않고 복부 끝만 작게 움찔합니다. 시선은 여전히 손을 따라옵니다.",
                "두 번째 손길에는 뒤돌아보지 않습니다. 다만 뒷다리 하나가 손 가까이 와서 가만히 멈춥니다.",
                "조금 더 오래 쓸어주자 복부 끝의 긴장이 풀리고 다리 움직임도 잦아듭니다.",
                "이번에는 피하지 않습니다.\n“조심해서 하면 괜찮슴미댜.”",
            ],
            [
                "세 번째에는 몸을 피하지 않습니다. 대신 뒷다리 하나가 손목 쪽으로 슬쩍 다가옵니다.",
                "마지막에는 복부 끝을 맡긴 채 다른 곳을 바라봅니다. 완전히 익숙해진 모양입니다.",
                "손길을 따라 복부가 아주 미세하게 움직입니다. 뒤돌아보던 경계도 이제 없습니다.",
                "세 번째로 살살 쓸어주자 한숨처럼 숨을 내쉽니다.\n“이제 안 놀람미댜.”",
            ],
        ],
        "legs": [
            [
                "앞다리 하나를 따라 관절 사이를 천천히 쓸어줍니다. 다리 끝이 손가락을 피해 갔다가 다시 돌아옵니다.",
                "가장 앞쪽 다리 하나를 살짝 잡고 관절을 따라 문질러줍니다. 끝부분이 손등을 톡 건드립니다.",
                "다리 하나씩 손끝으로 훑자 여덟 다리가 제각각 다른 방향으로 꿈질거립니다.",
                "앞다리를 쓰다듬자 끝부분이 손가락을 툭 밀어냅니다.\n“간지럽슴미댜.”",
            ],
            [
                "이번에는 두 다리를 번갈아 쓰다듬습니다. 바닥을 두드리던 움직임이 점점 느려집니다.",
                "관절 사이를 손끝으로 눌러주자 앞다리 둘이 차례로 힘을 뺍니다. 뒤쪽 다리도 슬쩍 가까이 모입니다.",
                "다리 안쪽을 살살 긁어주자 바닥을 타닥거리던 소리가 잦아듭니다.\n“거기 시원합니댜.”",
                "두 번째에는 먼저 다리 하나를 내밉니다. 어느 다리를 만져달라는 건지 꽤 분명합니다.",
            ],
            [
                "세 번째에는 여러 다리가 한꺼번에 몸 안쪽으로 접힙니다. 완전히 편해진 자세입니다.",
                "여덟 다리를 차례로 쓰다듬고 나니 몸 전체가 낮아집니다. 앞다리 하나는 아예 손목 위에 얹혀 있습니다.",
                "마지막 다리까지 문질러주자 모든 다리가 느슨하게 접힙니다. 움직일 생각이 없어 보입니다.",
                "세 번째에는 다리 끝이 손가락을 살짝 감쌉니다.\n“이제 됐... 아니 조금 더 해도 됩니댜.”",
            ],
        ],
        "hand": [
            [
                "드로우의 손등을 엄지로 천천히 쓸어줍니다. 츄라이더가 손을 빼지 않고 가만히 내려다봅니다.",
                "손바닥 가장자리를 손끝으로 쓸자 손가락이 반사적으로 오므라듭니다.",
                "손목부터 손등까지 천천히 쓰다듬자 츄라이더가 자기 손과 플레이어의 손을 번갈아 봅니다.",
                "손끝을 살짝 만지자 눈썹이 올라갑니다.\n“손도 쓰다듬는 검미까?”",
            ],
            [
                "손가락 사이를 조심스럽게 문지르자 손끝이 아주 조금 마주 잡힙니다.",
                "두 번째에는 손을 빼기는커녕 손바닥을 조금 펴줍니다. 엄지가 손등을 천천히 따라옵니다.",
                "손가락 하나씩 가볍게 눌러주자 마지막에는 손을 느슨하게 맞잡습니다.\n“따뜻함미댜.”",
                "손등을 다시 쓸자 이번에는 먼저 손을 뒤집어 손바닥을 보여줍니다.",
            ],
            [
                "세 번째에는 먼저 손가락을 걸어옵니다. 표정은 태연하지만 놓을 생각은 없어 보입니다.",
                "손바닥을 맞댄 채 가만히 있자 손가락이 천천히 맞물립니다. 여덟 다리도 편하게 접혀 있습니다.",
                "마지막으로 손등을 쓸어주자 손목을 손바닥 쪽에 기대고 그대로 멈춥니다.",
                "세 번째 손길에는 먼저 손을 내밉니다.\n“이번엔 제가 잡겠슴미댜.”",
            ],
        ],
        "all": [
            [
                "머리부터 복부와 다리까지 와르르 북박북박 쓰다듬습니다. 츄라이더가 무슨 일이냐는 얼굴로 여덟 다리를 한꺼번에 버둥거립니다.",
                "양손으로 머리와 손, 복부와 다리를 한꺼번에 와르르 훑습니다. 츄라이더의 표정이 잠깐 완전히 멈춥니다.",
                "어디 하나 고르지 않고 온몸을 북박북박 문지릅니다. 여덟 다리가 순식간에 사방으로 펼쳐집니다.\n“잠깐만욧!”",
                "머리카락을 헝클고 복부를 쓸고 다리를 와르르 만집니다. 츄라이더가 몸을 수습하려다 포기합니다.",
            ],
            [
                "이번에는 양손으로 머리, 손, 복부, 다리를 정신없이 북박북박 훑습니다. 도망가려던 다리도 어느새 다시 가까이 붙습니다.",
                "두 번째 와르르 쓰다듬기가 시작되자 츄라이더가 미리 몸을 낮춥니다. 그래도 머리카락은 금세 엉망이 됩니다.",
                "온몸을 번갈아 북박북박 문지르자 처음의 당황은 사라지고 여덟 다리가 손을 피해 장난치듯 움직입니다.\n“또 합니댜?”",
                "손 두 개가 사방에서 움직이자 앞다리 둘이 플레이어 손을 붙잡으려 하지만 나머지 다리는 이미 편하게 접혀 있습니다.",
            ],
            [
                "마지막으로 온몸을 와르르 북박북박 쓰다듬자 흰 머리카락은 헝클어지고 여덟 다리는 전부 제멋대로 접혀 있습니다. 츄라이더는 체념한 얼굴로 손에 기대 있습니다.",
                "세 번째 와르르가 끝나자 머리카락은 폭발하고 다리는 뒤엉켰습니다. 츄라이더가 한참 플레이어를 보다가 그대로 기대버립니다.",
                "온몸을 마지막으로 북박북박 훑자 여덟 다리가 잠깐 버둥거리다가 한꺼번에 툭 풀립니다.\n“졌슴미댜...”",
                "마지막에는 도망가기는커녕 몸을 낮춰 손길을 전부 받아냅니다. 다 끝난 뒤에야 헝클어진 머리카락을 만지며 한숨을 쉽니다.",
            ],
        ],
    }
    COMBO_REACTIONS = {
        ("head", "head", "head"): "세 번 내내 머리만 쓰다듬자 이제 손이 올라오기 전부터 먼저 고개를 낮춥니다.\n“여기가 제일 좋슴미댜.”",
        ("belly", "belly", "belly"): "복부만 세 번 연달아 쓰다듬자 완전히 바닥에 엎드려 버립니다. 여덟 다리는 힘없이 사방으로 퍼져 있습니다.",
        ("legs", "legs", "legs"): "여덟 다리를 하나하나 오래 만져준 끝에 모든 다리가 몸 안쪽으로 포개집니다. 움직일 생각이 완전히 사라진 모양입니다.",
        ("hand", "hand", "hand"): "손만 계속 만지자 세 번째에는 츄라이더가 먼저 손가락을 깊게 맞잡습니다.\n“안 놓을 검미댜.”",
        ("tail", "tail", "tail"): "세 번 모두 복부 끝만 만지자 처음의 놀람은 사라지고 오히려 손길이 멈출 때마다 뒤를 돌아봅니다.",
        ("all", "all", "all"): "세 번 연속 와르르 북박북박 당한 츄라이더는 완전히 헝클어진 채 바닥에 퍼져 있습니다.\n“너무 많이 했슴미댜...”",
    }

    def __init__(self, player, care_manager, parent_view, *, step=0, history=None, opening=None, reaction=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        self.step = step
        self.history = list(history or [])
        self.opening = opening
        self.reaction = reaction
        if step < self.MAX_STROKES:
            for idx, (label, spot) in enumerate(self.SPOTS):
                btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary if spot == "all" else discord.ButtonStyle.secondary, row=idx // 3)
                btn.callback = self._make_spot_cb(spot)
                self.add_item(btn)
        done = discord.ui.Button(label="그만 쓰다듬기", style=discord.ButtonStyle.secondary, row=2)
        done.callback = self._done
        self.add_item(done)

    def _pick_reaction(self, spot: str, next_step: int, history: list[str]) -> str:
        full_history = history + [spot]
        if next_step == self.MAX_STROKES:
            combo = self.COMBO_REACTIONS.get(tuple(full_history))
            if combo and random.random() < 0.65:
                return combo
        pool = list(self.REACTIONS[spot][next_step - 1])
        state = get_care_state(self.player)
        # Small state-specific variants make frequently repeated petting feel tied to the day.
        if spot == "head" and self.player.fatigue >= 65:
            pool.append("피곤한지 머리를 쓰다듬는 동안 눈을 오래 감고 있습니다. 손이 멈추자 이마를 손바닥에 그대로 기댑니다.\n“졸림미댜...”")
        if spot in {"belly", "legs", "all"} and state["cleanliness"] < 35:
            pool.append("쓰다듬는 손끝에 바깥에서 묻혀 온 먼지가 조금 묻습니다. 츄라이더가 모른 척 시선을 피합니다.\n“그건 못 본 걸로 합니댜.”")
        if spot == "hand" and state["comfort"] >= 75:
            pool.append("손을 만지기도 전에 먼저 손가락을 걸어옵니다. 익숙한 동작처럼 자연스럽습니다.\n“손 주셰요.”")
        if spot == "all" and state["comfort"] >= 75:
            pool.append("와르르 손이 덮쳐오자 놀라기는커녕 몸을 낮춰 받아낼 준비부터 합니다. 여덟 다리가 들썩들썩 움직입니다.\n“이번엔 안 도망감미댜.”")

        flags = getattr(self.player, "_flags", {})
        recent = flags.setdefault("pet_reaction_recent", [])
        candidates = [line for line in pool if line not in recent[-4:]] or pool
        picked = random.choice(candidates)
        recent.append(picked)
        flags["pet_reaction_recent"] = recent[-8:]
        return picked

    def make_embed(self):
        if self.step == 0:
            text = "어디를 쓰다듬을지 고릅니다. 세 번까지 이어서 쓰다듬을 수 있습니다."
        else:
            text = self.reaction or self.REACTIONS[self.history[-1]][self.step - 1][0]
        embed = discord.Embed(title="🕷️🫳 쓰다듬기", description=text, color=0x8C668A)
        embed.add_field(name="쓰다듬기", value=f"**{self.step}/{self.MAX_STROKES}**", inline=True)
        if self.history:
            labels = {spot: label.split(" ", 1)[1] for label, spot in self.SPOTS}
            embed.add_field(name="이번 세션", value=" → ".join(labels[s] for s in self.history), inline=False)
        if self.step >= self.MAX_STROKES:
            embed.set_footer(text="충분히 쓰다듬었습니다.")
        return embed

    def _make_spot_cb(self, spot: str):
        async def cb(interaction):
            next_step = min(self.MAX_STROKES, self.step + 1)
            reaction = self._pick_reaction(spot, next_step, self.history)
            history = self.history + [spot]
            view = PettingView(self.player, self.care_manager, self.parent_view, step=next_step, history=history, reaction=reaction)
            view.bind_message(getattr(interaction, "message", None))
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.warning("쓰다듬기 반응 기록 저장 실패: %s", e)
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        return cb

    async def _done(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


class RestingView(ExpiringView):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        watch = discord.ui.Button(label="👀 지켜보기", style=discord.ButtonStyle.secondary)
        watch.callback = self._watch
        self.add_item(watch)
        wake = discord.ui.Button(label="🌤️ 깨우기", style=discord.ButtonStyle.primary)
        wake.callback = self._wake
        self.add_item(wake)

    def make_embed(self):
        status = self.care_manager.get_rest_status(self.player)
        if status.get("completed"):
            result = self.care_manager.finish_rest(self.player)
            return discord.Embed(title="🕷️💤 휴식 끝", description=result["message"], color=0x4A4AAA)
        remaining = status.get("remaining", 0)
        mins, secs = divmod(remaining, 60)
        progress = status.get("progress", 0.0)
        if progress < 0.33:
            scene = "담요와 실 사이에 몸을 접고 눈을 감았습니다. 앞다리 끝이 가끔 느리게 움직입니다."
        elif progress < 0.75:
            scene = "완전히 잠든 모양입니다. 드로우 상체의 숨이 고르고, 여덟 다리는 몸 가까이 편하게 접혀 있습니다."
        else:
            scene = "잠이 얕아졌는지 귀와 앞다리가 작은 소리에 한 번씩 반응합니다. 곧 스스로 일어날 것 같습니다."
        embed = discord.Embed(title="🕷️💤 쉬는 중", description=scene, color=0x4A4AAA)
        embed.add_field(name="남은 휴식", value=f"{mins}분 {secs:02d}초", inline=True)
        return embed

    async def _watch(self, interaction):
        view = RestingView(self.player, self.care_manager, self.parent_view)
        view.bind_message(getattr(interaction, "message", None))
        embed = view.make_embed()
        if not self.care_manager.get_rest_status(self.player).get("active"):
            await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)
        else:
            await interaction.response.edit_message(attachments=[], embed=embed, view=view)

    async def _wake(self, interaction):
        result = self.care_manager.finish_rest(self.player, wake_early=True)
        try:
            save_player_to_db(self.player)
        except Exception as e:
            logger.error("휴식 종료 저장 실패: %s", e, exc_info=True)
        embed = discord.Embed(title="🕷️🌤️ 깨우기", description=result["message"], color=0x5D637B)
        if result.get("success"):
            embed.add_field(name="회복", value=f"피로 -{result.get('fatigue_recovery', 0)} · 기운 +{result.get('energy_recovery', 0)}", inline=False)
        await interaction.response.edit_message(attachments=[], embed=embed, view=self.parent_view)


# ── 가위바위보 서브 View ─────────────────────────────────────────────────────
class RockPaperScissorsView(ExpiringView):
    def __init__(self, player, care_manager, parent_view, *, rounds=0):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        self.rounds = rounds
        self._build_choice_buttons()

    def _build_choice_buttons(self):
        self.clear_items()
        for label, choice in [("✊ 바위", "rock"), ("✌️ 가위", "scissors"), ("✋ 보", "paper")]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = self._make_cb(choice)
            self.add_item(btn)
        done = discord.ui.Button(label="그만 놀기", style=discord.ButtonStyle.secondary, row=1)
        done.callback = self._done
        self.add_item(done)

    def _make_cb(self, choice: str):
        async def cb(interaction: discord.Interaction):
            result = self.care_manager.play_result(self.player, choice, continue_session=self.rounds > 0)
            if not result.get("success"):
                embed = discord.Embed(title="🕷️🧶 놀기", description=result["message"], color=0x6B5C5C)
                await interaction.response.edit_message(attachments=[], embed=embed, view=self.parent_view)
                return
            event_store.append(GameEvent(event_type="care.play", actor_id=interaction.user.id, subject="츄라이더", location="비전의 탑", payload={"game": "rock_paper_scissors", "result": result.get("result")}))
            bond_service.award("care.play", actor_id=interaction.user.id)
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("놀아주기 후 저장 실패: %s", e, exc_info=True)
            next_view = RockPaperScissorsResultView(self.player, self.care_manager, self.parent_view, result=result, rounds=self.rounds + 1)
            next_view.bind_message(getattr(interaction, "message", None))
            await interaction.response.edit_message(attachments=[], embed=next_view.make_embed(), view=next_view)
        return cb

    async def _done(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


class RockPaperScissorsResultView(ExpiringView):
    def __init__(self, player, care_manager, parent_view, *, result, rounds):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        self.result = result
        self.rounds = rounds
        again = discord.ui.Button(label="🔁 한 판 더", style=discord.ButtonStyle.primary)
        again.callback = self._again
        self.add_item(again)
        done = discord.ui.Button(label="그만 놀기", style=discord.ButtonStyle.secondary)
        done.callback = self._done
        self.add_item(done)

    def make_embed(self):
        embed = discord.Embed(title="🕷️🧶 가위바위보", description=self.result["message"], color=0x655A8A)
        embed.add_field(name="나", value=self.result.get("player_choice", "?"), inline=True)
        embed.add_field(name="츄라이더", value=self.result.get("bot_choice", "?"), inline=True)
        embed.set_footer(text=f"이번 놀이 {self.rounds}판째")
        return embed

    async def _again(self, interaction):
        view = RockPaperScissorsView(self.player, self.care_manager, self.parent_view, rounds=self.rounds)
        view.bind_message(getattr(interaction, "message", None))
        embed = discord.Embed(title="🕷️🧶 한 판 더", description="이번에는 뭘 낼까요?", color=0x655A8A)
        await interaction.response.edit_message(attachments=[], embed=embed, view=view)

    async def _done(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


# ── 간식 제작 서브 View ──────────────────────────────────────────────────────
class SnackCraftView(ExpiringView):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view
        self._selected    = None

        options = []
        for snack_id, recipe in SNACK_RECIPES.items():
            snack = SNACK_ITEMS.get(snack_id, {})
            name  = snack.get("name", snack_id)
            grade = snack.get("grade", "일반")
            icon  = GRADE_EMOJI.get(grade, "⚬")
            can_craft = all(
                player.get_hyness_inventory().get(m, 0) >= n
                for m, n in recipe["materials"].items()
            )
            craft_icon = "✅" if can_craft else "❌"
            options.append(discord.SelectOption(
                label=f"{craft_icon} {icon} {name}",
                value=snack_id,
                description=recipe.get("desc", "")[:50],
            ))

        if options:
            select = discord.ui.Select(
                placeholder="제작할 간식을 선택합니다...",
                options=options[:25],
                custom_id="snack_craft_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        confirm_btn = discord.ui.Button(
            label="✅ 제작 확정",
            style=discord.ButtonStyle.success,
            custom_id="snack_craft_confirm",
            row=1,
        )
        confirm_btn.callback = self._on_confirm
        self.add_item(confirm_btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_snack_craft",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        self._selected = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self._selected:
            await interaction.response.send_message(
                "먼저 제작할 간식을 선택합니다.", ephemeral=True
            )
            return
        result = self.care_manager.craft_snack(self.player, self._selected)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("success") and result.get("item_id"):
            snack = SNACK_ITEMS.get(result["item_id"], {})
            recipe = SNACK_RECIPES.get(result["item_id"], {})
            mats_used = ", ".join(
                f"{mid} x{cnt}" for mid, cnt in recipe.get("materials", {}).items()
            )
            rows.append({"label": "재료 소모", "value": mats_used[:60]})
            rows.append({"label": "획득", "value": f"{snack.get('name', '')} x{result.get('count',1)}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("간식 제작 후 저장 실패: %s", e, exc_info=True)
        await interaction.response.edit_message(content=None, attachments=[], embed=_make_room_embed(self.player), view=self)

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=None, attachments=[], embed=_make_room_embed(self.player), view=self.parent_view
        )


# ── 의장 제작 서브 View ──────────────────────────────────────────────────────
class CostumeCraftView(ExpiringView):
    SLOT_LABEL = {
        "toy":       "🪄 장난감",
        "hat":       "🎀 모자",
        "outfit":    "👗 의상",
        "shoes":     "👢 신발",
        "accessory": "💎 악세사리",
    }

    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view
        self._selected    = None

        options = []
        for costume_id, recipe in COSTUME_RECIPES.items():
            costume = COSTUME_ITEMS.get(costume_id, {})
            name    = costume.get("name", costume_id)
            grade   = costume.get("grade", "일반")
            icon    = GRADE_EMOJI.get(grade, "⚬")
            slot    = costume.get("slot", "")
            slot_label = self.SLOT_LABEL.get(slot, slot)
            can_craft = all(
                player.get_hyness_inventory().get(m, 0) >= n
                for m, n in recipe["materials"].items()
            )
            craft_icon = "✅" if can_craft else "❌"
            options.append(discord.SelectOption(
                label=f"{craft_icon} {icon} {name} ({slot_label})",
                value=costume_id,
                description=recipe.get("desc", "")[:50],
            ))

        if options:
            select = discord.ui.Select(
                placeholder="제작할 의장을 선택합니다...",
                options=options[:25],
                custom_id="costume_craft_select",
            )
            select.callback = self._on_select
            self.add_item(select)

        confirm_btn = discord.ui.Button(
            label="✅ 제작 확정",
            style=discord.ButtonStyle.success,
            custom_id="costume_craft_confirm",
            row=1,
        )
        confirm_btn.callback = self._on_confirm
        self.add_item(confirm_btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_costume_craft",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_select(self, interaction: discord.Interaction):
        self._selected = interaction.data["values"][0]
        await interaction.response.defer()

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self._selected:
            await interaction.response.send_message(
                "먼저 제작할 의장을 선택합니다.", ephemeral=True
            )
            return
        result = self.care_manager.craft_costume(self.player, self._selected)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("success") and result.get("item_id"):
            costume = COSTUME_ITEMS.get(result["item_id"], {})
            recipe  = COSTUME_RECIPES.get(result["item_id"], {})
            mats_used = ", ".join(
                f"{mid} x{cnt}" for mid, cnt in recipe.get("materials", {}).items()
            )
            rows.append({"label": "재료 소모", "value": mats_used[:60]})
            rows.append({"label": "획득", "value": f"{costume.get('name','')} x{result.get('count',1)}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("의장 제작 후 저장 실패: %s", e, exc_info=True)
        if result.get("success") and result.get("item_id"):
            costume = COSTUME_ITEMS.get(result["item_id"], {})
            flavor = COSTUME_FLAVOR.get(result["item_id"], {})
            embed = discord.Embed(
                title=f"{costume.get('emoji', '✂️')} {costume.get('name', result['item_id'])} 완성",
                description=flavor.get("craft") or costume.get("description", result["message"]),
                color=0x6D596E,
            )
            embed.add_field(name="획득", value=f"{costume.get('name', result['item_id'])} x{result.get('count', 1)}", inline=True)
        else:
            embed = discord.Embed(title="✂️ 의장제작", description=result["message"], color=0x6B5C5C)
        await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)

    async def _on_back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=None, attachments=[], embed=_make_room_embed(self.player), view=self.parent_view
        )


# ── 아이템 선택 헬퍼 View ───────────────────────────────────────────────────
class _ItemSelectView(ExpiringView):
    """Select 메뉴 하나만 가지는 임시 뷰 (ephemeral 사용용)."""
    def __init__(self, select: discord.ui.Select, confirm_cb):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self._confirm_cb = confirm_cb
        select.callback  = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        chosen = interaction.data["values"][0]
        await self._confirm_cb(interaction, chosen)


# ── 비전의 탑 생활 공간 ──────────────────────────────────────────────────────
class TowerPlaceView(ExpiringView):
    """비전의 탑을 같은 메시지 안에서 오가는 장소 UI."""

    PLACES = {
        "upper": {
            "title": "비전의 탑 · 상층 생활 공간",
            "description": "마제스티와 카르니스가 생활하는 탑의 상층. 오래된 가구와 책장 사이, 눈에 잘 띄지 않는 곳에 작은 흔적들이 숨어 있다.",
            "actions": [
                ("책장 뒤 작은 틈", "🕸️", "nest"),
                ("마제스티가 남긴 흔적", "🕯️", "마제스티가 남긴 흔적", "손이 자주 닿은 물건들이 정돈되어 있다. 지금 누가 있는지는 알 수 없지만, 책장 아래에는 누군가 일부러 밀어 넣은 듯한 작은 간식 접시가 하나 놓여 있다."),
                ("복도에 남은 흔적", "🕷️", "복도에 남은 흔적", "돌바닥에 단단한 발끝이 스친 자국이 길게 남아 있다. 책장 아래의 작은 발자국은 그 자국을 피해 안쪽으로 향한다. 카르니스가 지금 근처에 있다는 뜻은 아니다."),
                ("전시관", "🏛️", "exhibition"),
                ("군락으로 가는 길", "🍄", "road_to_colony"),
            ],
        },
        "workshop": {
            "title": "비전의 탑 · 연금술 작업층",
            "description": "약초 냄새와 오래된 금속 냄새가 뒤섞인 작업층. 선반과 작업대에는 누군가 쓰다 만 도구와 병들이 남아 있다.",
            "actions": [
                ("연금술 작업대", "⚗️", "facility", "alchemy"),
                ("먹을거리 선반", "🥣", "facility", "pantry"),
            ],
        },
        "storage": {
            "title": "비전의 탑 · 하층 창고",
            "description": "탑 아래쪽의 서늘한 창고. 오래된 상자 너머로 수서 발전기의 금속 장치가 잠들어 있다.",
            "actions": [
                ("수서 발전기", "🌸", "generator"),
                ("보관 설비", "🗄️", "facility", "storage"),
                ("장비 보관 설비", "🛡️", "facility", "gear_storage"),
                ("쌓인 상자", "📦", "쌓인 상자", "오래된 상자들 사이에 작은 틈이 여럿 있다. 츄라이더가 숨바꼭질하기에는 꽤 그럴듯해 보인다."),
                ("바닥의 흔적", "🔎", "바닥의 흔적", "먼지 위로 작은 발자국이 몇 번 오갔다. 창고 안쪽을 구경하다 다시 승강기 쪽으로 돌아간 흔적이다."),
            ],
        },
        "roof": {
            "title": "비전의 탑 · 옥상",
            "description": "언더다크의 어둠과 푸른 균광이 멀리까지 내려다보이는 탑의 꼭대기. 아래층보다 공기가 차갑고 넓다.",
            "actions": [
                ("언더다크를 바라본다", "👁️", "언더다크", "멀리 균광과 폐허의 윤곽이 어둠 속에서 이어진다. 탑 바깥의 세계가 조용히 움직이고 있다."),
                ("난간의 흔적", "🐾", "난간의 흔적", "난간 아래쪽에 조그만 발자국이 남아 있다. 가장자리까지 갔다가 겁이 났는지 곧장 뒤로 물러난 모양이다."),
            ],
        },
    }

    FLOOR_BUTTONS = [
        ("상층", "🏠", "upper"),
        ("작업층", "⚗️", "workshop"),
        ("하층 창고", "📦", "storage"),
        ("옥상", "🌌", "roof"),
    ]

    def __init__(self, player, care_manager, *, place="upper", suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.place = place
        self.suspicious_actor_id = suspicious_actor_id
        self._rebuild_items()

    def _rebuild_items(self):
        self.clear_items()
        for action in self.PLACES[self.place]["actions"]:
            label, emoji = action[:2]
            style = discord.ButtonStyle.primary if action[2] == "nest" else discord.ButtonStyle.secondary
            button = discord.ui.Button(label=label, emoji=emoji, style=style)
            if action[2] == "nest":
                button.callback = self._open_nest
            elif action[2] == "generator":
                button.callback = self._open_generator
            elif action[2] == "facility":
                facility = action[3]
                button.callback = self._make_facility_callback(facility)
            elif action[2] == "road_to_colony":
                button.callback = self._open_colony_road
            elif action[2] == "exhibition":
                button.callback = self._open_exhibition
            else:
                button.callback = self._make_observation_callback(action[2], action[3])
            self.add_item(button)
        lift_btn = discord.ui.Button(label="승강기", emoji="↕️", style=discord.ButtonStyle.secondary)
        lift_btn.callback = self._open_lift
        self.add_item(lift_btn)

    def make_embed(self, observation=None):
        data = self.PLACES[self.place]
        embed = discord.Embed(title=data["title"], description=data["description"], color=0x544766)
        if observation:
            embed.add_field(name=observation[0], value=observation[1], inline=False)
        return embed

    async def _open_exhibition(self, interaction):
        view = TowerExhibitionView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction,"message",None))
        await interaction.response.edit_message(attachments=[],embed=view.make_embed(),view=view)

    async def _open_nest(self, interaction):
        view = CareRoomView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=_make_room_embed(self.player), view=view)

    async def _open_generator(self, interaction):
        from tower_power import ensure_tower_state
        state = ensure_tower_state(self.player)
        online = state["generator_online"]
        bloom_count = getattr(self.player, "inventory", {}).get("sussur_bloom", 0)
        desc = (
            "수서 꽃의 반마법 성질을 받아들이는 오래된 발전 장치가 낮게 울리고 있다. 탑의 동력이 돌아왔다."
            if online else
            f"오래 멈춘 발전 장치다. 중앙의 빈 홈은 수서 꽃 한 송이가 들어갈 만한 크기다.\n\n휴대 중인 수서 꽃: **{bloom_count}**"
        )
        view = TowerGeneratorView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=discord.Embed(title="비전의 탑 · 수서 발전기", description=desc, color=0x46594F), view=view)

    def _make_facility_callback(self, facility):
        async def callback(interaction):
            view = TowerFacilityView(self.player, self.care_manager, facility=facility, return_place=self.place, suspicious_actor_id=self.suspicious_actor_id)
            view.bind_message(getattr(interaction, "message", None))
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        return callback

    def _make_observation_callback(self, title, text):
        async def callback(interaction):
            await interaction.response.edit_message(attachments=[], embed=self.make_embed((title, text)), view=self)
        return callback

    async def _open_colony_road(self, interaction):
        view = TowerColonyRoadView(
            self.player,
            self.care_manager,
            direction="to_colony",
            suspicious_actor_id=self.suspicious_actor_id,
        )
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

    async def _open_lift(self, interaction):
        from tower_power import facility_online
        if not facility_online(self.player, "lift"):
            embed = self.make_embed(("멈춘 승강기", "승강기에는 동력이 들어오지 않는다. 하층의 수서 발전기를 먼저 살펴봐야 할 것 같다."))
            await interaction.response.edit_message(attachments=[], embed=embed, view=self)
            return
        view = TowerLiftView(self.player, self.care_manager, current_place=self.place, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


class TowerColonyRoadView(ExpiringView):
    """비전의 탑과 마이코니드 군락을 잇는 짧은 생활 이동로."""

    ROUTES = {
        "to_colony": [
            ("탑 바깥", "탑의 오래된 문을 밀고 나오면 차고 눅눅한 언더다크 공기가 닿습니다. 멀리 발광버섯 빛이 점점이 이어집니다."),
            ("균광 길", "절벽 아래쪽으로 난 좁은 길을 따라갑니다. 바위 틈의 푸른 균광과 작은 버섯들이 길 가장자리를 희미하게 밝힙니다."),
            ("군락 외곽", "공기 속 포자가 눈에 띄게 짙어지고, 멀리 거대한 버섯 기둥 사이로 상인과 여행자의 불빛이 보이기 시작합니다."),
        ],
        "to_tower": [
            ("군락 외곽", "발광버섯 숲을 빠져나오자 포자가 조금씩 옅어집니다. 뒤쪽에서는 군락의 빛이 천천히 멀어집니다."),
            ("균광 길", "바위 벽을 따라 난 좁은 길을 되짚습니다. 푸른 균광 너머로 절벽 위 탑의 윤곽이 조금씩 커집니다."),
            ("탑 아래", "마지막 굽이를 돌자 비전의 탑이 바로 위로 솟아 있습니다. 오래된 입구와 익숙한 돌계단이 눈앞에 나타납니다."),
        ],
    }

    def __init__(self, player, care_manager, *, direction="to_colony", step=0, suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.direction = direction
        self.step = step
        self.suspicious_actor_id = suspicious_actor_id
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        stages = self.ROUTES[self.direction]
        if self.step < len(stages) - 1:
            btn = discord.ui.Button(label="길을 따라간다", emoji="👣", style=discord.ButtonStyle.primary)
            btn.callback = self._advance
            self.add_item(btn)
            back = discord.ui.Button(label="돌아간다", emoji="↩️", style=discord.ButtonStyle.secondary)
            back.callback = self._turn_back
            self.add_item(back)
        else:
            label = "군락으로 들어간다" if self.direction == "to_colony" else "탑으로 들어간다"
            emoji = "🍄" if self.direction == "to_colony" else "🏰"
            btn = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.success)
            btn.callback = self._arrive
            self.add_item(btn)

    def make_embed(self):
        stages = self.ROUTES[self.direction]
        title, desc = stages[self.step]
        origin = "비전의 탑 → 마이코니드 군락" if self.direction == "to_colony" else "마이코니드 군락 → 비전의 탑"
        bar = "●" * (self.step + 1) + "○" * (len(stages) - self.step - 1)
        embed = discord.Embed(title=f"👣 {title}", description=desc, color=0x485B50)
        embed.add_field(name=origin, value=f"{bar}  {self.step + 1}/{len(stages)}", inline=False)
        return embed

    async def _advance(self, interaction):
        view = TowerColonyRoadView(
            self.player,
            self.care_manager,
            direction=self.direction,
            step=min(self.step + 1, len(self.ROUTES[self.direction]) - 1),
            suspicious_actor_id=self.suspicious_actor_id,
        )
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

    async def _turn_back(self, interaction):
        if self.direction == "to_colony":
            view = TowerUpperFloorView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
            view.bind_message(getattr(interaction, "message", None))
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        else:
            from ui.town_ui import VisionTownView
            import app_context
            from village import village_manager
            view = VisionTownView(
                self.player,
                app_context.get_affinity_manager(),
                app_context.get_npc_manager(),
                village_manager,
                care_manager=self.care_manager,
            )
            await view.send(interaction, edit=True)

    async def _arrive(self, interaction):
        if self.direction == "to_colony":
            self.player.current_location = "마이코니드 군락"
            save_player_to_db(self.player)
            from ui.town_ui import VisionTownView
            import app_context
            from village import village_manager
            view = VisionTownView(
                self.player,
                app_context.get_affinity_manager(),
                app_context.get_npc_manager(),
                village_manager,
                care_manager=self.care_manager,
            )
            await view.send(interaction, edit=True)
        else:
            self.player.current_location = "비전의 탑"
            from tower_exhibition import entry_notice as exhibition_entry_notice
            notice = exhibition_entry_notice(self.player)
            save_player_to_db(self.player)
            view = TowerUpperFloorView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id, entry_notice=notice)
            view.bind_message(getattr(interaction, "message", None))
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


class TowerFacilityView(ExpiringView):
    def __init__(self, player, care_manager, *, facility, return_place, suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.facility = facility
        self.return_place = return_place
        self.suspicious_actor_id = suspicious_actor_id
        from tower_power import ensure_tower_state
        online = bool(ensure_tower_state(player)["facilities"].get(facility))
        if not online:
            btn = discord.ui.Button(label="설비를 복구한다", emoji="🔧", style=discord.ButtonStyle.primary)
            btn.callback = self._restore
            self.add_item(btn)
        back = discord.ui.Button(label="돌아간다", emoji="↩️", style=discord.ButtonStyle.secondary)
        back.callback = self._back
        self.add_item(back)

    def make_embed(self, result=None):
        from tower_power import FACILITIES, ensure_tower_state, facility_cost
        from items import ALL_ITEMS
        data = FACILITIES[self.facility]
        state = ensure_tower_state(self.player)
        if state["facilities"].get(self.facility):
            desc = "탑의 동력을 받아 설비가 조용히 작동하고 있다."
            if data["storage_bonus"]:
                desc += f"\n\n비전의 탑 보관 공간 **+{data['storage_bonus']}칸**"
        elif not state["generator_online"]:
            desc = "설비는 멀쩡해 보이지만 동력이 없다. **수서 발전기**를 먼저 복구해야 한다."
        else:
            lines = []
            inv = getattr(self.player, "inventory", {})
            for item_id, count in facility_cost(self.facility).items():
                name = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                lines.append(f"{name} {inv.get(item_id, 0)}/{count}")
            desc = "먼지와 녹을 걷어내면 다시 쓸 수 있을 것 같다.\n\n필요한 재료\n" + "\n".join(lines)
        if result:
            desc = result + "\n\n" + desc
        return discord.Embed(title=f"비전의 탑 · {data['name']}", description=desc, color=0x46594F)

    async def _restore(self, interaction):
        from tower_power import restore_facility
        restored = restore_facility(self.player, self.facility)
        result = "낡은 부품을 맞추고 재료를 덧댄다. 잠시 뒤 설비에 불이 들어온다." if restored else "아직 설비를 복구할 수 없다. 동력과 필요한 재료를 확인해야 한다."
        view = TowerFacilityView(self.player, self.care_manager, facility=self.facility, return_place=self.return_place, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(result), view=view)

    async def _back(self, interaction):
        view = TowerPlaceView(self.player, self.care_manager, place=self.return_place, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


class TowerExhibitionView(ExpiringView):
    def __init__(self,player,care_manager,*,suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT);self.player=player;self.care_manager=care_manager;self.suspicious_actor_id=suspicious_actor_id
        from tower_exhibition import available_to_display,EXHIBITS
        for key in available_to_display(player):
            data=EXHIBITS[key];b=discord.ui.Button(label=f"전시: {data['name']}",emoji=data['emoji'],style=discord.ButtonStyle.success);b.callback=self._make_display(key);self.add_item(b)
        songs=discord.ui.Button(label="루바토의 노래 기억",emoji="🎼",style=discord.ButtonStyle.secondary);songs.callback=self._songs;self.add_item(songs)
        from tower_exhibition import piano_quest_state
        piano_state=piano_quest_state(player)
        if piano_state != "locked":
            label="지하실의 오래된 피아노" if piano_state != "restored" else "복원된 오래된 피아노"
            piano=discord.ui.Button(label=label,emoji="🎹",style=discord.ButtonStyle.primary if piano_state != "restored" else discord.ButtonStyle.success);piano.callback=self._piano;self.add_item(piano)
        back=discord.ui.Button(label="상층으로",emoji="↩️",style=discord.ButtonStyle.secondary);back.callback=self._back;self.add_item(back)
    def make_embed(self,note=None):
        from tower_exhibition import summary,hall_stage
        info=summary(self.player);stage=hall_stage(self.player);lines=[f"{x['emoji']} **{x['name']}** · {x['set']}\n{x['desc']}" for x in info['displayed']]
        desc=f"**Lv.{stage['level']} · {stage['name']}**\n{stage['desc']}\n\n{stage['change']}"
        e=discord.Embed(title=f"🏛️ 비전의 탑 · 전시관  {info['count']}/{info['total']}",description=desc,color=0x6A5B3F)
        e.add_field(name="전시품",value="\n\n".join(lines) if lines else "아직 진열장은 비어 있다.",inline=False)
        if stage["level"] >= 3:
            e.add_field(name="🤖 버나드의 관리 기록",value="‘전시물 상태 정상. 배치 순서를 기록했습니다. ...추가 보관 장소를 준비하겠습니다.’",inline=False)
        if info['next']:
            need,bonus,label=info['next'];pretty={"max_energy":"최대 기력","luck":"LUCK","dex":"DEX","int":"INT"};effect=" · ".join(f"{pretty.get(k,k)} +{v}" for k,v in bonus.items());e.add_field(name=f"🔮 다음 공명 · {need}점",value=f"{label} — {effect}",inline=False)
        else:e.add_field(name="🔮 전시관 공명",value="현재 준비된 모든 공명이 깨어났다.",inline=False)
        if note:e.add_field(name="✨ 변화",value=note,inline=False)
        return e
    def _make_display(self,key):
        async def cb(interaction):
            from tower_exhibition import display,EXHIBITS
            ok,rewards=display(self.player,key);note=f"{EXHIBITS[key]['name']}을 전시했습니다." if ok else "전시할 수 없습니다."
            if rewards: note+="\n"+"\n".join(f"🔮 **{label}** 공명이 깨어났습니다." for label,_ in rewards)
            try:
                from save_manager import save_manager;save_manager.save(self.player)
            except Exception: logger.warning('전시관 저장 실패',exc_info=True)
            v=TowerExhibitionView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(note),view=v)
        return cb
    async def _piano(self,interaction):
        v=TowerPianoQuestView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)
    async def _songs(self,interaction):
        v=LubatoSongMemoryView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)
    async def _back(self,interaction):
        v=TowerUpperFloorView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)


class TowerPianoQuestView(ExpiringView):
    """전시관 첫 공명으로 드러나는 지하실 피아노의 짧은 사이드 스토리."""
    SCENES = {
        "available": (
            "지하실의 닫힌 문",
            "전시관의 첫 공명이 가라앉은 뒤, 하층 창고 안쪽 벽에서 전에 없던 문 하나가 드러납니다.\n\n루바토가 먼지를 손끝으로 훑습니다.\n“이 탑, 아직도 숨기는 방이 있었네.”\n\n카르니스가 먼저 문 앞에 섭니다.\n“마제스티께서 원하신다면 제가 앞장서겠습니다. 하이네스의 작은 것은 뒤에 두십시오.”\n\n츄라이더는 말없이 루바토의 망토 뒤로 들어갑니다.",
            "지하실 문을 연다",
        ),
        "found": (
            "천 아래의 검은 윤곽",
            "문 아래에는 오래된 음악실이 있습니다. 무너진 악보대와 빈 상자 사이, 커다란 천에 덮인 물건 하나가 벽을 차지하고 있습니다.\n\n루바토가 천을 걷자 낡은 피아노가 나타납니다. 건반 몇 개는 내려앉았고 현은 오래 녹슬었습니다.\n\n“...이건 버리면 안 되겠다.”\n\n카르니스가 피아노와 루바토를 번갈아 봅니다.\n“마제스티께서 바라신다면, 이 흉물도 다시 소리를 내게 하지요.”\n\n카르니스가 부러진 해머 하나를 집어 듭니다. 손끝에서 짧은 수선 주문이 번뜩이자 갈라진 나무가 다시 맞물립니다.\n\n“흉물이라고 먼저 정하진 말자, 카르니스.”",
            "피아노 뚜껑을 살핀다",
        ),
        "opened": (
            "남아 있던 한 음",
            "루바토가 가장 온전한 건반 하나를 조심스럽게 누릅니다. 낮은 한 음이 먼지 낀 방 안으로 길게 번집니다.\n\n츄라이더가 피아노 다리 뒤에서 고개를 내밉니다.\n“살아 있슴미까?”\n\n“악기는 살아 있는 척을 잘하거든.”\n\n카르니스는 츄라이더를 노려보다가, 루바토가 다시 건반을 보는 순간 공구 상자를 집어 듭니다. 수선 주문으로 이어 붙인 부품의 축을 맞추고, 느슨해진 나사와 페달 장치를 하나씩 손봅니다.\n“마제스티. 손을 더럽히실 필요는 없습니다. 수리는 제가 하겠습니다.”\n\n루바토가 웃습니다. “그럼 나는 조율할게. 하이네스가 돌아오면 들려주자.”",
            "함께 피아노를 복원한다",
        ),
        "restored": (
            "오래된 피아노",
            "지하실의 오래된 피아노는 다시 연주할 수 있습니다. 새것처럼 반듯하지는 않지만, 낮은 음은 깊고 높은 음에는 오래된 금속성 울림이 조금 남아 있습니다.\n\n루바토의 레퍼토리에 이제 **피아노 편곡**을 만들 수 있는 악기가 하나 더 생겼습니다. 카르니스는 자신이 수리했다는 말을 굳이 하지 않지만, 건반 덮개와 페달은 유난히 깨끗합니다.",
            None,
        ),
    }
    def __init__(self,player,care_manager,*,suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT);self.player=player;self.care_manager=care_manager;self.suspicious_actor_id=suspicious_actor_id
        from tower_exhibition import piano_quest_state
        state=piano_quest_state(player);scene=self.SCENES[state]
        if scene[2]:
            b=discord.ui.Button(label=scene[2],emoji="🎹",style=discord.ButtonStyle.primary);b.callback=self._advance;self.add_item(b)
        back=discord.ui.Button(label="전시관으로",emoji="↩️",style=discord.ButtonStyle.secondary);back.callback=self._back;self.add_item(back)
    def make_embed(self):
        from tower_exhibition import piano_quest_state
        state=piano_quest_state(self.player);title,text,_=self.SCENES[state]
        return discord.Embed(title=f"🎹 사이드 스토리 · {title}",description=text,color=0x4C4358)
    async def _advance(self,interaction):
        from tower_exhibition import advance_piano_quest
        advance_piano_quest(self.player)
        try:
            from save_manager import save_manager;save_manager.save(self.player)
        except Exception: logger.warning('피아노 사이드 스토리 저장 실패',exc_info=True)
        v=TowerPianoQuestView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)
    async def _back(self,interaction):
        v=TowerExhibitionView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)


class LubatoSongMemoryView(ExpiringView):
    def __init__(self,player,care_manager,*,suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT);self.player=player;self.care_manager=care_manager;self.suspicious_actor_id=suspicious_actor_id
        from lubato_song_memory import unlocked_songs, repertoire_songs
        for key,song in unlocked_songs(player)[:12]:
            b=discord.ui.Button(label=song["title"],emoji="🎵",style=discord.ButtonStyle.secondary);b.callback=self._make_song(key);self.add_item(b)
        for key,song in repertoire_songs()[:6]:
            b=discord.ui.Button(label=song["title"],emoji="🎶",style=discord.ButtonStyle.primary);b.callback=self._make_repertoire(key);self.add_item(b)
        back=discord.ui.Button(label="전시관으로",emoji="↩️",style=discord.ButtonStyle.secondary);back.callback=self._back;self.add_item(back)
    def make_embed(self,note=None):
        from lubato_song_memory import unlocked_songs
        songs=unlocked_songs(self.player)
        desc="마제스티(루바토)가 기억한 모험의 노래와, 원래 즐겨 부르는 레퍼토리를 들을 수 있습니다."
        e=discord.Embed(title=f"🎼 루바토의 노래 기억 · {len(songs)}곡",description=desc,color=0x6B5578)
        if songs:
            e.add_field(name="기억하는 노래",value="\n".join(f"🎵 **{song['title']}** · {song['trigger']}" for _,song in songs),inline=False)
        else:e.add_field(name="아직 조용한 악보",value="함께 겪은 특별한 날이 생기면 루바토가 한 곡씩 기억합니다.",inline=False)
        if note:e.add_field(name="🎶 연주",value=note,inline=False)
        return e
    def _make_song(self,key):
        async def cb(interaction):
            from lubato_song_memory import song_text
            v=LubatoSongMemoryView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(song_text(key)),view=v)
        return cb
    def _make_repertoire(self,key):
        async def cb(interaction):
            from lubato_song_memory import repertoire_text
            from music_system import learn_melody
            learned=learn_melody(self.player,key)
            note=repertoire_text(key) + ("\n\n🎼 **새 선율을 배웠습니다.** 이제 츄라이더가 이 멜로디를 연주하거나 작곡에 사용할 수 있습니다." if learned else "")
            v=LubatoSongMemoryView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));v._add_music_actions(key);await interaction.response.edit_message(attachments=[],embed=v.make_embed(note),view=v)
        return cb
    def _add_music_actions(self,key):
        if len(self.children)<24:
            b=discord.ui.Button(label="츄라이더가 연주",emoji="🎻",style=discord.ButtonStyle.success);b.callback=self._make_perform(key);self.add_item(b)
        if len(self.children)<24:
            b=discord.ui.Button(label="이 선율로 작곡",emoji="✍️",style=discord.ButtonStyle.success);b.callback=self._make_compose(key);self.add_item(b)
    def _make_perform(self,key):
        async def cb(interaction):
            v=RhythmPerformanceView(self.player,self.care_manager,key,suspicious_actor_id=self.suspicious_actor_id)
            v.bind_message(getattr(interaction,"message",None))
            await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)
        return cb
    def _make_compose(self,key):
        async def cb(interaction):
            from music_system import compose_variation
            ok,msg=compose_variation(self.player,key)
            v=LubatoSongMemoryView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));v._add_music_actions(key);await interaction.response.edit_message(attachments=[],embed=v.make_embed(msg),view=v)
        return cb
    async def _back(self,interaction):
        v=TowerExhibitionView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)


class RhythmPerformanceView(ExpiringView):
    """Discord 버튼으로 한 음씩 따라가는 짧은 연주 미니게임."""
    def __init__(self,player,care_manager,melody_id,*,suspicious_actor_id=None):
        super().__init__(timeout=90);self.player=player;self.care_manager=care_manager;self.melody_id=melody_id;self.suspicious_actor_id=suspicious_actor_id
        from music_system import rhythm_chart
        self.chart=rhythm_chart(melody_id);self.step=0;self.hits=0;self.finished=False;self._build_keys()
    def _build_keys(self):
        self.clear_items()
        if self.finished:return
        from music_system import RHYTHM_KEYS
        for key in RHYTHM_KEYS:
            b=discord.ui.Button(label=key,style=discord.ButtonStyle.primary,custom_id=f"rhythm_{self.melody_id}_{self.step}_{RHYTHM_KEYS.index(key)}")
            b.callback=self._make_key(key);self.add_item(b)
        q=discord.ui.Button(label="연주 그만두기",emoji="↩️",style=discord.ButtonStyle.secondary);q.callback=self._quit;self.add_item(q)
    def make_embed(self,note=None):
        from lubato_song_memory import REPERTOIRE
        title=REPERTOIRE.get(self.melody_id,{}).get("title",self.melody_id);total=len(self.chart)
        if self.finished: desc=note or "연주가 끝났습니다."
        else:
            target=self.chart[self.step]["key"] if self.step<total else "🎵"
            upcoming="  ".join(x["key"] for x in self.chart[self.step:self.step+4])
            desc=f"**지금:** {target}\n\n`{upcoming}`\n\n진행 **{self.step}/{total}** · 정확 **{self.hits}**\n표시된 키를 눌러 선율을 이어가세요."
            if note: desc=note+"\n\n"+desc
        return discord.Embed(title=f"🎻 연주 · {title}",description=desc,color=0x6B5578)
    def _make_key(self,key):
        async def cb(interaction):
            if self.finished or self.step>=len(self.chart):return
            expected=self.chart[self.step]["key"];correct=key==expected
            if correct:self.hits+=1
            self.step+=1
            if self.step>=len(self.chart):
                from music_system import performance_result
                grade,exp=performance_result(self.player,self.melody_id,self.hits,len(self.chart));self.finished=True;self.clear_items()
                try: save_player_to_db(self.player)
                except Exception: logger.warning("연주 미니게임 저장 실패",exc_info=True)
                back=discord.ui.Button(label="노래 기억으로",emoji="↩️",style=discord.ButtonStyle.secondary);back.callback=self._back;self.add_item(back)
                msg=f"{grade}\n**{self.hits}/{len(self.chart)}** 음을 맞혔습니다.  `악기 연주 EXP +{exp}`"
                await interaction.response.edit_message(attachments=[],embed=self.make_embed(msg),view=self);return
            self._build_keys();await interaction.response.edit_message(attachments=[],embed=self.make_embed("✨ 정확!" if correct else f"💫 살짝 빗나갔습니다. 정답은 {expected}"),view=self)
        return cb
    async def _quit(self,interaction): await self._back(interaction)
    async def _back(self,interaction):
        v=LubatoSongMemoryView(self.player,self.care_manager,suspicious_actor_id=self.suspicious_actor_id);v.bind_message(getattr(interaction,"message",None));await interaction.response.edit_message(attachments=[],embed=v.make_embed(),view=v)


class TowerGeneratorView(ExpiringView):
    def __init__(self, player, care_manager, *, suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.suspicious_actor_id = suspicious_actor_id
        from tower_power import ensure_tower_state
        state = ensure_tower_state(player)
        if not state["generator_online"]:
            btn = discord.ui.Button(label="수서 꽃을 넣는다", emoji="🌸", style=discord.ButtonStyle.primary)
            btn.callback = self._restore
            self.add_item(btn)
        back = discord.ui.Button(label="하층 창고", emoji="📦", style=discord.ButtonStyle.secondary)
        back.callback = self._back
        self.add_item(back)

    async def _restore(self, interaction):
        from tower_power import restore_generator
        restored = restore_generator(self.player)
        if restored:
            text = "수서 꽃이 장치 안으로 가라앉는다. 잠시 뒤 탑 깊은 곳에서 둔한 진동이 올라오고, 죽어 있던 설비에 하나씩 불이 들어온다. **승강기가 다시 움직이기 시작했다.**"
        else:
            text = "발전기를 움직이려면 **수서 꽃 한 송이**를 휴대하고 있어야 한다."
        view = TowerGeneratorView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=discord.Embed(title="비전의 탑 · 수서 발전기", description=text, color=0x46594F), view=view)

    async def _back(self, interaction):
        view = TowerPlaceView(self.player, self.care_manager, place="storage", suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


class TowerUpperFloorView(TowerPlaceView):
    """기존 진입점 호환용 상층 View."""
    def __init__(self, player, care_manager, *, suspicious_actor_id=None, entry_notice=None):
        self.entry_notice = entry_notice
        super().__init__(player, care_manager, place="upper", suspicious_actor_id=suspicious_actor_id)

    def make_embed(self, observation=None):
        embed = super().make_embed(observation)
        if self.entry_notice:
            embed.add_field(name="📦 전시관 자동 보관", value=self.entry_notice, inline=False)
        return embed


class TowerLiftView(ExpiringView):
    """탑의 층을 실제로 연결하는 승강기."""
    def __init__(self, player, care_manager, *, current_place="upper", suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.current_place = current_place
        self.suspicious_actor_id = suspicious_actor_id
        for label, emoji, place in TowerPlaceView.FLOOR_BUTTONS:
            button = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.primary if place == current_place else discord.ButtonStyle.secondary, disabled=place == current_place)
            button.callback = self._make_floor_callback(place)
            self.add_item(button)

    def make_embed(self):
        current = TowerPlaceView.PLACES[self.current_place]["title"].split(" · ", 1)[-1]
        return discord.Embed(title="비전의 탑 · 승강기", description=f"낡은 승강기 장치가 낮게 울린다. 지금은 **{current}**에 멈춰 있다. 갈 곳을 고른다.", color=0x40374F)

    def _make_floor_callback(self, place):
        async def callback(interaction):
            view = TowerPlaceView(self.player, self.care_manager, place=place, suspicious_actor_id=self.suspicious_actor_id)
            view.bind_message(getattr(interaction, "message", None))
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        return callback


# ── 메인 비전의 탑 돌봄 View ──────────────────────────────────────────────────
WALK_UPDATE_SECONDS = 3
WALK_ROUTES = {
    "indoor": {
        "label": "🏠 실내",
        "duration": 24,
        "description": "비전의 탑 안을 돌아봅니다. 짧고 안전하며 피로와 오염이 적습니다.",
        "items": (1, 1),
        "outing": "walk_indoor",
    },
    "near": {
        "label": "🌿 집 근처",
        "duration": 36,
        "description": "탑 바로 주변까지 다녀옵니다. 적당히 움직이고 주울 것도 조금 많습니다.",
        "items": (1, 2),
        "outing": "walk_near",
    },
    "far": {
        "label": "🌒 좀 멀리",
        "duration": 54,
        "description": "탑에서 제법 멀리까지 다녀옵니다. 오래 걸리고 피곤하지만 더 많이 주워옵니다.",
        "items": (2, 3),
        "outing": "walk_far",
    },
}

WALK_SCENES = {
    "indoor": [
        (0.18, "🚪 출발", "책장 뒤 틈에서 몸을 빼낸 뒤 여덟 다리를 차례로 펴고 복도로 나갑니다."),
        (0.42, "🪜 계단", "난간 아래쪽으로 몸을 낮추고 계단 몇 칸을 오르내립니다. 다리 끝이 돌 틈을 하나씩 짚습니다."),
        (0.68, "🔎 구석 탐색", "상자 뒤 좁은 틈에 앞다리를 넣고 꿈질꿈질 더듬습니다."),
        (0.86, "🕸️ 실 정리", "복도 모서리에 늘어진 오래된 실을 앞다리로 감아 작은 뭉치로 만듭니다."),
        (1.01, "🏠 귀환", "익숙한 발소리로 상층 생활 공간을 돌아 책장 뒤 틈으로 향합니다."),
    ],
    "near": [
        (0.18, "🚪 출발", "탑 입구까지 내려가 바깥 공기를 한 번 확인한 뒤 조심스럽게 밖으로 나갑니다."),
        (0.42, "🌿 풀숲", "탑 벽을 따라 난 풀 사이를 헤치며 다리 끝으로 바닥을 꿈질꿈질 살핍니다."),
        (0.66, "🪨 돌무더기", "작은 돌무더기 앞에 멈춰 반짝이는 것을 찾듯 앞다리로 하나씩 뒤집어 봅니다."),
        (0.86, "🕷️ 한 바퀴", "탑 주변을 크게 한 바퀴 돕니다. 흙이 다리 끝에 조금씩 묻습니다."),
        (1.01, "🏠 귀환", "주운 것을 품에 안고 탑 입구를 지나 상층으로 돌아옵니다."),
    ],
    "far": [
        (0.16, "🚪 출발", "탑 입구를 벗어나 익숙한 길보다 더 멀리 향합니다. 여덟 다리의 보폭도 조금 넓어집니다."),
        (0.36, "🌒 먼 길", "희미한 빛이 닿는 바위길을 따라 한참 걷습니다. 드로우 상체는 주변 소리를 계속 살핍니다."),
        (0.58, "🔎 낯선 흔적", "처음 보는 자국 앞에 멈춰 앞다리 두 개로 가장자리를 꿈질꿈질 더듬습니다."),
        (0.78, "🕸️ 샛길", "좁은 바위 틈으로 들어갔다가 실 한 줄과 작은 물건을 끌고 다시 나타납니다."),
        (0.92, "🐾 돌아오는 길", "올 때보다 조금 느린 걸음으로 탑 쪽을 향합니다. 다리 끝에 흙과 먼지가 제법 묻었습니다."),
        (1.01, "🏠 귀환", "멀리 다녀온 티를 잔뜩 묻힌 채 탑 상층으로 돌아옵니다."),
    ],
}


WALK_RARE_EVENT_CHANCE = 0.30
WALK_RARE_EVENTS = {
    "indoor": {
        "karniss": {
            "title": "🕷️ 기척",
            "window": (0.42, 0.72),
            "text": "복도 끝에서 카르니스의 무거운 기척이 들립니다. 츄라이더는 이유를 묻지도 않고 여덟 다리를 접어 상자 뒤로 쏙 숨습니다. 카르니스가 자신을 왜 싫어하는지도, 마제스티와 하이네스 때문에 손대지 않는다는 것도 대충 압니다.\n“조용히 있으면 그냥 지나갈 검미댜...”",
            "summary": "카르니스와 마주치지 않으려고 익숙하게 상자 뒤로 피신했습니다.",
            "trace": "복도에서 급히 몸을 숨긴 탓인지 복부 옆에 먼지가 한 줄 길게 묻어 있습니다.",
        },
        "highness_pet": {
            "title": "🫳 하이네스의 복복",
            "window": (0.30, 0.58),
            "text": "복도를 돌던 츄라이더가 하이네스의 손이 보이자 경계도 잊고 쪼르르 다가갑니다. 머리부터 복부까지 한참 복복을 받고는 다리를 느슨하게 늘어뜨립니다.\n“하이네스는 영원히 복복해주실 검미댜.”",
            "summary": "하이네스에게 한참 복복을 받고 기분 좋게 늘어져 있었습니다.",
        },
        "majesty_pet": {
            "title": "👑 마제스티의 복복",
            "window": (0.36, 0.64),
            "text": "마제스티의 손길이 닿자 츄라이더가 도망갈 생각도 없이 얌전히 몸을 맡깁니다. 여덟 다리가 하나씩 풀리고, 끝내 손바닥 쪽으로 머리를 더 밀어 넣습니다.\n“조금만 더 해주셰요...”",
            "summary": "마제스티에게 복복을 받다가 한동안 그 자리에서 움직이지 않았습니다.",
        },
        "lubato_song": {
            "title": "🎵 복도 끝의 리라",
            "window": (0.38, 0.68),
            "text": "복도 끝에서 리라 소리가 가늘게 번집니다. 츄라이더가 카르니스의 기척인가 싶어 잠깐 멈췄다가, 루바토인 걸 알고 상자 뒤에서 슬그머니 나옵니다.\n“루바토였슴미댜. 노래는 안 물어뜯슴미댜.”",
            "summary": "루바토의 리라 소리를 따라가 한 곡이 끝날 때까지 얌전히 듣고 있었습니다.",
        },
        "lubato_karniss": {
            "title": "🎶 같은 복도, 다른 기척",
            "window": (0.52, 0.80),
            "text": "루바토가 복도 난간에 기대 리라를 튕깁니다. 멀리서 카르니스의 다리 소리가 들려오지만, 루바토는 태연히 연주를 이어갑니다. 츄라이더는 루바토의 망토 뒤로 몸 절반만 숨깁니다.\n“거기 있어도 돼. 대신 내 망토에 거미줄은 치지 마?”",
            "summary": "루바토의 망토 뒤에서 카르니스가 지나갈 때까지 리라 연주를 들었습니다.",
        },
        "majesty": {
            "title": "👑 마제스티의 자리",
            "window": (0.48, 0.78),
            "text": "마제스티가 자주 머무는 자리 근처에서 발걸음을 멈춥니다. 한참 주변을 맴돌다가 떨어진 리본 조각을 아주 조심스럽게 집어 듭니다.\n“이건 가져가도 됩니댜?”",
            "summary": "마제스티의 자리 근처에서 리본 조각을 하나 주웠습니다.",
            "bonus_item": "mat_ribbon_scrap",
        },
        "button": {
            "title": "✨ 반짝이는 단추",
            "window": (0.50, 0.80),
            "text": "상자 밑에서 무언가 반짝입니다. 츄라이더가 앞다리 끝으로 몇 번 굴려 본 뒤 손바닥에 올려놓습니다.\n“반짝입니댜.”",
            "summary": "상자 밑에서 반짝이는 단추를 찾아냈습니다.",
            "bonus_item": "mat_shiny_button",
        },
    },
    "near": {
        "bug": {
            "title": "🪲 벌레 추적",
            "window": (0.35, 0.68),
            "text": "풀숲 사이로 작은 벌레 하나가 튀어나옵니다. 츄라이더의 얼굴은 태연한데 여덟 다리가 동시에 방향을 틀어 쫓아갑니다.\n“잡을 수 있슴미댜.”",
            "summary": "풀숲에서 작은 벌레를 한참 쫓아다녔습니다.",
            "trace": "벌레를 쫓아 풀숲을 헤집은 흔적으로 다리 사이에 작은 풀씨가 잔뜩 붙어 있습니다.",
        },
        "feather": {
            "title": "🪶 날아온 깃털",
            "window": (0.46, 0.75),
            "text": "바람에 날린 깃털 하나가 거미 복부 위에 내려앉습니다. 츄라이더가 한동안 꼼짝하지 않다가 손으로 조심스럽게 떼어냅니다.\n“제 건가 봅니댜.”",
            "summary": "바람에 날아온 깃털을 하나 챙겨 왔습니다.",
            "bonus_item": "mat_feather",
        },
        "flower": {
            "title": "🌸 작은 꽃",
            "window": (0.52, 0.82),
            "text": "탑 벽 아래에서 작은 꽃을 발견합니다. 한참 들여다보다가 꽃잎 하나만 살짝 떼어 손에 쥡니다.\n“예쁩니댜.”",
            "summary": "탑 벽 아래에서 작은 꽃잎을 주워 왔습니다.",
            "bonus_item": "mat_flower_petal",
        },
    },
    "far": {
        "strange_object": {
            "title": "❖ 낯선 반짝임",
            "window": (0.42, 0.70),
            "text": "바위 틈 깊은 곳에서 희미한 빛이 납니다. 츄라이더가 몸을 낮추고 한참 끙끙거리더니 작은 마력 가루 묻은 조각을 끌어냅니다.\n“이상한 게 있슴미댜.”",
            "summary": "먼 바위 틈에서 마력이 남은 가루를 찾아냈습니다.",
            "bonus_item": "mat_magic_dust",
            "trace": "복부 아래와 앞다리에 희미하게 반짝이는 가루가 조금 묻어 있습니다.",
        },
        "web": {
            "title": "🕸️ 오래된 거미줄",
            "window": (0.50, 0.78),
            "text": "낯선 바위 틈에 오래된 거미줄이 걸려 있습니다. 츄라이더가 가까이 다가가 실의 결을 손끝과 앞다리로 번갈아 확인합니다.\n“이 실은 좀 다릅니댜.”",
            "summary": "낯선 바위 틈에서 질긴 실 한 가닥을 가져왔습니다.",
            "bonus_item": "mat_magic_thread",
        },
        "echo": {
            "title": "🌒 메아리",
            "window": (0.54, 0.82),
            "text": "멀리서 정체를 알 수 없는 울림이 한 번 퍼집니다. 츄라이더가 그대로 멈춰 모든 다리를 바닥에 붙이고 한참 귀를 기울입니다.\n“저쪽은 안 갈래요... 임니댜.”",
            "summary": "정체 모를 메아리를 듣고 한동안 움직이지 않았습니다.",
            "trace": "급히 방향을 바꿔 돌아온 흔적으로 다리 끝에 거친 흙먼지가 묻어 있습니다.",
        },
    },
}


def _choose_walk_rare_event(route: str, *, roll: float | None = None) -> str | None:
    value = random.random() if roll is None else roll
    if value >= WALK_RARE_EVENT_CHANCE:
        return None
    events = WALK_RARE_EVENTS.get(route, {})
    if not events:
        return None
    return random.choice(list(events.keys()))


def _walk_rare_event_scene(route: str, event_id: str | None, elapsed: float, duration: float):
    if not event_id:
        return None
    event = WALK_RARE_EVENTS.get(route, {}).get(event_id)
    if not event:
        return None
    ratio = max(0.0, min(1.0, elapsed / max(1.0, duration)))
    start, end = event["window"]
    if start <= ratio < end:
        return event["title"], event["text"]
    return None


def _walk_progress_bar(elapsed: float, duration: float, width: int = 10) -> str:
    ratio = max(0.0, min(1.0, elapsed / max(1.0, duration)))
    filled = min(width, int(ratio * width))
    return "▰" * filled + "▱" * (width - filled)


def _walk_scene(elapsed: float, duration: float = 24, route: str = "indoor") -> tuple[str, str]:
    ratio = max(0.0, min(1.0, elapsed / max(1.0, duration)))
    scenes = WALK_SCENES.get(route, WALK_SCENES["indoor"])
    for threshold, phase, text in scenes:
        if ratio < threshold:
            if phase == "🚪 출발":
                text += f"\n“{CHURIDER_SPEECH['walk_start']}”"
            elif "탐색" in phase or "흔적" in phase:
                text += f"\n“{CHURIDER_SPEECH['walk_find']}”"
            elif phase == "🏠 귀환":
                text += f"\n“{CHURIDER_SPEECH['walk_return']}”"
            return phase, text
    return scenes[-1][1], scenes[-1][2]


def _make_walk_progress_embed(route: str, remaining: int, elapsed: float, event_id: str | None = None, player=None) -> discord.Embed:
    profile = WALK_ROUTES[route]
    duration = profile["duration"]
    rare = _walk_rare_event_scene(route, event_id, elapsed, duration)
    phase, scene = rare if rare else _walk_scene(elapsed, duration, route)
    mark = _churider_mark(player) if player is not None else "🕷️"
    embed = discord.Embed(title=f"{mark} 🚶 산책 중 · {profile['label']}", description=scene, color=0x5C6574)
    embed.add_field(name=phase, value=f"{_walk_progress_bar(elapsed, duration)}  남은 시간 **{max(0, remaining)}초**", inline=False)
    embed.set_footer(text="츄라이더가 직접 움직이는 중입니다.")
    return embed


class WalkRouteView(ExpiringView):
    def __init__(self, player, care_manager, parent_view):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        for route, profile in WALK_ROUTES.items():
            btn = discord.ui.Button(label=profile["label"], style=discord.ButtonStyle.primary if route == "near" else discord.ButtonStyle.secondary)
            btn.callback = self._make_route_cb(route)
            self.add_item(btn)
        back = discord.ui.Button(label="◀ 돌아가기", style=discord.ButtonStyle.secondary, row=1)
        back.callback = self._back
        self.add_item(back)

    def make_embed(self):
        embed = discord.Embed(title="🕷️🚶 어디로 산책할까요?", description="거리마다 걸리는 시간과 피로, 주워 오는 것이 달라집니다.", color=0x5C6574)
        for profile in WALK_ROUTES.values():
            embed.add_field(name=f"{profile['label']} · {profile['duration']}초", value=profile["description"], inline=False)
        return embed

    def _make_route_cb(self, route: str):
        async def cb(interaction):
            await self.parent_view._start_walk(interaction, route)
        return cb

    async def _back(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


class CareRoomView(ExpiringView):
    def __init__(self, player, care_manager, *, suspicious_actor_id=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player       = player
        self.care_manager = care_manager
        self._message     = None
        self.suspicious_actor_id = suspicious_actor_id

        # Row 0: 관찰, 쓰다듬기, 먹이기
        observe_btn = discord.ui.Button(
            label="👀 관찰",
            style=discord.ButtonStyle.secondary,
            custom_id="care_observe",
            row=0,
        )
        observe_btn.callback = self._on_observe
        self.add_item(observe_btn)

        pet_btn = discord.ui.Button(
            label="🫳 쓰다듬기",
            style=discord.ButtonStyle.primary,
            custom_id="care_pet",
            row=0,
        )
        pet_btn.callback = self._on_pet
        self.add_item(pet_btn)

        snack_btn = discord.ui.Button(
            label="🍖 먹이기",
            style=discord.ButtonStyle.primary,
            custom_id="care_snack",
            row=0,
        )
        snack_btn.callback = self._on_snack
        self.add_item(snack_btn)

        # Row 1: 놀아주기, 의장관리
        play_btn = discord.ui.Button(
            label="🧶 놀기",
            style=discord.ButtonStyle.primary,
            custom_id="care_play",
            row=1,
        )
        play_btn.callback = self._on_play
        self.add_item(play_btn)

        wash_btn = discord.ui.Button(
            label="🛁 씻기기",
            style=discord.ButtonStyle.primary,
            custom_id="care_wash",
            row=1,
        )
        wash_btn.callback = self._on_wash
        self.add_item(wash_btn)

        rest_btn = discord.ui.Button(
            label="💤 쉬게 하기",
            style=discord.ButtonStyle.primary,
            custom_id="care_rest",
            row=1,
        )
        rest_btn.callback = self._on_rest
        self.add_item(rest_btn)

        costume_btn = discord.ui.Button(
            label="👗 의장관리",
            style=discord.ButtonStyle.secondary,
            custom_id="care_costume",
            row=1,
        )
        costume_btn.callback = self._on_costume
        self.add_item(costume_btn)

        # Row 2: 간식제작, 의장제작
        craft_snack_btn = discord.ui.Button(
            label="🍳 간식제작",
            style=discord.ButtonStyle.secondary,
            custom_id="care_craft_snack",
            row=2,
        )
        craft_snack_btn.callback = self._on_craft_snack
        self.add_item(craft_snack_btn)

        craft_costume_btn = discord.ui.Button(
            label="✂️ 의장제작",
            style=discord.ButtonStyle.secondary,
            custom_id="care_craft_costume",
            row=2,
        )
        craft_costume_btn.callback = self._on_craft_costume
        self.add_item(craft_costume_btn)

        # Row 3: 산책
        walk_btn = discord.ui.Button(
            label="🚶 산책",
            style=discord.ButtonStyle.secondary,
            custom_id="care_walk",
            row=3,
        )
        walk_btn.callback = self._on_walk
        self.add_item(walk_btn)

        # Row 4: 돌보기 방에서 상층 생활 공간으로 나가기
        leave_btn = discord.ui.Button(
            label="↩️ 상층으로 나가기",
            style=discord.ButtonStyle.secondary,
            custom_id="care_leave_room",
            row=4,
        )
        leave_btn.callback = self._leave_room
        self.add_item(leave_btn)

    async def _leave_room(self, interaction: discord.Interaction):
        view = TowerUpperFloorView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    # ── 관찰 / 몸단장 / 휴식 / 접촉 ─────────────────────────────────────
    async def _on_observe(self, interaction: discord.Interaction):
        view = ObserveView(self.player, self)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    async def _on_wash(self, interaction: discord.Interaction):
        result = self.care_manager.wash(self.player)
        if not result.get("success"):
            embed = discord.Embed(title="🕷️🛁 아직 목욕할 때가 아님", description=result["message"], color=0x596574)
            await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)
            return
        event_store.append(GameEvent(event_type="care.wash", actor_id=interaction.user.id, subject="츄라이더", location="비전의 탑", payload={"source": "care_room"}))
        try:
            save_player_to_db(self.player)
        except Exception as e:
            logger.error("씻기기 후 저장 실패: %s", e, exc_info=True)
        embed = discord.Embed(title="🕷️🛁 북북박박 목욕", description=result["message"], color=0x4F7186)
        embed.add_field(name="🫧 몸 상태", value="복부와 여덟 다리 사이까지 말끔해졌습니다. 다음 목욕까지 1시간.", inline=False)
        await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)

    async def _on_rest(self, interaction: discord.Interaction):
        status = self.care_manager.get_rest_status(self.player)
        if status.get("completed"):
            self.care_manager.finish_rest(self.player)
            status = self.care_manager.get_rest_status(self.player)
        if not status.get("active"):
            self.care_manager.start_rest(self.player)
            event_store.append(GameEvent(event_type="care.rest", actor_id=interaction.user.id, subject="츄라이더", location="비전의 탑", payload={"source": "care_room"}))
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("휴식 시작 저장 실패: %s", e, exc_info=True)
        view = RestingView(self.player, self.care_manager, self)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    async def _on_pet(self, interaction: discord.Interaction):
        result = self.care_manager.pet(self.player)
        from core.special_reactions import reaction_for
        special = reaction_for(interaction.user.id, suspicious_actor_id=self.suspicious_actor_id)
        if special and result.get("success"):
            opening = dict(result)
            opening["message"] = special.pet
        else:
            opening = result
        if result.get("success"):
            event_store.append(GameEvent(event_type="care.pet", actor_id=interaction.user.id, subject="츄라이더", location="비전의 탑", payload={"source": "care_room"}))
            bond_service.award("care.pet", actor_id=interaction.user.id)
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("쓰다듬기 후 저장 실패: %s", e, exc_info=True)
            try:
                import app_context
                app_context.get_diary_manager().increment("pet_count", 1)
            except Exception as e:
                logger.warning("일기 기록 실패: %s", e)
        view = PettingView(self.player, self.care_manager, self, opening=opening)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    # ── 산책 ──────────────────────────────────────────────────────────────
    WALK_COOLDOWN = 180  # 산책 완료 후 3분
    WALK_UPDATE_INTERVAL = WALK_UPDATE_SECONDS
    WALK_ITEMS = [
        # (아이템ID, 가중치)  — 장난감/의상 제작 재료
        ("mat_wood_scrap",    20),
        ("mat_feather",       18),
        ("mat_flower_petal",  18),
        ("mat_silk_thread",   12),
        ("mat_ribbon_scrap",  12),
        ("mat_soft_cotton",   10),
        ("mat_leather_piece",  8),
        ("mat_shiny_button",   8),
        ("mat_honey",         10),
        ("mat_fruit",         10),
        ("mat_magic_thread",   3),
        ("mat_magic_dust",     2),
    ]

    async def _on_walk(self, interaction: discord.Interaction):
        if not hasattr(self.player, "_flags") or self.player._flags is None:
            self.player._flags = {}
        now = _time.time()
        last_walk = self.player._flags.get("last_walk_time", 0)
        remaining_cd = self.WALK_COOLDOWN - (now - last_walk)
        if remaining_cd > 0:
            mins, secs = divmod(int(remaining_cd), 60)
            embed = discord.Embed(title="🕷️🚶 산책", description=f"아직 산책할 수 없습니다. {mins}분 {secs}초 남았습니다.", color=0x5C6574)
            await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)
            return
        view = WalkRouteView(self.player, self.care_manager, self)
        view.bind_message(getattr(interaction, "message", None))
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    async def _start_walk(self, interaction: discord.Interaction, route: str):
        profile = WALK_ROUTES[route]
        duration = profile["duration"]
        started = _time.time()
        self.player._flags["walk_started_at"] = started
        self.player._flags["walk_active_until"] = started + duration
        self.player._flags["walk_route"] = route
        event_id = _choose_walk_rare_event(route)
        self.player._flags["walk_rare_event"] = event_id or ""
        first = _make_walk_progress_embed(route, duration, 0, event_id, self.player)
        await interaction.response.edit_message(content=None, attachments=[], embed=first, view=None)
        message = getattr(interaction, "message", None)
        asyncio.create_task(self._run_walk_activity(message, started, route, event_id))

    async def _run_walk_activity(self, message, started: float, route: str, event_id: str | None = None):
        profile = WALK_ROUTES[route]
        duration = profile["duration"]
        elapsed = 0.0
        while elapsed < duration:
            await asyncio.sleep(self.WALK_UPDATE_INTERVAL)
            elapsed = min(duration, _time.time() - started)
            remaining = max(0, int(round(duration - elapsed)))
            if message is not None:
                try:
                    await message.edit(embed=_make_walk_progress_embed(route, remaining, elapsed, event_id, self.player), view=None)
                except (discord.NotFound, discord.Forbidden):
                    message = None
                except Exception as e:
                    logger.warning("산책 진행 화면 갱신 실패: %s", e)

        items_found = []
        min_items, max_items = profile["items"]
        num_items = random.randint(min_items, max_items)
        pool_ids, pool_weights = zip(*self.WALK_ITEMS)
        for _ in range(num_items):
            chosen_id = random.choices(pool_ids, weights=pool_weights)[0]
            self.player.add_hyness_item(chosen_id, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(chosen_id, {}).get("name", chosen_id)
            items_found.append(item_name)

        gains = {"indoor": (2, 1), "near": (3, 2), "far": (4, 3)}
        cond_gain, stab_gain = gains[route]
        self.player.condition = min(100, self.player.condition + cond_gain)
        self.player.stability = min(100, self.player.stability + stab_gain)
        from care import apply_outing_effect
        rare_event = WALK_RARE_EVENTS.get(route, {}).get(event_id) if event_id else None
        trace = rare_event.get("trace") if rare_event else None
        apply_outing_effect(self.player, profile["outing"], trace=trace)
        if event_id in {"karniss", "highness_pet", "majesty_pet", "lubato_song", "lubato_karniss"}:
            try:
                from lubato_song_memory import remember
                remember(self.player, event_id)
            except Exception:
                logger.warning("루바토 노래 기억 기록 실패", exc_info=True)
        if rare_event and rare_event.get("bonus_item"):
            bonus_id = rare_event["bonus_item"]
            self.player.add_hyness_item(bonus_id, 1)
            from items import ALL_ITEMS
            bonus_name = ALL_ITEMS.get(bonus_id, {}).get("name", bonus_id)
            items_found.append(f"✨ {bonus_name}")
        self.player._flags["walk_active_until"] = 0.0
        self.player._flags["walk_started_at"] = 0.0
        self.player._flags["walk_route"] = ""
        self.player._flags["walk_rare_event"] = ""
        self.player._flags["last_walk_time"] = _time.time()

        try:
            save_player_to_db(self.player)
        except Exception as e:
            logger.error("산책 후 저장 실패: %s", e, exc_info=True)

        embed = discord.Embed(title=f"{_churider_mark(self.player)} 🚶 산책 완료 · {profile['label']}", description=f"츄라이더가 책장 뒤 틈으로 돌아와 주운 것을 내려놓습니다.\n“{CHURIDER_SPEECH['walk_return']}”", color=0x5C6574)
        if rare_event:
            embed.add_field(name="✨ 특별한 일", value=rare_event["summary"], inline=False)
        embed.add_field(name="🎁 주워 온 것", value=", ".join(items_found), inline=False)
        embed.add_field(name="변화", value=f"컨디션 +{cond_gain} · 안정감 +{stab_gain}", inline=False)
        if message is not None:
            try:
                await message.edit(embed=embed, view=self)
                self.bind_message(message)
            except Exception as e:
                logger.warning("산책 완료 화면 갱신 실패: %s", e)

    # ── 간식주기 ──────────────────────────────────────────────────────────
    async def _on_snack(self, interaction: discord.Interaction):
        sub_view = SnackFeedView(self.player, self.care_manager, self)
        sub_view.bind_message(getattr(interaction, "message", None))
        embed = discord.Embed(title="🕷️🍖 먹이기", description="츄라이더에게 줄 먹을 것을 고릅니다.", color=0x7B6545)
        await interaction.response.edit_message(
            content=None, attachments=[], embed=embed, view=sub_view
        )

    # ── 놀아주기 ──────────────────────────────────────────────────────────
    async def _on_play(self, interaction: discord.Interaction):
        # 쿨타임 체크
        remaining = self.care_manager.get_play_cooldown_remaining(self.player)
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            embed = discord.Embed(title="🕷️🧶 놀기", description=f"아직 놀아줄 수 없습니다. {mins}분 {secs}초 남았습니다.", color=0x6B5C5C)
            await interaction.response.edit_message(
                content=None, attachments=[], embed=embed, view=self
            )
            return

        sub_view = RockPaperScissorsView(self.player, self.care_manager, self)
        sub_view.bind_message(getattr(interaction, "message", None))
        embed = discord.Embed(title="🕷️🧶 놀기 — 가위바위보", description="✊ 바위 / ✌️ 가위 / ✋ 보 중 하나를 선택합니다.", color=0x655A8A)
        await interaction.response.edit_message(
            content=None, attachments=[], embed=embed, view=sub_view
        )

    # ── 의장관리 ──────────────────────────────────────────────────────────
    async def _on_costume(self, interaction: discord.Interaction):
        sub_view = CostumeManageView(self.player, self)
        sub_view.bind_message(getattr(interaction, "message", None))
        rows = sub_view._build_status_rows()
        embed = discord.Embed(title="🕷️👗 의장관리", description="츄라이더의 장난감과 의장을 정리합니다.", color=0x6D596E)
        for row in rows[:5]:
            embed.add_field(name=row["label"], value=row["value"], inline=True)
        await interaction.response.edit_message(
            content=None, attachments=[], embed=embed, view=sub_view
        )

    # ── 간식제작 ──────────────────────────────────────────────────────────
    async def _on_craft_snack(self, interaction: discord.Interaction):
        sub_view = SnackCraftView(self.player, self.care_manager, self)
        sub_view.bind_message(getattr(interaction, "message", None))
        file = _result_card(
            "🍳 간식제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 간식을 선택합니다."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 의장제작 ──────────────────────────────────────────────────────────
    async def _on_craft_costume(self, interaction: discord.Interaction):
        sub_view = CostumeCraftView(self.player, self.care_manager, self)
        sub_view.bind_message(getattr(interaction, "message", None))
        file = _result_card(
            "✂️ 의장제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 의장을 선택합니다."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    async def on_timeout(self):
        await super().on_timeout()
