"""quest_bridge.py — 퀘스트-채집 연동 브릿지

알바/의뢰가 인벤토리를 참조할 때 거치는 브릿지.
Economy를 경유하여 트랜잭션 로그가 자동 기록됩니다.
"""
import logging

from transaction_log import tx_log

logger = logging.getLogger(__name__)


class QuestBridge:
    """퀘스트/알바 완료 처리를 Economy를 통해 수행하는 브릿지."""

    def check_collect_progress(
        self, economy, item_id: str, required_count: int
    ) -> tuple:
        """아이템 보유량 확인.

        Returns:
            (보유량: int, 충족 여부: bool)
        """
        have = economy.player.inventory.get(item_id, 0)
        enough = have >= required_count
        return have, enough

    def complete_quest(self, economy, quest_data: dict) -> dict:
        """퀘스트 완료 처리: 아이템 차감 → Economy.pay_reward() → 로그.

        Args:
            economy: Economy 인스턴스
            quest_data: {
                "name": str,
                "items": {item_id: count},     # 차감할 아이템 (옵션)
                "reward_gold": int,
                "reward_exp": float,
                "reward_items": {item_id: count}  # 보상 아이템 (옵션)
            }

        Returns:
            {"gold": int, "exp": float, "items": dict}
        """
        quest_name = quest_data.get("name", "퀘스트")
        source = f"퀘스트:{quest_name}"

        items_to_deduct = quest_data.get("items", {})
        for item_id, count in items_to_deduct.items():
            economy.remove_item(source, item_id, count)

        gold = quest_data.get("reward_gold", 0)
        exp = quest_data.get("reward_exp", 0.0)
        reward_items = quest_data.get("reward_items", {}) or {}

        economy.pay_reward(source=source, gold=gold, exp=exp, items=reward_items or None)
        return {"gold": gold, "exp": exp, "items": reward_items}

    def complete_job(
        self, economy, job_data: dict, npc_name: str
    ) -> dict:
        """알바 완료 처리: 타입별(hunt/gather/deliver) 로직 → Economy.pay_reward() → 로그.

        Args:
            economy: Economy 인스턴스
            job_data: 알바 데이터 dict
            npc_name: NPC 이름

        Returns:
            {"gold": int, "exp": float, "items": dict}
        """
        source = f"알바:{npc_name}"
        job_type = job_data.get("type", "hunt")

        if job_type == "gather":
            target_item = job_data.get("target_item", "")
            target_count = job_data.get("target_count", 1)
            if target_item:
                economy.remove_item(source, target_item, target_count)

        gold = job_data.get("reward_gold", 0)
        exp = job_data.get("reward_exp", 0.0)
        items: dict = {}
        if job_data.get("reward_item"):
            items[job_data["reward_item"]] = 1

        economy.pay_reward(
            source=source, gold=gold, exp=exp, items=items or None
        )
        return {"gold": gold, "exp": exp, "items": items}


# 모듈 레벨 싱글톤
quest_bridge = QuestBridge()
