"""economy.py — 재화 중재 계층 (Economy Layer)

모든 gold/exp/item 변동을 단일 경로로 처리하는 중재자 모듈.
모든 메서드는 transaction_log.tx_log를 호출하여 [LOG: TRANSACTION]을 자동 기록합니다.
"""
from transaction_log import tx_log


class Economy:
    """gold/exp/item 변동의 단일 진입점."""

    def __init__(self, player):
        self.player = player

    def _name(self) -> str:
        return getattr(self.player, "name", "unknown")

    def pay_reward(
        self,
        source: str,
        gold: int = 0,
        exp: float = 0,
        items: dict = None,
    ):
        """보상 지급 — 골드·EXP 추가, 아이템 추가 + 자동 트랜잭션 로그.

        Args:
            source: 지급 원인 (예: "알바:다몬", "퀘스트:허브 채집")
            gold: 지급할 골드 양
            exp: 지급할 EXP 양
            items: {item_id: count} 형태의 지급 아이템 dict
        """
        changes: dict = {}
        if gold:
            self.player.gold += gold
            changes["gold"] = gold
        if exp:
            self.player.exp = getattr(self.player, "exp", 0.0) + exp
            changes["exp"] = exp
        if items:
            for item_id, count in items.items():
                self.player.add_item(item_id, count)
                changes[item_id] = count
        tx_log.log(self._name(), "TRANSACTION", source, "보상 지급", changes)

    def deduct(
        self,
        source: str,
        gold: int = 0,
        items: dict = None,
    ):
        """차감 — 골드·아이템 제거 + 자동 트랜잭션 로그.

        Args:
            source: 차감 원인 (예: "구매:철광석", "알바:실렌")
            gold: 차감할 골드 양
            items: {item_id: count} 형태의 차감 아이템 dict
        """
        changes: dict = {}
        if gold:
            self.player.gold -= gold
            changes["gold"] = -gold
        if items:
            for item_id, count in items.items():
                self.player.remove_item(item_id, count)
                changes[item_id] = -count
        tx_log.log(self._name(), "TRANSACTION", source, "차감", changes)

    def add_item(self, source: str, item_id: str, count: int = 1) -> bool:
        """아이템 추가 + 로그.

        Returns:
            인벤토리 공간이 있어 추가 성공하면 True, 실패하면 False.
        """
        result = self.player.add_item(item_id, count)
        if result:
            tx_log.log(
                self._name(),
                "TRANSACTION",
                source,
                f"아이템 추가: {item_id}",
                {item_id: count},
            )
        return result

    def remove_item(self, source: str, item_id: str, count: int = 1) -> bool:
        """아이템 제거 + 로그.

        Returns:
            아이템이 충분해 제거 성공하면 True, 실패하면 False.
        """
        result = self.player.remove_item(item_id, count)
        if result:
            tx_log.log(
                self._name(),
                "TRANSACTION",
                source,
                f"아이템 제거: {item_id}",
                {item_id: -count},
            )
        return result

    def check_item(self, item_id: str, count: int = 1) -> bool:
        """아이템 보유 여부 확인 (변동 없음).

        Returns:
            count 개 이상 보유 중이면 True.
        """
        return self.player.inventory.get(item_id, 0) >= count
