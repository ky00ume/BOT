"""npc_conversation.py — 마비노기식 NPC 키워드 대화 시스템 (PIL 이미지+버튼 UI)"""
import random
import io
import discord
from discord.ui import View, Button
from database import NPC_DATA
from npc_dialogue_db import NPC_KEYWORDS, DEFAULT_KEYWORDS, AFFINITY_UNLOCK_KEYWORDS
from bg3_renderer import get_renderer
from utils.logger import setup_logger

logger = setup_logger('npc_conversation')

# ── NPC 초상화 파일 ID 매핑 ─────────────────────────────────────────────────
# BG3 위키 매칭 NPC: 파일명은 static/portraits/npc/{portrait_id}.png
# 창작 캐릭터(카엘릭, 브룩샤, 실렌, 루바토)는 placeholder 유지
NPC_PORTRAIT_MAP: dict[str, str] = {
    "라파엘":    "라파엘",    # BG3 Raphael
    "카르니스":  "카르니스",  # BG3 Kar'niss (드라이더)
    "다몬":      "다몬",      # BG3 Dammon
    "오멜룸":    "오멜룸",    # BG3 Omeluum
    "몰":        "몰",        # BG3 Mol
    "아라벨라":  "아라벨라",  # BG3 Arabella
    "알피라":    "알피라",    # BG3 Alfira
    "엘레라신":  "엘레라신",  # BG3 Jaheira
    "게일의 환영": "게일의 환영",  # BG3 Gale
    # 창작 캐릭터 (placeholder)
    "카엘릭":    "카엘릭",    # 창작 캐릭터
    "브룩샤":    "브룩샤",    # 창작 캐릭터
    "실렌":      "실렌",      # 창작 캐릭터
    "루바토":    "루바토",    # 창작 캐릭터
    "파울":      "파울",      # 창작 캐릭터 (여관 주인)
}


def _get_affinity_level_name(aff_manager, npc_name: str) -> str:
    if aff_manager is None:
        return "낯선이"
    return aff_manager.get_level_name(npc_name)


def _get_affinity_points(aff_manager, npc_name: str) -> int:
    if aff_manager is None:
        return 0
    return aff_manager.affinities.get(npc_name, 0)


def _level_index(level_name: str) -> int:
    order = ["낯선이", "지인", "친구", "절친", "영혼의 동반자"]
    try:
        return order.index(level_name)
    except ValueError:
        return 0


def _get_response(keyword_data: dict, level_name: str) -> str:
    """호감도 단계에 맞는 응답을 반환. 값이 list이면 랜덤 선택."""
    order = ["영혼의 동반자", "절친", "친구", "지인", "default"]
    lv_idx = _level_index(level_name)
    for key in order:
        if key == "default":
            val = keyword_data.get("default", "...")
        else:
            key_idx = _level_index(key)
            if lv_idx < key_idx or key not in keyword_data:
                continue
            val = keyword_data[key]
        if isinstance(val, list):
            return random.choice(val)
        return val
    return keyword_data.get("default", "...")


def get_available_keywords(npc_name: str, player_keywords: list) -> list:
    npc_keywords = NPC_KEYWORDS.get(npc_name, {})
    result = []
    for kw in player_keywords:
        kw_data = npc_keywords.get(kw)
        if kw_data is None:
            continue
        req = kw_data.get("required_keyword")
        if req:
            if isinstance(req, list):
                if not all(r in player_keywords for r in req):
                    continue
            else:
                if req not in player_keywords:
                    continue
        result.append(kw)
    return result


def _render_greeting_image(npc_name: str, aff_manager, show_limit_warning: bool = False) -> io.BytesIO:
    """NPC 인사 이미지를 PIL로 생성합니다."""
    npc = NPC_DATA.get(npc_name, {})
    greeting = random.choice(npc.get("greetings", ["..."]))
    role = npc.get("role", "???")
    aff_pts = _get_affinity_points(aff_manager, npc_name)
    aff_lv = _get_affinity_level_name(aff_manager, npc_name)

    if show_limit_warning:
        greeting += "\n오늘의 최대 호감도 획득량을 달성했슴미댜!"

    return get_renderer().render_npc_dialogue(
        npc_name=npc.get("name", npc_name),
        npc_role=role,
        greeting=greeting,
        affinity_pts=aff_pts,
        affinity_level=aff_lv,
        portrait_type="npc",
        portrait_id=npc_name,
    )


def _render_keyword_response_image(
    npc_name: str,
    keyword: str,
    response_text: str,
    aff_manager,
    aff_gain: int,
    show_limit_warning: bool,
    unlocked: list,
    leveled: bool,
    lv_name: str,
) -> io.BytesIO:
    """키워드 응답 이미지를 PIL로 생성합니다 (초상화 포함)."""
    npc = NPC_DATA.get(npc_name, {})
    aff_pts = _get_affinity_points(aff_manager, npc_name)
    aff_lv = _get_affinity_level_name(aff_manager, npc_name)

    # 대사 + 추가 정보를 하나의 greeting 문자열로 조합
    greeting_parts = [response_text]
    if not show_limit_warning and aff_gain > 0:
        greeting_parts.append(f"[호감도 +{aff_gain}]")
    if leveled:
        greeting_parts.append(f"[단계 상승 → {lv_name}]")
    if unlocked:
        greeting_parts.append(f"[새 키워드: {', '.join(unlocked)}]")
    if show_limit_warning:
        greeting_parts.append(f"[오늘의 최대 호감도 달성! ({aff_pts}pt)]")
    combined_greeting = "\n".join(greeting_parts)

    role = npc.get("role", "???")
    return get_renderer().render_npc_dialogue(
        npc_name=npc.get("name", npc_name),
        npc_role=f"{role} — [{keyword}]",
        greeting=combined_greeting,
        affinity_pts=aff_pts,
        affinity_level=aff_lv,
        portrait_type="npc",
        portrait_id=npc_name,
    )


class NPCConversationView(View):
    """NPC 대화 이미지+버튼 View"""

    def __init__(self, npc_name: str, player, aff_manager, npc_manager_ref=None):
        super().__init__(timeout=180.0)
        self.npc_name = npc_name
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref
        self._build_buttons()

    def _build_buttons(self):
        """현재 키워드 목록과 NPC 기능에 따라 버튼을 구성합니다."""
        self.clear_items()
        npc = NPC_DATA.get(self.npc_name, {})
        player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
        available = get_available_keywords(self.npc_name, player_kws)

        # 기능 버튼 수에 따라 키워드 버튼 최대 수 동적 계산 (Discord 한계: 25)
        # D-3: "마을로 돌아가기" 버튼 1개 추가 계산
        extra_count = (
            (1 if npc.get("job") else 0) +
            (1 if self.npc_name in __import__("shop").NPC_CATALOGS else 0) +
            (1 if npc.get("train") else 0) +
            1  # D-3: 마을로 돌아가기 버튼
        )
        max_kw_buttons = max(0, 25 - extra_count)

        # 기본 키워드 버튼들 (마을, 날씨, 소문 및 해금된 키워드들)
        for kw in available[:max_kw_buttons]:
            btn = Button(
                label=kw,
                style=discord.ButtonStyle.secondary,
                custom_id=f"kw_{self.npc_name}_{kw}",
            )
            btn.callback = self._make_keyword_callback(kw)
            self.add_item(btn)

        # 아르바이트 버튼 (NPC에 job이 있으면)
        if npc.get("job"):
            job_btn = Button(
                label="아르바이트",
                style=discord.ButtonStyle.primary,
                emoji="💼",
            )
            job_btn.callback = self._job_callback
            self.add_item(job_btn)

        # 구매 버튼 (NPC_CATALOGS에 있으면)
        from shop import NPC_CATALOGS
        if self.npc_name in NPC_CATALOGS:
            buy_btn = Button(
                label="구매",
                style=discord.ButtonStyle.success,
                emoji="🛒",
            )
            buy_btn.callback = self._buy_callback
            self.add_item(buy_btn)

        # 수련 버튼 (NPC에 train이 있으면)
        if npc.get("train"):
            train_btn = Button(
                label="수련",
                style=discord.ButtonStyle.success,
                emoji="⚔️",
            )
            train_btn.callback = self._train_callback
            self.add_item(train_btn)

        # 여관 휴식 버튼 (NPC에 inn이 있으면)
        if npc.get("inn"):
            inn_btn = Button(
                label="휴식",
                style=discord.ButtonStyle.success,
                emoji="🛏️",
            )
            inn_btn.callback = self._inn_callback
            self.add_item(inn_btn)

        # 연주 버튼 (알피라 + 연주 스킬 보유 시)
        if self.npc_name == "알피라" and "music" in getattr(self.player, "skill_ranks", {}):
            music_btn = Button(
                label="연주",
                style=discord.ButtonStyle.success,
                emoji="🎵",
            )
            music_btn.callback = self._music_callback
            self.add_item(music_btn)

        # 제련 배우기 버튼 (다몬 + 제련 스킬 미보유 시)
        if self.npc_name == "다몬" and "metallurgy" not in getattr(self.player, "skill_ranks", {}):
            smelt_btn = Button(
                label="제련 배우기",
                style=discord.ButtonStyle.success,
                emoji="🔥",
            )
            smelt_btn.callback = self._learn_metallurgy_callback
            self.add_item(smelt_btn)

        # D-3: 마을로 돌아가기 버튼
        back_btn = Button(
            label="마을로 돌아가기",
            style=discord.ButtonStyle.secondary,
            emoji="🏠",
        )
        back_btn.callback = self._back_to_town_callback
        self.add_item(back_btn)

    async def _back_to_town_callback(self, interaction: discord.Interaction):
        """D-3: 마을 메인 UI로 전환합니다."""
        try:
            from town_ui import VisionTownView
            import app_context
            view = VisionTownView(app_context.get_player(), app_context.get_affinity_manager(), app_context.get_npc_manager())
            await view.send(interaction, edit=True)
        except Exception:
            logger.warning('npc_conversation: _back_to_town_callback 실패 — 안내 메시지 전송', exc_info=True)
            await interaction.response.send_message(
                "🏠 `/비전타운` 명령어로 마을로 돌아가세요!", ephemeral=True
            )

    def _make_keyword_callback(self, keyword: str):
        async def callback(interaction: discord.Interaction):
            await self._handle_keyword(interaction, keyword)
        return callback

    async def _handle_keyword(self, interaction: discord.Interaction, keyword: str):
        npc = NPC_DATA.get(self.npc_name)
        if not npc:
            await interaction.response.send_message("NPC를 찾을 수 없슴미댜.", ephemeral=True)
            return

        npc_kws = NPC_KEYWORDS.get(self.npc_name, {})
        kw_data = npc_kws.get(keyword)
        if not kw_data:
            await interaction.response.send_message("이 키워드에 대한 응답이 없슴미댜.", ephemeral=True)
            return

        level_name = _get_affinity_level_name(self.aff_manager, self.npc_name)

        # 일일 제한 체크 (차단하지 않고 경고만)
        show_limit_warning = False
        if self.aff_manager and hasattr(self.aff_manager, "check_talk_limit"):
            allowed, _ = self.aff_manager.check_talk_limit(self.npc_name)
            if not allowed:
                show_limit_warning = True

        response_text = _get_response(kw_data, level_name)
        aff_gain = kw_data.get("affinity_points", 2)

        leveled = False
        lv_name = level_name
        if self.aff_manager and not show_limit_warning:
            self.aff_manager.record_talk(self.npc_name)
            _, leveled, lv_name = self.aff_manager.add_affinity(self.npc_name, aff_gain)

        # 새 키워드 해금
        unlocked = []
        unlock_raw = kw_data.get("unlock_keyword")
        if unlock_raw:
            to_unlock = unlock_raw if isinstance(unlock_raw, list) else [unlock_raw]
            player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
            for new_kw in to_unlock:
                if new_kw not in player_kws:
                    player_kws.append(new_kw)
                    unlocked.append(new_kw)
            if not hasattr(self.player, "keywords"):
                self.player.keywords = player_kws

        # 레벨업 시 추가 키워드 해금
        if leveled and self.aff_manager:
            level_unlocks = AFFINITY_UNLOCK_KEYWORDS.get(self.npc_name, {}).get(lv_name, [])
            player_kws = getattr(self.player, "keywords", list(DEFAULT_KEYWORDS))
            for new_kw in level_unlocks:
                if new_kw not in player_kws:
                    player_kws.append(new_kw)
                    unlocked.append(new_kw)

        # PIL 이미지로 응답 생성
        buf = _render_keyword_response_image(
            self.npc_name, keyword, response_text,
            self.aff_manager, aff_gain, show_limit_warning,
            unlocked, leveled, lv_name,
        )
        file = discord.File(buf, filename="npc_response.png")

        # 새 키워드가 해금됐으면 버튼 재구성
        if unlocked or leveled:
            self._build_buttons()

        # 친밀도/키워드 변경 시 저장
        if aff_gain or unlocked or leveled:
            try:
                from save_manager import save_manager
                save_manager.save(self.player)
            except Exception as e:
                logger.error("대화 후 저장 실패 (npc=%s): %s", self.npc_name, e, exc_info=True)

        await interaction.response.edit_message(attachments=[file], embed=None, view=self)

    async def _job_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.npc_manager_ref:
            class _FakeCtx:
                def __init__(self, inter):
                    self.channel = inter.channel
                    self.send = inter.channel.send
                    self.author = inter.user
            fake_ctx = _FakeCtx(interaction)
            await self.npc_manager_ref.start_job_async(fake_ctx, self.npc_name)
        else:
            await interaction.followup.send(f"**{self.npc_name}** 알바를 시작합미댜!", ephemeral=False)

    async def _buy_callback(self, interaction: discord.Interaction):
        from shop import NPC_CATALOGS
        from shop_ui import BuyView
        from database import NPC_DATA
        catalog = NPC_CATALOGS.get(self.npc_name)
        if not catalog:
            await interaction.response.send_message("이 NPC는 상점이 없슴미댜.", ephemeral=True)
            return
        npc = NPC_DATA.get(self.npc_name, {})
        embed = discord.Embed(
            title=f"🛒 {npc.get('name', self.npc_name)} 상점",
            description=f"💰 소지금: **{self.player.gold:,}G**",
            color=0xFFD700,
        )
        lines = []
        for item_id, item in list(catalog.items())[:20]:
            from ui_theme import GRADE_ICON_PLAIN
            grade = item.get("grade", "Normal")
            icon = GRADE_ICON_PLAIN.get(grade, "⚬")
            name = item.get("name", item_id)
            price = item.get("price", 0)
            extra = f" (+{item.get('slots',0)}칸)" if item.get("type") == "bag" else ""
            lines.append(f"{icon} **{name}**{extra} — {price:,}G")
        embed.add_field(name="📦 판매 상품", value="\n".join(lines) if lines else "상품이 없슴미댜.", inline=False)
        embed.set_footer(text="아래 드롭다운에서 상품과 수량을 선택하세요.")

        from shop import ShopManager
        shop_mgr = ShopManager(self.player)
        view = BuyView(self.player, shop_mgr, self.npc_name, catalog)
        msg = await interaction.response.send_message(embed=embed, view=view)
        view._message = msg

    async def _train_callback(self, interaction: discord.Interaction):
        from training import TrainingSystem
        ts = TrainingSystem(self.player)
        view = _TrainingView(self.player, ts)
        menu_buf = view.render_menu()
        file = discord.File(menu_buf, filename="train_menu.png")
        await interaction.response.send_message(file=file, view=view)

    async def _learn_metallurgy_callback(self, interaction: discord.Interaction):
        """다몬에게 제련 스킬을 배운다."""
        if "metallurgy" in getattr(self.player, "skill_ranks", {}):
            await interaction.response.send_message("이미 제련 스킬을 보유하고 있슴미댜!", ephemeral=True)
            return
        self.player.skill_ranks["metallurgy"] = "연습"
        self.player.skill_exp["metallurgy"] = 0.0
        try:
            from save_manager import save_manager
            save_manager.save(self.player)
        except Exception as e:
            logger.error("제련 스킬 학습 후 저장 실패: %s", e, exc_info=True)
        # 버튼 재구성 (배우기 버튼 제거)
        self._build_buttons()
        dialogue_text = (
            "좋습니다. 제련의 기초를 알려드리죠. "
            "광석을 대장간 화로에 넣고, 적절한 온도에서 불순물을 걸러내는 겁니다. "
            "처음엔 슬래그가 많이 나오겠지만... 연습하면 나아질 거예요. "
            "/제련 명령어로 광석을 제련할 수 있습니다."
        )
        buf = get_renderer().render_npc_dialogue(
            npc_name="다몬",
            npc_role="대장장이",
            greeting=dialogue_text,
            affinity_pts=_get_affinity_points(self.aff_manager, "다몬"),
            affinity_level=_get_affinity_level_name(self.aff_manager, "다몬"),
            portrait_type="npc",
            portrait_id="다몬",
        )
        file = discord.File(buf, filename="npc_dialogue.png")
        await interaction.response.edit_message(attachments=[file], view=self)

    async def _music_callback(self, interaction: discord.Interaction):
        """연주 곡 선택 View를 전송."""
        from music import SONGS
        view = _MusicSelectView(self.player)
        buf = get_renderer().render_card(
            title="🎵 연주 — 곡 선택",
            rows=[
                {"label": s["name"], "value": f"음표 {s['length']}개 | +{s['reward_gold']}G | 기여도 +{s['reward_contrib']}"}
                for s in SONGS
            ],
            system_key="npc",
        )
        file = discord.File(buf, filename="music_select.png")
        await interaction.response.send_message(file=file, view=view)

    async def _inn_callback(self, interaction: discord.Interaction):
        p = self.player
        buf = get_renderer().render_card(
            title="🛏️ 여관 — 휴식",
            rows=[
                {"label": "현재 상태", "value": f"HP {p.hp}/{p.max_hp} | 기력 {p.energy}/{p.max_energy}"},
                {"label": "간이 휴식", "value": "50G → HP+30, 기력+30"},
                {"label": "숙박", "value": "150G → HP+80, 기력+80"},
                {"label": "특실", "value": "300G → HP·기력 완전 회복"},
            ],
            system_key="rest",
        )
        file = discord.File(buf, filename="inn.png")
        view = _InnRestView(self.player)
        await interaction.response.send_message(file=file, view=view)


class _TrainingView(View):
    """스탯 수련 UI View — NPC 대화 내 훈련소."""

    def __init__(self, player, training_system):
        super().__init__(timeout=120.0)
        self.player = player
        self.ts = training_system
        from training import STAT_TRAIN_CONFIG
        self._config = STAT_TRAIN_CONFIG
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        from training import STAT_TRAIN_CONFIG
        for stat_id, cfg in STAT_TRAIN_CONFIG.items():
            btn = Button(
                label=f"{cfg['icon']} {cfg['name']}",
                style=discord.ButtonStyle.success,
                custom_id=f"train_{stat_id}",
            )
            btn.callback = self._make_train_cb(stat_id)
            self.add_item(btn)
        close_btn = Button(label="닫기", style=discord.ButtonStyle.secondary, emoji="◀️")
        close_btn.callback = self._close_cb
        self.add_item(close_btn)

    def render_menu(self):
        rows = []
        for stat_id, cfg in self._config.items():
            cur = self.player.base_stats.get(stat_id, 0)
            from training import _train_cost, ENERGY_PER_POINT, MIN_ENERGY_COST
            cost = _train_cost(stat_id, cur)
            energy_cost = max(MIN_ENERGY_COST, ENERGY_PER_POINT * cur)
            rows.append({
                "label": f"{cfg['icon']} {cfg['name']} (현재 {cur})",
                "value": f"비용 {cost}G / 기력 {energy_cost} — {cfg['desc']}",
            })
        rows.append({"label": "소지금", "value": f"{self.player.gold:,}G | 기력 {self.player.energy}/{self.player.max_energy}"})
        return get_renderer().render_card(
            title="🏋️ 훈련소 — 수련",
            rows=rows,
            system_key="battle",
        )

    def _make_train_cb(self, stat_id: str):
        async def _cb(interaction: discord.Interaction):
            result_text = self.ts.train(stat_id)
            # 수련 성공 후 메뉴 갱신
            try:
                from save_manager import save_manager
                save_manager.save(self.player)
            except Exception as e:
                logger.error("수련 후 저장 실패: %s", e, exc_info=True)
            menu_buf = self.render_menu()
            file = discord.File(menu_buf, filename="train_menu.png")
            await interaction.response.edit_message(attachments=[file], view=self)
            # 결과 메시지를 followup으로 전송
            await interaction.followup.send(result_text)
        return _cb

    async def _close_cb(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


class _MusicSelectView(View):
    """연주 곡 선택 View."""
    def __init__(self, player):
        super().__init__(timeout=60.0)
        self.player = player
        from music import SONGS
        for song in SONGS:
            btn = Button(
                label=song["name"],
                style=discord.ButtonStyle.primary,
                custom_id=f"music_{song['id']}",
            )
            btn.callback = self._make_perform_cb(song)
            self.add_item(btn)

    def _make_perform_cb(self, song):
        async def _cb(interaction: discord.Interaction):
            import random
            from music import NOTES, MusicView
            energy_cost = 5
            if not self.player.consume_energy(energy_cost):
                await interaction.response.send_message(
                    f"```ansi\n  \u001b[0;31m✖ 기력이 부족함미댜! (필요: {energy_cost})\u001b[0m\n```",
                    ephemeral=True,
                )
                return
            target = [random.choice(NOTES) for _ in range(song["length"])]
            target_s = " ".join(target)
            embed = discord.Embed(
                title=f"🎵 {song['name']} — 연주 시작!",
                description=(
                    f"아래 음표를 **순서대로** 버튼으로 입력하셰요!\n\n"
                    f"🎶 목표: **{target_s}**\n\n"
                    f"⏱ 60초 안에 완성하셰요!"
                ),
                color=0x4488cc,
            )
            view = MusicView(target, song, self.player)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            msg = await interaction.followup.send(embed=embed, view=view)
            view._message = msg
        return _cb


INN_REST_CONFIG = {
    "basic":  {"label": "간이 휴식 (50G)", "gold": 50,  "energy": 30, "hp": 30},
    "full":   {"label": "숙박 (150G)",      "gold": 150, "energy": 80, "hp": 80},
    "deluxe": {"label": "특실 (300G)",      "gold": 300, "energy_full": True, "hp_full": True},
}


class _InnRestView(View):
    """여관 휴식 UI View."""

    def __init__(self, player):
        super().__init__(timeout=60.0)
        self.player = player
        for key, cfg in INN_REST_CONFIG.items():
            btn = Button(
                label=cfg["label"],
                style=discord.ButtonStyle.success,
                custom_id=f"inn_rest_{key}",
            )
            btn.callback = self._make_rest_cb(key, cfg)
            self.add_item(btn)

    def _make_rest_cb(self, key, cfg):
        async def _cb(interaction: discord.Interaction):
            p = self.player
            cost = cfg["gold"]
            if p.gold < cost:
                await interaction.response.send_message(
                    f"```ansi\n  \u001b[0;31m✖ 골드가 부족함미댜! (필요: {cost}G, 보유: {p.gold}G)\u001b[0m\n```",
                    ephemeral=True,
                )
                return
            p.gold -= cost
            if cfg.get("energy_full"):
                p.energy = p.max_energy
            else:
                p.energy = min(p.max_energy, p.energy + cfg.get("energy", 0))
            if cfg.get("hp_full"):
                p.hp = p.max_hp
            else:
                p.hp = min(p.max_hp, p.hp + cfg.get("hp", 0))
            try:
                from save_manager import save_manager
                save_manager.save(p)
            except Exception as e:
                logger.error("여관 휴식 후 저장 실패: %s", e, exc_info=True)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"```ansi\n  \u001b[0;32m✔ 휴식 완료!\u001b[0m\n"
                f"  \u001b[0;37mHP: {p.hp}/{p.max_hp}  기력: {p.energy}/{p.max_energy}\u001b[0m\n"
                f"  \u001b[0;31m-{cost}G\u001b[0m (현재: {p.gold:,}G)\n```"
            )
            self.stop()
        return _cb


class ConversationManager:
    """NPC 키워드 대화 관리 클래스"""

    def __init__(self, player, aff_manager=None, npc_manager_ref=None):
        self.player = player
        self.aff_manager = aff_manager
        self.npc_manager_ref = npc_manager_ref

    async def send_conversation(self, ctx, npc_name: str):
        """대화 명령어 실행 — BG3 스타일 PIL 이미지 + 버튼 전송"""
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(f"[{npc_name}]을(를) 찾을 수 없슴미댜.")
            return

        # deliver 타입 퀘스트: 목표 NPC 방문 시 자동 전달 처리
        try:
            import app_context
            deliver_msg = app_context.get_quest_manager().deliver_to_npc(npc_name)
            if deliver_msg:
                await ctx.send(deliver_msg)
        except Exception as e:
            logger.warning("퀘스트 배달 처리 실패 (npc=%s): %s", npc_name, e, exc_info=True)

        # 알바 배달형: 보류 중인 배달 작업 완료 처리
        try:
            _flags = getattr(self.player, "_flags", {})
            for key in [k for k in list(_flags.keys()) if k.startswith("pending_deliver:")]:
                job_info = _flags.get(key, {})
                if job_info.get("target_npc") != npc_name:
                    continue
                d_item = job_info.get("deliver_item", "")
                if not d_item or self.player.inventory.get(d_item, 0) < 1:
                    continue
                # 아이템 제거 — 실패 시 보상 지급 없이 오류 메시지만 전송
                if not self.player.remove_item(d_item, 1):
                    d_name_err = job_info.get("deliver_item_name", d_item)
                    await ctx.send(
                        f"⚠️ **{d_name_err}** 아이템 제거에 실패했슴미댜. 배달을 완료할 수 없어요."
                    )
                    continue
                gold = job_info.get("reward_gold", 0)
                exp  = job_info.get("reward_exp", 0.0)
                self.player.gold += gold
                self.player.exp = getattr(self.player, "exp", 0.0) + exp
                for sid, amt in job_info.get("reward_skill_exp", {}).items():
                    self.player.train_skill(sid, float(amt))
                r_item = job_info.get("reward_item")
                if r_item:
                    self.player.add_item(r_item, 1)
                del _flags[key]
                self.player._flags = _flags
                # 마을 기여도 추가
                try:
                    from village import village_manager
                    village_manager.add_contribution(5, "job")
                except Exception as _ve:
                    logger.warning("배달 완료 village contribution 실패: %s", _ve)
                src_npc = job_info.get("npc_name", "")
                job_nm  = job_info.get("job_name", "배달 알바")
                d_name  = job_info.get("deliver_item_name", d_item)
                # 결과 카드 전송 (실패 시 텍스트 폴백)
                card_sent = False
                try:
                    import fishing_card
                    buf = fishing_card.generate_job_card(
                        job_nm, "완료! [배달]", gold, f"EXP +{exp}"
                    )
                    file = discord.File(buf, filename="job_result.png")
                    embed = discord.Embed(
                        title=f"📦 {src_npc} 알바 [{job_nm}] 완료!",
                        description=f"**{npc_name}**에게 **{d_name}**을(를) 전달했슴미댜!",
                        color=0x4A7856,
                    )
                    embed.set_image(url="attachment://job_result.png")
                    await ctx.send(embed=embed, file=file)
                    card_sent = True
                except Exception as _ce:
                    logger.warning("배달 완료 카드 렌더링 실패 — 텍스트 폴백: %s", _ce)
                if not card_sent:
                    await ctx.send(
                        f"📦 **{src_npc} 알바 [{job_nm}]** 완료!\n"
                        f"**{npc_name}**에게 {d_name}을(를) 전달했슴미댜!\n"
                        f"+**{gold:,}G**  /  EXP +**{exp}**"
                    )
                try:
                    from save_manager import save_manager
                    save_manager.save(self.player)
                except Exception as e:
                    logger.error("배달 완료 후 저장 실패: %s", e, exc_info=True)
        except Exception as e:
            logger.error("배달 알바 자동 완료 처리 실패: %s", e, exc_info=True)

        # 일일 제한 확인 (차단 없음, 경고만)
        show_limit_warning = False
        if self.aff_manager and hasattr(self.aff_manager, "check_talk_limit"):
            allowed, _ = self.aff_manager.check_talk_limit(npc_name)
            if not allowed:
                show_limit_warning = True

        # BG3 대화 UI 이미지 (초상화 + 대사창)
        buf = _render_greeting_image(npc_name, self.aff_manager, show_limit_warning)
        file = discord.File(buf, filename="npc_dialogue.png")

        view = NPCConversationView(npc_name, self.player, self.aff_manager, self.npc_manager_ref)
        await ctx.send(file=file, view=view)
