"""quest.py — 알바/의뢰 퀘스트 시스템 (전면 재설계)"""
import time
from ui_theme import C, ansi, header_box, divider, GRADE_ICON_PLAIN

QUEST_DB = {
    # ── 다몬 (대장장이) ──────────────────────────────────────────────────────
    "q_damion_collect_easy": {
        "name":         "대장장이의 소소한 부탁",
        "npc":          "다몬",
        "type":         "collect",
        "difficulty":   "easy",
        "target_item":  "iron_ore",
        "target_count": 5,
        "reward_gold":  300,
        "reward_exp":   50,
        "reward_item":  None,
        "desc":         "광산에서 철광석을 5개 캐와 다오.",
    },
    "q_damion_collect_normal": {
        "name":         "미스릴 광석 확보",
        "npc":          "다몬",
        "type":         "collect",
        "difficulty":   "normal",
        "target_item":  "mithril_ore",
        "target_count": 3,
        "reward_gold":  700,
        "reward_exp":   100,
        "reward_item":  "iron_bar",
        "desc":         "소금광산 깊은 곳에서 미스릴 광석을 3개 캐와라.",
    },
    "q_damion_collect_hard": {
        "name":         "전설의 광석 의뢰",
        "npc":          "다몬",
        "type":         "collect",
        "difficulty":   "hard",
        "target_item":  "orichalcum_ore",
        "target_count": 2,
        "reward_gold":  2000,
        "reward_exp":   300,
        "reward_item":  "mithril_bar",
        "desc":         "오리할콘 광석을 2개 구해와라. 매우 위험한 깊은 광산에서만 나온다.",
    },
    "q_damion_kill_easy": {
        "name":         "광산 정리",
        "npc":          "다몬",
        "type":         "kill",
        "difficulty":   "easy",
        "target_count": 5,
        "reward_gold":  250,
        "reward_exp":   40,
        "reward_item":  None,
        "desc":         "방울숲에서 몬스터 5마리를 처치해 재료를 구해와라.",
    },
    "q_damion_kill_normal": {
        "name":         "동굴 정벌",
        "npc":          "다몬",
        "type":         "kill",
        "difficulty":   "normal",
        "target_count": 10,
        "reward_gold":  600,
        "reward_exp":   100,
        "reward_item":  "copper_bar",
        "desc":         "고블린 동굴에서 몬스터 10마리를 물리쳐라.",
    },
    "q_damion_kill_hard": {
        "name":         "광산의 악몽",
        "npc":          "다몬",
        "type":         "kill",
        "difficulty":   "hard",
        "target_count": 20,
        "reward_gold":  1500,
        "reward_exp":   250,
        "reward_item":  "iron_bar",
        "desc":         "소금광산에서 언데드 20마리를 처치해라.",
    },
    "q_damion_deliver_easy": {
        "name":         "편지 전달",
        "npc":          "다몬",
        "type":         "deliver",
        "difficulty":   "normal",
        "deliver_to":   "브룩샤",
        "quest_item":   "sq_letter_from_damon",
        "reward_gold":  600,
        "reward_exp":   100,
        "reward_item":  "iron_bar",
        "desc":         "다몬의 편지를 브룩샤에게 전달하고 돌아와.",
    },
    "q_damion_deliver_normal": {
        "name":         "귀한 도면 전달",
        "npc":          "다몬",
        "type":         "deliver",
        "difficulty":   "normal",
        "deliver_to":   "카엘릭",
        "quest_item":   "sq_blueprint_damion",
        "reward_gold":  800,
        "reward_exp":   120,
        "reward_item":  "copper_bar",
        "desc":         "다몬이 그린 무기 도면을 카엘릭에게 전달해라.",
    },
    "q_damion_deliver_hard": {
        "name":         "비밀 주문서 배달",
        "npc":          "다몬",
        "type":         "deliver",
        "difficulty":   "hard",
        "deliver_to":   "오멜룸",
        "quest_item":   "sq_secret_order_damion",
        "reward_gold":  1800,
        "reward_exp":   280,
        "reward_item":  "mithril_bar",
        "desc":         "다몬의 비밀 주문서를 오멜룸에게 조용히 전달해라. 아무도 몰라야 한다.",
    },

    # ── 브룩샤 (요리사) ──────────────────────────────────────────────────────
    "q_brooksha_collect_easy": {
        "name":         "신선한 버섯 구해줘",
        "npc":          "브룩샤",
        "type":         "collect",
        "difficulty":   "easy",
        "target_item":  "mushroom",
        "target_count": 8,
        "reward_gold":  200,
        "reward_exp":   35,
        "reward_item":  "simple_soup",
        "desc":         "버섯 군락지에서 버섯을 8개 채집해 가져와요.",
    },
    "q_brooksha_collect_normal": {
        "name":         "희귀 약초 재료",
        "npc":          "브룩샤",
        "type":         "collect",
        "difficulty":   "normal",
        "target_item":  "healing_herb",
        "target_count": 5,
        "reward_gold":  500,
        "reward_exp":   90,
        "reward_item":  "mushroom_soup",
        "desc":         "힐링허브를 5개 채집해 가져오면 특제 요리를 드릴게요.",
    },
    "q_brooksha_collect_hard": {
        "name":         "전설의 식재료",
        "npc":          "브룩샤",
        "type":         "collect",
        "difficulty":   "hard",
        "target_item":  "pine_mushroom",
        "target_count": 3,
        "reward_gold":  1500,
        "reward_exp":   250,
        "reward_item":  "meat_stew",
        "desc":         "귀한 송이버섯을 3개 구해와요. 특별한 스튜를 만들어줄게요.",
    },
    "q_brooksha_kill_easy": {
        "name":         "신선한 고기 확보",
        "npc":          "브룩샤",
        "type":         "kill",
        "difficulty":   "easy",
        "target_count": 5,
        "reward_gold":  180,
        "reward_exp":   30,
        "reward_item":  "potato_pancake",
        "desc":         "방울숲에서 몬스터를 5마리 잡고 고기를 확보해와요.",
    },
    "q_brooksha_kill_normal": {
        "name":         "독 재료 수집",
        "npc":          "브룩샤",
        "type":         "kill",
        "difficulty":   "normal",
        "target_count": 8,
        "reward_gold":  450,
        "reward_exp":   80,
        "reward_item":  "tofu",
        "desc":         "독버섯 주변 몬스터를 8마리 처치해요. 재료가 필요해요.",
    },
    "q_brooksha_kill_hard": {
        "name":         "보스 고기 파티",
        "npc":          "브룩샤",
        "type":         "kill",
        "difficulty":   "hard",
        "target_count": 15,
        "reward_gold":  1200,
        "reward_exp":   200,
        "reward_item":  "eel_special",
        "desc":         "소금광산 몬스터 15마리를 잡아요. 파티 요리 재료가 필요해요.",
    },
    "q_brooksha_deliver_easy": {
        "name":         "레시피 전달",
        "npc":          "브룩샤",
        "type":         "deliver",
        "difficulty":   "easy",
        "deliver_to":   "알피라",
        "quest_item":   "sq_recipe_brooksha",
        "reward_gold":  350,
        "reward_exp":   60,
        "reward_item":  "honey_milk",
        "desc":         "브룩샤의 특제 레시피를 알피라에게 전해줘요.",
    },
    "q_brooksha_deliver_normal": {
        "name":         "도시락 배달",
        "npc":          "브룩샤",
        "type":         "deliver",
        "difficulty":   "normal",
        "deliver_to":   "제블로어",
        "quest_item":   "sq_lunchbox_brooksha",
        "reward_gold":  550,
        "reward_exp":   90,
        "reward_item":  "mushroom_soup",
        "desc":         "제블로어에게 점심 도시락을 배달해요. 경비 순찰 중이에요.",
    },
    "q_brooksha_deliver_hard": {
        "name":         "비밀 식재료 조달",
        "npc":          "브룩샤",
        "type":         "deliver",
        "difficulty":   "hard",
        "deliver_to":   "오멜룸",
        "quest_item":   "sq_special_ingredient",
        "reward_gold":  1400,
        "reward_exp":   230,
        "reward_item":  "meat_stew",
        "desc":         "오멜룸에게 특제 식재료를 비밀리에 받아와요.",
    },

    # ── 오멜룸 (약사) ────────────────────────────────────────────────────────
    "q_omelum_collect_easy": {
        "name":         "약초 채집 의뢰",
        "npc":          "오멜룸",
        "type":         "collect",
        "difficulty":   "easy",
        "target_item":  "herb",
        "target_count": 10,
        "reward_gold":  150,
        "reward_exp":   30,
        "reward_item":  None,
        "desc":         "야생 약초를 10개 채집해 가져오시오.",
    },
    "q_omelum_collect_normal": {
        "name":         "마나 허브 수집",
        "npc":          "오멜룸",
        "type":         "collect",
        "difficulty":   "normal",
        "target_item":  "mana_herb",
        "target_count": 5,
        "reward_gold":  500,
        "reward_exp":   90,
        "reward_item":  "con_potion_h",
        "desc":         "마나 허브를 5개 채집해 오시오. 포션 제조에 필요하오.",
    },
    "q_omelum_collect_hard": {
        "name":         "독초 수집 (위험)",
        "npc":          "오멜룸",
        "type":         "collect",
        "difficulty":   "hard",
        "target_item":  "poison_herb",
        "target_count": 3,
        "reward_gold":  1500,
        "reward_exp":   250,
        "reward_item":  "pot_potion",
        "desc":         "독초를 3개 수집해 오시오. 취급에 주의하시오.",
    },
    "q_omelum_kill_easy": {
        "name":         "독주머니 수거",
        "npc":          "오멜룸",
        "type":         "kill",
        "difficulty":   "easy",
        "target_count": 5,
        "reward_gold":  200,
        "reward_exp":   35,
        "reward_item":  None,
        "desc":         "방울숲 독 몬스터를 5마리 처치해 독 재료를 얻어오시오.",
    },
    "q_omelum_kill_normal": {
        "name":         "마력 결정 채취",
        "npc":          "오멜룸",
        "type":         "kill",
        "difficulty":   "normal",
        "target_count": 8,
        "reward_gold":  480,
        "reward_exp":   85,
        "reward_item":  "con_potion_h",
        "desc":         "마법 몬스터를 8마리 처치해 마력 결정을 모아오시오.",
    },
    "q_omelum_kill_hard": {
        "name":         "강력한 독소 채취",
        "npc":          "오멜룸",
        "type":         "kill",
        "difficulty":   "hard",
        "target_count": 15,
        "reward_gold":  1300,
        "reward_exp":   220,
        "reward_item":  "pot_potion",
        "desc":         "소금광산의 강력한 몬스터 15마리를 처치해 독소를 얻어오시오.",
    },
    "q_omelum_deliver_easy": {
        "name":         "약품 전달",
        "npc":          "오멜룸",
        "type":         "deliver",
        "difficulty":   "easy",
        "deliver_to":   "브룩샤",
        "quest_item":   "sq_medicine_omelum",
        "reward_gold":  300,
        "reward_exp":   50,
        "reward_item":  "con_potion_h",
        "desc":         "오멜룸이 조제한 약을 브룩샤에게 전달하시오.",
    },
    "q_omelum_deliver_normal": {
        "name":         "포션 견본 전달",
        "npc":          "오멜룸",
        "type":         "deliver",
        "difficulty":   "normal",
        "deliver_to":   "카엘릭",
        "quest_item":   "sq_potion_sample",
        "reward_gold":  600,
        "reward_exp":   100,
        "reward_item":  "con_potion_h",
        "desc":         "오멜룸의 포션 견본을 카엘릭에게 전달하시오.",
    },
    "q_omelum_deliver_hard": {
        "name":         "희귀 시약 조달",
        "npc":          "오멜룸",
        "type":         "deliver",
        "difficulty":   "hard",
        "deliver_to":   "게일의 환영",
        "quest_item":   "sq_rare_reagent",
        "reward_gold":  1600,
        "reward_exp":   270,
        "reward_item":  "pot_potion",
        "desc":         "게일의 환영에게 희귀 시약을 전달하고 답신을 받아오시오.",
    },

    # ── 카엘릭 (전투 교관) ──────────────────────────────────────────────────
    "q_kaelig_collect_easy": {
        "name":         "수련 재료 준비",
        "npc":          "카엘릭",
        "type":         "collect",
        "difficulty":   "easy",
        "target_item":  "gt_wood_01",
        "target_count": 10,
        "reward_gold":  200,
        "reward_exp":   50,
        "reward_item":  None,
        "desc":         "수련용 목재를 10개 모아와라.",
    },
    "q_kaelig_collect_normal": {
        "name":         "무기 재료 조달",
        "npc":          "카엘릭",
        "type":         "collect",
        "difficulty":   "normal",
        "target_item":  "iron_ore",
        "target_count": 8,
        "reward_gold":  550,
        "reward_exp":   100,
        "reward_item":  None,
        "desc":         "철광석 8개를 모아와라. 수련생들을 위한 무기가 필요하다.",
    },
    "q_kaelig_collect_hard": {
        "name":         "정예 훈련 재료",
        "npc":          "카엘릭",
        "type":         "collect",
        "difficulty":   "hard",
        "target_item":  "hardwood",
        "target_count": 5,
        "reward_gold":  1400,
        "reward_exp":   260,
        "reward_item":  None,
        "desc":         "단단한 목재 5개를 구해와라. 훈련 장비 제작에 필요하다.",
    },
    "q_kaelig_kill_easy": {
        "name":         "초급 전투 테스트",
        "npc":          "카엘릭",
        "type":         "kill",
        "difficulty":   "easy",
        "target_count": 5,
        "reward_gold":  250,
        "reward_exp":   60,
        "reward_item":  None,
        "desc":         "방울숲에서 몬스터 5마리를 처치해 전투 감각을 키워라.",
    },
    "q_kaelig_kill_normal": {
        "name":         "중급 전투 임무",
        "npc":          "카엘릭",
        "type":         "kill",
        "difficulty":   "normal",
        "target_count": 12,
        "reward_gold":  700,
        "reward_exp":   130,
        "reward_item":  None,
        "desc":         "고블린 동굴에서 몬스터 12마리를 처치해라.",
    },
    "q_kaelig_kill_hard": {
        "name":         "고급 전투 임무",
        "npc":          "카엘릭",
        "type":         "kill",
        "difficulty":   "hard",
        "target_count": 25,
        "reward_gold":  2000,
        "reward_exp":   400,
        "reward_item":  None,
        "desc":         "소금광산에서 몬스터 25마리를 처치해라. 실전 훈련이다.",
    },
    "q_kaelig_deliver_easy": {
        "name":         "훈련 보고서 전달",
        "npc":          "카엘릭",
        "type":         "deliver",
        "difficulty":   "easy",
        "deliver_to":   "제블로어",
        "quest_item":   "sq_training_report",
        "reward_gold":  300,
        "reward_exp":   55,
        "reward_item":  None,
        "desc":         "훈련 보고서를 제블로어에게 전달해라.",
    },
    "q_kaelig_deliver_normal": {
        "name":         "무기 점검 요청",
        "npc":          "카엘릭",
        "type":         "deliver",
        "difficulty":   "normal",
        "deliver_to":   "다몬",
        "quest_item":   "sq_weapon_check_order",
        "reward_gold":  650,
        "reward_exp":   110,
        "reward_item":  None,
        "desc":         "무기 점검 의뢰서를 다몬에게 가져가라.",
    },
    "q_kaelig_deliver_hard": {
        "name":         "기밀 전술 서류",
        "npc":          "카엘릭",
        "type":         "deliver",
        "difficulty":   "hard",
        "deliver_to":   "엘레라신",
        "quest_item":   "sq_tactical_doc",
        "reward_gold":  1700,
        "reward_exp":   290,
        "reward_item":  None,
        "desc":         "기밀 전술 서류를 엘레라신에게 전달해라. 절대 열어보지 말 것.",
    },
}


class QuestManager:
    def __init__(self, player):
        self.player           = player
        self.active_quests    = {}   # quest_id -> {"progress": N, "accepted_at": ts, "delivered": bool}
        self.completed_quests = set()
        self.failed_quests    = set()

    # ── 퀘스트 목록 조회 ──────────────────────────────────────────────────────
    def list_quests(self) -> str:
        lines = [header_box("📋 퀘스트 목록")]
        available = [(qid, q) for qid, q in QUEST_DB.items()
                     if qid not in self.completed_quests and qid not in self.active_quests]
        active    = [(qid, q) for qid, q in QUEST_DB.items() if qid in self.active_quests]
        done      = [(qid, q) for qid, q in QUEST_DB.items() if qid in self.completed_quests]

        if active:
            lines.append(f"\n  {C.CYAN}── 진행 중 ──{C.R}")
            for qid, q in active:
                info = self.active_quests[qid]
                prog  = info["progress"]
                total = q.get("target_count", 1)
                tp = q["type"]
                if tp == "deliver":
                    delivered = info.get("delivered", False)
                    state = "전달 완료 → 귀환 필요" if delivered else "전달 중"
                    lines.append(f"  {C.WHITE}[{qid}] {q['name']}{C.R}  [{tp}] {state}")
                else:
                    lines.append(f"  {C.WHITE}[{qid}] {q['name']}{C.R}  {prog}/{total}")
                lines.append(f"    {C.DARK}{q['desc']}{C.R}")

        if available:
            lines.append(f"\n  {C.GREEN}── 수락 가능 ──{C.R}")
            for qid, q in available:
                diff_mark = {"easy": "⬜", "normal": "🟨", "hard": "🟥"}.get(q.get("difficulty", "easy"), "⬜")
                lines.append(f"  {diff_mark} {C.WHITE}[{qid}] {q['name']}{C.R}  +{q['reward_gold']}G  NPC: {q['npc']}")
                lines.append(f"    {C.DARK}{q['desc']}{C.R}")

        if done:
            lines.append(f"\n  {C.DARK}── 완료됨 ──{C.R}")
            for qid, q in done:
                lines.append(f"  {C.DARK}✔ [{qid}] {q['name']}{C.R}")

        if not available and not active and not done:
            lines.append(f"  {C.DARK}현재 퀘스트가 없슴미댜.{C.R}")

        lines.append(divider())
        return ansi("\n".join(lines))

    # ── 수락 ──────────────────────────────────────────────────────────────────
    def accept_quest(self, quest_id: str) -> str:
        if quest_id not in QUEST_DB:
            return ansi(f"  {C.RED}✖ [{quest_id}]은(는) 존재하지 않는 퀘스트임미댜!{C.R}")
        if quest_id in self.completed_quests:
            return ansi(f"  {C.RED}✖ 이미 완료한 퀘스트임미댜!{C.R}")
        if quest_id in self.active_quests:
            return ansi(f"  {C.RED}✖ 이미 진행 중인 퀘스트임미댜!{C.R}")

        q = QUEST_DB[quest_id]
        # 전달형 퀘스트: quest_item을 인벤토리에 지급
        if q["type"] == "deliver":
            quest_item = q.get("quest_item")
            if quest_item:
                self.player.add_item(quest_item, 1)
        self.active_quests[quest_id] = {
            "progress": 0,
            "accepted_at": time.time(),
            "delivered": False,
        }
        return ansi(
            f"  {C.GREEN}✔ 퀘스트 [{q['name']}] 수락!{C.R}\n"
            f"  {C.DARK}{q['desc']}{C.R}"
        )

    # ── 완료 ──────────────────────────────────────────────────────────────────
    def complete_quest(self, quest_id: str) -> str:
        if quest_id not in QUEST_DB:
            return ansi(f"  {C.RED}✖ 존재하지 않는 퀘스트임미댜!{C.R}")
        if quest_id not in self.active_quests:
            return ansi(f"  {C.RED}✖ 수락하지 않은 퀘스트임미댜!{C.R}")
        if quest_id in self.completed_quests:
            return ansi(f"  {C.RED}✖ 이미 완료한 퀘스트임미댜!{C.R}")

        q    = QUEST_DB[quest_id]
        info = self.active_quests[quest_id]
        tp   = q["type"]

        if tp == "collect":
            target_item  = q.get("target_item")
            target_count = q.get("target_count", 1)
            have = self.player.inventory.get(target_item, 0)
            if have < target_count:
                from items import ALL_ITEMS
                item_name = ALL_ITEMS.get(target_item, {}).get("name", target_item)
                return ansi(
                    f"  {C.RED}✖ [{item_name}] 이(가) {target_count}개 필요함미댜! (보유: {have}){C.R}"
                )
            self.player.remove_item(target_item, target_count)

        elif tp == "kill":
            prog  = info["progress"]
            total = q.get("target_count", 1)
            if prog < total:
                return ansi(f"  {C.RED}✖ 아직 목표 달성 못 함미댜! ({prog}/{total}){C.R}")

        elif tp == "deliver":
            if not info.get("delivered"):
                return ansi(f"  {C.RED}✖ 아직 전달하지 않았슴미댜! 목표 NPC에게 먼저 가세요.{C.R}")

        gold = q.get("reward_gold", 0)
        exp  = q.get("reward_exp",  0)
        self.player.gold += gold
        self.player.exp  += exp

        reward_item = q.get("reward_item")
        item_msg = ""
        if reward_item:
            self.player.add_item(reward_item, 1)
            from items import ALL_ITEMS
            item_name = ALL_ITEMS.get(reward_item, {}).get("name", reward_item)
            item_msg = f"\n  {C.CYAN}📦 보상 아이템: {item_name}{C.R}"

        try:
            from village import village_manager
            village_manager.add_contribution(max(1, gold // 50))
        except Exception:
            pass

        del self.active_quests[quest_id]
        self.completed_quests.add(quest_id)

        return ansi(
            f"  {C.GREEN}✔ 퀘스트 완료: [{q['name']}]{C.R}\n"
            f"  {C.GOLD}+{gold:,}G  +{exp} EXP{C.R}{item_msg}"
        )

    # ── 포기 ──────────────────────────────────────────────────────────────────
    def abandon_quest(self, quest_id: str) -> str:
        if quest_id not in self.active_quests:
            return ansi(f"  {C.RED}✖ 진행 중인 퀘스트가 아님미댜!{C.R}")
        q = QUEST_DB.get(quest_id, {})
        if q.get("type") == "deliver":
            quest_item = q.get("quest_item")
            if quest_item and quest_item in self.player.inventory:
                self.player.remove_item(quest_item, 1)
        del self.active_quests[quest_id]
        self.failed_quests.add(quest_id)
        return ansi(f"  {C.GOLD}퀘스트 [{q.get('name', quest_id)}]을(를) 포기했슴미댜.{C.R}")

    # ── 전달형: 목표 NPC에게 전달 처리 ──────────────────────────────────────
    def deliver_to_npc(self, npc_name: str) -> str:
        """목표 NPC에게 전달했을 때 호출 (아르바이트 버튼 연동 용)."""
        results = []
        for qid, info in list(self.active_quests.items()):
            q = QUEST_DB.get(qid, {})
            if q.get("type") == "deliver" and q.get("deliver_to") == npc_name and not info.get("delivered"):
                quest_item = q.get("quest_item")
                if quest_item and quest_item in self.player.inventory:
                    self.player.remove_item(quest_item, 1)
                    info["delivered"] = True
                    results.append(
                        f"  {C.GREEN}✔ [{q['name']}] 전달 완료!{C.R} 의뢰자 [{q['npc']}]에게 돌아가세요."
                    )
        if not results:
            return ""
        return ansi("\n".join(results))

    # ── 카운터 업데이트 ──────────────────────────────────────────────────────
    def update_kill_count(self, count: int = 1):
        for qid, info in list(self.active_quests.items()):
            q = QUEST_DB.get(qid)
            if q and q.get("type") == "kill":
                info["progress"] = min(info["progress"] + count, q.get("target_count", 1))

    def update_collect_count(self, item_id: str, count: int = 1):
        for qid, info in list(self.active_quests.items()):
            q = QUEST_DB.get(qid)
            if q and q.get("type") == "collect" and q.get("target_item") == item_id:
                info["progress"] = min(info["progress"] + count, q.get("target_count", 1))

    # ── 직렬화 ───────────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "active_quests":    self.active_quests,
            "completed_quests": list(self.completed_quests),
            "failed_quests":    list(self.failed_quests),
        }

    def from_dict(self, data: dict):
        self.active_quests    = data.get("active_quests",    {})
        self.completed_quests = set(data.get("completed_quests", []))
        self.failed_quests    = set(data.get("failed_quests", []))
        return self
