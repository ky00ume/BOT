"""quest.py — 다비드 퀘스트 시스템"""
import time
from ui_theme import C, ansi, header_box, divider, GRADE_ICON_PLAIN

QUEST_DB = {
    "q001": {
        "name":         "초보 낚시꾼",
        "desc":         "붕어를 5마리 잡아오세요.",
        "type":         "collect",
        "target_item":  "fs_carp_01",
        "target_count": 5,
        "reward_gold":  200,
        "reward_contrib": 30,
        "reward_title": "낚시 견습생",
        "npc":          "피터",
    },
    "q002": {
        "name":         "대장장이의 부탁",
        "desc":         "철 주괴를 3개 만들어 오세요.",
        "type":         "collect",
        "target_item":  "iron_bar",
        "target_count": 3,
        "reward_gold":  500,
        "reward_contrib": 50,
        "reward_title": None,
        "npc":          "크람",
    },
    "q003": {
        "name":         "몬스터 퇴치",
        "desc":         "방울숲에서 몬스터를 10마리 처치하세요.",
        "type":         "kill",
        "target_count": 10,
        "reward_gold":  350,
        "reward_contrib": 40,
        "reward_title": None,
        "npc":          "그레고",
    },
    "q004": {
        "name":         "약초상의 의뢰",
        "desc":         "약초를 10개 모아오세요.",
        "type":         "collect",
        "target_item":  "herb",
        "target_count": 10,
        "reward_gold":  150,
        "reward_contrib": 20,
        "reward_title": None,
        "npc":          "레이나",
    },
    "q005": {
        "name":         "전설의 물고기",
        "desc":         "황금장어를 1마리 잡아오세요.",
        "type":         "collect",
        "target_item":  "fs_gold_eel_01",
        "target_count": 1,
        "reward_gold":  2000,
        "reward_contrib": 100,
        "reward_title": "전설의 낚시꾼",
        "npc":          "피터",
    },
}


class QuestManager:
    def __init__(self, player):
        self.player           = player
        self.active_quests    = {}   # quest_id: {"progress": int, "accepted_at": float}
        self.completed_quests = set()

    def list_quests(self) -> str:
        lines = [header_box("📋 퀘스트 목록")]

        available = [
            (qid, q) for qid, q in QUEST_DB.items()
            if qid not in self.completed_quests and qid not in self.active_quests
        ]
        active = [(qid, q) for qid, q in QUEST_DB.items() if qid in self.active_quests]
        done   = [(qid, q) for qid, q in QUEST_DB.items() if qid in self.completed_quests]

        if active:
            lines.append(f"\n  {C.CYAN}── 진행 중 ──{C.R}")
            for qid, q in active:
                prog  = self.active_quests[qid]["progress"]
                total = q.get("target_count", 1)
                lines.append(f"  {C.WHITE}[{qid}] {q['name']}{C.R}  {prog}/{total}")
                lines.append(f"    {C.DARK}{q['desc']}{C.R}")

        if available:
            lines.append(f"\n  {C.GREEN}── 수락 가능 ──{C.R}")
            for qid, q in available:
                lines.append(f"  {C.WHITE}[{qid}] {q['name']}{C.R}  +{q['reward_gold']}G")
                lines.append(f"    {C.DARK}{q['desc']}{C.R}")
                lines.append(f"    {C.GREEN}/퀘스트수락 {qid}{C.R}")

        if done:
            lines.append(f"\n  {C.DARK}── 완료됨 ──{C.R}")
            for qid, q in done:
                lines.append(f"  {C.DARK}✔ [{qid}] {q['name']}{C.R}")

        if not available and not active and not done:
            lines.append(f"  {C.DARK}현재 퀘스트가 없슴미댜.{C.R}")

        lines.append(divider())
        return ansi("\n".join(lines))

    def accept_quest(self, quest_id: str) -> str:
        if quest_id not in QUEST_DB:
            return ansi(f"  {C.RED}✖ [{quest_id}]은(는) 존재하지 않는 퀘스트임미댜!{C.R}")
        if quest_id in self.completed_quests:
            return ansi(f"  {C.RED}✖ 이미 완료한 퀘스트임미댜!{C.R}")
        if quest_id in self.active_quests:
            return ansi(f"  {C.RED}✖ 이미 진행 중인 퀘스트임미댜!{C.R}")

        q = QUEST_DB[quest_id]
        self.active_quests[quest_id] = {"progress": 0, "accepted_at": time.time()}
        return ansi(
            f"  {C.GREEN}✔ 퀘스트 [{q['name']}] 수락!{C.R}\n"
            f"  {C.DARK}{q['desc']}{C.R}"
        )

    def check_progress(self, quest_id: str) -> str:
        if quest_id not in QUEST_DB:
            return ansi(f"  {C.RED}✖ 존재하지 않는 퀘스트임미댜!{C.R}")
        if quest_id not in self.active_quests:
            return ansi(f"  {C.RED}✖ 수락하지 않은 퀘스트임미댜!{C.R}")

        q     = QUEST_DB[quest_id]
        prog  = self.active_quests[quest_id]["progress"]
        total = q.get("target_count", 1)
        return ansi(
            f"  {C.WHITE}[{q['name']}]{C.R}  {prog}/{total}\n"
            f"  {C.DARK}{q['desc']}{C.R}"
        )

    def complete_quest(self, quest_id: str) -> str:
        if quest_id not in QUEST_DB:
            return ansi(f"  {C.RED}✖ 존재하지 않는 퀘스트임미댜!{C.R}")
        if quest_id not in self.active_quests:
            return ansi(f"  {C.RED}✖ 수락하지 않은 퀘스트임미댜!{C.R}")
        if quest_id in self.completed_quests:
            return ansi(f"  {C.RED}✖ 이미 완료한 퀘스트임미댜!{C.R}")

        q    = QUEST_DB[quest_id]
        prog = self.active_quests[quest_id]["progress"]

        # 수집 퀘스트: 아이템 보유 확인
        if q["type"] == "collect":
            target_item  = q.get("target_item")
            target_count = q.get("target_count", 1)
            have         = self.player.inventory.get(target_item, 0)
            if have < target_count:
                from items import ALL_ITEMS
                item_name = ALL_ITEMS.get(target_item, {}).get("name", target_item)
                return ansi(
                    f"  {C.RED}✖ [{item_name}] 이(가) {target_count}개 필요함미댜! (보유: {have}){C.R}"
                )
            self.player.remove_item(target_item, target_count)

        elif q["type"] == "kill":
            target_count = q.get("target_count", 1)
            if prog < target_count:
                return ansi(
                    f"  {C.RED}✖ 아직 목표 달성 못 함미댜! ({prog}/{target_count}){C.R}"
                )

        # 보상
        gold = q.get("reward_gold", 0)
        self.player.gold += gold

        contrib = q.get("reward_contrib", 0)
        try:
            from village import village_manager
            village_manager.add_contribution(contrib)
        except Exception:
            pass

        title = q.get("reward_title")
        if title and hasattr(self.player, "titles"):
            if title not in self.player.titles:
                self.player.titles.append(title)

        del self.active_quests[quest_id]
        self.completed_quests.add(quest_id)

        lines = [
            header_box("✅ 퀘스트 완료!"),
            f"  {C.WHITE}[{q['name']}]{C.R}",
            f"  {C.GOLD}+{gold:,}G{C.R}  기여도 +{contrib}",
        ]
        if title:
            lines.append(f"  {C.PINK}칭호 획득: [{title}]{C.R}")
        return ansi("\n".join(lines))

    def update_kill_count(self, count: int = 1):
        """진행 중인 kill 퀘스트 진행도를 갱신합니다."""
        for qid, info in list(self.active_quests.items()):
            q = QUEST_DB.get(qid)
            if q and q.get("type") == "kill":
                info["progress"] = min(info["progress"] + count, q.get("target_count", 1))

    def update_collect_count(self, item_id: str, count: int = 1):
        """진행 중인 collect 퀘스트 진행도를 갱신합니다."""
        for qid, info in list(self.active_quests.items()):
            q = QUEST_DB.get(qid)
            if q and q.get("type") == "collect" and q.get("target_item") == item_id:
                info["progress"] = min(info["progress"] + count, q.get("target_count", 1))

    def to_dict(self) -> dict:
        return {
            "active_quests":    self.active_quests,
            "completed_quests": list(self.completed_quests),
        }

    def from_dict(self, data: dict):
        self.active_quests    = data.get("active_quests",    {})
        self.completed_quests = set(data.get("completed_quests", []))
        return self
