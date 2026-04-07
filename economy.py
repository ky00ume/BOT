"""economy.py — 재화 중재 계층 (Economy Layer)

모든 gold/exp/item 변동을 단일 경로로 처리하는 중재자 모듈.
모든 메서드는 transaction_log.tx_log를 호출하여 [LOG: TRANSACTION]을 자동 기록합니다.

REMEDIATION_PLAN 2-C / 5-C 적용:
    - pay_reward / deduct 가 스냅샷 기반 롤백으로 부분 실패를 방지한다.
    - 과거에는 ``from player import check_level_up`` 을 함수 내부에서 호출해
      순환 의존을 임시로 회피했으나, 이제는 모듈 최상단에서 import 한다.
"""
from typing import Dict, Optional

from player import Player, check_level_up
from transaction_log import tx_log
from utils.exceptions import InsufficientResourceError, InventoryFullError
from utils.logger import setup_logger

logger = setup_logger('economy')


class Economy:
    """gold/exp/item 변동의 단일 진입점."""

    def __init__(self, player: Player) -> None:
        self.player = player

    # ------------------------------------------------------------------ utils

    def _name(self) -> str:
        return getattr(self.player, "name", "unknown")

    def _snapshot(self) -> Dict[str, object]:
        """롤백에 필요한 최소 상태 스냅샷."""
        return {
            "gold": getattr(self.player, "gold", 0),
            "exp": getattr(self.player, "exp", 0.0),
            "inventory": dict(getattr(self.player, "inventory", {}) or {}),
        }

    def _restore(self, snapshot: Dict[str, object]) -> None:
        """스냅샷으로 플레이어 상태를 되돌린다."""
        self.player.gold = snapshot["gold"]  # type: ignore[assignment]
        # exp 는 속성이 없을 수도 있으므로 setattr 로 처리.
        setattr(self.player, "exp", snapshot["exp"])
        self.player.inventory = dict(snapshot["inventory"])  # type: ignore[arg-type]

    # ------------------------------------------------------------ pay_reward

    def pay_reward(
        self,
        source: str,
        gold: int = 0,
        exp: float = 0.0,
        items: Optional[Dict[str, int]] = None,
    ) -> None:
        """보상 지급 — 골드·EXP·아이템을 원자적으로 지급한다.

        구현 포인트:
            1) 인벤토리 여유 사전 검증 (슬롯 초과 예측)
            2) 스냅샷 저장
            3) gold → exp → items 순으로 적용
            4) 실패 시 스냅샷으로 복원 후 재-raise

        Raises:
            InventoryFullError: 새 아이템이 인벤토리에 들어가지 못할 때.
            Exception: 그 외 예외 시 상태를 복구한 뒤 재-raise.
        """
        logger.info(
            "보상 지급 시작: source=%s, gold=%s, exp=%s, items=%s",
            source, gold, exp, items,
        )

        # 1) 사전 검증: 새 슬롯이 필요한 아이템이 몇 개인지 계산해 수용 가능한지 체크.
        if items:
            try:
                used, max_slots = self.player.inventory_check()
            except Exception:  # inventory_check 미지원 플레이어 더미/테스트 대비
                used, max_slots = len(self.player.inventory), 9999
            current_inv = self.player.inventory or {}
            new_unique = sum(1 for iid in items if iid not in current_inv)
            if used + new_unique > max_slots:
                raise InventoryFullError(
                    f"인벤토리 슬롯 부족: {used}/{max_slots}, 추가 필요={new_unique}"
                )

        # 2) 스냅샷
        snapshot = self._snapshot()
        changes: Dict[str, object] = {}

        try:
            if gold:
                self.player.gold += gold
                changes["gold"] = gold
            if exp:
                self.player.exp = getattr(self.player, "exp", 0.0) + exp
                changes["exp"] = exp
            if items:
                for item_id, count in items.items():
                    if not self.player.add_item(item_id, count):
                        raise InventoryFullError(
                            f"아이템 추가 실패: item_id={item_id}, count={count}"
                        )
                    changes[item_id] = count

            tx_log.log(self._name(), "TRANSACTION", source, "보상 지급", changes)

            if exp:
                self._last_level_ups = check_level_up(self.player)

            logger.info(
                "보상 지급 완료: player=%s, changes=%s", self._name(), changes
            )
        except Exception as e:
            self._restore(snapshot)
            logger.error(
                "보상 지급 실패, 스냅샷으로 롤백됨: source=%s, 오류=%s",
                source, e, exc_info=True,
            )
            raise

    # ---------------------------------------------------------------- deduct

    def deduct(
        self,
        source: str,
        gold: int = 0,
        items: Optional[Dict[str, int]] = None,
    ) -> None:
        """차감 — 골드·아이템을 원자적으로 제거한다.

        구현 포인트:
            1) 모든 자원이 충분한지 먼저 검증 (부분 차감 방지)
            2) 스냅샷 저장 후 차감
            3) 실패 시 스냅샷으로 복원

        Raises:
            InsufficientResourceError: 골드 또는 아이템이 부족할 때.
        """
        logger.info(
            "차감 시작: source=%s, gold=%s, items=%s", source, gold, items,
        )

        # 1) 사전 검증
        if gold > 0 and getattr(self.player, "gold", 0) < gold:
            raise InsufficientResourceError(
                f"골드 부족: 필요={gold}, 보유={getattr(self.player, 'gold', 0)}"
            )
        if items:
            for item_id, count in items.items():
                have = (self.player.inventory or {}).get(item_id, 0)
                if have < count:
                    raise InsufficientResourceError(
                        f"아이템 부족: {item_id} 필요={count}, 보유={have}"
                    )

        # 2) 스냅샷 후 적용
        snapshot = self._snapshot()
        changes: Dict[str, object] = {}
        try:
            if gold:
                self.player.gold -= gold
                changes["gold"] = -gold
            if items:
                for item_id, count in items.items():
                    if not self.player.remove_item(item_id, count):
                        # 사전 검증을 통과했으므로 이 분기는 방어적.
                        raise InsufficientResourceError(
                            f"아이템 제거 실패: {item_id}"
                        )
                    changes[item_id] = -count
            tx_log.log(self._name(), "TRANSACTION", source, "차감", changes)
            logger.info(
                "차감 완료: player=%s, changes=%s", self._name(), changes
            )
        except Exception as e:
            self._restore(snapshot)
            logger.error(
                "차감 실패, 스냅샷으로 롤백됨: source=%s, 오류=%s",
                source, e, exc_info=True,
            )
            raise

    # ----------------------------------------------------- single-item helpers

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
            logger.debug(f"아이템 추가 성공: item_id={item_id}, count={count}")
        else:
            logger.warning(
                f"아이템 추가 실패 (인벤토리 부족): item_id={item_id}, count={count}"
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
            logger.debug(f"아이템 제거 성공: item_id={item_id}, count={count}")
        else:
            logger.warning(
                f"아이템 제거 실패 (수량 부족): item_id={item_id}, count={count}"
            )
        return result

    def check_item(self, item_id: str, count: int = 1) -> bool:
        """아이템 보유 여부 확인 (변동 없음).

        Returns:
            count 개 이상 보유 중이면 True.
        """
        return self.player.inventory.get(item_id, 0) >= count
