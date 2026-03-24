# battle_view.py — discord.ui.View 기반 전투 UI
import discord
import random
import io

MAX_AUTO_LOG_LINES = 20  # Auto 전투 로그 최대 표시 줄 수


class BattleEventView(discord.ui.View):
    """전투 중 이벤트 발생 시 선택지를 버튼으로 제공"""

    def __init__(self, battle_engine, event: dict, ctx_or_interaction, callback):
        super().__init__(timeout=60)
        self.battle_engine = battle_engine
        self.event = event
        self.callback = callback
        self.ctx_or_interaction = ctx_or_interaction
        self.responded = False

        for i, choice in enumerate(event.get("choices", [])):
            btn = discord.ui.Button(
                label=choice["label"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"battle_event_{i}",
            )
            self._add_event_button(btn, i, event["choices"][i])

    def _add_event_button(self, btn, idx, choice):
        async def _cb(interaction: discord.Interaction):
            if self.responded:
                await interaction.response.defer()
                return
            self.responded = True
            self.stop()
            self.battle_engine._apply_event_effect(choice.get("effect", {}))
            await interaction.response.defer()
            await self.callback(choice.get("result_text", ""), idx)
        btn.callback = _cb
        self.add_item(btn)


class BattleView(discord.ui.View):
    """
    전투 UI 뷰.
    스킬 버튼, 응원 버튼, Auto 버튼, 도주 버튼 포함.
    """

    def __init__(self, battle_engine, ctx, on_battle_end=None):
        super().__init__(timeout=300)
        self.battle_engine = battle_engine
        self.ctx = ctx
        self.on_battle_end = on_battle_end  # 전투 종료 시 호출할 코루틴 (승리/패배 처리)
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        """보유 스킬에 따라 버튼을 동적으로 구성"""
        self.clear_items()
        player = self.battle_engine.player

        from skills_db import COMBAT_SKILLS, MAGIC_SKILLS

        # 스킬 버튼 추가
        skill_icons = {
            "smash": "⚔",
            "defense": "🛡",
            "counter": "🔄",
            "windmill": "🌀",
            "firebolt": "🔥",
            "icebolt": "❄",
            "lightning": "⚡",
            "healing": "💊",
        }
        for skill_id, rank in player.skill_ranks.items():
            if skill_id in COMBAT_SKILLS or skill_id in MAGIC_SKILLS:
                all_skills = {**COMBAT_SKILLS, **MAGIC_SKILLS}
                sk = all_skills.get(skill_id, {})
                icon = skill_icons.get(skill_id, "⚔")
                label = f"{icon} {sk.get('name', skill_id)}"

                btn = discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"battle_skill_{skill_id}",
                )
                self._bind_skill_button(btn, skill_id)
                self.add_item(btn)

        # 응원 버튼
        cheer_left = 3 - self.battle_engine.cheer_count
        cheer_btn = discord.ui.Button(
            label=f"📣 응원 ({cheer_left}/3)",
            style=discord.ButtonStyle.success,
            custom_id="battle_cheer",
            disabled=(cheer_left <= 0),
        )
        cheer_btn.callback = self._cheer_callback
        self.add_item(cheer_btn)

        # Auto 버튼
        auto_btn = discord.ui.Button(
            label="⚡ Auto",
            style=discord.ButtonStyle.secondary,
            custom_id="battle_auto",
        )
        auto_btn.callback = self._auto_callback
        self.add_item(auto_btn)

        # 도주 버튼
        flee_btn = discord.ui.Button(
            label="🏃 도주",
            style=discord.ButtonStyle.danger,
            custom_id="battle_flee",
        )
        flee_btn.callback = self._flee_callback
        self.add_item(flee_btn)

    def _bind_skill_button(self, btn, skill_id):
        async def _cb(interaction: discord.Interaction):
            if not self.battle_engine.in_battle:
                await interaction.response.send_message("현재 전투 중이 아님미댜!", ephemeral=True)
                return
            await interaction.response.defer()
            await self._process_and_respond(interaction, skill_id)
        btn.callback = _cb

    async def _process_and_respond(self, interaction: discord.Interaction, skill_id: str):
        """턴 처리 후 결과 전송"""
        engine = self.battle_engine

        # 이벤트 발생 여부 확인 (20% 확률)
        if random.random() < 0.20:
            from battle_event_data import BATTLE_EVENTS
            event = random.choice(BATTLE_EVENTS)
            event_msg = await interaction.followup.send(
                f"⚡ **[전투 이벤트!]** {event['desc']}",
                view=_make_event_view(engine, event, interaction, skill_id, self),
            )
            return  # 이벤트 뷰가 결과를 이어서 처리

        await self._do_turn(interaction, skill_id)

    async def _do_turn(self, interaction: discord.Interaction, skill_id: str):
        engine = self.battle_engine
        was_in_battle = engine.in_battle
        result = engine.process_turn(skill_id)

        await self._send_result(interaction, result, was_in_battle)

    async def _send_result(self, interaction: discord.Interaction, result, was_in_battle: bool):
        engine = self.battle_engine
        try:
            if engine.in_battle:
                # 전투 계속 — 새 BattleView 첨부
                self._rebuild_buttons()
                if isinstance(result, io.BytesIO):
                    result.seek(0)
                    await interaction.followup.send(
                        file=discord.File(fp=result, filename="battle.png"),
                        view=self,
                    )
                else:
                    await interaction.followup.send(str(result), view=self)
            else:
                # 전투 종료
                if isinstance(result, io.BytesIO):
                    result.seek(0)
                    await interaction.followup.send(
                        file=discord.File(fp=result, filename="battle_result.png"),
                    )
                else:
                    await interaction.followup.send(str(result))

                if self.on_battle_end and was_in_battle:
                    await self.on_battle_end(engine.player.hp > 0)
        except Exception as e:
            try:
                await interaction.followup.send(f"오류 발생: {e}", ephemeral=True)
            except Exception:
                pass

    async def _cheer_callback(self, interaction: discord.Interaction):
        if not self.battle_engine.in_battle:
            await interaction.response.send_message("현재 전투 중이 아님미댜!", ephemeral=True)
            return
        msg = self.battle_engine.use_cheer()
        await interaction.response.defer()
        self._rebuild_buttons()
        await interaction.followup.send(msg, view=self)

    async def _auto_callback(self, interaction: discord.Interaction):
        if not self.battle_engine.in_battle:
            await interaction.response.send_message("현재 전투 중이 아님미댜!", ephemeral=True)
            return
        await interaction.response.defer()
        log_lines, final_result = self.battle_engine.auto_battle()

        # 로그 출력
        if log_lines:
            log_text = "\n".join(log_lines[:MAX_AUTO_LOG_LINES])
            await interaction.followup.send(f"⚡ **Auto 전투 진행 중...**\n```\n{log_text}\n```")

        # 최종 결과
        if isinstance(final_result, io.BytesIO):
            final_result.seek(0)
            await interaction.followup.send(
                file=discord.File(fp=final_result, filename="battle_result.png"),
            )
        else:
            await interaction.followup.send(str(final_result))

        if self.on_battle_end and not self.battle_engine.in_battle:
            await self.on_battle_end(self.battle_engine.player.hp > 0)

    async def _flee_callback(self, interaction: discord.Interaction):
        if not self.battle_engine.in_battle:
            await interaction.response.send_message("현재 전투 중이 아님미댜!", ephemeral=True)
            return
        await interaction.response.defer()
        result = self.battle_engine.flee()
        if isinstance(result, io.BytesIO):
            result.seek(0)
            await interaction.followup.send(
                file=discord.File(fp=result, filename="flee.png"),
            )
        else:
            await interaction.followup.send(str(result))
        # 도주 성공 시 (전투 종료) 콜백 호출 → 저장 처리
        if not self.battle_engine.in_battle and self.on_battle_end:
            await self.on_battle_end(False)


def _make_event_view(engine, event, interaction, skill_id, battle_view):
    """이벤트 선택지 View 생성 (클로저 방식)"""

    class _EventView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.responded = False
            for i, choice in enumerate(event.get("choices", [])):
                btn = discord.ui.Button(
                    label=choice["label"],
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"event_choice_{i}",
                )
                self._bind(btn, choice)
                self.add_item(btn)

        def _bind(self_inner, btn, choice):
            async def _cb(inner_interaction: discord.Interaction):
                if self_inner.responded:
                    await inner_interaction.response.defer()
                    return
                self_inner.responded = True
                self_inner.stop()
                engine._apply_event_effect(choice.get("effect", {}))
                await inner_interaction.response.defer()
                await inner_interaction.followup.send(f"→ {choice.get('result_text', '')}")
                # 이벤트 처리 후 실제 턴 처리
                await battle_view._do_turn(interaction, skill_id)
            btn.callback = _cb

    return _EventView()
