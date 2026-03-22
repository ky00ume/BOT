# adventure.py — 텍스트 어드벤처형 탐험 엔진 + discord.ui.View
import random
import discord
import asyncio
from datetime import datetime


class AdventureEngine:
    """텍스트 어드벤처형 미니 탐험 엔진"""

    def __init__(self, player):
        self.player = player
        self.active_adventure = None  # 현재 진행 중인 시나리오
        self.current_step = 0
        self.adventure_count: dict = {}  # zone → 완료 횟수
        self.in_adventure = False
        self._pending_rewards: list = []  # 미지급 보상 목록

    # ─── 탐험 시작 ────────────────────────────────────────────────────────
    def start_adventure(self, zone_name: str) -> dict:
        """
        탐험 시작.
        Returns dict with keys: 'ok', 'error', 'scenario', 'step_data', 'npc', 'hidden'
        """
        from adventure_data import ADVENTURE_SCENARIOS, RANDOM_ADVENTURE_EVENTS, HIDDEN_TRIGGERS
        from adventure_npc_data import ADVENTURE_NPCS, NPC_ENCOUNTER_RATE

        # 에너지 소비
        energy_cost = 3
        if not self.player.consume_energy(energy_cost):
            return {"ok": False, "error": f"기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy})"}

        # 숨겨진 트리거 체크
        hidden = self._check_hidden_trigger(zone_name)
        if hidden:
            reward = hidden.get("event", {}).get("reward", {})
            self._apply_reward(reward)
            return {
                "ok": True,
                "hidden": hidden,
                "scenario": None,
                "step_data": None,
                "npc": None,
            }

        # NPC 인카운터 (25%)
        if random.random() < NPC_ENCOUNTER_RATE:
            npc = random.choice(ADVENTURE_NPCS)
            self.in_adventure = True
            self.active_adventure = {"type": "npc", "npc": npc, "zone": zone_name}
            return {
                "ok": True,
                "hidden": None,
                "scenario": None,
                "step_data": None,
                "npc": npc,
            }

        # 시나리오 선택
        scenarios = ADVENTURE_SCENARIOS.get(zone_name)
        if not scenarios:
            # 범용 랜덤 이벤트 사용
            event = random.choice(RANDOM_ADVENTURE_EVENTS)
            scenario = {
                "id": event["id"],
                "title": event.get("desc", "랜덤 이벤트"),
                "steps": [
                    {
                        "step": 0,
                        "desc": event["desc"],
                        "choices": event["choices"],
                        "end": True,
                    }
                ],
            }
        else:
            scenario = random.choice(scenarios)

        self.active_adventure = {"type": "scenario", "scenario": scenario, "zone": zone_name}
        self.current_step = 0
        self.in_adventure = True
        self._pending_rewards = []

        step_data = scenario["steps"][0]
        return {
            "ok": True,
            "hidden": None,
            "scenario": scenario,
            "step_data": step_data,
            "npc": None,
        }

    # ─── 선택지 처리 ──────────────────────────────────────────────────────
    def process_choice(self, choice_index: int) -> dict:
        """
        선택지 처리.
        Returns dict: 'ok', 'text', 'reward', 'battle', 'next_step_data', 'end', 'error'
        """
        if not self.in_adventure or not self.active_adventure:
            return {"ok": False, "error": "현재 탐험 중이 아님미댜!"}

        adv = self.active_adventure
        if adv["type"] != "scenario":
            return {"ok": False, "error": "시나리오 탐험이 아님미댜!"}

        scenario = adv["scenario"]
        step_idx = self._find_step_idx(scenario, self.current_step)
        if step_idx is None:
            self.in_adventure = False
            return {"ok": True, "end": True, "text": "탐험이 완료됐슴미댜!"}

        step = scenario["steps"][step_idx]
        choices = step.get("choices", [])

        if not choices or choice_index >= len(choices):
            return {"ok": False, "error": "올바른 선택지가 아님미댜!"}

        choice = choices[choice_index]
        result = self._resolve_choice(choice)

        # 다음 단계 결정
        next_step_num = result.get("next_step")
        is_end = result.get("end", step.get("end", False))

        if is_end or next_step_num is None:
            self.in_adventure = False
            self._apply_pending_rewards()
            self.adventure_count[adv["zone"]] = self.adventure_count.get(adv["zone"], 0) + 1
            return {
                "ok": True,
                "text": result.get("text", ""),
                "reward": result.get("reward"),
                "battle": result.get("battle", False),
                "end": True,
                "next_step_data": None,
            }

        # 다음 스텝으로
        self.current_step = next_step_num
        next_step_idx = self._find_step_idx(scenario, next_step_num)
        next_step_data = scenario["steps"][next_step_idx] if next_step_idx is not None else None

        if next_step_data is None or next_step_data.get("end"):
            self.in_adventure = False
            self._apply_pending_rewards()
            self.adventure_count[adv["zone"]] = self.adventure_count.get(adv["zone"], 0) + 1

        return {
            "ok": True,
            "text": result.get("text", ""),
            "reward": result.get("reward"),
            "battle": result.get("battle", False),
            "end": (next_step_data is None or next_step_data.get("end", False)),
            "damage": result.get("damage", 0),
            "energy_cost": result.get("energy_cost", 0),
            "next_step_data": next_step_data,
        }

    # ─── NPC 상호작용 처리 ────────────────────────────────────────────────
    def process_npc_interaction(self, action: str, **kwargs) -> dict:
        """NPC 상호작용 처리. action: 'accept'/'refuse'/'trade'/'fight' 등"""
        if not self.in_adventure or not self.active_adventure:
            return {"ok": False, "error": "현재 탐험 중이 아님미댜!"}

        adv = self.active_adventure
        npc = adv.get("npc")
        if not npc:
            return {"ok": False, "error": "NPC가 없슴미댜!"}

        interaction = npc.get("interaction", "")
        player = self.player
        result = {"ok": True, "text": "", "reward": None}

        if interaction == "trade" and action == "trade":
            item_id = kwargs.get("item_id")
            prices = npc.get("trade_prices", {})
            cost = prices.get(item_id, 0)
            if player.gold < cost:
                result["text"] = "골드가 부족함미댜!"
            else:
                player.gold -= cost
                if player.add_item(item_id):
                    from items import ALL_ITEMS
                    iname = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                    result["text"] = f"{iname}을(를) {cost}G에 구매했슴미댜!"
                else:
                    player.gold += cost
                    result["text"] = "인벤토리 공간이 부족함미댜!"

        elif interaction == "help" and action == "accept":
            cost_info = npc.get("help_cost", {})
            item_req  = cost_info.get("item")
            cnt_req   = cost_info.get("count", 1)
            if item_req and not player.remove_item(item_req, cnt_req):
                result["text"] = f"필요한 아이템이 없슴미댜! ({item_req} x{cnt_req})"
            else:
                reward = npc.get("help_reward", {})
                self._apply_reward(reward)
                result["text"] = f"\"{npc['name']}\"을(를) 도와줬슴미댜!"
                result["reward"] = reward

        elif interaction == "help" and action == "refuse":
            result["text"] = npc.get("refuse_text", "\"알겠어...\"")

        elif interaction == "gamble" and action == "accept":
            cost = npc.get("gamble_cost", 30)
            if player.gold < cost:
                result["text"] = "골드가 부족함미댜!"
            else:
                player.gold -= cost
                win_chance = npc.get("gamble_win_chance", 0.5)
                if random.random() < win_chance:
                    reward = npc.get("gamble_win_reward", {"gold": 100})
                    self._apply_reward(reward)
                    result["text"] = f"🎉 당첨! {reward.get('gold', 0)}G를 획득했슴미댜!"
                    result["reward"] = reward
                else:
                    result["text"] = npc.get("gamble_lose_text", "안타깝게도 졌슴미댜...")

        elif interaction == "repair" and action == "accept":
            cost = npc.get("repair_cost", 25)
            if player.gold < cost:
                result["text"] = "골드가 부족함미댜!"
            else:
                player.gold -= cost
                eff = npc.get("repair_effect", {})
                result["text"] = f"장비를 수리했슴미댜! (ATK+{eff.get('atk_buff',0)}, DEF+{eff.get('def_buff',0)})"
                result["temp_buff"] = eff

        elif interaction == "bless" and action == "accept":
            eff = npc.get("bless_effect", {})
            hp_gain = int(player.max_hp * eff.get("heal_hp_percent", 0))
            mp_gain = int(player.max_mp * eff.get("heal_mp_percent", 0))
            player.hp = min(player.max_hp, player.hp + hp_gain)
            player.mp = min(player.max_mp, player.mp + mp_gain)
            result["text"] = f"바하무트의 축복을 받았슴미댜! HP+{hp_gain}, MP+{mp_gain}"

        elif interaction == "random_item" and action == "accept":
            possible = npc.get("possible_items", [])
            if possible:
                item_id = random.choice(possible)
                if player.add_item(item_id):
                    from items import ALL_ITEMS
                    iname = ALL_ITEMS.get(item_id, {}).get("name", item_id)
                    result["text"] = f"{npc['name']}에게서 {iname}을(를) 받았슴미댜!"
                    result["reward"] = {"item": item_id}
                else:
                    result["text"] = "인벤토리 공간이 부족해서 받을 수 없슴미댜!"

        elif interaction == "share_food" and action == "accept":
            eff = npc.get("share_effect", {})
            hp_gain = eff.get("heal_hp", 0)
            en_gain = eff.get("heal_en", 0)
            player.hp = min(player.max_hp, player.hp + hp_gain)
            player.energy = min(player.max_energy, player.energy + en_gain)
            result["text"] = f"{npc['name']}와 음식을 나눠먹었슴미댜! HP+{hp_gain}, EN+{en_gain}"

        elif interaction == "info":
            result["text"] = npc.get("info_text", "")
            reward = npc.get("info_reward", {})
            if reward:
                self._apply_reward(reward)
                result["reward"] = reward

        elif interaction == "fight_or_flee" and action == "fight":
            result["text"] = f"{npc['name']}와 전투가 시작됐슴미댜!"
            result["battle_monster"] = npc.get("fight_monster")

        elif action == "refuse" or action == "ignore":
            result["text"] = "상대를 무시하고 지나쳤슴미댜."

        self.in_adventure = False
        self.adventure_count[adv.get("zone", "")] = self.adventure_count.get(adv.get("zone", ""), 0) + 1
        return result

    # ─── 탐험 후 랜덤 이벤트 ──────────────────────────────────────────────
    def post_adventure_event(self, zone_name: str = "") -> dict | None:
        """탐험 종료 후 10% 확률로 외부 자극 이벤트"""
        if random.random() > 0.10:
            return None

        from adventure_npc_data import ADVENTURE_NPCS
        events = [
            {"type": "npc_visit",  "text": "누군가 찾아왔다!", "npc": random.choice(ADVENTURE_NPCS)},
            {"type": "gift",       "text": "선물이 도착했슴미댜!", "reward": {"gold": random.randint(20, 60)}},
            {"type": "lost_item",  "text": "탐험 중 흘린 아이템을 누군가 돌려줬슴미댜!", "reward": {"gold": 10}},
        ]
        return random.choice(events)

    # ─── 능력치 체크 ──────────────────────────────────────────────────────
    def check_stat(self, stat: str, difficulty: int) -> bool:
        """
        D&D 5e 스타일 능력치 체크.
        stat: base_stats 키 (str/int/dex/will/luck, 기본값 10)
        difficulty: 목표 수치 (예: 10=쉬움, 12=보통, 14=어려움)
        판정: stat_val + 1d20 >= difficulty 이면 성공
        """
        stat_val = self.player.base_stats.get(stat, 10)
        roll = random.randint(1, 20)
        return (stat_val + roll) >= difficulty

    # ─── 내부 헬퍼 ────────────────────────────────────────────────────────
    def _find_step_idx(self, scenario: dict, step_num: int):
        """시나리오에서 step 번호에 해당하는 인덱스 반환"""
        for i, s in enumerate(scenario.get("steps", [])):
            if s.get("step") == step_num:
                return i
        return None

    def _resolve_choice(self, choice: dict) -> dict:
        """선택지를 해석하여 결과 반환"""
        result = {}

        # 아이템 비용 체크
        if "item_cost" in choice:
            cost = choice["item_cost"]
            if not self.player.remove_item(cost["item"], cost.get("count", 1)):
                return {"text": f"필요한 아이템이 없슴미댜! ({cost['item']})", "end": True}

        # 자동 결과
        if choice.get("auto"):
            r = choice.get("result", {})
            return self._build_result(r)

        # 능력치 체크
        if "stat_check" in choice:
            sc = choice["stat_check"]
            success = self.check_stat(sc["stat"], sc["difficulty"])
            branch = choice.get("success" if success else "fail", {})
            res = self._build_result(branch)
            if not success and "damage" in branch:
                self.player.hp = max(0, self.player.hp - branch["damage"])
                res["damage"] = branch["damage"]
            return res

        # 기본 result
        if "result" in choice:
            return self._build_result(choice["result"])

        return {"text": "아무 일도 없었다.", "end": True}

    def _build_result(self, r: dict) -> dict:
        """결과 딕셔너리 정규화"""
        result = {
            "text":      r.get("text", ""),
            "next_step": r.get("next_step"),
            "end":       r.get("end", False),
            "battle":    r.get("battle", False),
            "reward":    r.get("reward"),
            "damage":    r.get("damage", 0),
            "energy_cost": r.get("energy_cost", 0),
        }
        if result["reward"]:
            self._pending_rewards.append(result["reward"])
        if result.get("damage", 0) > 0:
            self.player.hp = max(0, self.player.hp - result["damage"])
        if result.get("energy_cost", 0) > 0:
            self.player.consume_energy(result["energy_cost"])
        return result

    def _apply_reward(self, reward: dict):
        if not reward:
            return
        player = self.player
        if "gold" in reward:
            player.gold += reward["gold"]
        if "exp" in reward:
            player.exp = getattr(player, "exp", 0.0) + reward["exp"]
        if "item" in reward:
            player.add_item(reward["item"])
        if "hp" in reward:
            player.hp = min(player.max_hp, player.hp + reward["hp"])
        if "mp" in reward:
            player.mp = min(player.max_mp, player.mp + reward["mp"])
        if "energy" in reward:
            player.energy = min(player.max_energy, player.energy + reward["energy"])

    def _apply_pending_rewards(self):
        for reward in self._pending_rewards:
            self._apply_reward(reward)
        self._pending_rewards = []

    def _check_hidden_trigger(self, zone_name: str) -> dict | None:
        """숨겨진 트리거 조건 체크. hour_range는 UTC 기준."""
        from adventure_data import HIDDEN_TRIGGERS
        now_hour = datetime.utcnow().hour  # UTC 기준 시간
        player_level = self.player.level
        adv_count = self.adventure_count.get(zone_name, 0)

        for trigger in HIDDEN_TRIGGERS:
            conds = trigger.get("conditions", {})
            if conds.get("zone") != zone_name:
                continue
            if "hour_range" in conds:
                h_min, h_max = conds["hour_range"]
                if not (h_min <= now_hour < h_max):
                    continue
            if "min_level" in conds and player_level < conds["min_level"]:
                continue
            if "min_adventures" in conds and adv_count < conds["min_adventures"]:
                continue
            return trigger

        return None


# ─── discord.ui.View ────────────────────────────────────────────────────
class AdventureView(discord.ui.View):
    """탐험 단계별 선택지를 버튼으로 제시하는 View"""

    def __init__(self, adventure_engine: AdventureEngine, step_data: dict,
                 scenario_title: str = "", on_end=None, zone_name: str = ""):
        super().__init__(timeout=120)
        self.adventure_engine = adventure_engine
        self.step_data = step_data
        self.scenario_title = scenario_title
        self.on_end = on_end  # 탐험 완료 시 호출 코루틴(result_dict)
        self.zone_name = zone_name
        self.responded = False
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        choices = self.step_data.get("choices", [])
        for i, choice in enumerate(choices):
            label = choice.get("label", f"선택 {i+1}")
            btn = discord.ui.Button(
                label=label[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"adv_choice_{i}",
            )
            self._bind_choice(btn, i)
            self.add_item(btn)

    def _bind_choice(self, btn, idx):
        async def _cb(interaction: discord.Interaction):
            if self.responded:
                await interaction.response.defer()
                return
            self.responded = True
            self.stop()
            await interaction.response.defer()
            await self._handle_choice(interaction, idx)
        btn.callback = _cb

    async def _handle_choice(self, interaction: discord.Interaction, idx: int):
        engine = self.adventure_engine
        result = engine.process_choice(idx)

        text_parts = []
        if result.get("text"):
            text_parts.append(result["text"])
        if result.get("damage", 0) > 0:
            text_parts.append(f"💔 {result['damage']} 피해를 입었슴미댜!")
        if result.get("reward"):
            reward = result["reward"]
            rparts = []
            if reward.get("gold"):
                rparts.append(f"+{reward['gold']}G")
            if reward.get("exp"):
                rparts.append(f"+{reward['exp']} EXP")
            if reward.get("item"):
                from items import ALL_ITEMS
                iname = ALL_ITEMS.get(reward["item"], {}).get("name", reward["item"])
                rparts.append(f"{iname} 획득")
            if rparts:
                text_parts.append("🎁 " + ", ".join(rparts))

        msg = "\n".join(text_parts) if text_parts else "..."

        if result.get("end") or not result.get("next_step_data"):
            # 탐험 종료
            await interaction.followup.send(
                f"**[{self.scenario_title}]** 탐험 완료!\n{msg}"
            )
            if self.on_end:
                await self.on_end(result)
        elif result.get("battle"):
            await interaction.followup.send(
                f"**[{self.scenario_title}]** {msg}\n⚔ 전투가 시작됩니다!"
            )
            if self.on_end:
                await self.on_end({**result, "battle": True})
        else:
            # 다음 단계
            next_step = result["next_step_data"]
            new_view = AdventureView(
                adventure_engine=engine,
                step_data=next_step,
                scenario_title=self.scenario_title,
                on_end=self.on_end,
                zone_name=self.zone_name,
            )
            await interaction.followup.send(
                f"**[{self.scenario_title}]**\n{msg}\n\n📜 {next_step['desc']}",
                view=new_view,
            )


class NPCInteractionView(discord.ui.View):
    """탐험 중 NPC 상호작용 View"""

    def __init__(self, adventure_engine: AdventureEngine, npc: dict,
                 on_end=None):
        super().__init__(timeout=120)
        self.adventure_engine = adventure_engine
        self.npc = npc
        self.on_end = on_end
        self.responded = False
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        interaction_type = self.npc.get("interaction", "")

        button_configs = {
            "trade":        [("🛒 거래하기", "trade_open", discord.ButtonStyle.primary),
                             ("👋 거절하기", "refuse", discord.ButtonStyle.secondary)],
            "help":         [("✅ 도와준다", "accept", discord.ButtonStyle.success),
                             ("❌ 거절한다", "refuse", discord.ButtonStyle.secondary)],
            "gamble":       [("🎲 내기한다", "accept", discord.ButtonStyle.primary),
                             ("👋 거절한다", "refuse", discord.ButtonStyle.secondary)],
            "repair":       [("🔧 수리 맡긴다", "accept", discord.ButtonStyle.primary),
                             ("👋 거절한다", "refuse", discord.ButtonStyle.secondary)],
            "bless":        [("🙏 축복을 받는다", "accept", discord.ButtonStyle.success),
                             ("👋 지나친다", "refuse", discord.ButtonStyle.secondary)],
            "random_item":  [("🎁 받아든다", "accept", discord.ButtonStyle.success),
                             ("👋 거절한다", "refuse", discord.ButtonStyle.secondary)],
            "share_food":   [("🍖 함께 먹는다", "accept", discord.ButtonStyle.success),
                             ("👋 거절한다", "refuse", discord.ButtonStyle.secondary)],
            "info":         [("👂 이야기를 듣는다", "accept", discord.ButtonStyle.primary),
                             ("👋 무시한다", "ignore", discord.ButtonStyle.secondary)],
            "fight_or_flee":[("⚔ 싸운다", "fight", discord.ButtonStyle.danger),
                             ("🏃 도망친다", "refuse", discord.ButtonStyle.secondary)],
        }

        for label, action, style in button_configs.get(interaction_type, [("👋 지나친다", "ignore", discord.ButtonStyle.secondary)]):
            btn = discord.ui.Button(label=label, style=style, custom_id=f"npc_{action}")
            self._bind(btn, action)
            self.add_item(btn)

    def _bind(self, btn, action):
        async def _cb(interaction: discord.Interaction):
            if self.responded:
                await interaction.response.defer()
                return
            self.responded = True
            self.stop()
            await interaction.response.defer()
            result = self.adventure_engine.process_npc_interaction(action)
            await interaction.followup.send(result.get("text", "..."))
            if self.on_end:
                await self.on_end(result)
        btn.callback = _cb
