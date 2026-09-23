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
    state.setdefault("last_update", time.time())
    state.setdefault("traces", [])
    return state


def update_care_over_time(player, *, now: float | None = None) -> dict:
    """Apply lazy real-time needs decay. No background task is required."""
    state = _care_state(player)
    current = time.time() if now is None else float(now)
    last = float(state.get("last_update", current) or current)
    elapsed = max(0.0, min(current - last, 72 * 3600))
    if elapsed < 60:
        return state
    hours = elapsed / 3600.0
    # Slow enough to be forgiving: hunger is the main clock, grime is activity-led.
    state["hunger"] = min(100, state["hunger"] + 7.0 * hours)
    state["boredom"] = min(100, state["boredom"] + 4.0 * hours)
    state["cleanliness"] = max(0, state["cleanliness"] - 0.75 * hours)
    state["comfort"] = max(0, state["comfort"] - 0.35 * hours)
    state["last_update"] = current
    return state


def get_care_state(player) -> dict:
    return dict(update_care_over_time(player))


OUTING_EFFECTS = {
    "walk": {"hunger": 3, "boredom": -12, "cleanliness": -4, "fatigue": 5,
             "trace": "산책에서 묻혀 온 잔먼지가 다리 끝에 조금 남아 있습니다."},
    "fishing": {"hunger": 4, "boredom": -10, "cleanliness": -9, "fatigue": 7,
                "trace": "거미 다리와 복부 아래쪽에 물기가 마른 자국이 있고 희미한 물비린내가 남아 있습니다."},
    "gathering": {"hunger": 4, "boredom": -7, "cleanliness": -7, "fatigue": 7,
                  "trace": "다리 관절 사이에 흙가루와 잘게 부서진 잎 조각이 끼어 있습니다."},
    "woodcut": {"hunger": 5, "boredom": -6, "cleanliness": -8, "fatigue": 9,
                "trace": "다리와 복부 아래에 옅은 톱밥과 나무 껍질 가루가 붙어 있습니다."},
    "adventure": {"hunger": 6, "boredom": -9, "cleanliness": -10, "fatigue": 11,
                  "trace": "밖을 오래 돌아다닌 듯 다리 끝과 복부 아래에 길먼지와 마른 흙자국이 남아 있습니다."},
    "battle": {"hunger": 7, "boredom": -8, "cleanliness": -14, "fatigue": 14,
               "trace": "전투 뒤의 먼지와 마른 얼룩이 거미 다리와 복부 가장자리에 남아 있습니다."},
    "flee": {"hunger": 5, "boredom": -5, "cleanliness": -11, "fatigue": 12,
             "trace": "급하게 빠져나온 흔적인지 다리 끝마다 흙과 먼지가 거칠게 묻어 있습니다."},
}


def apply_outing_effect(player, kind: str, *, trace: str | None = None) -> dict:
    """Apply one completed outing to Churider's persistent home-care state."""
    effect = OUTING_EFFECTS.get(kind)
    if not effect:
        return {}
    state = update_care_over_time(player)
    state["hunger"] = min(100, state["hunger"] + effect.get("hunger", 0))
    state["boredom"] = max(0, min(100, state["boredom"] + effect.get("boredom", 0)))
    state["cleanliness"] = max(0, min(100, state["cleanliness"] + effect.get("cleanliness", 0)))
    player.fatigue = max(0, min(100, player.fatigue + effect.get("fatigue", 0)))
    traces = state.setdefault("traces", [])
    traces.append({"kind": kind, "text": trace or effect.get("trace", ""), "at": time.time()})
    state["traces"] = traces[-4:]
    return {
        "kind": kind,
        "hunger": effect.get("hunger", 0),
        "boredom": effect.get("boredom", 0),
        "cleanliness": effect.get("cleanliness", 0),
        "fatigue": effect.get("fatigue", 0),
        "trace": state["traces"][-1]["text"],
    }


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
                "message":  f"아직 쓰다듬기 보상 쿨타임입니다. ({mins}분 {secs}초 남음)",
            }

        gain_condition = random.randint(5, 10)
        gain_stability = random.randint(3, 5)
        player.condition = min(100, player.condition + gain_condition)
        player.stability = min(100, player.stability + gain_stability)
        state = update_care_over_time(player)
        state["comfort"] = min(100, state["comfort"] + random.randint(5, 9))
        player._flags["last_pet_time"] = now

        lines = [
            "손길을 따라 고개를 조금 기울입니다. 🐾",
            "어깨의 힘이 풀리고 앞다리가 천천히 접힙니다. 🐾",
            "손바닥 쪽으로 머리를 기대며 가만히 있습니다. ✨",
            "표정은 태연하지만 거미 다리는 한층 편하게 접혀 있습니다. 🎶",
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
                "message": f"[{item.get('name', snack_id)}]이(가) 없습니다.",
            }

        item = ALL_ITEMS.get(snack_id) or SNACK_ITEMS.get(snack_id, {})
        if not item or item.get("type") != "snack":
            return {"success": False, "message": "간식으로 먹일 수 없는 아이템입니다."}

        effect = item.get("effect", {})
        player.remove_hyness_item(snack_id)
        state = update_care_over_time(player)
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
            f"[{item.get('name', snack_id)}]을(를) 받아 들고 금세 먹습니다. 🍴",
            f"[{item.get('name', snack_id)}]을(를) 먹고 입가를 닦으며 자리를 고쳐 앉습니다. 😊",
            f"[{item.get('name', snack_id)}]을(를) 먹는 동안 앞다리가 음식 쪽으로 조금씩 모입니다. ✨",
        ]
        return {
            "success": True,
            "message": random.choice(lines),
            "changes": changes,
            "item_name": item.get("name", snack_id),
        }

    def available_foods(self, player) -> list[tuple[str, int, dict]]:
        """Portable real foods Churider can be fed: cooked dishes, fish, groceries."""
        from items import ALL_ITEMS, COOKED_DISHES, FISH_ITEMS, GROCERIES
        edible_ids = set(COOKED_DISHES) | set(FISH_ITEMS) | set(GROCERIES)
        result = []
        for item_id, count in getattr(player, "inventory", {}).items():
            if count > 0 and item_id in edible_ids:
                result.append((item_id, count, ALL_ITEMS.get(item_id, {})))
        return result

    def feed_food(self, player, item_id: str) -> dict:
        from items import ALL_ITEMS, COOKED_DISHES, FISH_ITEMS, GROCERIES
        edible_ids = set(COOKED_DISHES) | set(FISH_ITEMS) | set(GROCERIES)
        item = ALL_ITEMS.get(item_id, {})
        if item_id not in edible_ids:
            return {"success": False, "message": "츄라이더에게 먹일 수 있는 음식이 아닙니다."}
        if getattr(player, "inventory", {}).get(item_id, 0) <= 0:
            return {"success": False, "message": f"[{item.get('name', item_id)}]이(가) 가방에 없습니다."}
        if not player.remove_item(item_id, 1):
            return {"success": False, "message": "먹을 것을 꺼내지 못했습니다."}

        state = update_care_over_time(player)
        if item_id in COOKED_DISHES:
            hunger_drop = max(20, min(55, 22 + int(item.get("en", 0)) // 3))
            mood_gain = 4
            kind = "요리"
        elif item_id in FISH_ITEMS:
            hunger_drop = 24
            mood_gain = 6
            kind = "생선"
        else:
            hunger_drop = 16
            mood_gain = 2
            kind = "먹을거리"
        before = state["hunger"]
        state["hunger"] = max(0, state["hunger"] - hunger_drop)
        player.stability = min(100, player.stability + mood_gain)
        name = item.get("name", item_id)
        if kind == "생선":
            message = f"[{name}]을 내밀자 태연한 얼굴을 하면서도 앞다리가 먼저 두 걸음 다가옵니다. 금세 받아 먹습니다. 🕷️🐟"
        elif kind == "요리":
            message = f"[{name}] 냄새를 맡고 잠깐 들여다보더니 자리를 잡고 제대로 먹기 시작합니다. 🕷️🍽️"
        else:
            message = f"[{name}]을 받아 들고 한참 살펴본 뒤 천천히 먹습니다. 🕷️"
        return {
            "success": True,
            "message": message,
            "item_name": name,
            "hunger_recovery": round(before - state["hunger"], 1),
            "kind": kind,
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
                "message":  f"아직 놀아주기 쿨타임입니다. ({mins}분 {secs}초 남음)",
            }

        options = ["rock", "scissors", "paper"]
        bot_choice = random.choice(options)
        state = update_care_over_time(player)
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
                "츄라이더가 이겼습니다. 태연한 얼굴과 달리 앞다리가 들썩입니다. 🎉",
                "츄라이더가 이겼습니다. 거미 다리가 바닥을 가볍게 두드립니다. 🎊",
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
                "무승부입니다. 츄라이더가 바로 다음 손을 준비합니다. 😄",
                "무승부입니다. 앞다리가 다시 선택지 쪽으로 향합니다. 😊",
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
                "츄라이더가 졌습니다. 눈은 가늘어지고 앞다리는 다시 자세를 잡습니다. 😤",
                "츄라이더가 졌습니다. 잠깐 굳었다가 곧 다음 판을 준비합니다. 💪",
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
                "message": f"아직 몸과 다리 사이에 목욕 뒤 물기가 남아 있습니다. ({mins}분 {secs}초 남음)",
            }
        state = update_care_over_time(player)
        before = state["cleanliness"]
        state["cleanliness"] = min(100, before + random.randint(35, 55))
        state["wash_count"] += 1
        state["traces"] = []
        player.condition = min(100, player.condition + random.randint(1, 3))
        player._flags["last_wash_time"] = time.time()
        lines = [
            "욕조에 넣자 여덟 다리가 가장자리를 단단히 붙잡습니다. 복부부터 북북박박 씻기자 결국 체념한 얼굴이 됩니다. 🛁",
            "거품을 잔뜩 내서 다리 사이까지 북북 씻깁니다. 츄라이더는 죽을상으로 쳐다보지만 몸은 아주 깨끗해집니다. 🫧",
            "욕조 밖으로 빠져나가려는 다리를 하나씩 다시 넣어 가며 북북박박 씻깁니다. 🕷️🛁",
        ]
        if state["wash_count"] >= 3:
            lines.append("욕조를 보자 도망칠지 잠깐 고민하더니 먼저 앞다리 두 개를 걸칩니다. 어차피 잡힐 것을 아는 눈치입니다. 🕷️🫧")
        return {"success": True, "message": random.choice(lines), "cleanliness_gain": state["cleanliness"] - before}

    # ── 쉬게 하기 ─────────────────────────────────────────────────────────
    def get_rest_status(self, player) -> dict:
        state = update_care_over_time(player)
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
        state = update_care_over_time(player)
        now = time.time()
        state["rest_started_at"] = now
        state["rest_until"] = now + self.REST_DURATION
        state["rest_count"] += 1
        state["last_rest_summary"] = ""
        return {
            "success": True,
            "remaining": self.REST_DURATION,
            "message": "책장 뒤 담요와 실 사이에 몸을 접습니다. 앞다리부터 하나씩 힘이 풀리더니 곧 눈을 감습니다. 🕷️💤",
        }

    def finish_rest(self, player, *, wake_early: bool = False) -> dict:
        state = update_care_over_time(player)
        status = self.get_rest_status(player)
        if not status.get("active"):
            return {"success": False, "message": "지금은 쉬고 있지 않습니다."}
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
            msg = "조심히 깨우자 츄라이더가 눈을 가늘게 뜨고 앞다리를 다시 펼칩니다. 조금은 쉬었지만 아직 잠기운이 남아 있습니다."
        else:
            msg = "푹 쉬고 난 츄라이더가 몸을 길게 펴며 여덟 다리를 하나씩 바닥에 디딥니다."
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
            return {"success": False, "message": "제작 레시피가 없습니다."}

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
                "message": "재료가 부족합니다.\n" + "\n".join(f"  ✗ {m}" for m in missing),
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
            return {"success": False, "message": "제작 레시피가 없습니다."}

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
                "message": "재료가 부족합니다.\n" + "\n".join(f"  ✗ {m}" for m in missing),
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
