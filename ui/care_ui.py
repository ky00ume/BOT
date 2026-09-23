"""care_ui.py — 비전의 탑 상층 · 츄라이더의 숨은 보금자리 돌봄 UI"""
import discord
from ui.view_timeouts import CARE_VIEW_TIMEOUT
from ui.expiring_view import ExpiringView
import random
import time as _time
from utils.logger import setup_logger
logger = setup_logger('care_ui')
from bg3_renderer import get_renderer
from costume_data import (
    COSTUME_ITEMS, SNACK_ITEMS, SNACK_RECIPES, COSTUME_RECIPES,
    GRADE_EMOJI, GRADE_LABELS,
)
from database import save_player_to_db
from core.events import GameEvent, event_store
from core.bond import bond_service
from core.pet_state import observe_pet
from care import get_care_state


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
    details.append(_nest_trace(player))
    return details


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
        title="🕷️ 츄라이더",
        description=description,
        color=0x544766,
    )
    embed.add_field(name="상태", value=_status_line(player), inline=False)
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

        # 뒤로 가기
        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_costume",
            row=3,
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
                    [{"label": "안내", "value": f"{slot_label}에 장착 가능한 의장 아이템이 없슴미댜."}],
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
                content=f"**{self.SLOT_LABELS.get(slot, slot)} 슬롯 장착**\n장착할 의장을 선택하셰요.",
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
        file = _result_card(
            "의장 장착",
            grade=grade_eng,
        )
        await interaction.response.edit_message(content=None, attachments=[file], view=None)

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
                [{"label": "안내", "value": "장착된 의장이 없슴미댜."}],
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
            content="해제할 의장 슬롯을 선택하셰요.",
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
        self.player       = player
        self.care_manager = care_manager
        self.parent_view  = parent_view

        from items import ALL_ITEMS
        options = []
        h_inv = player.get_hyness_inventory()
        for item_id, count in h_inv.items():
            item = ALL_ITEMS.get(item_id, {})
            if item.get("type") == "snack":
                grade = item.get("grade", "일반")
                icon  = GRADE_EMOJI.get(grade, "⚬")
                eff   = item.get("effect", {})
                eff_str = " ".join(
                    f"{k[0].upper()}{'+'if v>0 else ''}{v}"
                    for k, v in eff.items()
                )
                options.append(discord.SelectOption(
                    label=f"{icon} {item.get('name', item_id)} x{count}",
                    value=item_id,
                    description=eff_str[:50],
                ))

        if options:
            select = discord.ui.Select(
                placeholder="줄 간식을 선택하셰요...",
                options=options[:25],
                custom_id="snack_select",
            )
            select.callback = self._on_snack_select
            self.add_item(select)
        else:
            # 간식 없음 안내 버튼 (비활성화)
            btn = discord.ui.Button(
                label="보유한 간식이 없슴미댜",
                style=discord.ButtonStyle.secondary,
                disabled=True,
            )
            self.add_item(btn)

        back_btn = discord.ui.Button(
            label="◀ 돌아가기",
            style=discord.ButtonStyle.secondary,
            custom_id="back_from_snack",
            row=1,
        )
        back_btn.callback = self._on_back
        self.add_item(back_btn)

    async def _on_snack_select(self, interaction: discord.Interaction):
        snack_id = interaction.data["values"][0]
        result = self.care_manager.feed_snack(self.player, snack_id)
        rows = [{"label": "결과", "value": result["message"]}]
        if result.get("changes"):
            for k, v in result["changes"].items():
                labels = {"condition": "💛 컨디션", "stability": "💙 안정감", "fatigue": "🔥 피로도"}
                sign = "+" if v >= 0 else ""
                rows.append({"label": labels.get(k, k), "value": f"{sign}{v}"})
        grade = "Normal" if result["success"] else "Fail"
        if result["success"]:
            event_store.append(GameEvent(event_type="care.feed", actor_id=interaction.user.id, subject="츄라이더", location="비전의 탑", payload={"snack": SNACK_ITEMS.get(snack_id, {}).get("name", snack_id)}))
            try:
                save_player_to_db(self.player)
            except Exception as e:
                logger.error("간식 급여 후 저장 실패: %s", e, exc_info=True)
        await interaction.response.edit_message(
            content=None, attachments=[], embed=_make_room_embed(self.player), view=self
        )

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
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

    async def _done(self, interaction):
        await interaction.response.edit_message(attachments=[], embed=_make_room_embed(self.player), view=self.parent_view)


class PettingView(ExpiringView):
    REACTIONS = [
        "손을 내밀자 츄라이더가 시선을 올립니다. 앞다리 하나가 잠깐 들렸다가 다시 바닥에 내려옵니다.",
        "흰 머리카락 사이를 천천히 쓰다듬자 어깨의 힘이 조금 풀립니다. 거미 다리 두 개도 몸 안쪽으로 접힙니다.",
        "조금 더 쓰다듬자 츄라이더가 먼저 머리를 손바닥 쪽으로 기울입니다. 복부도 바닥에 편하게 내려놓습니다.",
        "손을 떼지 않자 눈을 반쯤 감고 가만히 있습니다. 앞다리 하나가 손목 가까이에 조심스럽게 걸립니다.",
        "이제는 손길이 멈출 때마다 고개를 아주 조금 따라옵니다. 더 쓰다듬어도 괜찮다는 뜻처럼 보입니다.",
    ]

    def __init__(self, player, care_manager, parent_view, *, step=0, opening=None):
        super().__init__(timeout=CARE_VIEW_TIMEOUT)
        self.player = player
        self.care_manager = care_manager
        self.parent_view = parent_view
        self.step = step
        self.opening = opening
        if step < len(self.REACTIONS) - 1:
            more = discord.ui.Button(label="🫳 계속 쓰다듬기", style=discord.ButtonStyle.primary)
            more.callback = self._more
            self.add_item(more)
        done = discord.ui.Button(label="그만 쓰다듬기", style=discord.ButtonStyle.secondary)
        done.callback = self._done
        self.add_item(done)

    def make_embed(self):
        text = self.REACTIONS[min(self.step, len(self.REACTIONS) - 1)]
        return discord.Embed(title="🕷️🫳 쓰다듬기", description=text, color=0x8C668A)

    async def _more(self, interaction):
        view = PettingView(self.player, self.care_manager, self.parent_view, step=self.step + 1)
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)

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
        view.bind_message(interaction.message)
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
            next_view.bind_message(interaction.message)
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
        view.bind_message(interaction.message)
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
                placeholder="제작할 간식을 선택하셰요...",
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
                "먼저 제작할 간식을 선택하셰요!", ephemeral=True
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
                placeholder="제작할 의장을 선택하셰요...",
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
                "먼저 제작할 의장을 선택하셰요!", ephemeral=True
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
        await interaction.response.edit_message(content=None, attachments=[], embed=_make_room_embed(self.player), view=self)

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
                ("마제스티의 자리", "🕯️", "마제스티의 자리", "손이 자주 닿는 물건들이 정돈되어 있다. 책장 아래에는 누군가 일부러 밀어 넣은 듯한 작은 간식 접시가 하나 놓여 있다."),
                ("카르니스의 기척", "🕷️", "카르니스의 기척", "복도 너머에서 단단한 발끝이 바닥을 긁는 소리가 난다. 책장 아래의 작은 발자국은 그 소리가 가까워질수록 안쪽으로 향한다."),
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

    async def _open_nest(self, interaction):
        view = CareRoomView(self.player, self.care_manager, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(interaction.message)
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
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=discord.Embed(title="비전의 탑 · 수서 발전기", description=desc, color=0x46594F), view=view)

    def _make_facility_callback(self, facility):
        async def callback(interaction):
            view = TowerFacilityView(self.player, self.care_manager, facility=facility, return_place=self.place, suspicious_actor_id=self.suspicious_actor_id)
            view.bind_message(interaction.message)
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        return callback

    def _make_observation_callback(self, title, text):
        async def callback(interaction):
            await interaction.response.edit_message(attachments=[], embed=self.make_embed((title, text)), view=self)
        return callback

    async def _open_lift(self, interaction):
        from tower_power import facility_online
        if not facility_online(self.player, "lift"):
            embed = self.make_embed(("멈춘 승강기", "승강기에는 동력이 들어오지 않는다. 하층의 수서 발전기를 먼저 살펴봐야 할 것 같다."))
            await interaction.response.edit_message(attachments=[], embed=embed, view=self)
            return
        view = TowerLiftView(self.player, self.care_manager, current_place=self.place, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(interaction.message)
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
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(result), view=view)

    async def _back(self, interaction):
        view = TowerPlaceView(self.player, self.care_manager, place=self.return_place, suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


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
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=discord.Embed(title="비전의 탑 · 수서 발전기", description=text, color=0x46594F), view=view)

    async def _back(self, interaction):
        view = TowerPlaceView(self.player, self.care_manager, place="storage", suspicious_actor_id=self.suspicious_actor_id)
        view.bind_message(interaction.message)
        await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)


class TowerUpperFloorView(TowerPlaceView):
    """기존 진입점 호환용 상층 View."""
    def __init__(self, player, care_manager, *, suspicious_actor_id=None):
        super().__init__(player, care_manager, place="upper", suspicious_actor_id=suspicious_actor_id)


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
            view.bind_message(interaction.message)
            await interaction.response.edit_message(attachments=[], embed=view.make_embed(), view=view)
        return callback


# ── 메인 비전의 탑 돌봄 View ──────────────────────────────────────────────────
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

    # ── 관찰 / 몸단장 / 휴식 / 접촉 ─────────────────────────────────────
    async def _on_observe(self, interaction: discord.Interaction):
        view = ObserveView(self.player, self)
        view.bind_message(interaction.message)
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
        view.bind_message(interaction.message)
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
        view.bind_message(interaction.message)
        await interaction.response.edit_message(content=None, attachments=[], embed=view.make_embed(), view=view)

    # ── 산책 ──────────────────────────────────────────────────────────────
    WALK_COOLDOWN = 180  # 3분
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

        # 쿨타임 체크
        now = _time.time()
        last_walk = self.player._flags.get("last_walk_time", 0)
        remaining = self.WALK_COOLDOWN - (now - last_walk)
        if remaining > 0:
            mins, secs = divmod(int(remaining), 60)
            embed = discord.Embed(title="🕷️🚶 산책", description=f"아직 산책할 수 없슴미댜! {mins}분 {secs}초 남음", color=0x5C6574)
            await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)
            return

        # 쿨타임 갱신
        self.player._flags["last_walk_time"] = now

        # 랜덤 아이템 1~2개 획득
        items_found = []
        num_items = random.choices([1, 2], weights=[70, 30])[0]
        pool_ids, pool_weights = zip(*self.WALK_ITEMS)
        for _ in range(num_items):
            chosen_id = random.choices(pool_ids, weights=pool_weights)[0]
            self.player.add_hyness_item(chosen_id, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(chosen_id, {}).get("name", chosen_id)
            items_found.append(item_name)

        # 컨디션/안정감 소량 변화
        cond_gain = random.randint(2, 5)
        stab_gain = random.randint(1, 3)
        self.player.condition = min(100, self.player.condition + cond_gain)
        self.player.stability = min(100, self.player.stability + stab_gain)

        rows = [
            {"label": "🐾 상태", "value": "츄라이더가 신나게 산책하고 돌아왔슴미댜~!"},
            {"label": "🎁 획득", "value": ", ".join(items_found)},
            {"label": "💛 컨디션", "value": f"+{cond_gain} → {self.player.condition}"},
            {"label": "💙 안정감", "value": f"+{stab_gain} → {self.player.stability}"},
        ]

        embed = discord.Embed(title="🕷️🚶 산책", description=rows[0]["value"], color=0x5C6574)
        embed.add_field(name="🎁 획득", value=", ".join(items_found), inline=False)

        try:
            save_player_to_db(self.player)
        except Exception as e:
            logger.error("산책 후 저장 실패: %s", e, exc_info=True)
        await interaction.response.edit_message(content=None, attachments=[], embed=embed, view=self)

    # ── 간식주기 ──────────────────────────────────────────────────────────
    async def _on_snack(self, interaction: discord.Interaction):
        sub_view = SnackFeedView(self.player, self.care_manager, self)
        sub_view.bind_message(interaction.message)
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
            embed = discord.Embed(title="🕷️🧶 놀기", description=f"아직 쿨타임임미댜... ({mins}분 {secs}초 남음)", color=0x6B5C5C)
            await interaction.response.edit_message(
                content=None, attachments=[], embed=embed, view=self
            )
            return

        sub_view = RockPaperScissorsView(self.player, self.care_manager, self)
        sub_view.bind_message(interaction.message)
        embed = discord.Embed(title="🕷️🧶 놀기 — 가위바위보", description="✊ 바위 / ✌️ 가위 / ✋ 보 중 선택하셰요!", color=0x655A8A)
        await interaction.response.edit_message(
            content=None, attachments=[], embed=embed, view=sub_view
        )

    # ── 의장관리 ──────────────────────────────────────────────────────────
    async def _on_costume(self, interaction: discord.Interaction):
        sub_view = CostumeManageView(self.player, self)
        sub_view.bind_message(interaction.message)
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
        sub_view.bind_message(interaction.message)
        file = _result_card(
            "🍳 간식제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 간식을 선택하셰요."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    # ── 의장제작 ──────────────────────────────────────────────────────────
    async def _on_craft_costume(self, interaction: discord.Interaction):
        sub_view = CostumeCraftView(self.player, self.care_manager, self)
        sub_view.bind_message(interaction.message)
        file = _result_card(
            "✂️ 의장제작",
            [{"label": "안내", "value": "✅ = 재료 충분 / ❌ = 재료 부족\n제작할 의장을 선택하셰요."}],
        )
        await interaction.response.edit_message(
            content=None, attachments=[file], view=sub_view
        )

    async def on_timeout(self):
        await super().on_timeout()
