"""care.py — 돌봄 시스템 (쓰담쓰담 / 간식주기 / 놀아주기)"""
import random
import time

from costume_data import SNACK_ITEMS, COSTUME_ITEMS, SNACK_RECIPES, COSTUME_RECIPES


def _care_state(player) -> dict:
    if not hasattr(player, "_flags") or player._flags is None:
        player._flags = {}
    state = player._flags.setdefault("pet_care", {})
    state.setdefault("hunger", 35)       # 0=배부름, 100=매우 배고픔
    state.setdefault("cleanliness", 70)  # 0=매우 더러움, 100=깨끗함
    state.setdefault("boredom", 30)      # 0=만족, 100=매우 심심함
    state.setdefault("comfort", 50)      # 0=불안, 100=안정/친숙
    state.setdefault("wash_count", 0)
    state.setdefault("rest_count", 0)
    state.setdefault("rest_started_at", 0.0)
    state.setdefault("rest_until", 0.0)
    state.setdefault("last_rest_summary", "")
    return state


def get_care_state(player) -> dict:
    return dict(_care_state(player))


class CareManager:
    """하이네스 돌봄 시스템 매니저."""

    PET_COOLDOWN  = 30 * 60   # 쓰다듬기 보상 쿨타임 30분 (세션 안 연속 접촉은 허용)
    PLAY_COOLDOWN = 60 * 60   # 새 놀이 세션 쿨타임 1시간
    WASH_COOLDOWN = 60 * 60   # 목욕 1시간
    REST_DURATION = 20 * 60   # 실제 휴식 20분

    # ── 쓰담쓰담 ──────────────────────────────────────────────────────────
    def pet(self, player) -> dict:
        """쓰담쓰담: condition +5~10, stability +3~5. 쿨타임 30분."""
        now = time.time()
        last = player._flags.get("last_pet_time", 0)
        remaining = int(self.PET_COOLDOWN - (now - last))

        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            return {
                "success":  False,
                "cooldown": True,
                "message":  f"아직 쓰담쓰담 쿨타임임미댜... ({mins}분 {secs}초 남음)",
            }

        gain_condition = random.randint(5, 10)
        gain_stability = random.randint(3, 5)
        player.condition = min(100, player.condition + gain_condition)
        player.stability = min(100, player.stability + gain_stability)
        state = _care_state(player)
        state["comfort"] = min(100, state["comfort"] + random.randint(5, 9))
        player._flags["last_pet_time"] = now

        lines = [
            "기분이 좋아졌슴미댜! 🐾",
            "따뜻하고 좋슴미댜~ 🐾",
            "쓰담쓰담 좋아하슴미댜! ✨",
            "기분이 업됐슴미댜! 🎶",
        ]
        return {
            "success":         True,
            "message":         random.choice(lines),
            "condition_gain":  gain_condition,
            "stability_gain":  gain_stability,
        }

    # ── 간식주기 ──────────────────────────────────────────────────────────
    def feed_snack(self, player, snack_id: str) -> dict:
        """간식주기: 인벤에서 간식 소모 → effect 적용."""
        from items import ALL_ITEMS

        # 하이네스 방 인벤토리에서 확인
        h_inv = player.get_hyness_inventory()
        if h_inv.get(snack_id, 0) <= 0:
            item = ALL_ITEMS.get(snack_id) or SNACK_ITEMS.get(snack_id, {})
            return {
                "success": False,
                "message": f"[{item.get('name', snack_id)}]이(가) 없슴미댜.",
            }

        item = ALL_ITEMS.get(snack_id) or SNACK_ITEMS.get(snack_id, {})
        if not item or item.get("type") != "snack":
            return {"success": False, "message": "간식이 아닌 아이템임미댜."}

        effect = item.get("effect", {})
        player.remove_hyness_item(snack_id)
        state = _care_state(player)
        hunger_drop = max(12, abs(int(effect.get("condition", 0))) + 10)
        state["hunger"] = max(0, state["hunger"] - hunger_drop)

        changes = {"hunger": -hunger_drop}
        if "condition" in effect:
            delta = effect["condition"]
            player.condition = max(0, min(100, player.condition + delta))
            changes["condition"] = delta
        if "stability" in effect:
            delta = effect["stability"]
            player.stability = max(0, min(100, player.stability + delta))
            changes["stability"] = delta
        if "fatigue" in effect:
            delta = effect["fatigue"]
            player.fatigue = max(0, min(100, player.fatigue + delta))
            changes["fatigue"] = delta

        lines = [
            f"[{item.get('name', snack_id)}] 냠냠~ 맛있슴미댜! 🍴",
            f"[{item.get('name', snack_id)}] 주셔서 감사슴미댜! 😊",
            f"[{item.get('name', snack_id)}] 맛있는 간식임미댜! ✨",
        ]
        return {
            "success": True,
            "message": random.choice(lines),
            "changes": changes,
            "item_name": item.get("name", snack_id),
        }

    # ── 놀아주기 ──────────────────────────────────────────────────────────
    def play_result(self, player, choice: str, *, continue_session: bool = False) -> dict:
        """놀아주기 결과 처리. 같은 놀이 세션의 재경기는 쿨타임을 무시한다."""
        now = time.time()
        last = player._flags.get("last_play_time", 0)
        remaining = int(self.PLAY_COOLDOWN - (now - last))

        if remaining > 0 and not continue_session:
            mins = remaining // 60
            secs = remaining % 60
            return {
                "success":  False,
                "cooldown": True,
                "message":  f"아직 놀아주기 쿨타임임미댜... ({mins}분 {secs}초 남음)",
            }

        options = ["rock", "scissors", "paper"]
        bot_choice = random.choice(options)
        state = _care_state(player)
        state["boredom"] = max(0, state["boredom"] - random.randint(18, 28))

        # 승패 판정
        win_map = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        if choice == bot_choice:
            result = "draw"
        elif win_map[choice] == bot_choice:
            result = "win"
        else:
            result = "lose"

        EMOJI = {"rock": "✊", "scissors": "✌️", "paper": "✋"}
        bot_emoji   = EMOJI[bot_choice]
        player_emoji = EMOJI[choice]

        if result == "win":
            gain_stability = random.randint(10, 15)
            gain_fatigue   = random.randint(3, 6)
            player.stability = min(100, player.stability + gain_stability)
            player.fatigue   = min(100, player.fatigue   + gain_fatigue)
            player._flags["last_play_time"] = now
            messages = [
                "이겼슴미댜! 신나슴미댜! 🎉",
                "야호~ 제가 이겼슴미댜! 🎊",
            ]
            return {
                "success":        True,
                "result":         result,
                "player_choice":  player_emoji,
                "bot_choice":     bot_emoji,
                "message":        random.choice(messages),
                "stability_gain": gain_stability,
                "fatigue_gain":   gain_fatigue,
            }
        elif result == "draw":
            gain_stability = random.randint(5, 8)
            gain_fatigue   = random.randint(2, 4)
            player.stability = min(100, player.stability + gain_stability)
            player.fatigue   = min(100, player.fatigue   + gain_fatigue)
            player._flags["last_play_time"] = now
            messages = [
                "비겼슴미댜~ 다시 해요! 😄",
                "무승부임미댜! 재미있슴미댜! 😊",
            ]
            return {
                "success":        True,
                "result":         result,
                "player_choice":  player_emoji,
                "bot_choice":     bot_emoji,
                "message":        random.choice(messages),
                "stability_gain": gain_stability,
                "fatigue_gain":   gain_fatigue,
            }
        else:  # lose
            gain_fatigue = random.randint(5, 8)
            player.fatigue = min(100, player.fatigue + gain_fatigue)
            player._flags["last_play_time"] = now
            messages = [
                "졌슴미댜... 다음엔 이길 거임미댜! 😤",
                "으... 졌슴미댜. 다시 도전임미댜! 💪",
            ]
            return {
                "success":      True,
                "result":       result,
                "player_choice": player_emoji,
                "bot_choice":   bot_emoji,
                "message":      random.choice(messages),
                "fatigue_gain": gain_fatigue,
            }

    # ── 씻기기 ───────────────────────────────────────────────────────────
    def get_wash_cooldown_remaining(self, player) -> int:
        last = getattr(player, "_flags", {}).get("last_wash_time", 0)
        return max(0, int(self.WASH_COOLDOWN - (time.time() - last)))

    def wash(self, player) -> dict:
        remaining = self.get_wash_cooldown_remaining(player)
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            return {
                "success": False,
                "cooldown": True,
                "remaining": remaining,
                "message": f"아직 털과 다리 사이에 목욕 뒤 물기가 남아 있슴미댜. ({mins}분 {secs}초 남음)",
            }
        state = _care_state(player)
        before = state["cleanliness"]
        state["cleanliness"] = min(100, before + random.randint(35, 55))
        state["wash_count"] += 1
        player.condition = min(100, player.condition + random.randint(1, 3))
        player._flags["last_wash_time"] = time.time()
        lines = [
            "욕조에 넣자 여덟 다리가 욕조 가장자리를 붙잡았슴미댜. 그래도 복부부터 북북박박 씻겼더니 결국 체념한 얼굴이 됐슴미댜. 🛁",
            "거품을 잔뜩 내서 다리 사이까지 북북 씻겼슴미댜. 츄라이더가 죽을상으로 쳐다보지만 아주 깨끗해졌슴미댜. 🫧",
            "욕조 밖으로 빠져나가려는 다리를 하나씩 다시 넣어 가며 북북박박 씻겼슴미댜. 🕷️🛁",
        ]
        if state["wash_count"] >= 3:
            lines.append("욕조를 보자 도망칠지 잠깐 고민하더니 먼저 앞다리 두 개를 걸쳤슴미댜. 어차피 잡힐 걸 아는 눈치임미댜. 🕷️🫧")
        return {"success": True, "message": random.choice(lines), "cleanliness_gain": state["cleanliness"] - before}

    # ── 쉬게 하기 ─────────────────────────────────────────────────────────
    def get_rest_status(self, player) -> dict:
        state = _care_state(player)
        now = time.time()
        until = float(state.get("rest_until", 0) or 0)
        if until <= 0:
            return {"active": False, "remaining": 0, "progress": 0.0}
        started = float(state.get("rest_started_at", until - self.REST_DURATION) or (until - self.REST_DURATION))
        if now >= until:
            return {"active": True, "remaining": 0, "progress": 1.0, "completed": True, "started": started, "until": until}
        progress = max(0.0, min(1.0, (now - started) / max(1, until - started)))
        return {"active": True, "remaining": int(until - now), "progress": progress, "completed": False, "started": started, "until": until}

    def start_rest(self, player) -> dict:
        status = self.get_rest_status(player)
        if status.get("active") and not status.get("completed"):
            return {"success": False, "already_resting": True, **status}
        if status.get("completed"):
            self.finish_rest(player)
        state = _care_state(player)
        now = time.time()
        state["rest_started_at"] = now
        state["rest_until"] = now + self.REST_DURATION
        state["rest_count"] += 1
        state["last_rest_summary"] = ""
        return {
            "success": True,
            "remaining": self.REST_DURATION,
            "message": "책장 뒤 담요와 실 사이에 몸을 접었슴미댜. 앞다리부터 하나씩 힘이 풀리더니 곧 눈을 감았슴미댜. 🕷️💤",
        }

    def finish_rest(self, player, *, wake_early: bool = False) -> dict:
        state = _care_state(player)
        status = self.get_rest_status(player)
        if not status.get("active"):
            return {"success": False, "message": "지금은 쉬고 있지 않슴미댜."}
        fraction = status.get("progress", 0.0)
        if status.get("completed"):
            fraction = 1.0
        fatigue_recovery = max(1, round(22 * fraction))
        energy_recovery = max(1, round(15 * fraction))
        before = player.fatigue
        player.fatigue = max(0, player.fatigue - fatigue_recovery)
        player.restore_energy(energy_recovery)
        state["comfort"] = min(100, state["comfort"] + max(1, round(5 * fraction)))
        state["rest_started_at"] = 0.0
        state["rest_until"] = 0.0
        actual = before - player.fatigue
        if wake_early and fraction < 1.0:
            msg = "조심히 깨우자 츄라이더가 눈을 가늘게 뜨고 앞다리를 다시 펼쳤슴미댜. 조금은 쉬었지만 아직 잠기운이 남아 있슴미댜."
        else:
            msg = "푹 쉬고 난 츄라이더가 몸을 길게 펴며 여덟 다리를 하나씩 바닥에 디뎠슴미댜."
        state["last_rest_summary"] = msg
        return {"success": True, "message": msg, "fatigue_recovery": actual, "energy_recovery": energy_recovery, "fraction": fraction}

    def finish_rest_if_ready(self, player) -> dict | None:
        status = self.get_rest_status(player)
        if status.get("completed"):
            return self.finish_rest(player)
        return None

    def rest(self, player) -> dict:
        """Backward-compatible alias: rest now starts a timed rest session."""
        return self.start_rest(player)

    # ── 간식 제작 ─────────────────────────────────────────────────────────
    def craft_snack(self, player, snack_id: str) -> dict:
        """간식 제작: 재료 소모 → 간식 아이템 획득."""
        recipe = SNACK_RECIPES.get(snack_id)
        if not recipe:
            return {"success": False, "message": "제작 레시피가 없슴미댜."}

        snack_item = SNACK_ITEMS.get(snack_id, {})
        snack_name = snack_item.get("name", snack_id)

        # 재료 확인 (하이네스 방 인벤토리에서)
        h_inv = player.get_hyness_inventory()
        missing = []
        for mat_id, need in recipe["materials"].items():
            have = h_inv.get(mat_id, 0)
            if have < need:
                from items import ALL_ITEMS
                mat = ALL_ITEMS.get(mat_id, {})
                missing.append(f"{mat.get('name', mat_id)} x{need} (보유: {have})")

        if missing:
            return {
                "success": False,
                "message": "재료가 부족슴미댜!\n" + "\n".join(f"  ✗ {m}" for m in missing),
            }

        # 재료 소모 (하이네스 방 인벤토리에서)
        for mat_id, need in recipe["materials"].items():
            player.remove_hyness_item(mat_id, need)

        # 결과물 지급 (하이네스 방 인벤토리로)
        count = recipe.get("result_count", 1)
        player.add_hyness_item(snack_id, count)

        return {
            "success": True,
            "message": f"[{snack_name}] x{count} 제작 완료임미댜! 🍴",
            "item_id": snack_id,
            "count":   count,
        }

    # ── 의장 제작 ─────────────────────────────────────────────────────────
    def craft_costume(self, player, costume_id: str) -> dict:
        """의장 제작: 재료 소모 → 의장 아이템 획득."""
        recipe = COSTUME_RECIPES.get(costume_id)
        if not recipe:
            return {"success": False, "message": "제작 레시피가 없슴미댜."}

        costume_item = COSTUME_ITEMS.get(costume_id, {})
        costume_name = costume_item.get("name", costume_id)

        # 재료 확인 (하이네스 방 인벤토리에서)
        h_inv = player.get_hyness_inventory()
        missing = []
        for mat_id, need in recipe["materials"].items():
            have = h_inv.get(mat_id, 0)
            if have < need:
                from items import ALL_ITEMS
                mat = ALL_ITEMS.get(mat_id, {})
                missing.append(f"{mat.get('name', mat_id)} x{need} (보유: {have})")

        if missing:
            return {
                "success": False,
                "message": "재료가 부족슴미댜!\n" + "\n".join(f"  ✗ {m}" for m in missing),
            }

        # 재료 소모 (하이네스 방 인벤토리에서)
        for mat_id, need in recipe["materials"].items():
            player.remove_hyness_item(mat_id, need)

        # 결과물 지급 (하이네스 방 인벤토리로)
        count = recipe.get("result_count", 1)
        player.add_hyness_item(costume_id, count)

        return {
            "success": True,
            "message": f"[{costume_name}] 제작 완료임미댜! ✂️",
            "item_id": costume_id,
            "count":   count,
        }

    # ── 쿨타임 확인 헬퍼 ──────────────────────────────────────────────────
    def get_pet_cooldown_remaining(self, player) -> int:
        """쓰담쓰담 쿨타임 남은 초. 0이면 사용 가능."""
        now = time.time()
        last = player._flags.get("last_pet_time", 0)
        return max(0, int(self.PET_COOLDOWN - (now - last)))

    def get_play_cooldown_remaining(self, player) -> int:
        """놀아주기 쿨타임 남은 초. 0이면 사용 가능."""
        now = time.time()
        last = player._flags.get("last_play_time", 0)
        return max(0, int(self.PLAY_COOLDOWN - (now - last)))
